import numpy as np
import pandas as pd
import util
import random
import threading
import STcpClient
import time
import sys

class MyThread(threading.Thread): 
   def __init__(self, *args, **keywords): 
       threading.Thread.__init__(self, *args, **keywords) 
       self.killed = False      
   def start(self):         
       self.__run_backup = self.run         
       self.run = self.__run                
       threading.Thread.start(self)         
   def __run(self):         
       sys.settrace(self.globaltrace)         
       self.__run_backup()         
       self.run = self.__run_backup         
   def globaltrace(self, frame, event, arg):         
       if event == 'call':             
           return self.localtrace         
       else:             
           return None        
   def localtrace(self, frame, event, arg):         
       if self.killed:             
          if event == 'line':                 
              raise SystemExit()         
       return self.localtrace         
   def kill(self):         
       self.killed = True

def getStep(playerStat, ghostStat, propsStat):
    global action

    # player = (playerStat[0],playerStat[1])
    # state = (player, ghostStat, propsStat)
    state = (playerStat, ghostStat, propsStat)

    move = RL.choose_action(state)

    # move = random.choice([0, 1, 2, 3, 4])
    landmine = False
    # if playerStat[2] > 0:
    #     landmine = random.choice([True, False])
    action = [move, landmine]


class QLearningAgent():

    def __init__(self, learning_rate=0.01, discount_factor=0.9, exploration_rate=0.9):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.Q_table = util.Counter()


    def choose_action(self, state):
        legalActions = self.getLegalActions(state)
        action = None

        if np.random.uniform() < self.epsilon:
            state_action = [self.Q_table[state, act] for act in legalActions]
            action = legalActions[np.random.choice(np.where(state_action == np.max(state_action))[0])]
        else:
            action = np.random.choice(legalActions)

        return action
    
    def update(self, state, action, reward, next_state):
        q_predict = self.Q_table[state, action]

        # if next_state != 'terminal':
        legalActions = self.getLegalActions(next_state)
        new = np.max([self.Q_table[next_state, act] for act in legalActions])
        q_target = reward + self.gamma * new
        # else:
            # q_target = reward

        self.Q_table[(state, action)] += self.lr * (q_target - q_predict)
    

    def getLegalActions(self, state):
        
        # 0: left, 1:right, 2: up, 3: down 4:no control
        directions = {0: (0, -1), 1: (0, 1), 2: (-1, 0), 3: (1, 0), 4: (0, 0)}

        # state[0][2] = landmain
        # state[0][3] = super_time

        possible = []
        for dir, (dx, dy) in directions.items():

            if dir == 4:
                possible.append(dir)
                continue

            next_x = state[0][0] + dx
            next_y = state[0][1] + dy


            if next_x < 0: next_x = 0
            if next_y < 0: next_y = 0

            # if next_x > 15 or next_x < 0 or next_y > 15 or next_y < 0:
            #     continue

            
            if (dir == 0) and not vertical_wall[state[0][0]][state[0][1]]: # left
                possible.append(dir)
            elif (dir == 1) and not vertical_wall[next_x][next_y]: # right
                possible.append(dir)
            elif (dir == 2) and not parallel_wall[state[0][0]][state[0][1]]: # up
                possible.append(dir)
            elif (dir == 3) and not parallel_wall[next_x][next_y]: # down
                possible.append(dir)

        return possible

# parallel_wall = np.zeros((16, 17))
# vertical_wall = np.zeros((17, 16))
parallel_wall = np.zeros((17, 16))
vertical_wall = np.zeros((16, 17))


"""
(0,0) (0,1) (0,2)
(1,0) (1,1) (1,2)
(2,0) (2,1) (2,2)

(0,0) (1,0) (2,0)
(0,1) (1,1) (2,1)
(0,2) (1,2) (2,2)

"""

# playerStat: [x, y, n_landmine,super_time, score]
# otherplayerStat: [x, y, n_landmine, super_time]
# ghostStat: [[x, y],[x, y],[x, y],[x, y]]
# propsStat: [[type, x, y] * N]

def parse_player(playerStat):
    landmain = 1 if playerStat[2]>0 else 0
    super_time = 1 if playerStat[3]>0 else 0
    return (playerStat[0]//25, playerStat[1]//25, landmain, super_time), playerStat[4]
    # return (playerStat[0]//25, playerStat[1]//25, playerStat[2], playerStat[3], playerStat[4])

def parse_ghost(ghostStat):
    g = [[ ghostStat[x][y]//25 for y in range(len(ghostStat[0]))] for x in range(len(ghostStat))]
    return tuple(map(tuple, g))

def parse_prop(propsStat):
    prop = np.full((16, 16), -1, dtype=int)
    for p in propsStat:
        prop[p[1]//25][p[2]//25] = p[0]
    return tuple(map(tuple, prop))


rw = []

def training():
    
    for episode in range(1):
        
        # TODO reset game
        (stop_program, id_package, p_wall, v_wall) = STcpClient.GetMap()
        (stop_program, id_package, playerStat, otherPlayerStat, ghostStat, propsStat) = STcpClient.GetGameStat()

        playerStat, reward = parse_player(playerStat)
        ghostStat = parse_ghost(ghostStat)
        propsStat = parse_prop(propsStat)

        # player = (playerStat[0],playerStat[1])
        # state = (player, ghostStat, propsStat)
        state = (playerStat, ghostStat, propsStat)

        parallel_wall = p_wall
        vertical_wall = v_wall

        while True:
            global action
            action = None

            user_thread = MyThread(target=getStep, args=(playerStat, ghostStat, propsStat))
            user_thread.start()
            time.sleep(4/100)
            if action == None:
                user_thread.kill()
                user_thread.join()
                action = [4, False]
            is_connect = STcpClient.SendStep(id_package, action[0], action[1])

            (stop_program, id_package, playerStat, otherPlayerStat, ghostStat, propsStat) = STcpClient.GetGameStat()

            if stop_program or stop_program is None or not is_connect:
                print(f'Episode {episode} score = {reward}')
                print(rw)
                break

            playerStat, reward = parse_player(playerStat)
            ghostStat = parse_ghost(ghostStat)
            propsStat = parse_prop(propsStat)

            # player = (playerStat[0],playerStat[1])
            # next_state = (player, ghostStat, propsStat)
            next_state = (playerStat, ghostStat, propsStat)

            # reward = playerStat[3]
            rw.append(reward)


            RL.update(state, action[0], reward, next_state)

            state = next_state

            
        # print(RL.Q_table)
        
        


if __name__ == "__main__":

    RL = QLearningAgent()

    training()