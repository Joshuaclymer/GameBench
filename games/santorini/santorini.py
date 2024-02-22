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
class Santorini(Game):
    rules: Rules = Rules(
        title="Santorini",
        summary='Win by moving one of your pawns to the third level of the board or forcing your opponent to be unable to finish their turn. The game is played on a five by five grid of squares, and each player controls two pawns. Play alternates between the players, starting with player 1. The pawn that a player plays with alternates during each of their turns: for example, player 1 plays pawn A on their first turn, pawn B on their next turn, then pawn A, and so on. Blocks can be placed on squares on the board up to four blocks high, creating four possible height levels.\n\nThe board begins with no blocks placed, so every square begins at level 0. Before the game starts, each of the players takes turns placing each of their pawns on the board. A square is occupied if a pawn is on it.\n\nEach turn consists of two stages: the "move" stage and the "build" stage. During the move stage, the player moves their pawn by one square (horizontally, vertically, or diagonally). They cannot move their pawn onto a square that is occupied by another pawn, more than one level higher than the pawn, or at level 4. They can move a pawn any number of levels down, to the same level, or one level higher, but not more than one level higher and not to level 4.\n\nDuring the build stage, the player must select an unoccupied square adjacent to the pawn they moved during the move stage and place a block on it. They can place a block onto an unoccupied square at any level less than 4. Once a square has been built to level 4, it is "complete", meaning pawns cannot move to it and blocks cannot be placed on it. The player instantly wins if they move their pawn onto a square at level 3 or if they force their opponent to not be able to finish their turn.',  # noqa: E501
        additional_details=None,
    )
    id: str = "santorini"
    agents: List[Agent] = None
    show_state: bool = False
    game_is_over: bool = False
    board: Board = None
    colored_output: bool = True

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
        pawns = []
        for pawn in self.board.pawns:
            if pawn.player_number == agent.team_id:
                pawns.append(pawn)
        return pawns

    def get_opponent_pawns(self, agent: Agent) -> List[Pawn]:
        pawns = []
        for pawn in self.board.pawns:
            if pawn.player_number != agent.team_id:
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
        board_matrix = board.board
        board_string = ""

        for pawn in board.pawns:
            position = pawn.pos
            if position is None or position[0] is None or position[1] is None:
                continue
            letter = self.pawn_letter(pawn)
            board_matrix[position[0]][position[1]] = letter

        for i in range(len(board_matrix)):
            for square in board_matrix[i]:
                board_string += self.square_to_string(square)
                # Add a space between each square to help the LLM read the board (to ensure that each square is parsed as a separate token)
                board_string += " "
            board_string += "\n" if i != len(board_matrix) - 1 else ""

        return board_string

    def square_to_string(self, square: int) -> str:
        square_color_mapping = {
            0: Fore.BLACK,
            1: Fore.BLUE,
            2: Fore.GREEN,
            3: Fore.CYAN,
            4: Fore.WHITE,
            "A": Back.BLUE,
            "B": Back.CYAN,
            "X": Back.RED,
            "Y": Back.MAGENTA,
        }
        if self.colored_output:
            return square_color_mapping[square] + str(square) + Style.RESET_ALL
        else:
            return str(square)

    def get_general_observation(self, agent: Agent) -> Observation:
        board_string = self.board_string()
        pawns = self.get_pawns(agent)
        pawn_letters = [self.pawn_letter(pawn) for pawn in pawns]
        opponent_pawns = self.get_opponent_pawns(agent)
        opponent_pawn_letters = [self.pawn_letter(pawn) for pawn in opponent_pawns]

        observation_text = f"Player {agent.team_id}, it is your turn. You control two pawns, represented as the letters {pawn_letters[0]} and {pawn_letters[1]}, and your opponent controls pawns {opponent_pawn_letters[0]} and {opponent_pawn_letters[1]}. Each non-occupied square is represented as a digit corresponding to what level it is, from 0 to 4. Here is the board:\n\n{board_string}"
        return Observation(text=observation_text)

    # These direction–name functions are not elegant. I just had CodePilot manually write them for me. One idea if I wanted to refactor the code is to define a class-level constant matrix with each of the direction names and use it in each function to translate between relative directions and names.
    def relative_direction_name(
        self, pawn: Pawn, second_position: Tuple[int, int]
    ) -> str:
        """Given a pawn and a position adjacent to the pawn, return the relative direction name. For example, if a pawn is at (0, 0), the position (0, 1) returns 'east' and (1, 1), returns 'southeast'."""
        pawn_position = pawn.pos
        if pawn_position[0] == second_position[0]:
            if pawn_position[1] < second_position[1]:
                return "east"
            else:
                return "west"
        elif pawn_position[1] == second_position[1]:
            if pawn_position[0] < second_position[0]:
                return "south"
            else:
                return "north"
        else:
            if pawn_position[0] < second_position[0]:
                if pawn_position[1] < second_position[1]:
                    return "southeast"
                else:
                    return "northeast"
            else:
                if pawn_position[1] < second_position[1]:
                    return "southwest"
                else:
                    return "northwest"

    def adjacent_position(self, pawn: Pawn, direction: str) -> Tuple[int, int]:
        """ "Given a pawn and a direction name (e.g. "north"), return the position adjacent to the pawn in that direction."""
        direction_name_mapping = {
            "north": [-1, 0],
            "south": [1, 0],
            "east": [0, 1],
            "west": [0, -1],
            "northeast": [-1, 1],
            "northwest": [-1, -1],
            "southeast": [1, 1],
            "southwest": [1, -1],
        }
        try:
            assert direction in direction_name_mapping
        except AssertionError:
            raise Exception(f"Invalid direction: {direction}")
        x_offset, y_offset = direction_name_mapping[direction]
        pawn_position = pawn.pos
        return (pawn_position[0] + x_offset, pawn_position[1] + y_offset)

    def get_move_build_observation(
        self, agent: Agent
    ) -> Tuple[Observation, AvailableActions, Dict[str, Play]]:  # noqa: E501
        observation = self.get_general_observation(agent)

        # TODO: double check that tokenization makes sense (ints are separate tokens)

        pawn = self.board.get_playing_pawn()

        if pawn.player_number != agent.team_id:
            self.display_message(
                f"The agent's team ID is out of sync with the current pawn's player number, which means that the agent ran out of options and lost."
            )
            return {}, {}, {}

        pawn_letter = self.pawn_letter(pawn)

        available_actions = AvailableActions(
            instructions=f"For this turn, you are playing with pawn {pawn_letter}. Pick which direction you want to move pawn {pawn_letter} and where you want to build a block relative to it after it has moved.",  # noqa: E501
            predefined={},
            openended={},
        )
        possible_plays: List[
            Tuple[Tuple[int, int], Tuple[int, int]]
        ] = self.board.get_possible_movement_and_building_positions(pawn)  # noqa: E501
        action_name_mapping: Dict[str, Play] = {}
        for play in possible_plays:
            (move, build) = play
            move_direction = self.relative_direction_name(pawn, move)
            build_direction = self.relative_direction_name(pawn, build)
            action_id = f"Move {move_direction}, build {build_direction}"
            action_name_mapping[action_id] = play
            action_description = f"Move pawn {pawn_letter} from {pawn.pos} to {play} and then build a block on {build}."  # noqa: E501
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

    def place_pawn(self, action: Action):
        move: Tuple = ast.literal_eval(action.action_id)
        # This returns false if the move is invalid, but it should never return false because I will only present the agent with valid moves.
        self.display_message(f"Placed at {move}.\n")
        self.board.place_pawn(move)

    def play_turn(
        self,
        action: Action,
        available_actions: AvailableActions,
        action_name_mapping: Dict[str, Play],
    ):
        action = action.action_id
        if action not in available_actions.predefined:
            action = random.choice(list(available_actions.predefined.keys()))

        play = action_name_mapping[action]
        move, build = play
        self.display_message(f"Moved to {move} and built at {build}.\n")
        self.board.play_move(move, build)

    def play(self) -> Tuple[float, float]:
        """Return the scores for agent_1 and agent_2 after the game is finished."""
        # Returns 1 for the winning team, 0 for the losing team, and 0.5 for a draw.

        self.display_message("Placing the pawns.\n")
        for i in range(2):
            for agent in self.agents:
                self.display_message(
                    f"Player {agent.team_id} is placing pawn {self.pawn_letter(self.board.get_playing_pawn())}."
                )  # noqa: E501
                self.display_message(self.board_string())
                observation, available_actions = self.get_pawn_placement_observation(
                    agent
                )
                action = agent.take_action(
                    self.rules,
                    observation,
                    available_actions,
                    show_state=self.show_state,
                )
                self.place_pawn(action)

        self.display_message("Playing the game.\n")
        while not self.board.is_game_over():
            for agent in self.agents:
                self.display_message(
                    f"Player {agent.team_id} is playing pawn {self.pawn_letter(self.board.get_playing_pawn())}."
                )  # noqa: E501
                self.display_message(self.board_string())
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
            self.display_message("It was a draw.")
            return (0.5, 0.5)
        else:
            self.display_message(f"Player {winner_number} wins!")
            return (1.0, 0.0) if winner_number == 1 else (0.0, 1.0)
