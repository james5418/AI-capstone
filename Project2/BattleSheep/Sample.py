import STcpClient
import numpy as np
# import random

'''
    選擇起始位置
    選擇範圍僅限場地邊緣(至少一個方向為牆)
    
    return: init_pos
    init_pos=[x,y],代表起始位置
    
'''
def find_longest(mapStat,pos):
    max_step = 0
    dir = 0
    dist = np.zeros(6).tolist()
    offset = -1 if pos[1] % 2 == 0 else 0
    dir_map = [[offset,-1],[offset+1,-1],[-1,0],[1,0],[offset,1],[offset+1,1]]
    for i in range(6):
        step = 0
        cur = [pos[0]+dir_map[i][0],pos[1]+dir_map[i][1]]
        while (cur[0] >= 0 and cur[0] < 12 and cur[1] >= 0 and cur[1] < 12) and mapStat[cur[0]][cur[1]] == 0:
            step += 1
            cur = [cur[0]+dir_map[i][0],cur[1]+dir_map[i][1]]
        if max_step < step:
            max_step = step
            dir = i + 1
    return dir

def InitPos(mapStat):
    for i in range(12):
        for j in range(12):
            # print("i, j, mapStat[i][j] :", [i,j,mapStat[i][j]])
            if mapStat[i][j] == 0:
                init_pos = [i, j]
                break

    return init_pos


'''
    產出指令
    
    input: 
    playerID: 你在此局遊戲中的角色(1~4)
    mapStat : 棋盤狀態(list of list), 為 12*12矩陣, 
              0=可移動區域, -1=障礙, 1~4為玩家1~4佔領區域
    sheepStat : 羊群分布狀態, 範圍在0~16, 為 12*12矩陣

    return Step
    Step : 3 elements, [(x,y), m, dir]
            x, y 表示要進行動作的座標 
            m = 要切割成第二群的羊群數量
            dir = 移動方向(1~6),對應方向如下圖所示
              1  2
            3  x  4
              5  6
'''
def GetStep(playerID, mapStat, sheepStat):
    # step = [(0, 0), 0, 1]
    # get max sheep pos
    pos = (0,0)
    max = 0
    for i in range(12):
        for j in range(12):
            if mapStat[i][j] == playerID and max < sheepStat[i][j]:
                pos = (i,j)
                max = int(sheepStat[i][j])
    dir = find_longest(mapStat,pos)
    step = [pos,max-1,dir]
    # print("GetStep :",step)
    return step


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
