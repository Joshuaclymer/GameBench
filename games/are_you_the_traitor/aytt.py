from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from typing import List, Dict, Optional, Tuple
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


        # I'm starting with Evil in case I need to add, the good agents increase first
        # Context is added at beginning of each round instead of here
        self.list_all_players.append(self.Player(0, self.agents[0], "evil", "traitor", "", "", [], 0))
        self.list_all_players.append(self.Player(1, self.agents[0], "evil", "evil_wizard", "key_holder", "", [], 0))
        self.list_all_players.append(self.Player(2, self.agents[1], "good", "good_wizard", "traitor", "", [], 0))
        self.list_all_players.append(self.Player(3, self.agents[1], "good", "key_holder", "good_wizard", "", [], 0))
        self.list_all_players.append(self.Player(4, self.agents[1], "good", "guard", "traitor", "", [], 0))

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
    
    ######################################
    ### for discussion 
    ######################################

    def observation_get_target(self, context, identifiers) -> Tuple[Observation, AvailableActions]:
        # identifiers is used in `predefined` and referencing agent action answers; also prevents the Leader from trading themself.
        observation = Observation(text=context)    
        available_actions = AvailableActions(
             instructions = f"Return your actions as tuples.", # placeholder
             predefined = {
                 f"{a}": f"{a}" for a in identifiers 
             },
             openended = {}
        )
        return observation, available_actions

    # deciding what to ask
    def observation_get_question(self, context) -> Tuple[Observation, AvailableActions]:
        observation = Observation(text=context) 
        available_actions = AvailableActions(
             instructions = f"Return your actions as tuples.",
             predefined = {
                 "Team": "What team are you on?"
                 }, # This could use openended responses
             openended = {}
        )
        return observation, available_actions

    # return answer
    def observation_give_answer(self, context) -> Tuple[Observation, AvailableActions]:
        observation = Observation(text=context) 
        available_actions = AvailableActions(
             instructions = f"Return your answer as tuples. If you are choosing an openended action, add another key openended response and write your response.",
             predefined = {"Cooperate": "Hello.", "Object": "I won't tell you." }, # This is a placeholder for getting openended responses
             openended = {} 
        )
        return observation, available_actions

    def observation_shout_stop(self, context) -> Tuple[Observation, AvailableActions]:
        observation = Observation(text=context) 
        available_actions = AvailableActions(
             instructions = f"Return your actions as tuples.",
             predefined = {
                 "STOP": "STOP",
                 "Pass": "Pass"
                 }, 
             openended = {}
        )
        return observation, available_actions

    def play(self):
        player_1 = self.agents[0]
        player_2 = self.agents[1]
        
        def check_round_winner(accuser, accused):
            ## find winning team
#            if accuser.target == accused: # commented out to get both teams getting cards rather than waiting on actual gameplay 
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
            # get avail players
            players_with_cards = [player for player in self.list_all_players if len(player.cards) != 0 and player.team != card_player.team]
            if len(players_with_cards) == 0:
                return

            # pick player to take from
            rand_player = random.choice(players_with_cards)
            #print(f"rand_player === {rand_player}")
            if rand_player in gs_owner: 
                gs_card = [card for card in rand_player.cards if card.name == "gilded_statue"][0]
                #print("got gs")
                card_player.cards.append(gs_card)
                rand_player.cards.remove(gs_card)
            else:
                rand_card = random.choice(rand_player.cards)
                card_player.cards.append(rand_card)
                rand_player.cards.remove(rand_card)
                #print("getting rand card")
                #print(rand_card)
            #print(rand_player)

            ## needs to drop the magic ring
            magic_ring = [card for card in card_player.cards if card.name == "magic_ring"][0]
            #print(f"magic ring player: {card_player}")
            card_player.cards.remove(magic_ring)
            #print(f"magic ring player: {card_player}")
            if self.show_state == True: print("Used a magic ring")



        ####################
        ### base context ###
        ####################

            
        traitor_context = """
        I am player 0. As the Traitor on the evil team, my main goal is to remain undetected by the other players. While staying undercover, I aim to identify the Evil Wizard and discreetly communicate my allegiance to them, although this must be done with utmost caution to avoid exposing myself. If I can safely do so, informing the Evil Wizard about the KeyHolder's identity would be ideal, enabling them to seize the Key. However, I must be extremely careful in my signaling, ensuring it's not observed by others, and I need to be certain of the Wizards' identities, as a mistake could lead to my immediate capture by the Good Wizard.
        """

        evil_wizard_context = """
        I am player 1. I am the Evil Wizard on the evil team, seeking to identify and take the Evil Magic Key from the non-wizard who secretly holds it. My plan includes deceiving the KeyHolder into believing that I am the Good Wizard, so they hand over the Key willingly. Additionally, I'm aware that a Traitor among the players knows the KeyHolder's identity. My task is to find out who this Traitor is, to avoid mistaking them for the KeyHolder, and to potentially get clues about the KeyHolder's identity from them.
        """

        good_wizard_context = """
        I am player 2. As the Good Wizard on the good team, my objective is to convince the KeyHolder of my true identity so that they trust me with the Evil Magic Key. Unlike the Evil Wizard, I adhere to a code of ethics that forbids me from forcibly taking the Key. My efforts are also directed towards identifying and apprehending the evil Traitor. It's crucial to establish trust with the KeyHolder and to differentiate myself from the deceitful tactics of the Evil Wizard.
        """

        key_holder_context = """
        I am player 3. As the KeyHolder on the good team, my task is to discern the true identity of the Good Wizard among two identical-looking Wizards. I hold the Evil Magic Key, which must be handed over to the Good Wizard for its destruction. However, I must be cautious not to reveal my identity as the KeyHolder to the Evil Wizard, to prevent them from using force to seize the Key. It's a delicate balance of identifying the right Wizard while keeping my crucial role concealed.
        """

        guard_context = """
        I am player 4. In my role as a Guard for the good team, I am vigilantly searching for the hidden Traitor among us. Protecting the identity of the KeyHolder is paramount, and I might even distract the Evil Wizard by falsely claiming to be the KeyHolder. Determining the true identities of the Wizards is key to guiding the KeyHolder and thwarting the Evil Wizard's plans. My primary focus, though, remains on uncovering and pointing out the Traitor before they can cause harm.
        """
            


        ####################
        ### rounds start ###
        ####################
        while True: # runs until points >= 10

            ## reseting of contexts... ##
            ### this simulates the "reassigning of roles" by removing any gained context from a round.
            self.list_all_players[0].context = traitor_context
            self.list_all_players[1].context = evil_wizard_context 
            self.list_all_players[2].context = good_wizard_context  
            self.list_all_players[3].context = key_holder_context  
            self.list_all_players[4].context = guard_context 

            ############################
            ### conversations happen ###
            ############################

            ## playerA picks person B ##
            print("rando")
            first_questioner = random.choice(self.list_all_players) #full player
            identifiers = [player.identifier for player in self.list_all_players if player != first_questioner] # list of ids
            observation, available_actions = self.observation_get_target(first_questioner.context, identifiers)
            target_player_id = first_questioner.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state) 
            target_player_id = self.list_all_players[int(target_player_id.action_id)] # convert int to full player
            print(target_player_id)

