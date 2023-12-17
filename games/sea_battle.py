from dataclasses import dataclass, field
import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import ast

# two agents, but multiple copies on each team

@dataclass
class SeaBattle(Game):
    id : str = "sea_battle"
    rules : Rules = Rules(
        title="Sea Battle",
        summary="Sink all of your opponent team's ships before they sink all of your team's ships.",
        additional_details=None
    )

    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.agents = []

    def get_board_string(self):
        """Ideas
        - the grid is 2d, so return a 2d grid of symbols
        - a list of objects and their coordinates
        """
        board_string = ""
        return board_string

    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        """Ideas
        - a list of actions followed by a number
        - a certain syntax that describes a move
        """


        available_actions = AvailableActions(
            instructions="Return your action as a number ",
            predefined = {

            }
        )

    def update(self, action : Action, available_actions : AvailableActions):
        action = action.action_id
        if action not in available_actions.predefined:
            action = random.choice(list(available_actions.keys()))

    def play(self) -> Tuple[float, float]:
        while True:
            for player in self.agents:
                observation, available_actions = self.get_observation(player)
                action = player.take_action(self.rules, observation, available_actions)
                self.update(action, available_actions, player)

            if self.game_is_over:
                break

                return (1., 0.) if self.winning_team == 0 else (0., 1.)