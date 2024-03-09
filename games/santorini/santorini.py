import ast
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from colorama import Back, Fore, Style
from santorinai.board import Board, Pawn

from api.classes import Action, Agent, AvailableActions, Game, Observation, Rules


@dataclass
class Play:
    move: Tuple[int, int]
    build: Tuple[int, int]


@dataclass
class BoardSquare:
    """Used to represent a square on the board when converting the board into a string."""

    level: int
    pawn_letter: str


@dataclass
class RelativePosition:
    name: str
    position: Tuple[int, int]


@dataclass
class Santorini(Game):
    rules: Rules = Rules(
        title="Santorini",
        summary='Win by moving one of your pawns to the third level of the board or forcing your opponent to be unable to finish their turn. The game is played on a five by five grid of squares, and each player controls two pawns. Play alternates between the players, starting with player 1. The pawn that a player plays with alternates during each of their turns: for example, player 1 plays pawn A on their first turn, pawn B on their next turn, then pawn A, and so on. Blocks can be placed on squares on the board up to four blocks high, creating four possible height levels.\n\nThe board begins with no blocks placed, so every square begins at level 0. Before the game starts, each of the players takes turns placing each of their pawns on the board. A square is occupied if a pawn is on it.\n\nEach turn consists of two stages: the "move" stage and the "build" stage. During the move stage, the player moves their pawn by one square (horizontally, vertically, or diagonally). They cannot move their pawn onto a square that is occupied by another pawn, more than one level higher than the pawn, or at level 4. They can move a pawn any number of levels down, to the same level, or one level higher, but not more than one level higher and not to level 4.\n\nDuring the build stage, the player must select an unoccupied square adjacent to the pawn they moved during the move stage and place a block on it. They can place a block onto an unoccupied square at any level less than 4. Once a square has been built to level 4, it is "complete", meaning pawns cannot move to it and blocks cannot be placed on it. The player instantly wins if they move their pawn onto a square at level 3 or if they force their opponent to not be able to finish their turn.',
        additional_details=None,
    )
    id: str = "santorini"
    agents: List[Agent] = None
    show_state: bool = False
    game_is_over: bool = False
    board: Board = None
    colored_output: bool = True
    DIRECTION_NAME_MATRIX = [
        ["northwest", "north", "northeast"],
        ["west", None, "east"],
        ["southwest", "south", "southeast"],
    ]

    def init_game(self, agent_1: Agent, agent_2: Agent):
        self.agents = [agent_1(team_id=1, agent_id=1), agent_2(team_id=2, agent_id=2)]
        self.board = Board(2)

    def pawn_letter(self, pawn: Pawn) -> str:
        letter_mapping = {
            1: "A",
            2: "X",
            3: "B",
            4: "Y",
        }
        return letter_mapping[pawn.number]

    def get_pawns(self, agent: Agent) -> List[Pawn]:
        return [
            pawn for pawn in self.board.pawns if pawn.player_number == agent.team_id
        ]

    def get_opponent_pawns(self, agent: Agent) -> List[Pawn]:
        return [
            pawn for pawn in self.board.pawns if pawn.player_number != agent.team_id
        ]

    def get_board_matrix(self) -> List[List[BoardSquare]]:
        """Return a matrix representation of the board, where each square is represented as a list of two elements: the first element is the level of the square, and the second element is the letter of the pawn that is on the square, or "." if the square is not occupied."""

        original_board = self.board.copy()
        board_matrix: List[List[BoardSquare]] = [
            [
                BoardSquare(level=original_board.board[i][j], pawn_letter=".")
                for j in range(5)
            ]
            for i in range(5)
        ]

        for pawn in original_board.pawns:
            position = pawn.pos
            if position is None or position[0] is None or position[1] is None:
                continue
            letter = self.pawn_letter(pawn)
            board_matrix[position[0]][position[1]].pawn_letter = letter

        return board_matrix

    def board_string_for_agent(self) -> str:
        """Return a string representation of the board to be displayed to an agent."""

        board_matrix = self.get_board_matrix()
        board_string = ""

        for i in range(len(board_matrix)):
            for square in board_matrix[i]:
                board_string += str(square.level) + square.pawn_letter + " "
            board_string += "\n" if i != len(board_matrix) - 1 else ""

        return board_string

    def board_string_for_user(self) -> str:
        """Return a string representation of the board to be displayed to a human user in the terminal."""
        # TODO: replace board_string_for_user with a print board for user function
        level_color_mapping = {
            0: Back.BLACK,
            1: Back.BLUE,
            2: Back.GREEN,
            3: Back.CYAN,
            4: Back.WHITE,
        }
        pawn_color_mapping = {
            "A": Fore.BLACK,
            "B": Fore.BLACK,
            "X": Fore.WHITE,
            "Y": Fore.WHITE,
            " ": "",
        }

        board_matrix = self.get_board_matrix()
        board_string = ""

        for i in range(len(board_matrix)):
            for square in board_matrix[i]:
                pawn_letter = square.pawn_letter
                if pawn_letter == ".":
                    pawn_letter = " "
                if self.colored_output:
                    board_string += (
                        level_color_mapping[square.level]
                        + pawn_color_mapping[pawn_letter]
                        + pawn_letter
                        + Style.RESET_ALL
                    )
                else:
                    board_string += pawn_letter
            board_string += "\n" if i != len(board_matrix) - 1 else ""

        board_string += "\n"

        return board_string

    def get_general_observation(self, agent: Agent) -> Observation:
        board_string = self.board_string_for_agent()
        pawns = self.get_pawns(agent)
        pawn_letters = [self.pawn_letter(pawn) for pawn in pawns]
        opponent_pawns = self.get_opponent_pawns(agent)
        opponent_pawn_letters = [self.pawn_letter(pawn) for pawn in opponent_pawns]

        observation_text = f"Player {agent.team_id}, it is your turn. You control two pawns, represented as the letters {pawn_letters[0]} and {pawn_letters[1]}, and your opponent controls pawns {opponent_pawn_letters[0]} and {opponent_pawn_letters[1]}. Each non-occupied square is represented as a digit corresponding to what level it is, from 0 to 4. Here is the board:\n\n{board_string}"
        return Observation(text=observation_text)

    def relative_direction_name(
        self, first_position: Tuple[int, int], second_position: Tuple[int, int]
    ) -> str:
        """Given a pawn and a position adjacent to the pawn, return the relative direction name. For example, if a pawn is at (0, 0), the position (0, 1) returns 'east' and (1, 1), returns 'southeast'."""
        relative_position = (
            second_position[0] - first_position[0],
            second_position[1] - first_position[1],
        )
        # matrix_lookup = map(lambda x: x + 1, relative_position)
        matrix_lookup = (relative_position[0] + 1, relative_position[1] + 1)
        return self.DIRECTION_NAME_MATRIX[matrix_lookup[0]][matrix_lookup[1]]

    def relative_position(self, pawn: Pawn, direction: str) -> Tuple[int, int]:
        """Given a pawn and a direction name (e.g. "north"), return the position adjacent to the pawn in that direction."""
        # try:
        #     assert direction in self.DIRECTION_NAME_MAPPING
        # except AssertionError:
        #     raise Exception(f"Invalid direction: {direction}")
        # x_offset, y_offset = self.DIRECTION_NAME_MAPPING[direction]
        # pawn_position = pawn.pos
        # return (pawn_position[0] + x_offset, pawn_position[1] + y_offset)

        matrix_position = (1, 1)
        for i, row in enumerate(self.DIRECTION_NAME_MATRIX):
            if direction in row:
                matrix_position = (i, row.index(direction))
                break
        relative_position = map(lambda x: x - 1, matrix_position)

        if relative_position == (0, 0):
            raise ValueError(f"Direction '{direction}' not found in matrix.")

        return relative_position

    def get_move_build_observation(
        self, agent: Agent
    ) -> Tuple[Observation, AvailableActions, Dict[str, Play]]:
        observation = self.get_general_observation(agent)

        # TODO: double check that tokenization makes sense (ints are separate tokens)

        pawn = self.board.get_playing_pawn()

        if pawn.player_number != agent.team_id:
            self.display_message(
                "The agent's team ID is out of sync with the current pawn's player number, which means that the agent ran out of options and lost."
            )
            return {}, {}, {}

        pawn_letter = self.pawn_letter(pawn)

        available_actions = AvailableActions(
            instructions=f"For this turn, you are playing with pawn {pawn_letter}. Pick which direction you want to move pawn {pawn_letter} and where you want to build a block relative to it after it has moved.",
            predefined={},
            openended={},
        )
        possible_plays: List[Tuple[Tuple[int, int], Tuple[int, int]]] = (
            self.board.get_possible_movement_and_building_positions(pawn)
        )
        action_name_mapping: Dict[str, Play] = {}
        for play in possible_plays:
            (move, build) = play
            move_direction = self.relative_direction_name(pawn.pos, move)
            build_direction = self.relative_direction_name(move, build)
            action_id = f"Move {move_direction}, build {build_direction}"
            action_name_mapping[action_id] = play
            action_description = f"Move pawn {pawn_letter} from {pawn.pos} to {play} and then build a block on {build}."
            available_actions.predefined[action_id] = action_description

        return observation, available_actions, action_name_mapping

    def get_pawn_placement_observation(
        self, agent: Agent
    ) -> Tuple[Observation, AvailableActions]:
        observation = self.get_general_observation(agent)

        pawn = self.board.get_playing_pawn()
        pawn_letter = self.pawn_letter(pawn)

        available_actions = AvailableActions(
            instructions=f'You are in the "initial pawn placement" phase of the game. Decide where you want to place pawn {pawn_letter}.',
            predefined={},
            openended={},
        )

        possible_placement_positions = self.board.get_possible_movement_positions(pawn)
        for position in possible_placement_positions:
            action_id = f"{position}"
            action_description = f"Place pawn {pawn_letter} at {position}."
            available_actions.predefined[action_id] = action_description

        return observation, available_actions

    def display_message(self, message: str):
        """Prints a message to the console."""
        if self.show_state:
            print(message)

    def place_pawn(self, action: Action, available_actions: AvailableActions):
        # If the agent chose an invalid action, replace it with a random action instead.
        if action.action_id not in available_actions.predefined.keys():
            action = random.choice(list(available_actions.predefined.keys()))

        move: Tuple = ast.literal_eval(action.action_id)

        pawn_letter = self.pawn_letter(self.board.get_playing_pawn())
        player_number = self.board.get_playing_pawn().player_number

        pawn_placed, pawn_placement_error = self.board.place_pawn(move)
        if not pawn_placed:
            raise Exception(pawn_placement_error)

        self.display_message(
            f"Player {player_number} placed pawn {pawn_letter} at {move}."
        )
        self.display_message(self.board_string_for_user())

    def play_turn(
        self,
        action: Action,
        available_actions: AvailableActions,
        action_name_mapping: Dict[str, Play],
    ):
        # If the agent chose an invalid action, replace it with a random action instead.
        if action.action_id not in available_actions.predefined.keys():
            action = random.choice(list(available_actions.predefined.keys()))

        play = action_name_mapping[action.action_id]
        move, build = play
        pawn_letter = self.pawn_letter(self.board.get_playing_pawn())
        player_number = self.board.get_playing_pawn().player_number

        self.board.play_move(move, build)

        self.display_message(
            f"Player {player_number} moved pawn {pawn_letter} to {move} and built at {build}."
        )
        self.display_message(self.board_string_for_user())

    def play(self) -> Tuple[float, float]:
        """Return the scores for agent_1 and agent_2 after the game is finished."""
        # Returns 1 for the winning team and 0 for the losing team.
        # There are no draws in Santorini.

        self.display_message("Placing the pawns.\n")
        for i in range(2):
            for agent in self.agents:
                observation, available_actions = self.get_pawn_placement_observation(
                    agent
                )
                action = agent.take_action(
                    self.rules,
                    observation,
                    available_actions,
                    show_state=self.show_state,
                )
                self.place_pawn(action, available_actions)

        self.display_message("Playing the game.\n")
        while not self.board.is_game_over():
            for agent in self.agents:
                (
                    observation,
                    available_actions,
                    action_name_mapping,
                ) = self.get_move_build_observation(agent)
                if available_actions == {} or available_actions.predefined == {}:
                    self.display_message(
                        f"Player {agent.team_id} ran out of options and loses."
                    )
                    return (0.0, 1.0) if agent.team_id == 1 else (1.0, 0.0)
                current_pawn = self.board.get_playing_pawn()
                try:
                    assert current_pawn.player_number == agent.team_id
                except AssertionError:
                    raise Exception(
                        f"Agent {agent.team_id} is trying to take a turn when it is not their turn."
                    )

                action = agent.take_action(
                    self.rules,
                    observation,
                    available_actions,
                    show_state=self.show_state,
                )

                self.play_turn(action, available_actions, action_name_mapping)

        self.display_message("Game over.")

        winner_number = self.board.winner_player_number
        if winner_number is None:
            raise Exception("The game is over, but there is no winner.")
        else:
            self.display_message(f"Player {winner_number} wins!")
            return (1.0, 0.0) if winner_number == 1 else (0.0, 1.0)
