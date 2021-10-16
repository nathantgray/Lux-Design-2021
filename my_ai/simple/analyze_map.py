
from kaggle_environments import make
import numpy as np
import matplotlib.pyplot as plt
from lux.game import Game
from lux import annotate
from matplotlib.colors import ListedColormap  # , LinearSegmentedColormap


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


game_state: Game = None


def agent(observation, configuration):
    global game_state

    # ## Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])

    # ## Bot code ###
    actions = []

    if game_state.turn == 0:
        actions.append(annotate.circle(0, 0))

    return actions


def _map_state_to_visual(map_state):
    """ Takes a map state and produces the visualisation"""
    map_state.set_resources()
    map_state.binarise()
    map_state.find_city()

    visualizer_array = np.add(np.add(map_state.bd_wood, 2 * map_state.bd_coal), 3 * map_state.bd_uranium)

    start_position_list = []

    for start_pos in map_state.start_pos:
        start_position_list.append((start_pos[1], start_pos[0]))

    return visualizer_array, start_position_list


def get_plot_arrays(map_count_target, target_mapsize):
    map_count_seen = 0  # counter variable, leaves as zero
    visualizer_list = []
    start_position_list = []

    while map_count_seen < map_count_target:
        # run the simulation
        env = make('lux_ai_2021', configuration={
            'loglevel': 0,
            'annotations': False,
            'episodeSteps': 2,
        }, debug=False)

        steps = env.run([agent, 'simple_agent'])

        # initiate the relevant class
        map_state = MapState(
            gamemap=game_state.map.map,
            width=game_state.map.width,
            height=game_state.map.height,
            player=game_state.players[0],
            opponent=game_state.players[(0 + 1) % 2],
        )

        if np.isclose(map_state.width, target_mapsize):
            visualizer_array, start_positions_sim = _map_state_to_visual(map_state)
            visualizer_list.append(visualizer_array)
            start_position_list.append(start_positions_sim)
            map_count_seen += 1

    return visualizer_list, start_position_list


def plot_visualizer_arrays(visualizer_arrays,start_positions_list, cmap):
    imgwidth = 4
    length = len(visualizer_arrays)
    if length < imgwidth:
        length = imgwidth
    fig, axs = plt.subplots(int((length/imgwidth)+0.5), imgwidth)
    for i, varray in enumerate(visualizer_arrays):
        for remainder in range(imgwidth):
            if i % imgwidth == remainder:
                axs[int((i-remainder)/imgwidth), remainder].imshow(varray, cmap)
                for start_pos in start_positions_list[i]:
                    axs[int((i-remainder)/imgwidth), remainder].plot(start_pos[0], start_pos[1], 'k2', markersize=50)


def main():
    cmap = ListedColormap(["white", "green", "blue", "red"]) #color map, key is: blank space, wood, coal, uranium
    map_count_target = 12 #how many maps do you want
    target_mapsize = 12 # size of maps you want to look at, if none all maps are returned

    plt.rcParams['figure.figsize'] = [12*5, 8*5] #make plots bigger

    visualizer_list, start_positions_list = get_plot_arrays(map_count_target, target_mapsize)
    plot_visualizer_arrays(visualizer_list, start_positions_list, cmap)
    plt.show()


if __name__ == '__main__':
    main()