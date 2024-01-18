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
from santorinai.board import (Board, Pawn)
from santorinai.board_displayer.board_displayer import (
    init_window,
    update_board,
    close_window,
)
from time import sleep

class MyPlayer(Player):

# TODO: revise the rules; players don't choose which of their pawns to play each round
@dataclass
class Santorini(Game):
    rules: Rules = Rules(
        title="Santorini",
        summary='Win by moving one of your pawns to the third level of the board or forcing your opponent to be unable to move. The game is played on a five by five grid of squares, and each player controls two pawns. Blocks can be placed on squares on the board up to three blocks high, creating three possible height levels. The board begins with no blocks placed, so every square begins at level 0. Before the game starts, player 1 places each of their pawns anywhere on the board, and then player 2 places their pawns in any two unoccupied squares. A square is occupied if a pawn is on it.\n\nPlay alternates between the players, starting with player 1. Each turn consists of two stages: the "move" stage and the "build" stage. During the move stage, the player  (horizontally, vertically, or diagonally). They cannot move a pawn onto a square that is occupied by another pawn, occupied by a dome, or is more than one level higher than the pawn. They can move a pawn any number of levels down, to the same level, or one level higher, but not more than one level higher.\n\nDuring the build stage, the player must select an unoccupied square adjacent to the pawn they moved during the move stage and place a block or dome on it. They can place a block onto an unoccupied square at any level except level 3, or they can place a dome onto a square at level 3, marking the square as "complete". The player instantly wins if they move their pawn onto a square at level 3, or if their opponent is finish their turn by moving and building.',
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
    
    def pawn_letter(pawn: Pawn) -> str:
        letter_mapping = {
            1: "A",
            2: "X",
            3: "B",
            4: "Y",
        }
        return letter_mapping[pawn.number]

    def get_pawns(self, agent: Agent) -> List[Pawn]:
        pawns = []
        for pawn in self.board.pawns:
            if pawn.player_number == Agent.team_id + 1:
                pawns.append(pawn)
        return pawns
    
    def get_opponent_pawns(self, agent: Agent) -> List[Pawn]:
        pawns = []
        for pawn in self.board.pawns:
            if pawn.player_number != Agent.team_id + 1:
                pawns.append(pawn)
        return pawns

    def board_string(self) -> str:
        # 1. Convert matrix of ints into a string, with more semantic characters
        # 2. Add the pawns to the string
        # Board values:
        # 0 = empty
        # 1 = tower level 1
        # 2 = tower level 2
        # 3 = tower level 3
        # 4 = terminated tower
        board = self.board.copy()
        board_matrix = board.board_matrix
        board_string = ""

        for pawn in board.pawns:
            position = pawn.pos
            letter = self.pawn_letter(pawn.number)
            board_matrix[position[0]][position[1]] = letter

        for row in board:
            for square in row:
                board_string += str(square)
                # Add a space between each square to help the LLM read the board (to ensure that each square is parsed as a separate token)
                board_string += " "
            board_string += "\n"

        return board_string

    def get_general_observation(self, agent: Agent) -> Observation:
        board_string =  self.board_string()
        pawns = self.get_pawns(agent)
        pawn_letters = [self.pawn_letter(pawn) for pawn in pawns]
        opponent_pawns = self.get_opponent_pawns(agent)
        opponent_pawn_letters = [self.pawn_letter(pawn) for pawn in opponent_pawns]

        current_pawn = self.board.get_playing_pawn()
        assert current_pawn.player_number == agent.team_id + 1

        observation_text = f"Player {agent.team_id + 1}, it is your turn. You control two pawns, represented as the letters {pawn_letters[0]} and {pawn_letters[1]}, and your opponent controls pawns {opponent_pawn_letters[0]} and {opponent_pawn_letters[1]}. Each non-occupied square is represented as a digit corresponding to what level it is, from 0 to 4. Here is the board:\n\n{board_string}"
        return Observation(text=board_string)
    
    def direction_name(self, pawn: Pawn, next_position: Tuple[int, int]) -> str:
        """Given a pawn and a position that it can move to, return the direction name corresponding to that move. For example, if a pawn is at (0, 0) and can move to (0, 1), return 'east', and if it can move to (1, 1), return 'southeast'."""
        current_position = pawn.pos
        if current_position[0] == next_position[0]:
            if current_position[1] < next_position[1]:
                return "east"
            else:
                return "west"
        elif current_position[1] == next_position[1]:
            if current_position[0] < next_position[0]:
                return "south"
            else:
                return "north"
        else:
            if current_position[0] < next_position[0]:
                if current_position[1] < next_position[1]:
                    return "southeast"
                else:
                    return "northeast"
            else:
                if current_position[1] < next_position[1]:
                    return "southwest"
                else:
                    return "northwest"

    def get_move_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        observation = self.get_general_observation(agent)
        
        # TODO: double check that tokenization makes sense (ints are separate tokens)

        pawn = self.board.get_playing_pawn()
        pawn_letter = self.pawn_letter(pawn)

        available_actions = AvailableActions(
            instructions=f'You are in the "move" phase of your turn, and you are controlling pawn {pawn_letter}. Pick which direction you want to move your pawn in.',
            predefined={},
            openended={},
        )
        possible_moves = self.board.get_possible_movement_positions(pawn)
        for move in possible_moves:
            move_direction = self.direction_name(pawn, move)
            action_label = f"Move {move_direction}"
            action_description = f"Move pawn {pawn_letter} from {pawn.pos} to {move}."
            available_actions.predefined[action_label] = action_description

        return observation, available_actions
    
    def get_build_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        observation = self.get_general_observation(agent)

        pawn = self.board.get_playing_pawn()
        pawn_letter = self.pawn_letter(pawn)

        available_actions = AvailableActions(
            instructions=f'You are in the "build" phase of your turn, and you are controlling pawn {pawn_letter}. Pick which direction relative to your pawn you want to build a block in.',
            predefined={},
            openended={},
        )

        possible_building_positions = self.board.get_possible_building_positions(pawn)
        for position in possible_building_positions:
            build_direction = self.direction_name(pawn, position)
            action_label = f"Build {build_direction}"
            action_description = f"Place a block on square {position}."
            available_actions.predefined[action_label] = action_description

        return observation, available_actions
    
    def get_pawn_placement_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        observation = self.get_general_observation(agent)

        pawn = self.board.get_playing_pawn()
        pawn_letter = self.pawn_letter(pawn)

        available_actions = AvailableActions(
            instructions=f'You are in the "initial pawn placement" phase of the game, and you are controlling pawn {pawn_letter}. Pick where you want to place it.',
            predefined={},
            openended={},
        )

        possible_placement_positions = self.board.get_possible_movement_positions(pawn)
        for position in possible_placement_positions:
            action_label = f"Place pawn at {position}"
            action_description = f"Place pawn {pawn_letter} at {position}."
            available_actions.predefined[action_label] = action_description

        return observation, available_actions
    
    def update(self, action: Action, available_actions: AvailableActions, agent: Agent):
        # Choose a random action if an invalid action was chosen
        action = action.action_id
        if action not in available_actions.predefined:
            action = random.choice(list(available_actions.predefined.keys()))

        

    def play(self) -> Tuple[float, float]:
        """Returns the scores for agent_1 and agent_2 after the game is finished."""
        # Returns 1 for the winning team, 0 for the losing team
        # A tie should not be possible since the other player wins if a player can't finish their move, and it must end since a block is placed on every turn, so eventually the board will be full and a player will not be able to move their pawn or build another block
        # First, let each agent place their pawns
        # Then, enter a loop where each agent takes a turn
        # The loop exits when one of the agents wins
        # Originally was planning to use SantoriniAI's tester.py, but I've realized it makes more sense to implement a version of it myself
        
        self.display_message("\nPlacing the pawns")
        for i in range(2):
            for agent in self.agents:
                observation, available_actions = self.get_pawn_placement_observation(agent)
                action = agent.take_action(
                    self.rules,
                    observation,
                    available_actions,
                    show_state=self.show_state,
                )
                self.update(action, available_actions, agent)

        self.display_message("\nPlaying the game")
        while not board.is_game_over():
            current_pawn = board.get_playing_pawn()
            # self.display_message(f"   Current pawn: {current_pawn}", 2)

            # Check if the player can move
            if len(board.get_possible_movement_positions(current_pawn)) == 0:
                # self.display_message("   The pawn cannot move", 2)
                board.next_turn()
                # We don't ask the player to move, we just skip his turn
                continue
        
            # Move the pawn and build
            player = players[current_pawn.player_number - 1]
            move_choice = [0,2]
            build_choice = [0,1]
            success, reason = board.play_move(move_choice, build_choice)

            # If they give an invalid move
            if not success:
                    # self.display_message(
                    #     f"   Pawn moved at an invalid position: {reason}", 1
                    # )
                    # self.display_message(f"   Player {player.name()} loses")
                    return [1.0, 0.0] if player_num == 0 else [0.0, 1.0]
                    break
        
            winner_number = board.winner_player_number
            # If there's a draw
            if winner_number is None:
                return [0.5, 0.5]
            
            return [1.0, 0.0] if winner_number == 0 else [0.0, 1.0]
        
        while True:
            for agent in self.agents:
                observation, available_actions = self.get_move_observation(agent)
                action = agent.take_action(
                    self.rules,
                    observation,
                    available_actions,
                    show_state=self.show_state,
                )
                self.update(action, available_actions, agent)

            # if len(self.players) == 0:
            #     return (0.5, 0.5)

            # if all(player.agent.team_id == 0 for player in self.players):
            #     return (1.0, 0.0)

            # if all(player.agent.team_id == 1 for player in self.players):
            #     return (0.0, 1.0)