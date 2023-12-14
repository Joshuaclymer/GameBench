from dataclasses import dataclass, field
import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import ast

@dataclass
class TicTacToe(Game):
    rules : Rules = Rules(
        title="Tic Tac Toe",
        summary="Get 3 in a row of your own marker to win (and avoid letting the other player get 3 in a row of their marker)",
        additional_details = None
    )
    id : str = "tic_tac_toe"

    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.states = [{
            "board" : [
                ['-','-','-'],
                ['-','-','-'],
                ['-','-','-'],
            ],
        }]
        self.agents = [agent1(team_id = 0, agent_id = 0), agent2(team_id = 1, agent_id = 1)]

        self.agent_data = {
            0: {"marker": "X"},
            1: {"marker": "O"}
        }
        self.winning_team = None
        if self.show_state:
            print(f"Agent {self.agents[0].agent_type_id} is X and agent {self.agents[1].agent_type_id} is O")

    def get_board_string(self):
        board = self.states[-1]["board"]
        row_strings = [", ".join(row) for row in board]
        board_string = "\n".join(row_strings)
        return board_string
        
    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        board_string = self.get_board_string()
        observation = Observation(text=board_string)

        marker = self.agent_data[agent.agent_id]["marker"]
        available_actions = AvailableActions(
            instructions = f"Return your actions as tuples with zero-indexed (x, y) coordinates of where you'd like to place your marker. The origin is the top left. Your marker is {marker}.",
            predefined = {
                f"({i},{j})" : None for i in range(3) for j in range(3)
                    if self.states[-1]["board"][i][j] == '-'
                },
            openended = {}
        )
        return observation, available_actions

    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        action = action.action_id

        # Select a random action if no valid actions are provided
        if action not in available_actions.predefined:
            action = random.choice(list(available_actions.keys()))
        
        x, y = ast.literal_eval(action)

        marker = self.agent_data[agent.agent_id]["marker"]
        board = self.states[-1]["board"]
        board[x][y] = marker

        # Show the board
        if self.show_state:
            print("")
            print(self.get_board_string())
            print("")

        # Check if player has won
        player_won = False

        # Check rows
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] == marker:
                player_won = True

        # Check columns
        for i in range(3):
            if board[0][i] == board[1][i] == board[2][i] == marker:
                player_won = True

        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] == marker:
            player_won = True
        if board[0][2] == board[1][1] == board[2][0] == marker:
            player_won = True
        
        if player_won:
            self.winning_team = agent.team_id
            self.game_is_over = True
            if self.show_state:
                print(f"Game over: {marker} won")
        
        # check if there is a tie
        if not player_won and '-' not in [board[i][j] for i in range(3) for j in range(3)]:
            self.winning_team = None
            self.game_is_over = True
            if self.show_state:
                print("Game over: tie")

        

    def play(self):
        player_1 = self.agents[0]
        player_2 = self.agents[1]
        while True:
            # Player 1 moves
            observation, available_actions = self.get_observation(player_1)
            action = player_1.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            self.update(action, available_actions, player_1)
            if self.game_is_over:
                break

            # Player 2 moves
            observation, available_actions = self.get_observation(player_2)
            action = player_2.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            self.update(action, available_actions, player_2)
            if self.game_is_over:
                break

        return (0.5, 0.5) if self.winning_team == None else (float(self.winning_team == 0), float(self.winning_team == 1))