from abc import ABC, abstractmethod
class HivePiece(ABC):
    def __init__(self, type, owner):
        self.type = type
        self.owner = owner

    @abstractmethod
    def valid_moves(self, board):
        pass

    def find_current_hex(self, board):
        for hex, piece in board.board.items():
            if piece is self:
                return hex
        return None
    
class QueenBee(HivePiece):
    def __init__(self, owner):
        super().__init__("Queen Bee", owner)

    def valid_moves(self, board):
        current_hex = self.find_current_hex(board)
        if current_hex is None:
            return []

        valid_moves = []
        for direction in range(6):
            neighbor_hex = current_hex.neighbor(direction)
            if board.can_move_piece(current_hex, neighbor_hex):
                valid_moves.append(neighbor_hex)

        return valid_moves


    
class Spider(HivePiece):
    def __init__(self, owner):
        super().__init__("Spider", owner)

    def valid_moves(self, board):
        start_hex = self.find_current_hex(board)
        if start_hex is None:
            return []

        return self.find_moves(start_hex, board, 3)

    def find_moves(self, current_hex, board, steps_remaining):
        if steps_remaining == 0:
            return [current_hex]

        moves = []
        for direction in range(6):
            neighbor_hex = current_hex.neighbor(direction)
            if board.can_move_piece(current_hex, neighbor_hex):
                further_moves = self.find_moves(neighbor_hex, board, steps_remaining - 1)
                moves.extend([move for move in further_moves if move != current_hex])

        return list(set(moves))  # Removing duplicates

    def find_current_hex(self, board):
        for hex, piece in board.board.items():
            if piece is self:
                return hex
        return None
    
class Grasshopper(HivePiece):
    def __init__(self, owner):
        super().__init__("Grasshopper", owner)

    def valid_moves(self, board):
        current_hex = self.find_current_hex(board)
        if current_hex is None:
            return []

        valid_moves = []
        for direction in range(6):
            jump_hex = self.jump_over_pieces(board, current_hex, direction)
            if jump_hex and board.can_move_piece(current_hex, jump_hex):
                valid_moves.append(jump_hex)

        return valid_moves

    def jump_over_pieces(self, board, start_hex, direction):
        """
        Jump over the pieces in the given direction and return the landing hex.
        """
        current_hex = start_hex.neighbor(direction)
        while board.get_piece_at(current_hex) is not None:
            current_hex = current_hex.neighbor(direction)

        return current_hex if current_hex != start_hex else None

class SoldierAnt(HivePiece):
    def __init__(self, owner):
        super().__init__("Soldier Ant", owner)

    def valid_moves(self, board):
        current_hex = self.find_current_hex(board)
        if current_hex is None:
            return []

        return self.find_moves(current_hex, board, set(), current_hex)

    def find_moves(self, current_hex, board, visited, start_hex):
        """
        Recursively find all valid moves for the Soldier Ant.
        """
        if current_hex in visited:
            return []

        visited.add(current_hex)
        moves = []
        for direction in range(6):
            neighbor_hex = current_hex.neighbor(direction)
            if board.can_move_piece(current_hex, neighbor_hex) and neighbor_hex != start_hex:
                moves.append(neighbor_hex)
                moves.extend(self.find_moves(neighbor_hex, board, visited, start_hex))

        return list(set(moves))
    
# expansion and not necessarily part of the core gmae. not using this for now
"""
class Mosquito(HivePiece):
    def __init__(self, owner):
        super().__init__("Mosquito", owner)

    def valid_moves(self, board):
        current_hex = self.find_current_hex(board)
        if current_hex is None:
            return []

        valid_moves = []
        for adjacent_piece in board.get_adjacent_pieces(current_hex):
            valid_moves.extend(adjacent_piece.valid_moves(board))

        return list(set(valid_moves))
"""

