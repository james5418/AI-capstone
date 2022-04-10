import copy
import numpy as np
import random

'''
mapStat: border=-1, free field=0, player_occupied=player_number(1~4)
gameStat: sheepStat
playerStat: position of player
'''


def initialMap():
    initGameStat = np.zeros((12, 12), dtype=np.int32)

    # create border
    temp_map = np.ones((14, 14), dtype=np.int32)
    temp_map[1:13, 1:13] = np.zeros([12, 12])

    while True:
        n_free = 0
        t = [[7, 7]]
        prob = 0.7
        rand = random.random()
        if rand < prob:
            # as free
            n_free += 1
            temp_map[7][7] = -1
        else:
            temp_map[7][7] = 1

        while n_free < 64:
            if len(t) == 0 & n_free != 64:
                # recreate
                print("recreate")
                n_free = 0
                temp_map[1:13, 1:13] = np.zeros([12, 12])
                t = [[7, 7]]
                prob = 0.7
                rand = random.random()
                if rand < prob:
                    # as free
                    n_free += 1
                    temp_map[7][7] = -1
                else:
                    temp_map[7][7] = 1
                continue
            random.shuffle(t)
            x, y = t.pop()
            window = temp_map[x - 1:x + 2, y - 1:y + 2]

            neighbor = []
            # 3
            if window[0][1] == 0:
                neighbor.append([x - 1, y])
            # 4
            if window[2][1] == 0:
                neighbor.append([x + 1, y])

            if y % 2 == 1:
                # 1
                if window[0][0] == 0:
                    neighbor.append([x - 1, y - 1])

                # 2
                if window[1][0] == 0:
                    neighbor.append([x, y - 1])

                # 5
                if window[0][2] == 0:
                    neighbor.append([x - 1, y + 1])

                # 6
                if window[1][2] == 0:
                    neighbor.append([x, y + 1])

            elif y % 2 == 0:
                # 1
                if window[1][0] == 0:
                    neighbor.append([x, y - 1])
                # 2
                if window[2][0] == 0:
                    neighbor.append([x + 1, y - 1])

                # 5
                if window[1][2] == 0:
                    neighbor.append([x, y + 1])
                # 6
                if window[2][2] == 0:
                    neighbor.append([x + 1, y + 1])

            rand = np.random.random(len(neighbor))
            rand = rand < prob

            for i in range(len(neighbor)):
                m, n = neighbor[i]
                if rand[i]:
                    # as free
                    n_free += 1
                    t.append([m, n])
                    temp_map[m][n] = 1
                else:
                    temp_map[m][n] = -1
                if n_free == 64: break

        n_component, _, _ = getConnectRegion(1, temp_map[1:13, 1:13])
        if n_component != 1:
            # print('recreate because not 1-component')
            temp_map[1:13, 1:13] = np.zeros([12, 12])
        else:
            break

    # fill all hole
    temp_map[temp_map == 0] = -1

    initMapStat = temp_map[1:13, 1:13]
    initMapStat[initMapStat == 1] = 0

    return initMapStat, initGameStat


def checkValidInit(mapStat, init_pos):
    x, y = init_pos

    if mapStat[x][y] != 0:
        return False

    walls = (mapStat == -1)
    flagArr = np.zeros((14, 14), dtype=np.int32)
    for i in range(12):
        flagArr[i + 1][1:13] = walls[i]

    window = flagArr[x:x + 3, y:y + 3]
    if y % 2 == 0:
        window[2][0] = 0
        window[2][2] = 0
    elif y % 2 == 1:
        window[0][0] = 0
        window[0][2] = 0

    return window.any()


def randomInitPlayer(mapStat):
    walls = (mapStat == -1)
    free_region = (mapStat == 0)
    wallArr = np.zeros((14, 14), dtype=np.int32)
    for i in range(12):
        wallArr[i + 1][1:13] = walls[i]

    candicate = []
    for i in range(12):
        for j in range(12):
            if free_region[i][j]:
                window = wallArr[i:i + 3, j:j + 3]
                if j % 2 == 0:
                    window[2][0] = 0
                    window[2][2] = 0
                elif j % 2 == 1:
                    window[0][0] = 0
                    window[0][2] = 0
                if window.any():
                    candicate.append([i, j])

    init_pos = random.choice(candicate)

    return init_pos


