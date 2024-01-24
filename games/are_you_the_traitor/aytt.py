from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import random

@dataclass
class AreYouTheTraitor(Game):
    rules : Rules = Rules(
        title="Are you the traitor?",
        summary="The Good team wants to destroy an Evil Magic Key while the Evil team wants to keep it. The key can be destroyed by giving it to the Good Wizard, but there is an Evil Wizard who looks exactly alike. Use social deduction to find out who is who, but also know that there is a traitor among the guards who have the key.",
        additional_details = None
    )
    id : str = "are_you_the_traitor"

    def init_game(self, agent1 : Agent, agent2 : Agent, show_state : bool):        
        
        self.agents = [agent1(team_id = 0, agent_id = 0), agent2(team_id = 1, agent_id = 1)]

        self.winning_team = None

        self.show_state = show_state
        return
    
    def get_observation(self, agent : Agent): 
        return

    def play(self):
        if self.show_state: print("test show_state")
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