# expansion and not necessarily part of the core gmae. not using this for now
"""
class Pillbug(HivePiece):
    def __init__(self, owner):
        super().__init__("Pillbug", owner)

    def valid_moves(self, board):
        current_hex = self.find_current_hex(board)
        if current_hex is None:
            return []

        valid_moves = []
        for direction in range(6):
            adjacent_hex = current_hex.neighbor(direction)
            piece = board.get_piece_at(adjacent_hex)
            if piece and not self.is_covered(board, adjacent_hex):
                for target_direction in range(6):
                    target_hex = current_hex.neighbor(target_direction)
                    if self.can_move_other_piece(board, adjacent_hex, target_hex):
                        valid_moves.append((adjacent_hex, target_hex))

        return valid_moves

    def can_move_other_piece(self, board, from_hex, to_hex):
        if from_hex == to_hex or board.get_piece_at(to_hex) is not None:
            return False

        if not board.is_adjacent(from_hex, to_hex) or self.is_covered(board, to_hex):
            return False

        if not board.is_one_hive_if_removed(from_hex):
            return False

        if board.has_recently_moved(from_hex) or self.has_recently_moved(board, self.find_current_hex(board)):
            return False

        if board.is_beetle_gate_present(from_hex, to_hex):
            return False

        return True

    def is_covered(self, board, hex):
        return board.is_piece_covered(hex)


    def find_current_hex(self, board):
        for hex, piece in board.board.items():
            if piece is self:
                return hex
        return None
"""
# expansion and not necessarily part of the core gmae. not using this for now
"""
class Ladybug(HivePiece):
    def __init__(self, owner):
        super().__init__("Ladybug", owner)

    def valid_moves(self, board):
        current_hex = self.find_current_hex(board)
        if current_hex is None:
            return []

        return self.find_moves(current_hex, board, 3)

    def find_moves(self, current_hex, board, steps_remaining):
        Recursively find all valid moves for the Ladybug.
        if steps_remaining == 0:
            return [current_hex] if board.get_piece_at(current_hex) is None else []

        moves = []
        for direction in range(6):
            neighbor_hex = current_hex.neighbor(direction)
            if steps_remaining > 1 or board.get_piece_at(neighbor_hex) is None:
                if board.can_move_piece(current_hex, neighbor_hex):  # Check for climb up/down
                    further_moves = self.find_moves(neighbor_hex, board, steps_remaining - 1)
                    moves.extend(further_moves)

        return list(set(moves))
    
"""

# this is currently not being used to simplify the implementation
"""
class Beetle(HivePiece):
    def __init__(self, owner):
        super().__init__("Beetle", owner)

    def valid_moves(self, board):
        current_hex = self.find_current_hex(board)
        if current_hex is None:
            return []

        valid_moves = []
        for direction in range(6):
            neighbor_hex = current_hex.neighbor(direction)
            if self.can_climb(board, current_hex, neighbor_hex) or board.can_move_piece(current_hex, neighbor_hex):
                valid_moves.append(neighbor_hex)

        return valid_moves

    def can_climb(self, board, current_hex, target_hex):
        Check if the Beetle can climb to the target hex.
        # If the target hex is empty or has a stack, the Beetle can climb onto it
        if board.get_piece_at(target_hex) is not None:
            return True

        # Check for the Beetle's special movement restriction:
        # It cannot move through a gap between two higher stacks
        current_height = self.stack_height(board, current_hex)
        target_height = self.stack_height(board, target_hex)
        
        for direction in range(6):
            adjacent_hex = current_hex.neighbor(direction)
            adjacent_height = self.stack_height(board, adjacent_hex)

            # Skip the target hex and the hex directly opposite to it
            if adjacent_hex == target_hex or adjacent_hex == current_hex.neighbor((direction + 3) % 6):
                continue

            if adjacent_height > current_height and adjacent_height > target_height:
                # Found a gap that the Beetle cannot move through
                return False

    def stack_height(self, board, hex):
        Returns the height of the stack at the given hex.
        piece = board.get_piece_at(hex)
        height = 0
        while piece:
            height += 1
            # Assuming we have a way to find the piece below in the stack
            piece = piece.below
        return height
"""