def getConnectRegion(targetLabel, mapStat):
    '''

    :param targetLabel:
    :param mapStat:
    :return: numbers of connect region, total occupied area, max connect region
    '''
    # turn into boolean array
    mask = mapStat == targetLabel
    n_field = np.count_nonzero(mask)

    # print(flagArr)

    n_components = 0
    # connection region

    ind = np.where(mask == 1)
    labels = np.zeros((14, 14), dtype=np.int32)
    for k in range(len(ind[0])):
        m, n = ind[0][k], ind[1][k]
        if labels[m + 1][n + 1] != 0:
            continue
        else:
            # haven't have mark
            l_window = labels[m:m + 3, n:n + 3]
            if (l_window == 0).all():
                n_components += 1
                labels[m + 1][n + 1] = n_components
            else:
                mark_pos = np.where(l_window != 0)
                neighbor = np.zeros(1, dtype=np.uint8)

                # connect region
                if n % 2 == 0:
                    for l in range(len(mark_pos[0])):
                        i, j = mark_pos[0][l], mark_pos[1][l]
                        if i == 0:
                            if j == 0:
                                neighbor = np.append(neighbor, l_window[i][j])
                            elif j == 1:
                                neighbor = np.append(neighbor, l_window[i][j])
                            elif j == 2:
                                neighbor = np.append(neighbor, l_window[i][j])
                            else:
                                continue
                        elif i == 1:
                            if j == 0:
                                neighbor = np.append(neighbor, l_window[i][j])
                            elif j == 2:
                                neighbor = np.append(neighbor, l_window[i][j])
                            else:
                                continue
                        elif i == 2:
                            if j == 1:
                                neighbor = np.append(neighbor, l_window[i][j])
                            else:
                                continue
                elif n % 2 == 1:
                    for l in range(len(mark_pos[0])):
                        i, j = mark_pos[0][l], mark_pos[1][l]
                        if i == 0:
                            if j == 1:
                                neighbor = np.append(neighbor, l_window[i][j])
                            else:
                                continue
                        elif i == 1:
                            if j == 0:
                                neighbor = np.append(neighbor, l_window[i][j])
                            elif j == 2:
                                neighbor = np.append(neighbor, l_window[i][j])
                            else:
                                continue
                        elif i == 2:
                            if j == 0:
                                neighbor = np.append(neighbor, l_window[i][j])
                            elif j == 1:
                                neighbor = np.append(neighbor, l_window[i][j])
                            elif j == 2:
                                neighbor = np.append(neighbor, l_window[i][j])
                            else:
                                continue

                neighbor = np.delete(neighbor, 0)
                # mark m,n as min class in the neighborhood
                if neighbor.size == 0:

                    n_components += 1
                    labels[m + 1][n + 1] = n_components
                else:
                    labels[m + 1][n + 1] = min(neighbor)
                    for i in np.unique(neighbor):
                        if i != min(neighbor):
                            # print(f'{i} -> {min(neighbor)}')
                            labels[labels == i] = min(neighbor)

    n_components = len(np.unique(labels)) - 1
    counts = []
    for k in np.unique(labels):
        if k == 0: continue
        c = np.count_nonzero(labels == k)
        counts = np.append(counts, c)
    return n_components, n_field, max(counts)


# move sheep with valid moving
def play(player, mapStat, gameStat, move):
    new_gameStat = copy.deepcopy(gameStat)
    new_mapStat = copy.deepcopy(mapStat)

    [move_pos_x, move_pos_y] = move[0]  # expected [x,y]
    move_sheep = move[1]  # the sheep moved to new destination
    move_dir = move[2]  # 1~6

    new_pos_x, new_pos_y = sheepMove(move[0], move_dir, mapStat)
    # valid movement
    new_gameStat[move_pos_x][move_pos_y] = gameStat[move_pos_x][move_pos_y] - move_sheep
    new_gameStat[new_pos_x][new_pos_y] = move_sheep
    new_mapStat[new_pos_x][new_pos_y] = player

    return new_gameStat, new_mapStat


# move along one direction until blocked
def sheepMove(start_pos, dir, mapStat):
    [x, y] = start_pos
    [new_x, new_y] = start_pos
    '''
      1  2
    3   x  4
      5  6
    '''

    if dir == 1:
        if y % 2 == 0:
            t, shift = 0, 1
        elif y % 2 == 1:
            t, shift = 1, 0
        while mapStat[new_x - shift][new_y - 1] == 0:
            new_x = new_x - shift
            new_y -= 1
            t += 1
            if t == 1:
                shift = 0
            if t == 2:
                shift = 1
                t = 0
            if (new_x - shift) < 0 or (new_y - 1) < 0:
                break

    elif dir == 2:
        if y % 2 == 0:
            t, shift = 1, 0
        elif y % 2 == 1:
            t, shift = 0, 1
        while mapStat[new_x + shift][new_y - 1] == 0:
            new_x = new_x + shift
            new_y -= 1
            t += 1
            if t == 1:
                shift = 0
            if t == 2:
                shift = 1
                t = 0
            if (new_x + shift) > 11 or (new_y - 1) < 0: break

    elif dir == 3:
        while mapStat[new_x - 1][new_y] == 0:
            new_x -= 1
            if new_x == 0: break
    elif dir == 4:
        while mapStat[new_x + 1][new_y] == 0:
            new_x += 1
            if new_x == 11: break
    elif dir == 5:
        if y % 2 == 0:
            t, shift = 0, 1
        elif y % 2 == 1:
            t, shift = 1, 0
        while mapStat[new_x - shift][new_y + 1] == 0:
            new_x = new_x - shift
            new_y += 1
            t += 1
            if t == 1:
                shift = 0
            if t == 2:
                shift = 1
                t = 0
            if (new_x - shift) < 0 or (new_y + 1) > 11:
                break


    elif dir == 6:
        if y % 2 == 0:
            t, shift = 1, 0
        elif y % 2 == 1:
            t, shift = 0, 1
        while mapStat[new_x + shift][new_y + 1] == 0:
            new_x = new_x + shift
            new_y += 1
            t += 1
            if t == 1:
                shift = 0
            if t == 2:
                shift = 1
                t = 0
            if (new_x + shift) > 11 or (new_y + 1) > 11:
                break

    return new_x, new_y


