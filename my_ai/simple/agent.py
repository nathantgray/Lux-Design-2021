"""
working on:

creating city assignments for each unit. Need to make sure deligate() gets all units,
then send units to appropriate city.
This should be working but there is bug causing the worker to never move.
"""


import math, sys
import numpy as np
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate


from matplotlib.colors import ListedColormap, LinearSegmentedColormap

DIRECTIONS = Constants.DIRECTIONS
game_state: Game = None


class MapState:

    def __init__(self, gamemap, width, height, player, opponent):
        self.height = width
        self.width = height
        self.bd = gamemap
        self.player = player
        self.opponent = opponent
        self.bd_wood = np.zeros([height, width], np.int16)
        self.bd_coal = np.zeros([height, width], np.int16)
        self.bd_uranium = np.zeros([height, width], np.int16)
        self.start_pos = []

    def set_resources(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.bd[y][x].has_resource():
                    if self.bd[y][x].resource.type == 'wood':
                        self.bd_wood[y][x] = self.bd[y][x].resource.amount
                    elif self.bd[y][x].resource.type == 'coal':
                        self.bd_coal[y][x] = self.bd[y][x].resource.amount
                    elif self.bd[y][x].resource.type == 'uranium':
                        self.bd_uranium[y][x] = self.bd[y][x].resource.amount

    def binarise(self):
        self.bd_wood[self.bd_wood > 0] = 1
        self.bd_coal[self.bd_coal > 0] = 1
        self.bd_uranium[self.bd_uranium > 0] = 1

    def find_city(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.bd[y][x].citytile is not None:
                    self.start_pos.append((y, x))

    def get_resource_tiles(self, game_state):
        resource_tiles: list[Cell] = []
        for y in range(self.height):
            for x in range(self.width):
                cell = game_state.map.get_cell(x, y)
                if cell.has_resource():
                    resource_tiles.append(cell)
        return resource_tiles


class UnitControl:
    def __init__(self, unit, player):
        self.player = player
        self.unit = unit
        self.next_pos = None
        self.target = None
        self.tasks = []  # stack of tasks
        self.city = None

    def update(self, assignment, actions):
        self.city = assignment[self.unit.id]
        resource_tiles = get_resource_tiles(game_state)
        unit = self.unit
        actions.append(annotate.sidetext(f"start_{unit.id}"))
        if unit.is_worker() and unit.can_act():
            if unit.get_cargo_space_left() > 0:
                closest_resource_tile = get_closest_resource_tile(resource_tiles, unit, self.player)
                if closest_resource_tile is not None:
                    self.target = closest_resource_tile.pos
                    actions = self.goto_target(actions)
            else:
                # if unit is a worker and there is no cargo space left, and we have cities, lets return to them
                if len(self.player.cities) > 0:
                    if unit.id in assignment.keys():
                        actions.append(annotate.sidetext(f"send {unit.id}"))
                        dest_city = assignment[unit.id]
                        dest = get_closest_obj(unit.pos, dest_city.citytiles).pos
                        move_dir = unit.pos.direction_to(dest)
                        if dest_city.get_light_upkeep() < dest_city.fuel and self.player.city_tile_count < 2:  # build new city
                            if unit.can_build(game_map=game_state.map):
                                actions.append(unit.build_city())
                            else:
                                actions.append(unit.move(opposite_dir(move_dir)))
                        else:
                            actions.append(unit.move(move_dir))
                    else:
                        actions.append(annotate.sidetext("close_city"))
                        closest_city_tile = get_closest_city_tile(unit, self.player)
                        if closest_city_tile is not None:
                            city = self.player.cities[closest_city_tile.cityid]
                            dest = closest_city_tile.pos
                            move_dir = unit.pos.direction_to(dest)
                            if city.get_light_upkeep() < city.fuel:  # build new city
                                if unit.can_build(game_map=game_state.map):
                                    actions.append(unit.build_city())
                                else:
                                    actions.append(unit.move(opposite_dir(move_dir)))
                            else:
                                # print(closest_city_tile)
                                actions.append(annotate.line(
                                    dest.x, dest.y,
                                    unit.pos.x, unit.pos.y
                                ))

                                actions.append(unit.move(move_dir))
        pass

    def set_target(self):
        pass

    def goto_target(self, actions):
        clear_dir = [DIRECTIONS.NORTH, DIRECTIONS.EAST, DIRECTIONS.SOUTH, DIRECTIONS.WEST]
        move_dir = self.unit.pos.direction_to(self.target)
        self.next_pos = self.unit.pos.translate(move_dir, 1)
        next_cell = game_state.map.get_cell_by_pos(self.next_pos)
        while next_cell.citytile is not None:
            if next_cell.citytile.cityid != self.city.cityid:
                clear_dir.remove(move_dir)
                move_dir = clear_dir[0]
                self.next_pos = self.unit.pos.translate(move_dir, 1)
                next_cell = game_state.map.get_cell_by_pos(self.next_pos)

        actions.append(annotate.line(
            self.target.x, self.target.y,
            self.unit.pos.x, self.unit.pos.y
        ))
        actions.append(self.unit.move(move_dir))
        return actions



def setup(observation, game_state):
    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])

    actions = []
    return actions


