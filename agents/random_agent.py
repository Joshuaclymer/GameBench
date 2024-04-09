from dataclasses import dataclass, field
from api.classes import Agent, AvailableActions, Action, Observation, Rules
import random

@dataclass
class RandomAgent(Agent):
    agent_type_id : str = "random"

    def take_action(self, rules : Rules, observation: Observation, available_actions: AvailableActions, show_state : bool):
        actions = list(available_actions.predefined.keys()) + list(available_actions.openended.keys())
        return Action(action_id=random.choice(actions), openended_response="")