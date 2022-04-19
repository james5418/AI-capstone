import STcpClient
import numpy as np
import random
import math
import Server.gameRule as gr
from statistics import mean
from copy import copy

idTeam = 4

class State(object):
    def __init__(self,mapState,sheepStat):
        self.mapStat = mapState
        self.sheepStat = sheepStat
        self.remain_move = []
        for player in range(1,5):
            self.remain_move.append(gr.checkRemainMove(player, self.mapStat, self.sheepStat))
        
    def get_reward(self):
        return gr.countScore(self.mapStat)

    def is_terminal(self):
        return gr.end_game_check(self.mapStat, self.sheepStat)

    def random_next_state(self):
        next_step = []
        sheepStat = copy(self.sheepStat)
        mapStat = copy(self.mapStat)
        for player in range(1,5):
            if not self.remain_move[player-1]:
                next_step.append([])
                continue
            step = random.choice(self.remain_move[player-1])
            pos = step[0]
            new_x, new_y = gr.sheepMove(pos, step[1], self.mapStat)
            move_sheep = np.random.randint(1,self.sheepStat[pos[0]][pos[1]])
            sheepStat[pos[0]][pos[1]] = sheepStat[pos[0]][pos[1]] - move_sheep
            sheepStat[new_x][new_y] = move_sheep
            mapStat[new_x][new_y] = player
            next_step.append([pos,move_sheep,step[1]])

        next_state = State(mapStat, sheepStat)
        return next_state, next_step

class Node(object):
    def __init__(self, state):
        self.parent = None
        self.children = []
        self.visit_times = 0
        self.quality_value = 0
        self.from_step = []  # [pos, num, dir]
        self.state = state

    def get_state(self):
        return self.state

    def is_all_expand(self):
        all_posbilities = 1
        for i in range(4):
            if len(self.state.remain_move[i]) != 0:
                selection = 0
                for move in self.state.remain_move[i]:
                    pos = move[0]
                    selection += self.state.sheepStat[pos[0]][pos[1]] - 1
                all_posbilities *= selection
            else:
                all_posbilities *= 1
        # for i in range(4):
        #     print(self.state.remain_move[i])
        # print("posbility :",all_posbilities)
        return True if all_posbilities == len(self.children) else False
    
    def add_child(self, sub_node):
        sub_node.parent = self
        self.children.append(sub_node)

def best_child(node, is_exploration):
    best_score = -1
    best_sub_node = None
    for sub_node in node.children:
        if is_exploration:
            C = 1 / math.sqrt(2)
            # C = 1
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
    while node.get_state().is_terminal() == False:
        if node.is_all_expand():
            node = best_child(node, True)   
        else:
            sub_node = expand(node) 
            return sub_node
    return node

def default_policy(node):
    cur_state = node.get_state()
    while cur_state.is_terminal() == False:
        cur_state = cur_state.random_next_state()[0]
    reward = cur_state.get_reward()
    return reward

def backup(node, reward):
    while node != None:
        node.visit_times += 1
        node.quality_value += reward[idTeam-1]
        node = node.parent

def MCTS(node):
    round = 500
    for i in range(round):
        expand_node = tree_policy(node)
        reward = default_policy(expand_node)
        backup(expand_node, reward)
    best_node = best_child(node, False)
    return best_node