def get_resource_tiles(game_state):
    width, height = game_state.map.width, game_state.map.height
    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
    return resource_tiles


def get_closest_city_tile(unit, player):
    closest_dist = math.inf
    closest_city_tile = None
    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            dist = city_tile.pos.distance_to(unit.pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_city_tile = city_tile
    return closest_city_tile


def get_closest_resource_tile(resource_tiles, unit, player):
    closest_resource_tile = None
    closest_dist = math.inf
    # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
    for resource_tile in resource_tiles:
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal(): continue
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium(): continue
        dist = resource_tile.pos.distance_to(unit.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_resource_tile = resource_tile
    return closest_resource_tile


def move_around_city_to():
    pass


def expand_city():
    pass


def opposite_dir(direction):
        if direction == DIRECTIONS.NORTH:
            return DIRECTIONS.SOUTH
        elif direction == DIRECTIONS.EAST:
            return DIRECTIONS.WEST
        elif direction == DIRECTIONS.SOUTH:
            return DIRECTIONS.NORTH
        elif direction == DIRECTIONS.WEST:
            return DIRECTIONS.EAST
        elif direction == DIRECTIONS.CENTER:
            return direction


def get_closest_obj(pos, obj_list):
    # for unit in player.units:
    closest_obj = None
    closest_dist = math.inf
    # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
    for obj in obj_list:
        dist = obj.pos.distance_to(pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_obj = obj
    return closest_obj


def delegate(player):
    assignment = {}
    free_units = player.units.copy()
    for city in player.cities.values():
        for city_tile in city.citytiles:
            if len(free_units) > 0:
                closest_unit = get_closest_obj(city_tile.pos, free_units)
                free_units.remove(closest_unit)
                assignment[closest_unit.id] = city

    return assignment


def agent(observation, configuration):
    global game_state
    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])

    actions = []
    # actions = setup(observation, game_state)

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    resource_tiles = get_resource_tiles(game_state)


    for city in player.cities.values():
        for city_tile in city.citytiles:
            if city_tile.can_act():
                x = city_tile.pos.x
                y = city_tile.pos.y
                actions.append(annotate.sidetext(f"{x}-{y}-{city_tile.can_act()}"))
                actions.append(annotate.circle(x, y))
                if len(player.units) < player.city_tile_count:
                    actions.append(city_tile.build_worker())
                else:
                    actions.append(city_tile.research())
    assignment = delegate(player)
    for u_id, city in assignment.items():
        actions.append(annotate.sidetext(f"{u_id}->{city.cityid}"))
                # city_tile.build_worker()

    u_agents = {}
    for unit in player.units:
        if unit.id not in u_agents.keys():
            u_agents[unit.id] = UnitControl(unit, player)
    for uid, unit_ctr in u_agents.items():
        unit_ctr.update(assignment, actions)



    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))

    return actions
