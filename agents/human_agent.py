import random
from dataclasses import dataclass, field

from api.classes import Action, Agent, AvailableActions, Observation, Rules


@dataclass
class HumanAgent(Agent):
    agent_type_id : str = "random"

    def take_action(self, rules : Rules, observation: Observation, available_actions: AvailableActions, show_state : bool):
        actions = list(available_actions.predefined.keys())
        for i, action in enumerate(actions):
            print(f"\t{i}. {action}")
        try:
            action_id = actions[int(input(">>> "))]#random.choice(actions)
        except IndexError:
            raise Exception("Agent was given zero available actions.")
        return Action(action_id=action_id)