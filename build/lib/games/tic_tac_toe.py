import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
from api.classes import TwoPlayerTurnBasedGame, Observation, Action, Agent, AvailableActions

class TicTacToe(TwoPlayerTurnBasedGame):
    game_id = "tic_tac_toe"

    @abstractmethod
    def init_game(self, agent1, agent2):
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

    def get_board_string(self):
        board = self.states[-1]["board"]
        row_strings = [", ".join(row) for row in board]
        board_string = "\n".join(row_strings)
        return board_string
        
    @abstractmethod
    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        board_string = self.get_board_string()
        observation = Observation(text=board_string)

        marker = self.agent_data[agent.agent_id]["marker"]
        available_actions = AvailableActions(
            predefined = {
                f"{i},{j}" : f"Place an {marker} at the coordinates {i}, {j} (zero-indexed)" for i in range(3) for j in range(3)
                    if self.board[i][j] == '-'
                }
        )
        return observation, available_actions

    @abstractmethod
    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        action = action.action_id

        # Select a random action if no valid actions are provided
        if action not in available_actions.predefined:
            action = random.choice(list(available_actions.keys()))
        
        x, y = [int(item) for item in action.split(',')]

        marker = self.agent_data[agent.agent_id]["marker"]
        board = self.states[-1]["board"]
        board[x][y] = marker

        # Show the board
        if self.show_state:
            print(self.get_board_string(self))

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

    @abstractmethod
    def get_team_scores(self) -> Tuple(float, float):
        return self.winning_team == 0, self.winning_team == 1

def main(agent_1, agent_2):
    TicTacToe.init_game(agent_1, agent_2)
    return TicTacToe.game_loop()