import STcpClient
import numpy as np
import random
import math
import Server.gameRule as gr
from statistics import mean
from copy import copy
import time

idTeam = 3
global confident
global Round
global file
file = open("debug.txt",'w')
confident = 1
Round = 0

def to_print():
    return True

def countScore(mapStat):
    score = []
    for player in range(1, 5):
        _, n_field, max_field = gr.getConnectRegion(player, mapStat)
        # print(f'{player}=3*{n_field}+{max_field}')
        s = 3 * n_field + max_field
        score.append(s)
    return score

class State(object):
    def __init__(self,player,mapState,sheepStat):
        self.player = player
        self.mapStat = mapState
        self.sheepStat = sheepStat
        self.remain_move = []
        for player in range(1,5):
            self.remain_move.append(gr.checkRemainMove(player, self.mapStat, self.sheepStat))
        
    def check_move(self):
        return (self.remain_move[self.player-1] != [])

    def get_reward(self):
        return countScore(self.mapStat)

    def is_terminal(self):
        return gr.end_game_check(self.mapStat, self.sheepStat)

    def random_next_state(self):
        next_step = [[],[],[],[]]
        sheepStat = copy(self.sheepStat)
        mapStat = copy(self.mapStat)
        player = self.player
        if not self.remain_move[player-1]:
            next_step[player-1] = ["empty"]
        else:
            step = random.choice(self.remain_move[player-1])
            pos = step[0]
            new_x, new_y = gr.sheepMove(pos, step[1], self.mapStat)
            move_sheep = np.random.randint(1,self.sheepStat[pos[0]][pos[1]])
            sheepStat[pos[0]][pos[1]] = sheepStat[pos[0]][pos[1]] - move_sheep
            sheepStat[new_x][new_y] = move_sheep
            mapStat[new_x][new_y] = player
            next_step[player-1] = [pos,move_sheep,step[1]]
        player = player + 1 if player + 1 != 5 else 1
        next_state = State(player, mapStat, sheepStat)
        return next_state, next_step

class Node(object):
    def __init__(self, state):
        self.parent = None
        self.children = []
        self.visit_times = 0
        self.quality_value = 0
        self.from_step = []  # [pos, num, dir]
        self.state = state
        self.player = state.player

    def set_quality(self,scores,ID):
        global Round
        # if self.player - 1 == ID:
        player = self.player-2 if self.player != 1 else 3
        rank = sorted(range(len(scores)), key = lambda k: scores[k])
        # reward = rank.index(player) / 3
        reward = scores[player] - (scores[(player+1)%4] + scores[(player+2)%4] + scores[(player+3)%4]) * 0
        reward += 10 * rank.index(player)
        # reward = scores[player]
        self.quality_value += reward
        if to_print():
            global file
            file.write(f"player {self.player} visit : {self.visit_times} rank : {rank}, reward {reward}, {self.quality_value} , from : {self.from_step} \n")
            # print("player ",self.player,"rank :",rank,", reward",reward,",",self.quality_value,"from :",self.from_step)
        # else:
            # print("player ",self.player,"quality",self.quality_value,"from :",self.from_step)
    def get_state(self):
        return self.state

    def is_all_expand(self):
        possibilities = 0
        for move in self.state.remain_move[self.player-1]:
            pos = move[0]
            possibilities += self.state.sheepStat[pos[0]][pos[1]] - 1
        return True if possibilities == len(self.children) and possibilities != 0 else False
    
    def add_child(self, sub_node):
        sub_node.parent = self
        self.children.append(sub_node)

    def check_empty(self):
        return ((not self.state.check_move()) and len(self.children) == 1)

def best_child(node, is_exploration):
    best_score = -100000
    best_sub_node = None
    for sub_node in node.children:
        if is_exploration:
            # C = 1 / math.sqrt(2)
            C = 10
        else:
            C = 0
        left = sub_node.quality_value / sub_node.visit_times
        # left = sub_node.quality_value
        # left = mean([q.auqlity_value for q in sub_node.children])
        right = math.log(node.visit_times) / sub_node.visit_times
        score = left + C * math.sqrt(right)

        if score > best_score:
            best_sub_node = sub_node
            best_score = score

    return best_sub_node

