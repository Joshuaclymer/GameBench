from .pieces import HivePiece, Grasshopper
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

class HiveBoardVisualizer:
    def __init__(self, board):
        self.board = board

    def draw_hexagon(self, ax, center, size=1):
        """Draw a hexagon given a center, size, and the axis to draw on."""
        for angle in range(0, 360, 60):
            x = center[0] + size * np.cos(np.radians(angle))
            y = center[1] + size * np.sin(np.radians(angle))
            hexagon = patches.RegularPolygon((x, y), numVertices=6, radius=size, orientation=np.radians(30))
            ax.add_patch(hexagon)
            ax.text(x, y, '.', ha='center', va='center', size=20)  # Placeholder for empty hex

    def draw_board(self):
        """Draw the Hive board."""
        fig, ax = plt.subplots()
        ax.set_aspect('equal')

        # Set limits based on your board dimensions
        ax.set_xlim(-10, 10)
        ax.set_ylim(-10, 10)

        # Iterate through your board and draw each piece
        for hex, piece in self.board.items():
            x, y = self.hex_to_pixel(hex)
            self.draw_hexagon(ax, (x, y))
            ax.text(x, y, str(piece), ha='center', va='center', size=20)  # Replace str(piece) with your piece identifier

        plt.show()

    def hex_to_pixel(self, hex):
        """Convert hex coordinates to pixel coordinates."""
        x = 3/2 * hex.x
        y = np.sqrt(3) * (hex.y + 0.5 * (hex.x & 1))
        return (x, y)
    

class Hex:
    # Directions correspond to neighboring hexes in a hex grid
    DIRECTIONS = [
        (1, -1), (1, 0), (0, 1),
        (-1, 1), (-1, 0), (0, -1)
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
    
    def __str__(self):
        return f"({self.x},{self.y})"
    
class HiveBoard:
    def __init__(self):
        self.board = {}  # Dictionary to store pieces keyed by their Hex coordinates
        self.last_moved_piece = None
        self.queen_bee_placed = False

    def add_piece(self, piece, hex):
        if hex in self.board:
            raise ValueError("There is already a piece at this position")
        self.board[hex] = piece

    def create_text_board(self, team_id):
        """
        Print the board with the pieces. Do this in a way that it is easy to see the pieces and their positions on the board. Start by finding the current hex        """

        # Find the current hex
        if not self.board:
            return "Empty Board"
        min_x = min(hex.x for hex in self.board)
        max_x = max(hex.x for hex in self.board)
        min_y = min(hex.y for hex in self.board)
        max_y = max(hex.y for hex in self.board)

        for y in range(max_y, min_y - 1, -1):
            row = " " * (max_y - y)
            for x in range(min_x, max_x + 1):
                hex = Hex(x, y)
                if hex in self.board:
                    piece = self.board[hex]
                    row += f" {piece.type} "
                else:
                    row += " . "
            print(row)
        print()

    def display_board(self):
        """
        Display the board with the pieces and their positions. Produce a visual representation of the board such that an image can be exported.
        """
        visualizer = HiveBoardVisualizer(self)
        visualizer.draw_board()
    
    def is_queen_surrounded(self, owner):
        """
        Check if the queen bee is surrounded by enemy pieces.
        """
        queen_hex = next((hex for hex, piece in self.board.items() if piece.owner == owner and piece.name == "Queen Bee"), None)
        if queen_hex is None:
            return False

        for direction in range(6):
            neighbor_hex = queen_hex.neighbor(direction)
            if neighbor_hex in self.board and self.board[neighbor_hex].owner == owner:
                return False
            elif neighbor_hex not in self.board:
                return False
        return True
    

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
            temporary_piece = Grasshopper(0)
            self.board[hex] = temporary_piece
            is_connected = self.is_one_hive()
            del self.board[hex]
            return is_connected

    def can_place_piece(self, piece, hex):
        """
        Check if a piece can be placed at the given hex according to Hive rules.

        It must be placed adjacent to another piece and not break the One-Hive Rule.

        It cannot be adjacent to an enemy piece unless it is the first move.

        It cannot be placed on top of another piece.
        """
        if hex in self.board:
            return False

        if len(self.board) >= 2 and self.is_adjacent_to_enemy_piece(hex, piece.owner):
            return False

        if not self.is_one_hive_if_added(hex):
            return False
        return True

    def can_move_piece(self, from_hex, to_hex):
        """
        Check if a piece can move from from_hex to to_hex according to Hive rules.
        """
        if self.is_piece_covered(from_hex):
            return False
        
        if self.get_piece_at(to_hex) is not None:
            return False

        if not self.has_freedom_to_move(from_hex, to_hex):
            return False
        
        if not self.is_one_hive_if_removed(from_hex):
            return False

        # Temporarily move the piece to check One-Hive Rule
        piece = self.board[from_hex]  # Remove the top piece temporarily
        del self.board[from_hex]
        self.board[to_hex] = piece  # Move the piece to the destination

        one_hive = self.is_one_hive()

        # Move back after checking
        self.board[from_hex] = piece  # Put the piece back
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
