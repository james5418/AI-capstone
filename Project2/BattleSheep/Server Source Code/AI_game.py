# -*- coding: utf-8 -*-
"""
Created on Tue May  7 16:44:31 2019

@author: LAB031
"""
import copy
import STcpServer
import gameUI
import os
# import re
# import glob
# import time
# import logging
import numpy as np
# import pandas as pd
from gameRule import checkSkipPlayer, checkMoveValidation, end_game_check, checkRemainMove, checkValidInit, \
    randomInitPlayer
from gameRule import initialMap, countScore, play

"""
def get_players_info(route):
    total_id = []
    if not os.path.isabs(route):
        route = os.path.abspath(route)
    total_path = glob.glob(os.path.join(route,'*.exe'))
    for path in total_path:
        file_name = os.path.basename(path).split('.')[0]
        team_num = re.match('Team_([0-9]+)',file_name)
        total_id.append(int(team_num.group(1)))

    return total_id, total_path
"""


def battle(teamID):
    '''

    :param teamID: 4 teams in this game
    :return:
    '''

    initMapStat, initGameStat = initialMap()

    map_current = copy.deepcopy(initMapStat)
    game_current = copy.deepcopy(initGameStat)

    count_dis = [0, 0, 0, 0]  # to save whether disconnect
    for i in range(4):
        print(f'player {i + 1} = team {teamID[i]}')

    print("\n----------START GAME----------\n")

    replay = []
    action_record = {}
    action_record['text'] = '(initial state)'
    action_record['map'] = initMapStat
    action_record['game'] = initGameStat
    replay.append(action_record)

    # init player
    action_record = {}
    action_record['text'] = 'set initial position\n'
    for item in range(4):
        player = item + 1

        print(f"it's player {player}'s turn")
        action_record['text'] = action_record['text'] + "it's player " + str(player) + "'s turn\n"
        (connect, init_pos) = STcpServer.SendInitMap(item, map_current)

        if connect == 1:
            # time out
            print(f"player {player} no response.")
            action_record['text'] = action_record['text'] + "player " + str(player) + " no response.\n\n"
            init_pos = randomInitPlayer( map_current)
            print(
                'server plays a movement due to time limit exceeded: {}'.format(init_pos))
            action_record['text'] = action_record['text'] + 'server plays a movement due to time limit exceeded: ' \
                                    + str(init_pos) + '\n'

        elif connect == 2:
            count_dis[item] += 1
            print(f"player {player} disconnected.")
            action_record['text'] = action_record['text'] + "player " + str(player) + " disconnected.\n\n"
            init_pos = randomInitPlayer( map_current)
            print(
                'server plays a movement due to time limit exceeded: {}'.format(init_pos))
            action_record['text'] = action_record['text'] + 'server plays a movement due to time limit exceeded: ' \
                                    +str(init_pos) + '\n'
        else:
            count_dis[item] = 0
            print(f'set position at {init_pos}')
            action_record['text'] = action_record['text'] + 'movement: ' + str(init_pos) + '\n\n'

            legality_tag = checkValidInit(map_current, init_pos)
            if not legality_tag:
                print(f"player {player}: movement illegal.")
                init_pos = randomInitPlayer( map_current)

                print('server plays a movement due to illegal movement: {}'.format(init_pos))
                action_record['text'] = action_record['text'] + 'server plays a movement due to illegal movement: '\
                                        + str(init_pos) + '\n'

        # set player
        x, y = init_pos
        map_current[x][y] = player
        game_current[x][y] = 16

    # record for UI
    action_record['movement'] = None
    action_record['map'] = map_current
    action_record['game'] =game_current

    replay.append(action_record)

    # start game
    print('initial success.\n')

    while not end_game_check(map_current, game_current):
        for item in range(4):
            action_record = {}

            player = item + 1
            action_record['text'] = ''

            if checkSkipPlayer(player, map_current, game_current):
                print(f"player {player} will be skipped.\n")
                action_record['text'] = action_record['text'] + "player" + str(player) + " will be skipped.\n"
                action_record['game'] = game_current
                action_record['map'] = map_current
                replay.append(action_record)
                continue
            if count_dis[item] >= 10:
                print(f'player {player} is skipped because of disconnection.\n')
                action_record['text'] = action_record['text'] + " player " + str(player) + \
                                        "is skipped because of disconnection.\n"

                action_record['game'] = game_current
                action_record['map'] = map_current
                replay.append(action_record)
                continue

            print(f"it's player {player}'s turn")
            action_record['text'] = action_record['text'] + "it's player " + str(player) + "'s turn\n"
            (connect, movement) = STcpServer.SendBoard(item, map_current, game_current)

            if connect == 1:
                # time out
                print(f"player {player} no response.")
                action_record['text'] = action_record['text'] + "player " + str(player) + " no response.\n\n"

            elif connect == 2:
                count_dis[item] += 1
                print(f"player {player} disconnected.")
                action_record['text'] = action_record['text'] + "player " + str(player) + " disconnected.\n\n"

            else:
                count_dis[item] = 0
                print('movement: {}\n'.format(movement))
                action_record['text'] = action_record['text'] + 'movement: ' + str(movement) + '\n\n'

                legality_tag = checkMoveValidation(player, map_current, game_current, movement)
                if not legality_tag:
                    print(f"player {player}: movement illegal.")
                    action_record['text'] = action_record['text'] + "player " + str(player) + " : movement illegal.\n"
                else:
                    # move player
                    t_gameStat, t_mapStat = play(player, map_current, game_current, movement)
                    map_current = copy.deepcopy(t_mapStat)
                    game_current = copy.deepcopy(t_gameStat)
            # record for UI
            action_record['movement'] = movement
            action_record['map'] = map_current
            action_record['game'] = game_current

            replay.append(action_record)

    print("\n----------END GAME----------\n")

    for item in range(4):
        STcpServer.SendBoard(item, map_current, game_current, gameFlag=0)

    score = countScore(map_current)
    print('Score Board')
    for i in range(4):
        print(f'player {i + 1}=team {teamID[i]} : {score[i]} ')
    max_score = max(score)
    w = np.where(score == max_score)
    result = f'Winner : team {[teamID[c] for c in w[0]]}, Score= {max_score}'
    print(result)

    result = f'Winner : team {[teamID[c] for c in w[0]]}\n Score : {max_score}'
    UI = gameUI.gameUI(replay, initMapStat, initGameStat, result, score)

    # UI.show_result(replay)
    UI.window.mainloop()  # 運行視窗程式

    return


def main():
    teams = [0, 0, 0, 0]
    path = ['', '', '', '']

    # use cmd input
    '''for i in range(4):
        teamID = input(f'input Team{i + 1} team number(int): ')
        teams[i] = int(teamID)
        path[i] = input(f'input Path to Team{i + 1}exe(example: C:\\yourpath\\Team_number.exe): ')'''

    # use input.txt
    with open('input.txt', 'r') as file:
        lines = file.readlines()

    for l in range(4):
        i=l*2
        teams[l] = int(lines[i])
        path[l] =lines[i+1][:-1]
    print(teams)
    print(path)

    (success, failId) = STcpServer.StartMatch(teams, path)

    if (not success):
        print("connection fail, teamId:", failId)
    else:
        battle(teams)

    STcpServer.StopMatch()


if __name__ == "__main__":
    main()
    os.system('pause')





