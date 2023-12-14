from dataclasses import dataclass, field
from api.classes import Agent, AvailableActions, Action, Observation
import random

@dataclass
class OpenAIAgent(Agent):
    agent_type_id : str = "random"
    openai_model : str

    def take_action(self, observation: Observation, available_actions: AvailableActions, show_state : bool):
        actions = list(available_actions.predefined.keys())
        return Action(action_id=random.choice(actions))