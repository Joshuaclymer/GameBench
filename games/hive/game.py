from api.classes import Agent, Action, Observation, AvailableActions, Rules
from pieces import HivePiece, QueenBee, Beetle, Grasshopper, Spider, SoldierAnt
from .config import GameConfig as Config
from .board import HiveBoard

default_config = Config()


class HiveGame(Game):

    config : Config = default_config
    board : HiveBoard = None
    queen_bee_placed : bool = False
    
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
        return self.list_possible_moves(self.current_player_index)

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
        if self.turn_count == 3 and not self.queen_bee_placed:
            if piece.type == "Queen Bee":
                return [Action("place_" + str(hex) + "_" + str(piece.type)) for hex in self.board.board if self.board.board[hex] is None and self.board.is_adjacent_empty(hex)]
            else:
                return []
        else:
            return [Action("place_" + str(hex) + "_" + str(piece.type)) for hex in self.board.board if self.board.board[hex] is None and self.board.is_adjacent_empty(hex) and self.board.can_place_piece(piece, hex)]
        

    def list_possible_moves(self, player_index):
        """
        List all possible moves for the agent.
        THe possible moves are either to place a new piece or move an existing piece.
        """
        possible_moves = []

        possible_pieces_to_place = [piece for piece in self.pieces_remaining if piece.owner == player_index]

        for possible_piece in possible_pieces_to_place:
            possible_moves += self.list_possible_moves_for_unplaced_piece(possible_piece)
        
        for (x,y) in self.board.board:
            pieces = self.board.board[(x, y)]

            for piece in pieces:
                if piece.owner == player_index:
                    possible_moves += piece.valid_moves(self.board)

        return possible_moves 

    def update(self, action, agent):
        """
        Update the game state based on the agent's action.
        """
        if action.startswith("place"):
            hex = eval(action.split("_")[1])
            piece = self.pieces_remaining.pop()
            piece.owner = self.current_player_index
            self.board.add_piece(piece, hex)
        elif action.startswith("move"):
            from_hex, to_hex = eval(action.split("_")[1]), eval(action.split("_")[2])
            self.board.move_piece(from_hex, to_hex)
        else:
            raise ValueError("Invalid action")

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
