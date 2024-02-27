# TODO: handle beetle movement
from api.classes import Agent, Action, Observation, AvailableActions, Rules
from .pieces import HivePiece, QueenBee, Grasshopper, Spider, SoldierAnt
from .config import GameConfig as Config
from api.classes import Game
from .board import HiveBoard, Hex
import random

default_config = Config()



class HiveGame(Game):

    config : Config = default_config
    board : HiveBoard = None
    rules : Rules = None
    
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
        self.players = [agent_1_class(agent_id="Player1", agent_type_id=0, team_id=0), agent_2_class(agent_id="Player2", agent_type_id=0,team_id=1)]
        self.current_player_index = 0
        self.turn_count = 0
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
        - 2 Beetles
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
            actions = [Action("pass")]
        
        return Observation(observation), AvailableActions(instructions="Choose a move:", predefined=actions, openended=[])

    def generate_observation(self, agent):
        """
        Generate the current game state observation for the agent.
        """
        image = self.board.display_board(interactive=False)
        return Observation(text="Current game state. {current_team} to move.".format(current_team="Green" if agent.team_id == 1 else "Blue"), image=image)

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

        for direction in range(6):
            neighbor_hex = hex.neighbor(direction)
            if self.board.can_move_piece(hex, neighbor_hex) and neighbor_hex in piece.valid_moves(self.board):
                possible_moves.append(Action("move_" + str(hex) +  "_" + str(neighbor_hex)))

        return possible_moves

    def list_possible_moves_for_unplaced_piece(self, piece, player_index):
        """
        List all possible moves for a piece that has not been placed on the board yet.

        If 3 moves have passed without the Queen Bee being placed, then it can be the only possible move.
        """
        if self.turn_count == 3 and not self.board.queen_bee_placed[player_index]:
            if piece.type == "QueenBee":
                return [Action("place_" + str(hex) + "_" + str(piece.type)) for hex in self.board.board if self.board.board[hex] is None and self.board.is_adjacent_empty(hex)]
            else:
                return []
        else:
            current_hexes = [hex for hex in self.board.board if self.board.board[hex]]
            possible_places = []
            for hex in current_hexes:
                for direction in range(6):
                    neighbor_hex = hex.neighbor(direction)
                    if neighbor_hex not in self.board.board:
                        possible_places.append(neighbor_hex)
            if self.turn_count == 0:
                possible_places.append(Hex(20, 20))
            return [Action("place_" + str(hex) + "_" + str(piece.type)) for hex in possible_places if self.board.can_place_piece(piece, hex)]
        

    
    def list_actionable_pieces(self, player_index):
        """
        List all pieces that can be moved or placed by the player.
        """
        
        possible_actions = []

        possible_pieces_to_place = [piece for piece in self.pieces_remaining if piece.owner == player_index]
        seen_pieces = set()

        for possible_piece in possible_pieces_to_place:
            if possible_piece.type in seen_pieces:
                continue
            seen_pieces.add(possible_piece.type)
            possible_moves = self.list_possible_moves_for_unplaced_piece(possible_piece, player_index)
            if len(possible_moves) > 0:
                possible_actions.append(Action("list_place_" + str(possible_piece.type)))
    
        if not self.board.queen_bee_placed[player_index]:
            return possible_actions
        
        for hex in list(self.board.board.keys()):
            print(hex, self.board.board[hex])
            if self.board.board[hex].owner == player_index:
                possible_moves = self.list_possible_moves_for_placed_piece(self.board.board[hex], hex)
                possible_piece = self.board.board[hex]
                if len(possible_moves) > 0:
                    print(possible_piece, possible_piece.type)
                    possible_actions.append(Action("list_move_" + str(possible_piece.type) + "_" + str(hex)))

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
            if piece.type == "QueenBee":
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
        if self.board.can_move_piece(from_hex, to_hex) and to_hex in piece.valid_moves(self.board):
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
        if not actions or not actions.predefined:
            self.next_player()
            return
        piece_actions = actions.predefined
        action = agent.take_action(self.rules, observation, actions)
        if action not in piece_actions:
            action = random.choice(piece_actions)
        if action.action_id == "pass":
            self.next_player()
            return
        specific_move_actions = self.update(action, agent)
        new_actions = AvailableActions(instructions="Choose a move:", predefined=specific_move_actions, openended=[])
        if specific_move_actions:
            action = agent.take_action(self.rules, observation, new_actions)
            if action not in specific_move_actions:
                action = random.choice(specific_move_actions)
        else:
            self.next_player()
            return
        if action.action_id == "pass":
            self.next_player()
            return
        self.update(action, agent)
        self.next_player()

    def next_player(self):
        """
        Switch to the next player.
        """
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
    
    def is_game_over(self):
        """
        Check if the game is over by checking if either player's Queen Bee is surrounded.
        
        """
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
            self.turn_count += 1
            
        if self.board.is_queen_surrounded(self.players[0].team_id):
            return [0, 1]
        elif self.board.is_queen_surrounded(self.players[1].team_id):
            return [1, 0]
        else:
            return [0, 0]
            
        

# Agent class and other relevant classes/methods not shown for brevity