def expand(node):
    sub_node_steps = [sub_node.from_step for sub_node in node.children]
    new_state, new_step = node.get_state().random_next_state()
    while new_step in sub_node_steps and node.state.check_move():
        new_state, new_step = node.get_state().random_next_state()
    sub_node = Node(new_state)
    sub_node.from_step = new_step
    # if new_step not in sub_node_steps:
    node.add_child(sub_node)

    return sub_node

def tree_policy(node):
    # print("--- tree ---")
    global Round
    while node.get_state().is_terminal() == False:
        if node.is_all_expand() or node.check_empty():
            node = best_child(node, True)
            if to_print():
                global file
                file.write(f"tree player  {node.player} children {len(node.children)} visit : {node.visit_times} quality {node.quality_value} from : {node.from_step} \n")
                # print("player ",node.player,"children",len(node.children),"quality",node.quality_value,"from :",node.from_step)
        else:
            # print("   ! expand")
            sub_node = expand(node)
            return sub_node
    return node

def default_policy(node,ID,ratio):
    # print("default")
    cur_state = node.get_state()
    while cur_state.is_terminal() == False:
        # print("state :",cur_state.player)
        cur_state = cur_state.random_next_state()[0]
    scores = cur_state.get_reward()
    # print("score :",scores)
    return scores

def backup(node, reward, ID):
    global Round
    global file
    if to_print():
        file.write("----- backup -----\n")
        # print("----- backup -----")
    while node != None:
        node.visit_times += 1
        node.set_quality(reward,ID)
        node = node.parent
    if to_print():
        file.write("\n")

def MCTS(node,ID,start_t):
    global confident
    # for i in range(sim_round):
    while time.time() < start_t + 4:
    # if True:
        # print(i)
        expand_node = tree_policy(node)
        reward = default_policy(expand_node,ID,confident)
        backup(expand_node, reward, ID)
    best_node = best_child(node, False)
    return best_node

def find_init(mapStat,playerID):
    start_t = time.time()
    init_pos = []
    pos_list = []
    best = -1000000
    while time.time() < start_t + 4:
        cur_pos = []
        Map = copy(mapStat)
        Sheep = (Map > 0).astype('int32')
        for i in range(12):
            for j in range(12):
                Sheep[i][j] = 16 if Sheep[i][j] == 1 else 0
        for i in range(playerID,5):
            pos = gr.randomInitPlayer(Map)
            while pos in pos_list:
                pos = gr.randomInitPlayer(Map)
            pos_list.append(pos)
            Map[pos[0]][pos[1]] = i
            Sheep[pos[0]][pos[1]] = 16
            if i == playerID:
                cur_pos = pos
        state = State(playerID,Map,Sheep)
        node = Node(state)
        reward = 0
        for i in range(30):
            reward += default_policy(node,playerID,0)[playerID-1]
        if best < reward:
            best = reward
            init_pos = cur_pos
    return init_pos

def InitPos(mapStat,playerID):
    init_pos = find_init(mapStat,playerID)
    # init_pos = gr.randomInitPlayer(mapStat)
    # init_pos = [5,5]
    # while mapStat[init_pos[0]][init_pos[1]] != 0:
    #     init_pos[0 if init_pos[0] <= init_pos[1] else 1] += 1
    return init_pos

def GetStep(playerID, mapStat, sheepStat):
    global confident
    global Round
    global file
    if to_print():
        file.write(f"round : {Round}\n")
    start_t = time.time()
    cur_state = State(playerID,mapStat,sheepStat)
    cur_node = Node(cur_state)
    next_node = MCTS(cur_node,playerID,start_t)
    # print('next step :',next_node.from_step)
    confident *= 1
    Round += 1
    print("round :",Round)
    # print(next_node.from_step)
    if to_print():
        file.write(f"move : {next_node.from_step}\n")
    return next_node.from_step[playerID-1]


# player initial
(id_package, playerID, mapStat) = STcpClient.GetMap()
init_pos = InitPos(mapStat,playerID)
STcpClient.SendInitPos(id_package, init_pos)

# start game
while (True):
    (end_program, id_package, mapStat, sheepStat) = STcpClient.GetBoard()
    if end_program:
        STcpClient._StopConnect()
        break
    Step = GetStep(playerID, mapStat, sheepStat)

    STcpClient.SendStep(id_package, Step)

if to_print():
    file.close()