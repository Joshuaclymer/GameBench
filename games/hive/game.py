from api.classes import Agent, Action, Observation, AvailableActions, Rules

class Hex:
    # Directions correspond to neighboring hexes in a hex grid
    DIRECTIONS = [
        (1, -1, 0), (1, 0, -1), (0, 1, -1),
        (-1, 1, 0), (-1, 0, 1), (0, -1, 1)
    ]

    def __init__(self, x, y, z):
        if x + y + z != 0:
            raise ValueError("x, y, z coordinates of a hex must sum to 0")
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __hash__(self):
        return hash((self.x, self.y, self.z))

    def neighbor(self, direction):
        """ Returns the neighboring hex in the given direction """
        dx, dy, dz = Hex.DIRECTIONS[direction]
        return Hex(self.x + dx, self.y + dy, self.z + dz)
    
class HiveBoard:
    def __init__(self):
        self.board = {}  # Dictionary to store pieces keyed by their Hex coordinates
        self.last_moved_piece = None

    def add_piece(self, piece, hex):
        if hex in self.board:
            raise ValueError("There is already a piece at this position")
        self.board[hex] = piece

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

class HiveGame:

    def init_game(self, agent_1_class: Agent, agent_2_class : Agent):
        """
        Initialize the game.
        """
        self.board = HiveBoard()
        self.players = [agent_1_class("Player1"), agent_2_class("Player2")]
        self.current_player_index = 0
        self.turn_count = 0

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
        return self.list_possible_moves(agent)

    def list_possible_moves(self, agent):
        """
        List all possible moves for the agent.
        """
        # Implement logic to list all valid moves for the agent
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
