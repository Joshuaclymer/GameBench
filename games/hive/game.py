# TODO: handle beetle movement
from api.classes import Agent, Action, Observation, AvailableActions, Rules
from .pieces import HivePiece, QueenBee, Grasshopper, Spider, SoldierAnt
from .config import GameConfig as Config
from api.classes import Game
from .board import HiveBoard, Hex
from dataclasses import dataclass, field
import random

default_config = Config()


@dataclass
class HiveGame(Game):

    id : str = "hive"
    config : Config = default_config
    board : HiveBoard = None
    rules : Rules = None
    image_mode : bool = True
    interactive_mode : bool = False
    
    def export_state(self):
        """
        Export the current game state.
        """
        return {
            "board": self.board.board,
            "players": self.players,
            "current_player_index": self.current_player_index,
            "turn_count": self.turn_count,
            "pieces_remaining": self.pieces_remaining,
            "queen_bee_placed": self.board.queen_bee_placed
        }
    
    def init_game(self, agent_1_class: Agent, agent_2_class : Agent):
        """
        Initialize the game.
        """
        self.board = HiveBoard()
        self.players = [agent_1_class(team_id=0, agent_id=0, **self.agent_1_kwargs), agent_2_class(team_id=1, agent_id=1, **self.agent_2_kwargs)]
        self.current_player_index = 0
        self.turn_count = [0, 0]
        self.pieces_remaining = []
        self.rules = self.config.rules

        self.add_starting_pieces(0)
        self.add_starting_pieces(1)


    def add_starting_pieces(self, team_id):
        """
        Add the starting pieces to the board. 
        Per the official rules without expansions this includes the following for each team:
        - 1 Queen Bee
        - 2 Spiders
        - 3 Grasshoppers
        - 3 Soldier Ants
        """
        for _ in range(self.config.NUM_QUEENBEE_CARDS):
            self.pieces_remaining.append(QueenBee(team_id))

        for _ in range(self.config.NUM_SPIDER_CARDS):
            self.pieces_remaining.append(Spider(team_id))

        for _ in range(self.config.NUM_GRASSHOPPER_CARDS):
            self.pieces_remaining.append(Grasshopper(team_id))
        
        for _ in range(self.config.NUM_SOLDIERANT_CARDS):
            self.pieces_remaining.append(SoldierAnt(team_id))

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
            actions = {"pass": "Pass the turn."}
        
        return Observation(observation), AvailableActions(instructions="Choose a move:", predefined=actions, openended={})

    def generate_observation(self, agent):
        """
        Generate the current game state observation for the agent.
        """
        image = None
        if self.image_mode:
            image = self.board.display_board(interactive=self.interactive_mode)

        remaining_turns = self.config.MAX_TURNS - max(self.turn_count)
        text = "{current_team} to move. Surround the enemy Queen. You have {remaining_turns} left.".format(current_team="Green" if agent.team_id == 1 else "Blue", remaining_turns=remaining_turns)
        if not self.image_mode:
            text += "\n\nBoard:\n\n" + self.board.generate_text_board()
        return Observation(text, image=image)

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
        possible_moves = {}
        for possible_move in piece.valid_moves(self.board):
            possible_moves["move_" + str(hex) + "_" + str(possible_move)] = "Move the piece to " + str(possible_move)
        return possible_moves

    def list_possible_moves_for_unplaced_piece(self, piece, player_index):
        """
        List all possible moves for a piece that has not been placed on the board yet.

        If 3 moves have passed without the Queen Bee being placed, then it can be the only possible move.
        """
        if self.turn_count[player_index] == 3 and not self.board.queen_bee_placed[player_index]:
            if piece.type != "Queen":
                return []
            
        current_hexes = [hex for hex in self.board.board if self.board.board[hex]]
        possible_places = []
        for hex in current_hexes:
            for direction in range(6):
                neighbor_hex = hex.neighbor(direction)
                if neighbor_hex not in self.board.board:
                    possible_places.append(neighbor_hex)
        if not self.board.board:
            possible_places.append(Hex(0, 0))
        
        actions = {}
        for hex in possible_places:
            if self.board.can_place_piece(piece, hex):
                actions["place_" + str(hex) + "_" + str(piece.type)] = ""
        return actions
    

    
    def list_actionable_pieces(self, player_index):
        """
        List all pieces that can be moved or placed by the player.
        """
        
        possible_actions = {}

        possible_pieces_to_place = [piece for piece in self.pieces_remaining if piece.owner == player_index]
        seen_pieces = set()

        for possible_piece in possible_pieces_to_place:
            if possible_piece.type in seen_pieces:
                continue
            seen_pieces.add(possible_piece.type)
            possible_moves = self.list_possible_moves_for_unplaced_piece(possible_piece, player_index)
            if len(possible_moves) > 0:
                possible_actions["list_place_" + str(possible_piece.type)] = "Place the " + str(possible_piece.type) + " piece."
    
        if not self.board.queen_bee_placed[player_index]:
            return possible_actions
        
        for hex in list(self.board.board.keys()):
            if self.board.board[hex].owner == player_index:
                possible_moves = self.list_possible_moves_for_placed_piece(self.board.board[hex], hex)
                possible_piece = self.board.board[hex]
                if len(possible_moves) > 0:
                    possible_actions["list_move_" + str(possible_piece.type) + "_" + str(hex)] = "Move the " + str(possible_piece.type) + " piece."

        return possible_actions

    def process_piece_place_action(self, action, agent):
        """
        Process the action of placing a piece on the board.
        """
        hex_coords = action.split("_")[1].split(",")
        hex_x = int(hex_coords[0][1:])
        hex_y = int(hex_coords[1][0: -1])
        hex = Hex(hex_x, hex_y)            
        piece_type = action.split("_")[2]
        for piece in self.pieces_remaining:
            if piece.type == piece_type and piece.owner == agent.team_id:
                break
        else:
            raise ValueError("Invalid action")

        if self.board.can_place_piece(piece, hex):
            self.board.add_piece(piece, hex)
            self.pieces_remaining.remove(piece)
            if piece.type == "Queen":
                self.board.queen_bee_placed[agent.team_id] = True

    def process_piece_move_action(self, action, agent):
        """
        Process the action of moving a piece on the board.
        """
        from_hex = action.split("_")[1][1:-1].split(",")
        to_hex = action.split("_")[2][1:-1].split(",")

        from_hex = Hex(int(from_hex[0]), int(from_hex[1]))
        to_hex = Hex(int(to_hex[0]), int(to_hex[1]))

        if from_hex not in self.board.board or to_hex in self.board.board:
            raise ValueError("Invalid action")
        piece = self.board.board[from_hex]
        if piece.owner != agent.team_id:
            raise ValueError("Invalid action")
        if to_hex in piece.valid_moves(self.board):
            self.board.move_piece(from_hex, to_hex)

    def process_list_placement_action(self, action, agent):
        """
        Process the action of listing possible placements for a piece.
        """
        piece_type = action.split("_")[2]
        for piece in self.pieces_remaining:
            if piece.type == piece_type and piece.owner == agent.team_id:
                return self.list_possible_moves_for_unplaced_piece(piece, agent.team_id)
        

    def process_list_moves_action(self, action, agent):
        """
        Process the action of listing possible moves for a piece.
        """
        hex_coords = action.split("_")[3].split(",")
        hex_x = int(hex_coords[0][1:])
        hex_y = int(hex_coords[1][0:-1])
        hex = Hex(hex_x, hex_y)
        if hex not in self.board.board:
            raise ValueError("Invalid action")
        piece = self.board.board[hex]
        return self.list_possible_moves_for_placed_piece(piece, hex)
    
    def update(self, action, agent):
        """
        Update the game state based on the agent's action.
        """
        action_id = action.action_id
        if action_id.startswith("place"):
            self.process_piece_place_action(action_id, agent)
        elif action_id.startswith("move"):
            self.process_piece_move_action(action_id, agent)
        elif action_id.startswith("list_place"):
            return self.process_list_placement_action(action_id, agent)
        elif action_id.startswith("list_move"):
            return self.process_list_moves_action(action_id, agent)
            
        else:
            raise ValueError("Invalid action")

    def play_turn(self):
        """
        Play a turn for the current player.
        """
        agent = self.players[self.current_player_index]
        observation, actions = self.get_observation(agent)

        if self.show_state:
            print(self.board.board)

        if not actions or not actions.predefined:
            self.next_player()
            return
        
        piece_actions = actions.predefined
        action_id = agent.take_action(self.rules, observation, actions, show_state=self.show_state).action_id
        
        if self.show_state:
            print("Action ID: ", action_id)

        if action_id not in piece_actions:
            if self.show_state:
                print("Invalid action: ", action_id)
            action_id = random.choice(list(piece_actions.keys()))
        if action_id == "pass":
            self.next_player()
            return
        
        specific_move_actions = self.update(Action(action_id=action_id), agent)
        new_actions = AvailableActions(instructions="Choose a move:", predefined=specific_move_actions, openended={})
        if specific_move_actions:
            action_id = agent.take_action(self.rules, observation, new_actions, show_state=self.interactive_mode).action_id
            
            if self.show_state:
                print("Action ID: ", action_id)

            if action_id not in specific_move_actions:
                print("Invalid action: ", action_id)
                action_id = random.choice(list(specific_move_actions.keys()))
        else:
            self.next_player()
            return
        if action_id == "pass":
            self.next_player()
            return
        self.update(Action(action_id=action_id), agent)
        self.next_player()

    def next_player(self):
        """
        Switch to the next player.
        """
        self.turn_count[self.current_player_index] += 1
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
    
    def get_intermediate_score(self):
        """
        Intermediate scoring function based on how surrounded each Queen Bee is. The less surrounded Queen Bee wins. This is a heuristic if we run out of turns.
        """
        num_pieces_1 = len(self.board.get_surrounding_pieces(self.players[0].team_id, self.board.get_queen_bee(self.players[0].team_id)))
        num_pieces_2 = len(self.board.get_surrounding_pieces(self.players[1].team_id, self.board.get_queen_bee(self.players[1].team_id)))
        if num_pieces_1 < num_pieces_2:
            return [1, 0]
        elif num_pieces_2 < num_pieces_1:
            return [0, 1]
        else:
            return [0, 0]
        

    def is_game_over(self):
        """
        Check if the game is over by checking if either player's Queen Bee is surrounded.
        
        """
        if max(self.turn_count) >= self.config.MAX_TURNS:
            return True
        for player in self.players:
            if self.board.is_queen_surrounded(player.team_id):
                return True
        return False
    

    def play(self):
        """
        Run the game loop.
        """
        while not self.is_game_over():
            self.play_turn()
        if self.image_mode:
            image = self.board.display_board(interactive=self.interactive_mode)
        queen_1_surrounded = self.board.is_queen_surrounded(self.players[0].team_id)
        queen_2_surrounded = self.board.is_queen_surrounded(self.players[1].team_id)
        
        if queen_1_surrounded and queen_2_surrounded:
            return [0, 0]
        elif queen_1_surrounded:
            return [0, 1]
        elif queen_2_surrounded:
            return [1, 0]
        else:
            return [0, 0]
            #return self.get_intermediate_score()
        
            
        

# Agent class and other relevant classes/methods not shown for brevity
