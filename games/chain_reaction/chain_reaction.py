from dataclasses import dataclass, field
import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import ast

@dataclass
class ChainReaction(Game):
    rules : Rules = Rules(
        title="Chain Reaction",
        summary="Trigger a cascade of reactions by placing orbs strategically on the grid to eliminate opponents orbs and take over the board.",
        additional_details = ["The gameplay takes place in an MxN board. The size of the board used in this implementation is 11x6.",
        "For each cell in the board, we define a critical mass. The critical mass is equal to the number of orthogonally adjacent cells. That would be 4 for interior cells, 3 for edge cells, and 2 for cells in the corners.",
        "All cells are initially empty. The Red and the Green player take turns to place orbs of their corresponding colors. The Red/Green player can only place an (red/green) orb in an empty cell or a cell which already contains one or more red/green orbs. When two or more orbs are placed in the same cell, they stack up.",
        "The state of each cell is given by a two digit number, where the first digit is the occupying player ID and the second digit is the number of orbs in the cell. If the state is '--' the cell is empty.",
        "When a cell is loaded with a number of orbs equal to its critical mass, the stack immediately explodes. As a result of the explosion, to each of the orthogonally adjacent cells, an orb is added and the initial cell looses as many orbs as its critical mass.",
        "The explosions might result in overloading of an adjacent cell and the chain reaction of explosion continues until every cell is stable.",
        "When a red cell explodes and there are green cells around, the green cells are converted to red and the other rules of explosions still follow. The same rule is applicable for other colors.",
        "The winner is the one who eliminates all other player's orbs."
        ]
    )
    id : str = "chain_reaction"

    ## At every location we have a identifier 'an' where 'p' is the id corresponding to the agent and 'n' is the number of orbs
    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.states = [{
            "board" : [
                ['--','--','--','--','--','--'],
                ['--','--','--','--','--','--'],
                ['--','--','--','--','--','--'],
                ['--','--','--','--','--','--'],
                ['--','--','--','--','--','--'],
                ['--','--','--','--','--','--'],
                ['--','--','--','--','--','--'],
                ['--','--','--','--','--','--'],
                ['--','--','--','--','--','--'],
                ['--','--','--','--','--','--'],
                ['--','--','--','--','--','--']
            ],
        }]
        self.agents = [agent1(team_id = 0, agent_id = 0), agent2(team_id = 1, agent_id = 1)]

        ## added to make sure both players are given a turn before checking for winning or losing
        self.turncount_player0 = 0
        self.turncount_player1 = 0

        self.orbcount_player0 = 0
        self.orbcount_player1 = 0

        ## Replaced X with red and O with green
        ## Replaced marker with orb
        self.agent_data = {
            0: {"orb": "red"},
            1: {"orb": "green"}
        }
        self.winning_team = None
        if self.show_state:
            print(f"Agent {self.agents[0].agent_type_id} is red and agent {self.agents[1].agent_type_id} is green")

    def get_board_string(self):
        board = self.states[-1]["board"]
        row_strings = [", ".join(row) for row in board]
        board_string = "\n".join(row_strings)
        return board_string

    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        board_string = self.get_board_string()
        observation = Observation(text=board_string)

        orb = self.agent_data[agent.agent_id]["orb"]
        available_actions = AvailableActions(
            instructions = f"Return your actions as tuples with zero-indexed (row, column) coordinates of where you'd like to place your orb. The origin (0,0) is the top left. Your orb is {orb}.",
            predefined = {
                f"({row},{col})" : None for row in range(11) for col in range(6)
                    if self.states[-1]["board"][row][col] == '-'
                },
            openended = {}
        )
        return observation, available_actions

    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        action = action.action_id
        turncount_player0 = self.turncount_player0
        turncount_player1 = self.turncount_player1


        # Select a random action if no valid actions are provided
        if action not in available_actions.predefined:
            action = random.choice(list(available_actions.keys()))

        x, y = ast.literal_eval(action)

        orb = self.agent_data[agent.agent_id]["orb"]
        board = self.states[-1]["board"]
        board[x][y] = orb

        # Show the board
        if self.show_state:
            print("")
            print(self.get_board_string())
            print("")

        # Check if player has won
        if (turncount_player1*turncount_player2)>0:
            player_won = False
            ## Write in a way that is agnostic to whether it's player 0 or 1
            ## Do it in a way that doesn't depend on the id of the other agent

            ## Check if there are any orbs of other team
            ## If yes, no win yet

            # # Check rows
            # for i in range(3):
            #     if board[i][0] == board[i][1] == board[i][2] == marker:
            #         player_won = True
            #
            # # Check columns
            # for i in range(3):
            #     if board[0][i] == board[1][i] == board[2][i] == marker:
            #         player_won = True
            #
            # # Check diagonals
            # if board[0][0] == board[1][1] == board[2][2] == marker:
            #     player_won = True
            # if board[0][2] == board[1][1] == board[2][0] == marker:
            #     player_won = True

            if player_won:
                self.winning_team = agent.team_id
                self.game_is_over = True
                if self.show_state:
                    print(f"Game over: {orb} won")



    def play(self):
        player_1 = self.agents[0]
        player_2 = self.agents[1]
        while True:
            # Player 1 moves
            observation, available_actions = self.get_observation(player_1)
            action = player_1.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            self.turncount_player1 += 1
            self.update(action, available_actions, player_1)

            if self.game_is_over:
                break

            # Player 2 moves
            observation, available_actions = self.get_observation(player_2)
            action = player_2.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            self.turncount_player2 += 1
            self.update(action, available_actions, player_2)

            if self.game_is_over:
                break

        return (float(self.winning_team == 0), float(self.winning_team == 1))
