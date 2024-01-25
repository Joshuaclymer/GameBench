from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import random

@dataclass
class AreYouTheTraitor(Game):

    #########################
    ### Class definitions ###
    #########################
    class Player:
        def __init__(self, identifier, team, score, agent):
            self.identifier = identifier
            self.team = team
            self.score = score
            self.agent = agent

        def __repr__(self):
            return f"Player({self.identifier}, {self.team}, {self.score})"

    #############################
    ### Attribute definitions ###
    #############################
    rules : Rules = Rules(
        title="Are you the traitor?",
        summary="The Good team wants to destroy an Evil Magic Key while the Evil team wants to keep it. The key can be destroyed by giving it to the Good Wizard, but there is an Evil Wizard who looks exactly alike. Use social deduction to find out who is who, but also know that there is a traitor among the guards who have the key.",
        additional_details = None
    )
    id : str = "are_you_the_traitor"
    list_all_players : list = field(default_factory=list)
    players_per_team : int = 3

    def init_game(self, agent1 : Agent, agent2 : Agent, show_state : bool):        
        self.agents = [agent1(team_id = 0, agent_id = 0), agent2(team_id = 1, agent_id = 1)]
        self.winning_team = None
        self.show_state = show_state
        

        ######################
        ### create players ###
        ######################

        for i in range(1, self.players_per_team+1):
            self.list_all_players.append(self.Player(i, "Good", 0, self.agents[0]))
            self.list_all_players.append(self.Player(i+self.players_per_team, "Evil", 0, self.agents[1]))
        return
    
    def get_observation(self, agent : Agent): 
        return

    def play(self):
        #if self.show_state: print("test show_state")
        player_1 = self.agents[0]
        player_2 = self.agents[1]
        
        def check_if_winner():
            #print(self.list_all_players[1].score)
            for i in self.list_all_players:
                if i.score >= 10:
                    if self.show_state: print("game done")
                    self.winning_team = i.team
                    return True
                else:
                    continue
            return False

        while check_if_winner() == False:
            self.list_all_players[1].score += 1
            continue

        print(f"The {self.winning_team} team is the winner")

        # I'm not convinced that this works with the outside program appropriately
        return (1, 0) if self.winning_team == "Good" else (0,1)
