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
    '''
    control of your player
    0: left, 1:right, 2: up, 3: down 4:no control
    format is (control, set landmine or not) = (0~3, True or False)
    put your control in action and time limit is 0.04sec for one step
    '''
    move = random.choice([0, 1, 2, 3, 4])
    landmine = False
    if playerStat[2] > 0:
        landmine = random.choice([True, False])
    action = [move, landmine]


class QLearningAgent():

    def __init__(self, actions, learning_rate=0.01, discount_factor=0.9, exploration_rate=0.9):
        self.actoins = actions
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.Q_table = util.Counter()

    # state: playerStat, ghostStat, propsStat
    def choose_action(self, state):
        legalActions = self.getLegalActions(state)
        action = None

        if np.random.uniform() < self.epsilon:
            # 在這個 state 採取每個 legal action 後的 Qvalue
            state_action = [self.Q_table[state, act] for act in legalActions]
            action = legalActions[np.random.choice(np.where(state_action == np.max(state_action))[0])]
        else:
            action = np.random.choice(legalActions)

        return action
    
    def update(self, state, action, reward, next_state):
        q_predict = self.Q_table[state, action]

        if next_state != 'terminal':
            legalActions = self.getLegalActions(next_state)
            new = np.max([self.Q_table[next_state, act] for act in legalActions])
            q_target = reward + self.gamma * new
        else:
            q_target = reward

        self.Q_table[state, action] += self.lr * (q_target - q_predict)
    

    ###### TODO ######
    def getLegalActions(self, playerStat, parallel_wall, vertical_wall):

        directions = {"left": (0, -1), "right": (0, 1), "up": (-1, 0), "down": (1, 0), "no_control": (0, 0)}

        possible = []
        for dir, (dx, dy) in directions.items():

            if dir == "no_control":
                possible.append(dir)
                continue

            next_x = playerStat[0] + dx
            next_y = playerStat[1] + dy

            if next_x < 0: next_x = 0
            if next_y < 0: next_y = 0


            if (dir == "up" or dir == "down") and not parallel_wall[next_x][next_y]:
                possible.append(dir)
            elif (dir == "left" or dir == "right") and not vertical_wall[next_x][next_y]:
                possible.append(dir)

        return possible


"""
(0,0) (0,1) (0,2)
(1,0) (1,1) (1,2)
(2,0) (2,1) (2,2)

"""


def training():

    RL = QLearningAgent(actions=[0, 1, 2, 3, 4]) # landmine
    
    for episode in range(100):
        
        # TODO reset game
        (stop_program, id_package, parallel_wall, vertical_wall) = STcpClient.GetMap()
        (stop_program, id_package, playerStat, otherPlayerStat, ghostStat, propsStat) = STcpClient.GetGameStat()

        while True:
            global action
            action = None
            action = RL.choose_action(state)
            

            # TODO getStep
            user_thread = MyThread(target=getStep, args=(playerStat, ghostStat, propsStat))
            user_thread.start()
            time.sleep(4/100)
            if action == None:
                user_thread.kill()
                user_thread.join()
                action = [4, False]
            is_connect = STcpClient.SendStep(id_package, action[0], action[1])

            (stop_program, id_package, playerStat, otherPlayerStat, ghostStat, propsStat) = STcpClient.GetGameStat()

            next_state = playerStat
            reward = playerStat[3]


            RL.update(state, action, reward, next_state)

            state = next_state

            if stop_program or stop_program is None or not is_connect:
                break

        print(f'Episode {episode} game over')


if __name__ == "__main__":
    training()