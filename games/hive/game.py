# TODO: handle beetle movement
from api.classes import Agent, Action, Observation, AvailableActions, Rules
from pieces import HivePiece, QueenBee, Beetle, Grasshopper, Spider, SoldierAnt
from .config import GameConfig as Config
from .board import HiveBoard, Hex
import random

default_config = Config()


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
        
        if not actions:
            actions = [Action("pass")]
        
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
        return self.list_actionable_pieces(agent.team_id)

    def list_possible_moves_for_placed_piece(self, piece, hex):
        """
        List all possible moves for a piece that is already placed on the board.
        """
        possible_moves = []

        if not self.board.is_piece_covered(hex):
            for direction in range(6):
                neighbor_hex = hex.neighbor(direction)
                if self.board.can_move_piece(hex, neighbor_hex):
                    possible_moves.append(Action("move_" + str(hex) +  "_" + str(neighbor_hex)))

        return possible_moves

    def list_possible_moves_for_unplaced_piece(self, piece):
        """
        List all possible moves for a piece that has not been placed on the board yet.

        If 3 moves have passed without the Queen Bee being placed, then it can be the only possible move.
        """
        if self.turn_count == 3 and not self.board.queen_bee_placed:
            if piece.type == "Queen Bee":
                return [Action("place_" + str(hex) + "_" + str(piece.type)) for hex in self.board.board if self.board.board[hex] is None and self.board.is_adjacent_empty(hex)]
            else:
                return []
        else:
            return [Action("place_" + str(hex) + "_" + str(piece.type)) for hex in self.board.board if self.board.board[hex] is None and self.board.is_adjacent_empty(hex) and self.board.can_place_piece(piece, hex)]
        
    def list_possible_moves_for_placed_piece(self, piece, hex):
        """
        List all possible moves for a piece that is already placed on the board.
        """
        return [Action("move_" + str(hex) +  "_" + str(neighbor_hex)) for direction in range(6) for neighbor_hex in hex.neighbor(direction) if self.board.can_move_piece(hex, neighbor_hex)]
    
    def list_actionable_pieces(self, player_index):
        """
        List all pieces that can be moved or placed by the player.
        """
        possible_actions_set = set()

        possible_pieces_to_place = [piece for piece in self.pieces_remaining if piece.owner == player_index]

        for possible_piece in possible_pieces_to_place:
            possible_moves = self.list_possible_moves_for_unplaced_piece(possible_piece)
            if len(possible_moves) > 0:
                possible_actions_set += Action("list_place_" + str(possible_piece.type))

        
        possible_moves = self.list_possible_moves_for_placed_piece(possible_piece)
        if len(possible_moves) > 0:
            possible_actions_set += Action("list_move_" + str(possible_piece.type) + "_" + str(hex))

        return possible_moves 

    def process_piece_place_action(self, action, agent):
        """
        Process the action of placing a piece on the board.
        """
        hex_x = action.split("_")[1]
        hex_y = action.split("_")[2]
        hex = Hex(hex_x, hex_y)            
        piece_type = action.split("_")[3]
        for piece in self.pieces_remaining:
            if piece.type == piece_type and piece.owner == agent.team_id:
                break
        else:
            raise ValueError("Invalid action")
        
        if self.board.can_place_piece(piece, hex):
            self.board.add_piece(piece, hex)
            del self.pieces_remaining[piece]
            if piece.type == "Queen Bee":
                self.board.queen_bee_placed = True

    def process_piece_move_action(self, action, agent):
        """
        Process the action of moving a piece on the board.
        """
        from_hex = action.split("_")[1].split(",")
        to_hex = action.split("_")[2].split(",")

        from_hex = Hex(int(from_hex[0]), int(from_hex[1]))
        to_hex = Hex(int(to_hex[0]), int(to_hex[1]))

        if from_hex not in self.board.board or to_hex in self.board.board:
            raise ValueError("Invalid action")
        piece = self.board.board[from_hex]
        if piece.owner != agent.team_id:
            raise ValueError("Invalid action")
        if self.board.can_move_piece(from_hex, to_hex) and to_hex in piece.valid_moves(piece, self.board):
            self.board.move_piece(from_hex, to_hex)

    def process_list_placement_action(self, action, agent):
        """
        Process the action of listing possible placements for a piece.
        """
        possible_placements = []
        piece_type = action.split("_")[1]
        for piece in self.pieces_remaining:
            if piece.type == piece_type and piece.owner == agent.team_id:
                possible_placements += self.list_possible_moves_for_unplaced_piece(piece)
                break 
        return possible_placements
        

    def process_list_moves_action(self, action, agent):
        """
        Process the action of listing possible moves for a piece.
        """
        hex_x = action.split("_")[2]
        hex_y = action.split("_")[3]
        
        hex = Hex(hex_x, hex_y)
        if hex not in self.board.board:
            raise ValueError("Invalid action")
        piece = self.board.board[hex]
        return self.list_possible_moves_for_placed_piece(piece, hex)
    
    def update(self, action, agent):
        """
        Update the game state based on the agent's action.
        """
        if action.startswith("place"):
            self.process_piece_place_action(action, agent)
        elif action.startswith("move"):
            self.process_piece_move_action(action, agent)
        elif action.startswith("list_place"):
            return self.process_list_placement_action(action, agent)
        elif action.startswith("list_move"):
            return self.process_list_moves_action(action, agent)
        else:
            raise ValueError("Invalid action")

    def play_turn(self):
        """
        Play a turn for the current player.
        """
        agent = self.players[self.current_player_index]
        observation, piece_actions = self.get_observation(agent)
        if not piece_actions:
            self.next_player()
            return
        action = agent.take_action(observation, piece_actions)
        if action not in piece_actions:
            action = random.choice(piece_actions)
        output_actions = self.update(action, agent)
        if output_actions:
            action = agent.take_action(observation, output_actions)
            if action not in output_actions:
                action = random.choice(output_actions)
        else:
            self.next_player()
            return
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
