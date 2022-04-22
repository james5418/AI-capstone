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

    state = (playerStat, ghostStat, propsStat)

    move = RL.choose_action(state)

    # move = random.choice([0, 1, 2, 3, 4])
    landmine = False
    # if playerStat[2] > 0:
    #     landmine = random.choice([True, False])
    action = [move, landmine]


# playerStat: [x, y, n_landmine,super_time, score]
# otherplayerStat: [x, y, n_landmine, super_time]
# ghostStat: [[x, y],[x, y],[x, y],[x, y]]
# propsStat: [[type, x, y] * N]

class QLearningAgent():

    def __init__(self, learning_rate=1, discount_factor=0.8, exploration_rate=0.8):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.Q_table = util.Counter()
        self.parallel_wall = np.zeros((16, 17))
        self.vertical_wall = np.zeros((17, 16))


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

        legalActions = self.getLegalActions(next_state)
        new = np.max([self.Q_table[next_state, act] for act in legalActions])
        q_target = reward + self.gamma * new

        self.Q_table[state, action] += self.lr * (q_target - q_predict)
    
    def getReverseAction(self, dir):
        if dir==0 or dir==2:
            return dir+1
        elif dir==1 or dir==3:
            return dir-1
            

    def getLegalActions(self, state):
        
        # 0: left, 1:right, 2: up, 3: down 4:no control
        directions = {0: (-1,0), 1: (1,0), 2: (0,-1), 3: (0,1), 4: (0, 0)}

        # state[0][2] = landmain
        # state[0][3] = super_time

        possible = []
        for dir, (dx, dy) in directions.items():

            # if dir == 4:
            #     possible.append(dir)
            #     continue

            next_x = state[0][0] + dx
            next_y = state[0][1] + dy

            if next_x < 0: next_x = 0
            if next_y < 0: next_y = 0

            # if next_x<16 and next_y<16 and state[2][next_x][next_y]==3:
            #     possible.append(self.getReverseAction(dir))
            #     continue
            # if next_x<16 and next_y<16 and [next_x,next_y] in state[1]:
            #     possible.append(self.getReverseAction(dir))
            #     continue
            
            if (dir == 0) and not self.vertical_wall[state[0][0]][state[0][1]]: # left
                possible.append(dir)
            elif (dir == 1) and not self.vertical_wall[next_x][next_y]: # right
                possible.append(dir)
            elif (dir == 2) and not self.parallel_wall[state[0][0]][state[0][1]]: # up
                possible.append(dir)
            elif (dir == 3) and not self.parallel_wall[next_x][next_y]: # down
                possible.append(dir)

        if len(possible) == 0:
            possible.append(4)
            
        return possible


    def parse_player(self, playerStat):
        landmain = 1 if playerStat[2]>0 else 0
        super_time = 1 if playerStat[3]>0 else 0
        return (playerStat[0]//25, playerStat[1]//25, landmain, super_time), playerStat[4]

    def parse_ghost(self, ghostStat):
        g = [[ ghostStat[x][y]//25 for y in range(len(ghostStat[0]))] for x in range(len(ghostStat))]
        return tuple(map(tuple, g))

    def parse_prop(self, propsStat):
        prop = np.full((16, 16), -1, dtype=int)
        for p in propsStat:
            prop[p[1]//25][p[2]//25] = p[0]
        return tuple(map(tuple, prop))

    def training(self):
        for episode in range(1):

            # TODO reset game
            (stop_program, id_package, p_wall, v_wall) = STcpClient.GetMap()
            (stop_program, id_package, playerStat, otherPlayerStat, ghostStat, propsStat) = STcpClient.GetGameStat()

            playerStat, _ = self.parse_player(playerStat)
            ghostStat = self.parse_ghost(ghostStat)
            propsStat = self.parse_prop(propsStat)

            state = (playerStat, ghostStat, propsStat)

            self.parallel_wall = p_wall
            self.vertical_wall = v_wall

            old_reward = 0

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
                    print(f'Episode {episode} score = {pscore}')
                    # print(rw)
                    break

                playerStat, pscore = self.parse_player(playerStat)
                ghostStat = self.parse_ghost(ghostStat)
                propsStat = self.parse_prop(propsStat)

                next_state = (playerStat, ghostStat, propsStat)

                reward = pscore - old_reward

                # rw.append(reward)

                RL.update(state, action[0], reward, next_state)

                state = next_state
                old_reward = pscore


if __name__ == "__main__":

    RL = QLearningAgent()
    RL.training()