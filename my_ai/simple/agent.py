import math, sys
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate

DIRECTIONS = Constants.DIRECTIONS
game_state: Game = None


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


def get_resource_tiles(width, height, game_state):
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

    resource_tiles = get_resource_tiles(width, height, game_state)

    # we iterate over all our units and do something with them
    for unit in player.units:
        if unit.is_worker() and unit.can_act():
            if unit.get_cargo_space_left() > 0:
                closest_resource_tile = get_closest_resource_tile(resource_tiles, unit, player)
                if closest_resource_tile is not None:
                    actions.append(annotate.line(
                        closest_resource_tile.pos.x, closest_resource_tile.pos.y,
                        unit.pos.x, unit.pos.y
                    ))
                    actions.append(unit.move(unit.pos.direction_to(closest_resource_tile.pos)))
            else:
                # if unit is a worker and there is no cargo space left, and we have cities, lets return to them
                if len(player.cities) > 0:
                    closest_city_tile = get_closest_city_tile(unit, player)
                    if closest_city_tile is not None:
                        city = player.cities[closest_city_tile.cityid]
                        if city.get_light_upkeep() < city.fuel:
                            pass
                        # print(closest_city_tile)
                        actions.append(annotate.line(
                            closest_city_tile.pos.x, closest_city_tile.pos.y,
                            unit.pos.x, unit.pos.y
                        ))
                        move_dir = unit.pos.direction_to(closest_city_tile.pos)
                        actions.append(unit.move(move_dir))

    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            if city_tile.can_act():
                x = city_tile.pos.x
                y = city_tile.pos.y
                actions.append(annotate.sidetext(f"cityTile{x}-{y}"))
                actions.append(annotate.circle(x, y))
                city_tile.research()
                # city_tile.build_worker()

    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))

    return actions
