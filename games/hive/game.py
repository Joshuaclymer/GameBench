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
        piece = self.board.pop(from_hex)  # Remove the piece temporarily
        self.board[to_hex] = piece  # Place it on the target
        one_hive = self.is_one_hive()
        # Move back after checking
        self.board[from_hex] = self.board.pop(to_hex)

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
        if from_hex not in self.board:
            raise ValueError("There is no piece at the starting position")
        if to_hex in self.board:
            raise ValueError("There is already a piece at the destination")
        self.board[to_hex] = self.board.pop(from_hex)

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
