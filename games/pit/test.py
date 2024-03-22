# Small script to test game in VSCode

import random

# import time
from pit import PitGame
from gpt import OpenAITextAgent
from dataclasses import dataclass, field
from classes import Action, Agent, AvailableActions, Observation, Rules


@dataclass
class RandomAgent(Agent):
    agent_type_id: str = "random"

    def take_action(
        self,
        rules: Rules,
        observation: Observation,
        available_actions: AvailableActions,
        show_state: bool,
    ):
        actions = list(available_actions.predefined.keys())
        try:
            action_id = random.choice(actions)
        except IndexError:
            raise Exception("Agent was given zero available actions.")
        # time.sleep(1.5)
        return Action(action_id=action_id)


agents = [
    OpenAITextAgent(
        openai_model="gpt-4-1106-preview", agent_id=1, team_id=0, agent_type_id="agent"
    ),
    OpenAITextAgent(
        openai_model="gpt-4-1106-preview", agent_id=2, team_id=1, agent_type_id="agent"
    ),
    # RandomAgent(agent_id=1, team_id=0, agent_type_id="agent"),
    # RandomAgent(agent_id=2, team_id=1, agent_type_id="agent"),
]


if __name__ == "__main__":
    pit_game = PitGame()

    pit_game.init_game(
        agent_1_cls=agents[0],
        agent_2_cls=agents[1],
    )

    scores = pit_game.play()

    print("Final scores:", scores)
