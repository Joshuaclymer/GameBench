from api.classes import Agent, Action, Observation, AvailableActions, Rules
from pieces import HivePiece, QueenBee, Beetle, Grasshopper, Spider, SoldierAnt
from .config import GameConfig as Config

default_config = Config()

class Hex:
    # Directions correspond to neighboring hexes in a hex grid
    DIRECTIONS = [
        (1, -1, 0), (1, 0, -1), (0, 1, -1),
        (-1, 1, 0), (-1, 0, 1), (0, -1, 1)
    ]

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y 

    def __hash__(self):
        return hash((self.x, self.y))

    def neighbor(self, direction):
        """ Returns the neighboring hex in the given direction """
        dx, dy = Hex.DIRECTIONS[direction]
        return Hex(self.x + dx, self.y + dy)
    
class HiveBoard:
    def __init__(self):
        self.board = {}  # Dictionary to store pieces keyed by their Hex coordinates
        self.last_moved_piece = None

    def add_piece(self, piece, hex):
        if hex in self.board:
            raise ValueError("There is already a piece at this position")
        self.board[hex] = piece

    def is_adjacent_to_enemy_piece(self, hex, owner):
        """
        Check if the given hex is adjacent to a piece owned by the enemy player.
        """
        for direction in range(6):
            neighbor_hex = hex.neighbor(direction)
            if neighbor_hex in self.board and self.board[neighbor_hex].owner != owner:
                return True
        return False
    
    def is_one_hive_if_added(self, hex):
        """
        Check if the hive remains connected if a piece is temporarily added.
        """
        if hex in self.board:
            return self.is_one_hive()
        else:
            temporary_piece = HivePiece("Temporary", 0)
            self.board[hex] = temporary_piece
            is_connected = self.is_one_hive()
            del self.board[hex]

    def can_place_piece(self, piece, hex):
        """
        Check if a piece can be placed at the given hex according to Hive rules.

        It must be placed adjacent to another piece and not break the One-Hive Rule.

        It cannot be adjacent to an enemy piece unless it is the first move.

        It cannot be placed on top of another piece.
        """
        if hex in self.board:
            return False

        if len(self.board.board) != 1 and not self.is_adjacent_to_enemy_piece(hex, piece.owner):
            return False

        if not self.is_one_hive_if_added(hex):
            return False

        return True

    def can_move_piece(self, from_hex, to_hex):
        """
        Check if a piece can move from from_hex to to_hex according to Hive rules.
        """
        if self.get_piece_at(to_hex) is not None:
            return False

        if not self.has_freedom_to_move(from_hex, to_hex):
            return False
        
        if not self.is_one_hive_if_removed(from_hex):
            return False

        # Temporarily move the piece to check One-Hive Rule
        piece = self.board[from_hex].pop()  # Remove the top piece temporarily
        if not self.board[from_hex]:  # If there are no more pieces on the hex, remove the hex from the board
            del self.board[from_hex]
        self.board.setdefault(to_hex, []).append(piece)  # Place it on the target

        one_hive = self.is_one_hive()

        # Move back after checking
        self.board.setdefault(from_hex, []).append(self.board[to_hex].pop())  # Move the piece back
        if not self.board[to_hex]:  # If there are no more pieces on the hex, remove the hex from the board
            del self.board[to_hex]

        return one_hive
    
    def is_one_hive_if_removed(self, hex_to_remove):
        """
        Check if the hive remains connected if a piece is temporarily removed.
        """
        temp_piece = self.board.pop(hex_to_remove, None)
        is_connected = self.is_one_hive()
        self.board[hex_to_remove] = temp_piece  # Put the piece back
        return is_connected

    def has_freedom_to_move(self, from_hex, to_hex):
        """
        Check the Freedom to Move Rule between from_hex and to_hex.
        """
        adjacent_to_from = set(self.get_adjacent_hexes(from_hex))
        adjacent_to_to = set(self.get_adjacent_hexes(to_hex))

        # Identifying shared neighbors
        shared_neighbors = adjacent_to_from.intersection(adjacent_to_to)

        # The move is not allowed if all shared neighbors are occupied
        return not all(neighbor in self.board for neighbor in shared_neighbors)
    
    def is_one_hive(self):
        """
        Check if the board still forms one connected group (One-Hive Rule).
        This can be implemented using a depth-first search from any piece on the board.
        """
        if not self.board:
            return True

        start = next(iter(self.board))
        visited = set()
        stack = [start]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            for direction in range(6):
                neighbor = current.neighbor(direction)
                if neighbor in self.board:
                    stack.append(neighbor)

        return len(visited) == len(self.board)
    
    def move_piece(self, from_hex, to_hex):
        """
        Move a piece from from_hex to to_hex, accounting for stacks of pieces.
        """
        if from_hex not in self.board or not self.board[from_hex]:
            raise ValueError("There is no piece at the starting position")

        moving_piece = self.board[from_hex][-1]  # Get the top piece from the stack
        if not self.board.get(to_hex):
            self.board[to_hex] = []

        self.board[to_hex].append(moving_piece)  # Move it to the top of the destination stack
        self.board[from_hex].pop()  # Remove it from the original stack

        if not self.board[from_hex]:  # Clean up empty stack
            del self.board[from_hex]

        self.last_moved_piece = moving_piece

    def is_piece_covered(self, hex):
        """
        Check if the piece at the given hex is covered by another piece.
        """
        return len(self.board.get(hex, [])) > 1

    def get_piece_at(self, hex):
        """
        Return the top piece at the given hex.
        """
        return self.board.get(hex, [])[-1] if self.board.get(hex) else None

    def get_adjacent_pieces(self, hex):
        """
        Returns a list of pieces adjacent to the given hex.
        """
        adjacent_pieces = []
        for direction in range(6):
            neighbor_hex = hex.neighbor(direction)
            if neighbor_hex in self.board:
                adjacent_pieces.append(self.board[neighbor_hex])
        return adjacent_pieces
    
    def get_piece_at(self, hex):
        return self.board.get(hex, None)

    def is_adjacent_empty(self, hex):
        """ Check if there are empty adjacent spaces around the hex """
        return any(self.get_piece_at(hex.neighbor(direction)) is None for direction in range(6))

