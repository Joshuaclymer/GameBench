from dataclasses import dataclass, field
import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import ast

# TODO: probably gonna need a class to represent board state
    # TODO: probably gonna need a class to represent theater state
# TODO: probably gonna need a class to represent hand state
    # TODO: how to represent cards and deck

@dataclass
class AirLandSea(Game):
    rules : Rules = Rules(
        title="Air Land and Sea",
        # TODO: complete rules class
        summary="A game of strategy and bluffing",
        additional_details = {
            "Roles": 
        }
    
    )
    id : str = "air_land_sea"

    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.agents = [agent1(team_id = 0, agent_id = 0, **self.agent_1_kwargs), agent2(team_id = 1, agent_id = 1, **self.agent_2_kwargs)]
        pass

    # TODO: must create a way to represent the board state and hand state as string
    def get_board_string(self):
        pass

    # generate observation and available actions for the agent
    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        # TODO: generate available action list based on game state and hand
        # available_actions = AvailableActions(
            # instructions = "Return actions in json with the following keys. { 'action': str }",
            # predefined = {
                # deploy
                # improvise
                # withdraw
            # openended = {}
        # TODO: is there open ended actions in this game?
        pass

    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        pass
    
    # Returns the scores for agent_1 and agent_2 after the game is finished.
    # the high level gameplay loop
    def play(self):
        player_1 = self.agents[0]
        player_2 = self.agents[1]

        while True:
            # TODO: there are multiple rounds in one game
            # reach 12 victory points to win
            # must track victory points of each player
                # check after each battle if a player has reached 12 victory points
            # must track who is the supreme commander (influences victory points players get from withdrawing)
                # TODO: what are the exact points scored from withdrawing?
                # supreme commander goes first and wins ties in theaters
            # must track current position of theaters (in order to rotate them clockwise after each battle)
                # must randomly place 3 theaters in beginning of game
            # must track each player's hand (each gets 6 in beginning of battle)

            # at end of battle, compare strength scores in each theater to determine theater winner and overall battle winner
            # end of battle is when there are no more cards to play

            # player 1
            # observation
            # action
            # update

            # player 2
            # observation
            # action
            # update
            
        pass