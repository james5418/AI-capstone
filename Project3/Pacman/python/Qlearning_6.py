import numpy as np
import pandas as pd
import random
import threading
import STcpClient
import time
import sys
import csv

class Counter(dict):
    def __getitem__(self, idx):
        self.setdefault(idx, 0)
        return dict.__getitem__(self, idx)

    def incrementAll(self, keys, count):
        for key in keys:
            self[key] += count

    def argMax(self):
        if len(self.keys()) == 0: return None
        all = self.items()
        values = [x[1] for x in all]
        maxIndex = values.index(max(values))
        return all[maxIndex][0]

    def sortedKeys(self):
        sortedItems = self.items()
        compare = lambda x, y:  np.sign(y[1] - x[1])
        sortedItems.sort(cmp=compare)
        return [x[0] for x in sortedItems]

    def totalCount(self):
        return sum(self.values())

    def normalize(self):
        total = float(self.totalCount())
        if total == 0: return
        for key in self.keys():
            self[key] = self[key] / total

    def divideAll(self, divisor):
        divisor = float(divisor)
        for key in self:
            self[key] /= divisor

    def copy(self):
        return Counter(dict.copy(self))

    def __mul__(self, y ):
        sum = 0
        x = self
        if len(x) > len(y):
            x,y = y,x
        for key in x:
            if key not in y:
                continue
            sum += x[key] * y[key]
        return sum

    def __radd__(self, y):
        for key, value in y.items():
            self[key] += value

    def __add__( self, y ):
        addend = Counter()
        for key in self:
            if key in y:
                addend[key] = self[key] + y[key]
            else:
                addend[key] = self[key]
        for key in y:
            if key in self:
                continue
            addend[key] = y[key]
        return addend

    def __sub__( self, y ):
        addend = Counter()
        for key in self:
            if key in y:
                addend[key] = self[key] - y[key]
            else:
                addend[key] = self[key]
        for key in y:
            if key in self:
                continue
            addend[key] = -1 * y[key]
        return addend

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
    move, landmine = RL.choose_action(state)
    action = [move, landmine]


class QLearningAgent():

    def __init__(self, learning_rate=1, discount_factor=0.8, exploration_rate=0.8):
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = exploration_rate
        self.Q_table = Counter()
        self.parallel_wall = np.zeros((16, 17))
        self.vertical_wall = np.zeros((17, 16))


    def choose_action(self, state):
        legalActions = self.getLegalActions(state)

        if np.random.uniform() < self.epsilon:
            state_action = [self.Q_table[str((state[0], state[2], act))] for act in legalActions]
            actions = legalActions[np.random.choice(np.where(state_action == np.max(state_action))[0])]
        else:
            actions = legalActions.pop(random.randrange(len(legalActions)))

        return actions
    
    def update(self, state, action, reward, next_state):
        q_predict = self.Q_table[str((state[0], state[2], action))]

        legalActions = self.getLegalActions(next_state)
        new = np.max([self.Q_table[str((state[0], state[2], act))] for act in legalActions])
        q_target = reward + self.gamma * new

        self.Q_table[str((state[0], state[2], action))] += self.lr * (q_target - q_predict)
            

    def getLegalActions(self, state):
        
        # 0: left, 1:right, 2: up, 3: down 4:no control
        directions = {0: (-1,0), 1: (1,0), 2: (0,-1), 3: (0,1)}

        possible = []
        for dir, (dx, dy) in directions.items():
            next_x = state[0][0] + dx
            next_y = state[0][1] + dy

            if next_x < 0: next_x = 0
            if next_y < 0: next_y = 0

            # bomb
            if next_x<16 and next_y<16 and state[2][next_x][next_y]==3:
                continue

            # ghost
            if next_x<16 and next_y<16 and [next_x,next_y] in state[1] and state[0][3] == 0:
                continue
            
            if (dir == 0) and not self.vertical_wall[state[0][0]][state[0][1]]: # left
                if state[0][2]:
                    possible.append((dir, True))
                possible.append((dir, False))
            elif (dir == 1) and not self.vertical_wall[next_x][next_y]: # right
                if state[0][2]: 
                    possible.append((dir, True))
                possible.append((dir, False))
            elif (dir == 2) and not self.parallel_wall[state[0][0]][state[0][1]]: # up
                if state[0][2]: 
                    possible.append((dir, True))
                possible.append((dir, False))
            elif (dir == 3) and not self.parallel_wall[next_x][next_y]: # down
                if state[0][2]: 
                    possible.append((dir, True))
                possible.append((dir, False))

        if len(possible) == 0:
            mv = random.choice([0, 1, 2, 3])
            if state[0][2]:
                possible.append((mv, True))
            possible.append((mv, False))
            
        return possible


    def parse_player(self, playerStat):
        landmine = 1 if playerStat[2]>0 else 0
        super_time = 1 if playerStat[3]>0 else 0
        return (playerStat[0]//25, playerStat[1]//25, landmine, super_time), playerStat[4]

    def parse_ghost(self, ghostStat):
        g = [[ ghostStat[x][y]//25 for y in range(len(ghostStat[0]))] for x in range(len(ghostStat))]
        return tuple(map(tuple, g))

    def parse_prop(self, propsStat):
        prop = np.full((16, 16), -1, dtype=int)
        for p in propsStat:
            prop[p[1]//25][p[2]//25] = p[0]
        return tuple(map(tuple, prop))

    def load_agent(self):
        try:
            with open("../python/agent.csv","r") as f:
                reader = csv.reader(f)
                for row in reader:
                    key,reward = row
                    self.Q_table[key] = reward
        except:
            self.Q_table = Counter()
        # load the pre-trained agend in
        
        print("load the agent") 
    def save_agent(self):
        # save the Q-table
        
        with open('../python/agent.csv','w',newline='') as f:
            w = csv.writer(f)
            for key,value in self.Q_table.items():
                w.writerow([key,value])
        print("save the agent")

    def training(self):
        # rw = []

        (stop_program, id_package, p_wall, v_wall) = STcpClient.GetMap()
        (stop_program, id_package, playerStat, otherPlayerStat, ghostStat, propsStat) = STcpClient.GetGameStat()

        old_super_time  = playerStat[3]

        playerStat, old_reward = self.parse_player(playerStat)
        ghostStat = self.parse_ghost(ghostStat)
        propsStat = self.parse_prop(propsStat)

        state = (playerStat, ghostStat, propsStat)

        self.parallel_wall = p_wall
        self.vertical_wall = v_wall

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
                # print(f'score = {pscore}')
                self.save_agent()
                with open('../python/score.csv', 'a') as f:
                    f.write("%d\n"%pscore)
                # print(rw)
                break

            next_super_time = playerStat[3]
            playerStat, pscore = self.parse_player(playerStat)
            ghostStat = self.parse_ghost(ghostStat)
            propsStat = self.parse_prop(propsStat)

            next_state = (playerStat, ghostStat, propsStat)

            reward = pscore - old_reward

            if old_super_time < next_super_time:
                reward += 150

            # rw.append(reward)

            RL.update(state, tuple(action), reward, next_state)

            state = next_state
            old_reward = pscore
            old_super_time = next_super_time


if __name__ == "__main__":

    RL = QLearningAgent()
    RL.load_agent()
    RL.training()