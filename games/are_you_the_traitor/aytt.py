from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import random

@dataclass
class AreYouTheTraitor(Game):

    #########################
    ### Class definitions ###
    #########################
    class Player:
        def __init__(self, identifier, agent, team, role, target, context, cards, score):
            self.identifier = identifier
            self.agent = agent
            self.team = team
            self.role = role
            self.target = target
            self.context = context
            self.cards = cards
            self.score = score

        def __repr__(self):
            return f"Player({self.identifier}, {self.team}, {self.score}, {self.role}, {self.cards})" # not including self.context for brevity

    class TreasureCard:
        def __init__(self, identifier, name, num_points):
            self.identifier = identifier
            self.name = name
            self.num_points = num_points

        def __repr__(self):
            return f"Treasure({self.identifier}, {self.name}, {self.num_points})"

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
    list_all_treasures: list = field(default_factory=list)
    players_per_team : int = 3

    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.agents = [agent1(team_id = 0, agent_id = 0), agent2(team_id = 1, agent_id = 1)]
        self.round_winner = None
        self.game_winner = None

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
        self.list_all_players.append(self.Player(0, self.agents[0], "evil", "traitor", "", f"{traitor_context}", [], 0))
        self.list_all_players.append(self.Player(1, self.agents[0], "evil", "evil_wizard", "key_holder", f"{evil_wizard_context}", [], 0))
        self.list_all_players.append(self.Player(2, self.agents[1], "good", "good_wizard", "traitor", f"{good_wizard_context}", [], 0))
        self.list_all_players.append(self.Player(3, self.agents[1], "good", "key_holder", "good_wizard", f"{key_holder_context}", [], 0))
        self.list_all_players.append(self.Player(4, self.agents[1], "good", "guard", "traitor", f"{guard_context}", [], 0))

        #############################
        ### create Treasure cards ###
        #############################

        # name, num_cards, points
        name_treasures = {
            "crown_jewels": [2, 5],
            "platinum_pyramids": [5, 4],
            "bags_of_gold": [12, 3],
            "silver_goblets": [11, 2],
            "chest_of_copper": [5, 1],
            "magic_ring": [5, 1],
            "gilded_statue": [2, 0]
        }

        counter = 0
        for key in name_treasures.keys():
            for num_cards in range(name_treasures[key][0]):
                self.list_all_treasures.append(self.TreasureCard(counter, key, name_treasures[key][1]))
                counter += 1

        random.shuffle(self.list_all_treasures)
    
    def get_observation(self, agent : Agent): 
        return

    def play(self):
        player_1 = self.agents[0]
        player_2 = self.agents[1]
        
        def check_round_winner(accuser, accused):
            ## find winning team
#            if accuser.target == accused:
#                self.round_winner = accuser.team
#            else:
#                if accuser.team == "evil":
#                    self.round_winner = "good"
#                else:
#                    self.round_winner = "evil"
            teams = ["evil", "good"] 
            round_winner = random.choice(teams)
            #print(f"the {self.round_winner} team won!")
            print(f"the {round_winner} team won!")

            ## give them treasure cards
            #winning_team = [player for player in self.list_all_players if player.team == self.round_winner]
            winning_team = [player for player in self.list_all_players if player.team == round_winner]

            for player in winning_team:
                player.cards.append(self.list_all_treasures[0])
                self.list_all_treasures.pop(0)

        def check_game_winner():
            ## calc num points per player
            for player in self.list_all_players:
                player.score = 0 # reset and recount each time
                for card in player.cards:
                    player.score += card.num_points

            ## is over 10 points?
            for player in self.list_all_players:
                if player.score >= 10:
                    if self.show_state: print("game done")
                    self.game_winner = player.team
                    return True
                else:
                    continue
            return False

        def check_special_cards(card_type):
            players_with_cards = [player for player in self.list_all_players if len(player.cards) != 0]
            players_with_special = []
            for player in players_with_cards:
                for card in player.cards:
                    if card.name == card_type and player not in players_with_special:
                        players_with_special.append(player)
            return players_with_special

        def use_magic_ring(card_player, gs_owner):
            self_team = card_player.team
            players_with_cards = [player for player in self.list_all_players if len(player.cards) != 0 and player.team != self_team]

            print(f"player to magic ring: {card_player}")
            print("avail cards")
            print(players_with_cards) 

            if len(players_with_cards) == 0:
                return

            rand_player = random.choice(players_with_cards)
            rand_card = random.choice(rand_player.cards)

            card_player.cards.append(rand_card)
            rand_player.cards.remove(rand_card)

#            if rand_player in gs_owner: 
#                print("giev gs, remove gs?")
#                print(rand_player)
#            else:
#                rand_card = random.choice(rand_player.cards)
#                print(rand_card)

            ## take card

            
            


        ####################
        ### rounds start ###
        ####################
        while True: # runs until points >= 10

            ## reseting of contexts... ##
            ## conversations happen ##
            ## someone yells stop ##
            #check_round_winner(self.list_all_players[1], self.list_all_players[2].role) # good

            ## magic rings / gilded statue check##
            magic_ring_players = check_special_cards("magic_ring")
            gilded_statue_players = check_special_cards("gilded_statue")
            #use_magic_ring(self.list_all_players[3], gilded_statue_players)
            
            print("\n\n\t begin the outputs")

            check_round_winner(self.list_all_players[1], self.list_all_players[3].role) # evil
            for i in self.list_all_players:
                print(i)

            print("\n\n\t\t magic ring players")
            print(magic_ring_players) 

            print("\n\n\t\t GS players")
            print(gilded_statue_players )

            for i in magic_ring_players:
                print("\n\n\tbegin the magic ring")
                use_magic_ring(i, gilded_statue_players)
            

            ## check if winner ##
            if check_game_winner() == True:
                break
            else:
                continue

        print(f"The {self.game_winner} team is the winner")

        return (1, 0) if self.game_winner == "good" else (0,1)
