import STcpClient
import numpy as np
import random
import math
import Server.gameRule as gr
from statistics import mean
from copy import copy
import time

# 每個步驟一個 state，只顧自己

idTeam = 2
global confident
global Round
confident = 1
Round = 0

class State(object):
    def __init__(self,player,mapState,sheepStat):
        self.player = player
        self.mapStat = mapState
        self.sheepStat = sheepStat
        self.remain_move = []
        for player in range(1,5):
            self.remain_move.append(gr.checkRemainMove(player, self.mapStat, self.sheepStat))
        
    def check_move(self):
        return (self.remain_move[self.player-1] == [])

    def get_reward(self):
        return gr.countScore(self.mapStat)

    def is_terminal(self):
        return gr.end_game_check(self.mapStat, self.sheepStat)

    def random_next_state(self):
        next_step = [[],[],[],[]]
        sheepStat = copy(self.sheepStat)
        mapStat = copy(self.mapStat)
        player = self.player
        if not self.remain_move[player-1]:
            next_step[player-1] = []
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
        next_state = State(player,mapStat, sheepStat)
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

    def set_quality(self,scores,cur_ID):
        reward = scores[self.player-1]
        if self.player == cur_ID:
            self.quality_value += reward

    def get_state(self):
        return self.state

    def is_all_expand(self):
        return True if len(self.state.remain_move[self.player-1]) == len(self.children) else False
    
    def add_child(self, sub_node):
        sub_node.parent = self
        self.children.append(sub_node)

def best_child(node, is_exploration):
    best_score = -100000
    best_sub_node = node
    for sub_node in node.children:
        if is_exploration:
            C = 1 / math.sqrt(2)
        else:
            C = 0
        left = sub_node.quality_value / sub_node.visit_times
        # left = sub_node.quality_value
        # left = mean([q.auqlity_value for q in sub_node.children])
        right = 2 * math.log(node.visit_times) / sub_node.visit_times
        score = left + C * math.sqrt(right)

        if score > best_score:
            best_sub_node = sub_node
            best_score = score

    return best_sub_node

def expand(node):
    sub_node_states = [sub_node.get_state() for sub_node in node.children]
    new_state, new_step = node.get_state().random_next_state()
    while new_state in sub_node_states:
        new_state, new_step = node.get_state().random_next_state()
    sub_node = Node(new_state)
    sub_node.from_step = new_step
    node.add_child(sub_node)

    return sub_node

def tree_policy(node):
    temp = 0
    while node.get_state().is_terminal() == False:
        temp += 1
        if temp > 1000:
            print(temp)
        if node.is_all_expand() and node.state.check_move():
            node = best_child(node, True)   
        else:
            sub_node = expand(node) 
            return sub_node
    return node

def default_policy(node,ID,ratio):
    # print("default")
    cur_state = node.get_state()
    while cur_state.is_terminal() == False:
        cur_state = cur_state.random_next_state()[0]
    # reward = cur_state.get_reward()[idTeam-1]
    scores = cur_state.get_reward()
    reward = scores[ID-1] - (scores[ID%4] + scores[(ID+1)%4] + scores[(ID+2)%4]) * ratio * 0
    # print("score :",scores)
    # print("reward :",reward)
    return reward

def backup(node, reward):
    cur_ID = node.player
    while node != None:
        node.visit_times += 1
        node.quality_value = reward
        node = node.parent

def MCTS(node,ID,sim_round,start_t):
    global confident
    # for i in range(sim_round):
    while time.time() < start_t + 4.5:
        # print(i)
        expand_node = tree_policy(node)
        reward = default_policy(expand_node,ID,confident)
        backup(expand_node, reward)
    best_node = best_child(node, False)
    return best_node

def InitPos(mapStat,playerID):
    start_t = time.time()
    init_pos = []
    best = -1000000
    # for _ in range(15):
    while time.time() < start_t + 4:
        cur_pos = []
        Map = copy(mapStat)
        Sheep = (Map > 0).astype('int32')
        for i in range(12):
            for j in range(12):
                Sheep[i][j] = 16 if Sheep[i][j] == 1 else 0
        for i in range(playerID,5):
            pos = gr.randomInitPlayer(Map)
            Map[pos[0]][pos[1]] = i
            Sheep[pos[0]][pos[1]] = 16
            if i == playerID:
                cur_pos = pos
        state = State(playerID,Map,Sheep)
        node = Node(state)
        reward = 0
        for i in range(10):
            reward += default_policy(node,playerID,0)
        if best < reward:
            best = reward
            init_pos = cur_pos
    # init_pos = gr.randomInitPlayer(mapStat)
    return init_pos

def GetStep(playerID, mapStat, sheepStat):
    global confident
    global Round
    start_t = time.time()
    cur_state = State(playerID,mapStat,sheepStat)
    cur_node = Node(cur_state)
    next_node = MCTS(cur_node,playerID,100,start_t)
    # print('next step :',next_node.from_step)
    confident *= 1
    Round += 1
    print("round :",Round)
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