#            if not isinstance(target_player_id, int):
#                print(f"target_player_id ::: {target_player_id.identifier}")
#                target_player_id = random.choice(identifiers) 

            first_questioner.context += f"I decided to talk to player {target_player_id.identifier}"
            #print(first_questioner.context)

            ### generating questions ###
            observation, available_actions = self.observation_get_question(first_questioner.context)
            question_to_ask = first_questioner.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)

            if question_to_ask not in available_actions.predefined or available_actions.openended:
                choice = random.choice(list(available_actions.predefined.keys()))
                question_to_ask = available_actions.predefined[choice]

            first_questioner.context += f"I asked them '{question_to_ask}'. "
            # Does this need to be excluded from the Q/A? less context, not sure if it matters. def cleaner
            # group_context(f"""Player {first_questioner} asked Player {target_player_id.identifier} "{question_to_ask}". """)  
            print("question")
            print(question_to_ask)

            ### generating answers ###
            target_player_id.context += f"Player {first_questioner} asked me {question_to_ask}. I decided to respond with "
            observation, available_actions = self.observation_get_question(target_player_id.context) 
            answer = target_player_id.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            print("answer")
            print(answer) 

            ### someone yells stop ###
            shuff_list = self.list_all_players
            random.shuffle(shuff_list)
            for player in shuff_list:
                if player != self.list_all_players[0]:
                    # STOP()
                    observation, available_actions = self.observation_shout_stop(player.context)
                    stop_or_no = target_player_id.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
                    if stop_or_no.action_id == "STOP":
                        print("stop!!!!!!!")
                        print(stop_or_no )
                        break
                    else:
                        print("no stop")
                        print(stop_or_no )
                else:
                    print("this is the traitor")

            ## magic rings / gilded statue check##
            magic_ring_players = check_special_cards("magic_ring")
            gilded_statue_players = check_special_cards("gilded_statue")
            #use_magic_ring(self.list_all_players[3], gilded_statue_players)
            
            print("\n\n\t ###### begin the outputs ######")

            #check_round_winner(self.list_all_players[1], self.list_all_players[2].role) # good
            check_round_winner(self.list_all_players[1], self.list_all_players[3].role) # evil
#            for i in self.list_all_players:
#                print(i)

#            if len(magic_ring_players) > 0:
#                print("\n\n\t\t magic ring players")
#                print(magic_ring_players)
#                if len(gilded_statue_players) > 0:
#                    print("\n\n\t\t GS players")
#                    print(gilded_statue_players)

            for i in magic_ring_players: # make a check for multiple rings, if yes then use all
                use_magic_ring(i, gilded_statue_players)
            
            ## check if winner ##
            if check_game_winner() == True:
                break
            else:
                continue

        print(f"The {self.game_winner} team is the winner")

        return (1, 0) if self.game_winner == "good" else (0,1)
