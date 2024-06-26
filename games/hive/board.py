from .pieces import HivePiece, Grasshopper, Spider
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.animation import FuncAnimation
from multiprocessing import Process
from PIL import Image
import io
import os

class HiveBoardVisualizer:
    def __init__(self, board, piece_images=None):
        self.board = board
        self.counter = 0
        self.piece_images = piece_images if piece_images else {}
        if not os.path.exists('images'):
            os.makedirs('images')

    def draw_hexagon(self, ax, center, size=1, fill_color='white', edge_color='black'):
        """Draw a hexagon given a center, size."""
        hexagon = patches.RegularPolygon(center, numVertices=6, radius=size, orientation=0,
                                        facecolor=fill_color, edgecolor=edge_color, linewidth=1.5)
        ax.add_patch(hexagon)
        return hexagon

    def draw_piece(self, ax, center, coords, piece, label_color='black'):
        """Draw a piece on the hexagon."""
        ax.text(center[0], center[1], piece.type + "\n" + "(" + str(coords[0]) + ", " + str(coords[1]) + ")", 
                        ha='center', va='center', fontsize=6.5, color=label_color)

    def draw_fake_piece(self, ax, center, coords, label_color='black'):
        """Draw a fake piece on the hexagon."""
        ax.text(center[0], center[1], "(" + str(coords[0]) + ", " + str(coords[1]) + ")", 
                        ha='center', va='center', fontsize=6.5, color=label_color)
        
    def draw_board(self, interactive=False):
        """Draw and display the Hive board."""
        fig, ax = plt.subplots(figsize=(5.12, 5.12), dpi=100)
        ax.set_aspect('equal')
        ax.axis('off')  # Hide the axes

        # Find board limits
        min_x, max_x, min_y, max_y = self.find_board_limits()
        ax.set_xlim(min_x - 1, max_x + 1)
        ax.set_ylim(min_y - 1, max_y + 1)
        seen_set = set()
        # Draw hexagons and pieces
        for hex, piece in self.board.items():
            x, y = self.hex_to_pixel(hex)
            fill_color = 'lightgreen' if piece.owner == 1 else 'lightblue'
            self.draw_hexagon(ax, (x, y), fill_color=fill_color)
            self.draw_piece(ax, (x, y), (hex.x, hex.y), piece)
            for direction in range(6):
                neighbor_hex = hex.neighbor(direction)
                if neighbor_hex not in self.board and neighbor_hex not in seen_set:
                    nx, ny = self.hex_to_pixel(neighbor_hex)
                    self.draw_hexagon(ax, (nx, ny), fill_color='white', edge_color='black')
                    self.draw_fake_piece(ax, (nx, ny), (neighbor_hex.x, neighbor_hex.y), label_color='red')
                    seen_set.add(neighbor_hex)


        if interactive:
            plt.show()
        
        # return as PIL image
        self.counter += 1
        plt.savefig('images/board_' + str(self.counter) + '.png', format='png')
        plt.close()
        return Image.open('images/board_' + str(self.counter) + '.png')

    def find_board_limits(self):
        """Calculate the limits of the board to set the display size."""
        all_hexes = set(list(self.board.keys()))
        # add all neighbors to the list
        for hex in self.board.keys():
            for direction in range(6):
                neighbor_hex = hex.neighbor(direction)
                if neighbor_hex not in self.board:
                    all_hexes.add(neighbor_hex)

        x_coords = [self.hex_to_pixel(hex)[0] for hex in all_hexes]
        y_coords = [self.hex_to_pixel(hex)[1] for hex in all_hexes]
        if not x_coords or not y_coords:
            return (0, 0, 0, 0)
        return min(x_coords), max(x_coords), min(y_coords), max(y_coords)
      
    def hex_to_pixel(self, hex, size=1):
        """Convert hex coordinates to pixel coordinates for pointy-topped hexagons with odd-r vertical layout."""
        x = size * np.sqrt(3) * (hex.x + 0.5 * (hex.y & 1))
        y = size * 3/2 * hex.y
        return (x, y)

