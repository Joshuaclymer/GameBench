import ast
import random
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from api.classes import Action, Agent, AvailableActions, Game, Observation, Rules

import santorinai
from santorinai.player_examples.random_player import RandomPlayer
from santorinai.tester import Tester
from santorinai.player import Player
from santorinai.board import Board
from santorinai.board_displayer.board_displayer import (
    init_window,
    update_board,
    close_window,
)
from time import sleep

class MyPlayer(Player):

@dataclass
class Santorini(Game):
    rules: Rules = Rules(
        title="Santorini",
        summary='Win by moving one of your pawns to the third level of the board or forcing your opponent to be unable to move. The game is played on a five by five grid of squares, and each player controls two pawns. Blocks can be placed on squares on the board up to three blocks high, creating three possible height levels. The board begins with no blocks placed, so every square begins at level 0. Before the game starts, player 1 places each of their pawns anywhere on the board, and then player 2 places their pawns in any two unoccupied squares. A square is occupied if a pawn is on it. Play alternates between the players, starting with player 1. Each turn consists of two stages: the "move" stage and the "build" stage. During the move stage, a player must select one of their pawns and move it to an adjacent square (horizontally, vertically, or diagonally). They cannot move a pawn onto a square that is occupied by another pawn, occupied by a dome, or is more than one level higher than the pawn. They can move a pawn any number of levels down, to the same level, or one level higher, but not more than one level higher. During the build stage, the player must select an unoccupied square adjacent to the pawn they moved during the move stage and place a block or dome on it. They can place a block onto an unoccupied square at any level except level 3, or they can place a dome onto a square at level 3, marking the square as "complete". The player instantly wins if they move their pawn onto a square at level 3, or if their opponent is finish their turn by moving and building.',
        additional_details=None,
    )
    id: str = "santorini"
    agents: List[Agent] = None
    show_state: bool = False
    game_is_over: bool = False
    board: Board = None

    def init_game(self, agent_1: Agent, agent_2: Agent):
        self.agents = [agent_1(team_id=0, agent_id=0), agent_2(team_id=1, agent_id=1)]
        board = Board(2)

    def get_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        # return a tuple with observation and available actions
        # observation is just a text representation of the board, and maybe in the future an image
        # available actions has the possible actions the agent can take and instructions on how to use them
        pass

    def update(self, action: Action, available_actions: AvailableActions, agent: Agent):
        pass

    def play(self) -> Tuple[float, float]:
        """Returns the scores for agent_1 and agent_2 after the game is finished."""
        # Returns 1 for the winning team, 0 for the losing team
        # A tie should not be possible since the other player wins if a player can't finish their move, and it must end since a block is placed on every turn, so eventually the board will be full and a player will not be able to move their pawn or build another block
        # First, let each agent place their pawns
        # Then, enter a loop where each agent takes a turn
        # The loop exits when one of the agents wins
        # Originally was planning to use SantoriniAI's tester.py, but I've realized it makes more sense to implement a version of it myself