class HiveGame(Game):

    config : Config = default_config
    board : HiveBoard = None
    
    def init_game(self, agent_1_class: Agent, agent_2_class : Agent):
        """
        Initialize the game.
        """
        self.board = HiveBoard()
        self.players = [agent_1_class("Player1"), agent_2_class("Player2")]
        self.current_player_index = 0
        self.turn_count = 0
        self.pieces_remaining = set()

        self.add_starting_pieces(0)
        self.add_starting_pieces(1)


    def add_starting_pieces(self, team_id):
        """
        Add the starting pieces to the board. 
        Per the official rules without expansions this includes the following for each team:
        - 1 Queen Bee
        - 2 Spiders
        - 2 Beetles
        - 3 Grasshoppers
        - 3 Soldier Ants
        """
        for _ in range(self.config.NUM_QUEENBEE_CARDS):
            self.pieces_remaining.add(QueenBee(team_id))

        for _ in range(self.config.NUM_SPIDER_CARDS):
            self.pieces_remaining.add(Spider(team_id))

        for _ in range(self.config.NUM_BEETLE_CARDS):
            self.pieces_remaining.add(Beetle(team_id))

        for _ in range(self.config.NUM_GRASSHOPPER_CARDS):
            self.pieces_remaining.add(Grasshopper(team_id))
        
        for _ in range(self.config.NUM_SOLDIERANT_CARDS):
            self.pieces_remaining.add(SoldierAnt(team_id))

    def get_observation(self, agent):
        """
        Get the observation and available actions for the given agent.
        """
        if agent not in self.players:
            raise ValueError("Agent is not in the game.")

        # Define the observation based on the current state of the board
        observation = self.generate_observation(agent)

        # Define available actions (place a piece or move a piece)
        actions = self.get_available_actions(agent)
        
        return observation, actions

    def generate_observation(self, agent):
        """
        Generate the current game state observation for the agent.
        """
        # Include information about the board state, pieces, etc.
        # This information will be used by the agent to make a decision
        return {"board": self.board, "current_player": agent}

    def get_available_actions(self, agent):
        """
        Get the available actions for the agent based on the game rules and board state.
        """
        # List actions such as placing or moving pieces
        # The actions should be tailored based on the game's rules and the current turn
        return self.list_possible_moves(self.current_player_index)

    def list_possible_moves(self, player_index):
        """
        List all possible moves for the agent.
        THe possible moves are either to place a new piece or move an existing piece.
        """
        possible_pieces_to_place = [piece for piece in self.pieces_remaining if piece.owner == player_index]
        
        possible_piece_places = [hex for hex in self.board.board if self.board.board[hex] is None and self.board.is_adjacent_empty(hex)]

        possible_moves = []

        for (x,y) in self.board.board:
            pieces = self.board.board[(x, y)]

            for piece in pieces:
                if piece.owner == player_index:
                    possible_moves += piece.valid_moves(self.board)

        
                    


        return []

    def update(self, action, agent):
        """
        Update the game state based on the agent's action.
        """
        # Implement the logic to update the game state
        # This includes updating the board, changing turns, etc.
        pass

    def play_turn(self):
        """
        Play a turn for the current player.
        """
        agent = self.players[self.current_player_index]
        observation, actions = self.get_observation(agent)
        action = agent.take_action(observation, actions)

        self.update(action, agent)
        self.next_player()

    def next_player(self):
        """
        Switch to the next player.
        """
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn_count += 1

    def is_game_over(self):
        """
        Check if the game is over.
        """
        # Implement the logic to determine if the game has ended
        return False

    def run_game(self):
        """
        Run the game loop.
        """
        while not self.is_game_over():
            self.play_turn()

# Agent class and other relevant classes/methods not shown for brevity
