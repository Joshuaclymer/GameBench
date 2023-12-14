from api.classes import Agent, AvailableActions, Action
import random

class RandomAgent(Agent):
    agent_type_id = "random"
    def take_action(observation, available_actions: AvailableActions):
        actions = available_actions.predefined
        return Action(action_id=random.choice(actions))