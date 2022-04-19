import numpy as np
import pandas as pd
import util

class QLearnAgent():

    def __init__(self, alpha=0.2, epsilon=0.05, gamma=0.8, numTraining = 10):
        self.alpha = float(alpha) # learning rate
        self.epsilon = float(epsilon) # exploration rate
        self.gamma = float(gamma) # discount factor
        self.numTraining = int(numTraining)
        self.QValues = util.Counter()

    def getQValue(self, state, action):
        return self.QValues[state, action]

    def computeValueFromQValues(self, state):
         # Returns max_action Q(state,action)
        values = [self.getQValue(state, action) for action in self.getLegalActions(state)]
        # if (values):
        #     return max(values)
        # else:
        #     return 0.0

        return (max(values) if values else 0.0)
    
    def computeActionFromQValues(self, state):
        # Compute the best action to take in a state
        legal_actions = self.getLegalActions(state) #all the legal actions

        value = self.getValue(state)
        for action in legal_actions:
            if (value == self.getQValue(state, action)):
                return action

    def choose_action(self, state):
        legalActions = self.getLegalActions(state)
        action = None

        if np.random.uniform() < self.epsilon:
            action = np.random.choice(legalActions)
        else:
            action = self.getPolicy(state)

        return action

    def update(self, state, action, nextState, reward):
        newQValue = (1 - self.alpha) * self.getQValue(state, action)
        newQValue += self.alpha * (reward + (self.gamma * self.getValue(nextState)))
        self.QValues[state, action] = newQValue

    def getPolicy(self, state):
        return self.computeActionFromQValues(state)

    def getValue(self, state):
        return self.computeValueFromQValues(state)


    ###### TODO ######
    def getLegalActions(self, state):

        print(state)