class Hex:
    EVEN_R_DIRECTIONS = [(1, 0), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)]
    ODD_R_DIRECTIONS = [(1, 0), (1, -1), (0, -1), (-1, 0), (0, 1), (1, 1)]

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def neighbor(self, direction):
        """ Returns the neighboring hex in the given direction """
        directions = Hex.EVEN_R_DIRECTIONS if self.y % 2 == 0 else Hex.ODD_R_DIRECTIONS
        dq, dr = directions[direction]
        return Hex(self.x + dq, self.y + dr)

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

    def get_queen_bee(self, team_id):
        for hex, piece in self.board.items():
            if piece.type == "Queen" and piece.owner == team_id:
                return hex
        return None
    
    def get_surrounding_pieces(self, team_id, hex):
        """
        Get the pieces surrounding the given hex.
        """
        surrounding_pieces = []
        for direction in range(6):
            neighbor_hex = hex.neighbor(direction)
            if neighbor_hex in self.board:
                surrounding_pieces.append(self.board[neighbor_hex])
        return surrounding_pieces
    
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

    def generate_text_board(self):
        return self.visualizer.text_representation()

    def display_board(self, interactive=False):
        """
        Display the board with the pieces and their positions. Produce a visual representation of the board such that an image can be exported.
        """
        return self.visualizer.draw_board(interactive)
    
    def is_queen_surrounded(self, owner):
        """
        Check if the queen bee is surrounded by enemy pieces.
        """
        queen_hex = next((hex for hex, piece in self.board.items() if piece.owner == owner and piece.type == "Queen"), None)
        if queen_hex is None:
            return False

        for direction in range(6):
            neighbor_hex = queen_hex.neighbor(direction)
            if neighbor_hex not in self.board:
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
        
        self.board[from_hex] = piece  

        del self.board[to_hex]

        return one_hive
    
    def is_in_direct_contact(self, piece, hex):
        """
        Check if a piece is in direct contact with a given hex.
        """
        for direction in range(6):
            neighbor_hex = hex.neighbor(direction)
            if self.get_piece_at(neighbor_hex) is piece:
                return True
        return False
    
    def is_one_hive_if_removed(self, hex_to_remove):
        """
        Check if the hive remains connected if a piece is temporarily removed.
        """
        temp_piece = self.board.get(hex_to_remove)
        del self.board[hex_to_remove]
        is_connected = self.is_one_hive()
        self.board[hex_to_remove] = temp_piece  # Put the piece back
        return is_connected

    def is_almost_completely_surrounded(self, hex):
        """
        Check if a hex is almost completely surrounded by other pieces.
        A hex is almost completely surrounded if there is one or no empty spaces adjacent to it.
        """
        adjacent_hexes = self.get_adjacent_hexes(hex)
        empty_adjacent_hexes = [h for h in adjacent_hexes if h not in self.board]

        # If there is one or no empty adjacent hexes, the hex is almost completely surrounded
        return len(empty_adjacent_hexes) <= 1

    def get_adjacent_hexes(self, hex):
        """
        Returns a list of hexes adjacent to the given hex.
        """
        return [hex.neighbor(direction) for direction in range(6)]
    
    def has_freedom_to_move(self, from_hex, to_hex):
        """
        Check the Freedom to Move Rule between from_hex and to_hex.
        """
        # Grasshopper exception to freedom to move rule
        if from_hex in self.board and self.board[from_hex].type == "Hopper":
            return True
        # Check if the destination hex is empty and not almost completely surrounded
        if to_hex in self.board or self.is_almost_completely_surrounded(to_hex):
            return False

        # Check if the starting hex is almost completely surrounded
        if self.is_almost_completely_surrounded(from_hex):
            return False

        # If 'from_hex' and 'to_hex' are adjacent, we check if the move is directly possible
        if to_hex in self.get_adjacent_hexes(from_hex):
            return True

        return False  # If none of the conditions are met, the move is not allowed.
    
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