def checkRemainMove(player, mapStat, gameStat):
    valid_move = []

    movable_sheep = (mapStat == player) & (gameStat >= 2)
    # print(movable_sheep)
    free_region = (mapStat == 0)

    # padding for computational convenience
    flagArr = np.zeros((14, 14), dtype=np.int32)
    mapArr = np.zeros((14, 14), dtype=np.int32)
    for i in range(12):
        flagArr[i + 1][1:13] = movable_sheep[i]
        mapArr[i + 1][1:13] = free_region[i]

    # get free direction for each block having enough sheep
    ind = np.where(movable_sheep == 1)
    for k in range(len(ind[0])):
        m, n = ind[0][k], ind[1][k]
        # print(m,n)
        map_window = mapArr[m:m + 3, n:n + 3]
        mark_pos = np.where(map_window != 0)
        if n % 2 == 0:
            for l in range(len(mark_pos[0])):
                i, j = mark_pos[0][l], mark_pos[1][l]
                # print(f"find in {i},{j}")
                free_dir = 0
                if i == 0:
                    if j == 0:
                        free_dir = 1
                    elif j == 1:
                        free_dir = 3
                    elif j == 2:
                        free_dir = 5
                    else:
                        continue
                elif i == 1:
                    if j == 0:
                        free_dir = 2
                    elif j == 2:
                        free_dir = 6
                    else:
                        continue
                elif i == 2:
                    if j == 1:
                        free_dir = 4
                    else:
                        continue
                valid_move.append([[m, n], free_dir])

        elif n % 2 == 1:
            for l in range(len(mark_pos[0])):
                i, j = mark_pos[0][l], mark_pos[1][l]
                free_dir = 0
                if i == 0:
                    if j == 1:
                        free_dir = 3
                    else:
                        continue
                elif i == 1:
                    if j == 0:
                        free_dir = 1
                    elif j == 2:
                        free_dir = 5
                    else:
                        continue
                elif i == 2:
                    if j == 0:
                        free_dir = 2
                    elif j == 1:
                        free_dir = 4
                    elif j == 2:
                        free_dir = 6
                    else:
                        continue
                valid_move.append([[m, n], free_dir])
    # print(valid_move)
    return valid_move


def checkSkipPlayer(player, mapStat, gameStat):
    remain_move = checkRemainMove(player, mapStat, gameStat)
    if not remain_move:
        return True
    else:
        return False


def end_game_check(mapStat, gameStat):
    for player in range(1, 5):
        remain_move = checkRemainMove(player, mapStat, gameStat)
        if remain_move:
            # still have step
            return False
    return True


def countScore(mapStat):
    score = []
    for player in range(1, 5):
        _, n_field, max_field = getConnectRegion(player, mapStat)
        print(f'{player}=3*{n_field}+{max_field}')
        s = 3 * n_field + max_field
        score.append(s)
    return score


# if the player did a legal move, this function will return [True, the game status after move]
# if the player did a illegal move, this function will return [False, the game status before move]


def checkMoveValidation(player, mapStat, gameStat, move):
    # move =[move position, move sheep, move direction]
    [pos_x, pos_y] = move[0]  # expected [x,y]

    if mapStat[pos_x][pos_y] != player:
        print(f"It's not belong to player {player}.")
        # return [False, mapStat, gameStat]
        return False
    if gameStat[pos_x][pos_y] < 2:
        print(f"Your sheep cannot split into two non-empty group.")
        return False
        # return [False, mapStat, gameStat]
    if gameStat[pos_x][pos_y] <= move[1]:
        print(f'There is no enough sheep to move.')
        return False

    if [move[0], move[2]] in checkRemainMove(player, mapStat, gameStat):
        return True
        # new_gameStat = play(player, mapStat, gameStat, move)
    else:
        print('Illegal move.')
        return False
        # return [False, gameStat]
    return True
    # return [True, new_gameStat]


if __name__ == "__main__":
    mStat, gStat = initialMap()
    move = [[1, 5], 9, 5]
    new_gStat, new_mStat = play(1, mStat, gStat, move)
    valid_move = checkRemainMove(1, new_mStat, new_gStat)
    print(valid_move)
