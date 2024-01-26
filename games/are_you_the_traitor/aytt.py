from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import random

@dataclass
class AreYouTheTraitor(Game):

    #########################
    ### Class definitions ###
    #########################
    class Player:
        def __init__(self, identifier, agent, team, role, context, score):
            self.identifier = identifier
            self.agent = agent
            self.team = team
            self.role = role
            self.context = context
            self.score = score

        def __repr__(self):
            return f"Player({self.identifier}, {self.team}, {self.score}, {self.agent}, {self.role})" # not including self.context for brevity again

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

        traitor_context = """
        As the Traitor on the evil team, my main goal is to remain undetected by the other players. While staying undercover, I aim to identify the Evil Wizard and discreetly communicate my allegiance to them, although this must be done with utmost caution to avoid exposing myself. If I can safely do so, informing the Evil Wizard about the KeyHolder's identity would be ideal, enabling them to seize the Key. However, I must be extremely careful in my signaling, ensuring it's not observed by others, and I need to be certain of the Wizards' identities, as a mistake could lead to my immediate capture by the Good Wizard.
        """

        evil_wizard_context = """
        I am the Evil Wizard on the evil team, seeking to identify and take the Evil Magic Key from the non-wizard who secretly holds it. My plan includes deceiving the KeyHolder into believing that I am the Good Wizard, so they hand over the Key willingly. Additionally, I'm aware that a Traitor among the players knows the KeyHolder's identity. My task is to find out who this Traitor is, to avoid mistaking them for the KeyHolder, and to potentially get clues about the KeyHolder's identity from them.
        """

        good_wizard_context = """
        As the Good Wizard on the good team, my objective is to convince the KeyHolder of my true identity so that they trust me with the Evil Magic Key. Unlike the Evil Wizard, I adhere to a code of ethics that forbids me from forcibly taking the Key. My efforts are also directed towards identifying and apprehending the evil Traitor. It's crucial to establish trust with the KeyHolder and to differentiate myself from the deceitful tactics of the Evil Wizard.
        """

        key_holder_context = """
        As the KeyHolder on the good team, my task is to discern the true identity of the Good Wizard among two identical-looking Wizards. I hold the Evil Magic Key, which must be handed over to the Good Wizard for its destruction. However, I must be cautious not to reveal my identity as the KeyHolder to the Evil Wizard, to prevent them from using force to seize the Key. It's a delicate balance of identifying the right Wizard while keeping my crucial role concealed.
        """

        guard_context = """
        In my role as a Guard for the good team, I am vigilantly searching for the hidden Traitor among us. Protecting the identity of the KeyHolder is paramount, and I might even distract the Evil Wizard by falsely claiming to be the KeyHolder. Determining the true identities of the Wizards is key to guiding the KeyHolder and thwarting the Evil Wizard's plans. My primary focus, though, remains on uncovering and pointing out the Traitor before they can cause harm.
        """


        # I'm starting with Evil in case I need to add, the good agents increase first
        self.list_all_players.append(self.Player(0, self.agents[0], "evil", "traitor", f"{traitor_context}", 0))
        self.list_all_players.append(self.Player(1, self.agents[0], "evil", "evil_wizard", f"{evil_wizard_context}", 0))
        self.list_all_players.append(self.Player(2, self.agents[1], "good", "good_wizard", f"{good_wizard_context}", 0))
        self.list_all_players.append(self.Player(3, self.agents[1], "good", "key_holder", f"{key_holder_context}", 0))
        self.list_all_players.append(self.Player(4, self.agents[1], "good", "guard", f"{guard_context}", 0))
    
        for i in self.list_all_players:
            print(i.context)

    def get_observation(self, agent : Agent): 
        return

    def play(self):
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

        ####################
        ### rounds start ###
        ####################
        while True: # runs until points >= 10

            self.list_all_players[0].score += 4
            print(self.list_all_players[0].score)
            ## Assign roles ##
            ## conversations happen ##
            ## someone yells stop ##
            if check_if_winner() == True:
                break
            else:
                continue

        print(f"The {self.winning_team} team is the winner")

        return (1, 0) if self.winning_team == "good" else (0,1)
