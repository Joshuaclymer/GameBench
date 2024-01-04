from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import random

@dataclass
class TwoRoomsAndaBoom(Game):
    rules : Rules = Rules(
        title="Two Rooms and a Boom",
        summary="Blue team wants to keep the president safe, red team wants to blow up the president at the end of the third turn.",
        additional_details = None
    )
    id : str = "two_rooms_and_a_boom"

    def init_game(self, agent1 : Agent, agent2 : Agent):        
        self.states = [{
            "turn" : 0
        }]
        
        # Uncertain if "teams" is the correct way to assign teams (2024.01.02)
        self.agent_data = {
            0: {"team": "red"},
            1: {"team": "blue"}
        }
        
        self.agents = [agent1(team_id = 0, agent_id = 0), agent2(team_id = 1, agent_id = 1)]

        self.winning_team = None
        if self.show_state:
            print(f"Agent {self.agents[0].agent_type_id} is X and agent {self.agents[1].agent_type_id} is O")

        return
    
    def get_observation(self, agent : Agent): 
        return
    

    def play(self):
        player_1 = self.agents[0]
        player_2 = self.agents[1]
        
        
        # while True:
        #     # Player 1 moves
        #     observation, available_actions = self.get_observation(player_1)
        #     action = player_1.take_action(self.rules, observation, available_actions, show_state=self.show_state)
        #     self.update(action, available_actions, player_1)
        #     if self.game_is_over:
        #         break

        #     # Player 2 moves
        #     observation, available_actions = self.get_observation(player_2)
        #     action = player_2.take_action(self.rules, observation, available_actions, show_state=self.show_state)
        #     self.update(action, available_actions, player_2)
        #     if self.game_is_over:
        #         break

        self.winning_team = None

        return (0.5, 0.5) if self.winning_team == None else (float(self.winning_team == 0), float(self.winning_team == 1))