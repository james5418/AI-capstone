import STcpClient
import numpy as np
import random
import math
import Server.gameRule as gr
from statistics import mean
from mcts import *

idTeam = 4

def InitPos(mapStat):
    init_pos = gr.randomInitPlayer(mapStat)
    return init_pos

def GetStep(playerID, mapStat, sheepStat):
    cur_state = State(mapStat,sheepStat)
    cur_node = Node(cur_state)
    next_node = MCTS(cur_node)
    print('next step :',next_node.from_step)
    return next_node.from_step[idTeam-1]


# player initial
(id_package, playerID, mapStat) = STcpClient.GetMap()
init_pos = InitPos(mapStat)
STcpClient.SendInitPos(id_package, init_pos)

# start game
while (True):
    (end_program, id_package, mapStat, sheepStat) = STcpClient.GetBoard()
    if end_program:
        STcpClient._StopConnect()
        break
    Step = GetStep(playerID, mapStat, sheepStat)

    STcpClient.SendStep(id_package, Step)
