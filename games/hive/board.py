from .pieces import HivePiece, Grasshopper
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.animation import FuncAnimation
from multiprocessing import Process
from PIL import Image
import io

class HiveBoardVisualizer:
    def __init__(self, board, piece_images=None):
        self.board = board
        self.piece_images = piece_images if piece_images else {}

    def draw_hexagon(self, ax, center, size=1, fill_color='white', edge_color='black'):
        """Draw a hexagon given a center, size."""
        hexagon = patches.RegularPolygon(center, numVertices=6, radius=size, orientation=np.radians(30),
                                         facecolor=fill_color, edgecolor=edge_color, linewidth=1.5)
        ax.add_patch(hexagon)
        return hexagon

    def draw_piece(self, ax, center, coords, piece, size=0.6):
        """Draw a piece on the hexagon."""
        ax.text(center[0], center[1], piece.type + "\n" + "(" + str(coords[0]) + ", " + str(coords[1]) + ")", 
                        ha='center', va='center', fontsize=10, color='black')

    def draw_board(self, interactive=False):
        """Draw and display the Hive board."""
        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        ax.axis('off')  # Hide the axes

        # Find board limits
        min_x, max_x, min_y, max_y = self.find_board_limits()
        ax.set_xlim(min_x - 1, max_x + 1)
        ax.set_ylim(min_y - 1, max_y + 1)

        # Draw hexagons and pieces
        for hex, piece in self.board.items():
            x, y = self.hex_to_pixel(hex)
            fill_color = 'lightgreen' if piece.owner == 1 else 'lightblue'
            self.draw_hexagon(ax, (x, y), fill_color=fill_color)
            self.draw_piece(ax, (x, y), (hex.x, hex.y), piece)

        if interactive:
            plt.show()
        
        # return as PIL image
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        return Image.open(buf)
    

        

    def find_board_limits(self):
        """Calculate the limits of the board to set the display size."""
        x_coords = [self.hex_to_pixel(hex)[0] for hex in self.board]
        y_coords = [self.hex_to_pixel(hex)[1] for hex in self.board]
        if not x_coords or not y_coords:
            return (0, 0, 0, 0)
        return min(x_coords), max(x_coords), min(y_coords), max(y_coords)
      
    def hex_to_pixel(self, hex, size=1):
        """Convert hex coordinates to pixel coordinates."""
        x = size * 3/2 * hex.x
        y = size * np.sqrt(3) * (hex.y + hex.x / 2.0)
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
        self.queen_bee_placed = [False, False]
        self.visualizer = HiveBoardVisualizer(self.board)


    def add_piece(self, piece, hex):
        if hex in self.board:
            raise ValueError("There is already a piece at this position")
        self.board[hex] = piece

    def create_text_board(self, team_id):
        """
        Print the board with the pieces. Do this in a way that it is easy to see the pieces and their positions on the board. Start by finding the current hex.
        """

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
                    row += f" {piece.type}({x},{y}) "
                else:
                    row += f" .({x},{y}) "
            print(row)
        print()

    def display_board(self, interactive=False):
        """
        Display the board with the pieces and their positions. Produce a visual representation of the board such that an image can be exported.
        """
        return self.visualizer.draw_board(interactive)
    
    def is_queen_surrounded(self, owner):
        """
        Check if the queen bee is surrounded by enemy pieces.
        """
        queen_hex = next((hex for hex, piece in self.board.items() if piece.owner == owner and piece.type == "Queen Bee"), None)
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
        if self.get_piece_at(to_hex) is not None:
            return False
        
        if self.get_piece_at(from_hex) is None:
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
        temp_piece = self.board.get(hex_to_remove)
        del self.board[hex_to_remove]
        is_connected = self.is_one_hive()
        self.board[hex_to_remove] = temp_piece  # Put the piece back
        return is_connected

    def has_freedom_to_move(self, from_hex, to_hex):
        """
        Check the Freedom to Move Rule between from_hex and to_hex.
        """
        adjacent_to_from = set(self.get_adjacent_pieces(from_hex))
        adjacent_to_to = set(self.get_adjacent_pieces(to_hex))

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
        Move a piece from from_hex to to_hex.
        """
        if from_hex not in self.board or not self.board[from_hex]:
            raise ValueError("There is no piece at the starting position")

        moving_piece = self.board[from_hex]  
        if not self.board.get(to_hex):
            self.board[to_hex] = moving_piece

        del self.board[from_hex]


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
