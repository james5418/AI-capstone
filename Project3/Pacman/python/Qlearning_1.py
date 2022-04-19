import numpy as np
import pandas as pd

class QLearningTable:

    def __init__(self, actions, learning_rate=0.01, reward_decay=0.9, e_greedy=0.9):
        self.actoins = actions
        self.lr = learning_rate
        self.gamma = reward_decay
        self.epsilon = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)

    def choose_action(self, observation):
        self.check_state_exist(observation)

        if np.random.uniform() < self.epsilon:
            state_action = self.q_table.loc[observation, :]
            action = np.random.choice(state_action[state_action == np.max(state_action)].index)
        else:
            action = np.random.choice(self.actoins)

        return action
    
    def update(self, s, a, r, s_):
        self.check_state_exist(s_)
        q_predict = self.q_table.loc[s, a]
        if s_ != 'terminal':
            q_target = r + self.gamma * self.q_table.loc[s_, :].max()
        else:
            q_target = r
        self.q_table.loc[s, a] += self.lr * (q_target - q_predict)
    
    def check_state_exist(self, state):
         if state not in self.q_table.index:
            self.q_table = self.q_table.append(
                pd.Series(
                    [0]*len(self.actions),
                    index=self.q_table.columns,
                    name=state,
                )
            )


def learn():

    RL = QLearningTable(actions=[0, 1, 2, 3, 4]) # landmine = random.choice([True, False])

    for episode in range(100):
        # 初始化 state 的观测值
        observation = env.reset() # get state from server

        while True:

            action = RL.choose_action(str(observation))

            observation_, reward, done = env.step(action) # do action

            RL.update(str(observation), action, reward, str(observation_))

            observation = observation_

            if done:
                break

    print('game over')