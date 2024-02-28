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
    
    def __hash__(self) -> int:
        # hash based on the type and owner
        return hash((self.type, self.owner))
    
class QueenBee(HivePiece):
    def __init__(self, owner):
        super().__init__("Queen", owner)
    
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

        visited = set([start_hex])  # Initialize the visited set with the starting hex
        valid_moves = self.find_moves(start_hex, start_hex, board, 3, visited)
        return valid_moves
    
    def has_common_neighboring_piece(self, hex1, hex2, board):
        neighbors1 = self.get_neighbors_with_pieces(hex1, board) 
        neighbors2 = self.get_neighbors_with_pieces(hex2, board)
        return any(neighbor in neighbors2 for neighbor in neighbors1)

    def get_neighbors_with_pieces(self, hex, board):
        neighbors_with_pieces = set()
        for direction in range(6):
            neighbor_hex = hex.neighbor(direction)
            if neighbor_hex in board.board:
                neighbors_with_pieces.add(neighbor_hex)
        return neighbors_with_pieces

    def find_moves(self, start_hex, current_hex, board, steps_remaining, visited):
        if steps_remaining == 0:
            # If the spider has moved 3 steps, return the current hex as a possible move,
            # but only if it is not the starting hex (which is already in visited)
            return [current_hex] if current_hex not in visited else []
        new_visited = visited.union({current_hex})
        moves = []
        for direction in range(6):
            neighbor_hex = current_hex.neighbor(direction)

            is_current_hex_real = current_hex in board.board

            if not is_current_hex_real:
                temp_spider = Spider(0)
                board.board[current_hex] = temp_spider
                backup_old_spider = board.board[start_hex]
                del board.board[start_hex]

            if board.can_move_piece(current_hex, neighbor_hex) and neighbor_hex not in visited and self.has_common_neighboring_piece(current_hex, neighbor_hex, board):
                # Add the neighbor to the visited set to prevent backtracking in this move sequence
                if not is_current_hex_real:
                    is_current_hex_real = True
                    del board.board[current_hex]
                    board.board[start_hex] = backup_old_spider
                further_moves = self.find_moves(start_hex, neighbor_hex, board, steps_remaining - 1, new_visited)
                moves.extend(further_moves)

            if not is_current_hex_real:
                del board.board[current_hex]
                board.board[start_hex] = backup_old_spider

        return list(set(moves))  # Removing duplicates

    def find_current_hex(self, board):
        for hex, piece in board.board.items():
            if piece is self:
                return hex
        return None

    def find_current_hex(self, board):
        for hex, piece in board.board.items():
            if piece is self:
                return hex
        return None
    
class Grasshopper(HivePiece):
    def __init__(self, owner):
        super().__init__("Hopper", owner)

    def valid_moves(self, board):
        current_hex = self.find_current_hex(board)
        if current_hex is None:
            return []

        valid_moves = []
        for direction in range(6):
            jump_hex = self.jump_over_pieces(board, current_hex, direction)
            if jump_hex is not None:
                if board.can_move_piece(current_hex, jump_hex):
                    valid_moves.append(jump_hex)
        return valid_moves

    def jump_over_pieces(self, board, start_hex, direction):
        """
        Jump over the pieces in the given direction and return the landing hex. 
        At least one piece must be jumped over. Check if the hex is within the bounds of the board.
        """
        current_hex = start_hex.neighbor(direction)
        jumped_over_piece = False
        
        # Continue jumping over pieces until an empty hex is found
        while current_hex and board.get_piece_at(current_hex) is not None:
            current_hex = current_hex.neighbor(direction)
            jumped_over_piece = True

        # Ensure that we have jumped at least one piece and the landing hex is not the same as the starting hex
        return current_hex if current_hex and current_hex != start_hex and jumped_over_piece else None


class SoldierAnt(HivePiece):
    def __init__(self, owner):
        super().__init__("Ant", owner)

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

        if start_hex is None:
            start_hex = current_hex

        visited.add(current_hex)
        moves = []


        for direction in range(6):
            neighbor_hex = current_hex.neighbor(direction)

            temp_ant_created = False

            if current_hex not in board.board:
                temp_ant = SoldierAnt(0)
                board.board[current_hex] = temp_ant
                backup_old_ant = board.board[start_hex]
                temp_ant_created = True
                del board.board[start_hex]

            if board.can_move_piece(current_hex, neighbor_hex) and neighbor_hex != start_hex:
                moves.append(neighbor_hex)
                if temp_ant_created:
                    del board.board[current_hex]
                    board.board[start_hex] = backup_old_ant
                    temp_ant_created = False
                moves.extend(self.find_moves(neighbor_hex, board, visited, start_hex))

            if temp_ant_created:
                del board.board[current_hex]
                board.board[start_hex] = backup_old_ant
                temp_ant_created = False


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
