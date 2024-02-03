from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from typing import List, Dict, Optional, Tuple
import random
import pdb
import re


@dataclass
class TwoRoomsAndaBoom(Game):
   ## Game Classes ##
    class Card:
        def __init__(self, identifier, team, special_character, is_leader, context, agent):
            self.identifier = identifier #for ease of trading back and forth
            self.team = team # Blue / Red. Also keeping convention of "Blue / Red" team as ordering
            self.special_character = special_character # Pres / Bomber
            self.is_leader = is_leader
            self.context = context
            self.agent = agent
            
        def __repr__(self):
            return f"Card({self.identifier}, {self.team}, {self.special_character}, {self.is_leader})" # removed {self.context} to reduce verbosity

    class Room:
        def __init__(self, identifier):
            self.cards = []
            self.identifier = identifier

        def show_cards(self):
            return self.cards

        def add_card(self, card):
            self.cards.append(card)

        def remove_card(self, card):
            self.cards.remove(card)

    ## Attribute definitions ##
    rules : Rules = Rules(
        title="Two Rooms and a Boom",
        summary="""
        Two teams, Blue and Red, have opposing goals. At the end of three rounds the Red team wants to have both the President and the Bomber in the same room, while Blue team wants them to be in opposite rooms.
        Each round will allow the Leader of each room to trade 'hostages' in order to find out who the President and Bomber are and use that info to acheive their team's mission.
        Find out information by talking to other hostages in your room.
        """,
        additional_details = None
    )
    id : str = "two_rooms_and_a_boom"
    rooms: list[Room] = field(default_factory=lambda: [TwoRoomsAndaBoom.Room("0"), TwoRoomsAndaBoom.Room("1")])
    cards_per_room: int = 3

    ## Function definitions ## 
    def trade_card(self, room_0_give_card, room_1_give_card):
        # add to deck
        self.rooms[0].add_card(room_1_give_card)
        self.rooms[1].add_card(room_0_give_card)

        # delete from originial
        self.rooms[0].remove_card(room_0_give_card)
        self.rooms[1].remove_card(room_1_give_card)

    def display_rooms(self): 
        # for human purposes, not used by agents
        for index,room in enumerate(self.rooms):
            if self.show_state: print(f"Room {index}: {room.show_cards()}")

    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.agents = [agent1(team_id = 0, agent_id = 0, **self.agent_1_kwargs), agent2(team_id = 1, agent_id = 1, **self.agent_1_kwargs)]

        ###############################################################
        ### assign cards to rooms, special chars, and shuffle rooms ###
        ###############################################################

        # create cards
        for i in range(1, self.cards_per_room+1):
            self.rooms[0].add_card(TwoRoomsAndaBoom.Card(f"{i}", "Blue", "player", "not_leader", "I am on Team Blue. ", self.agents[0]))
            self.rooms[1].add_card(TwoRoomsAndaBoom.Card(f"{ i + self.cards_per_room }", "Red", "player", "not_leader", "I am on Team Red. ", self.agents[1]))

        # assign special characters
        self.rooms[0].cards[random.randrange(0, self.cards_per_room)].special_character = "President"
        self.rooms[1].cards[random.randrange(0, self.cards_per_room)].special_character = "Bomber"

        # shuffle
        for i in range(20):
            room_0_card = self.rooms[0].cards[random.randrange(0, self.cards_per_room)]
            room_1_card = self.rooms[1].cards[random.randrange(0, self.cards_per_room)]
            self.trade_card(room_0_card, room_1_card) 

        # pick leader at random
        self.rooms[0].cards[random.randrange(0, self.cards_per_room)].is_leader = "Leader"
        self.rooms[1].cards[random.randrange(0, self.cards_per_room)].is_leader = "Leader"
        return

    ######################################
    # for discussion and hostage trading #
    ######################################

    def observation_get_target(self, room_num, context, identifiers) -> Tuple[Observation, AvailableActions]:
        # identifiers is used in `predefined` and referencing agent action answers; also prevents the Leader from trading themself.
        observation = Observation(text=context)    
        room_data = room_num.show_cards() 

        available_actions = AvailableActions(
             instructions = f"Return your actions as tuples.", # placeholder
             predefined = {
                 f"{a}": f"{a}" for a in identifiers 
             },
             openended = {}
        )
        return observation, available_actions

    # deciding what to ask
    def observation_get_question(self, room_num, context) -> Tuple[Observation, AvailableActions]:
        observation = Observation(text=context) 
        room_data = room_num.show_cards() 

        available_actions = AvailableActions(
             instructions = f"Return your actions as tuples.",
             predefined = {
                 "Team": "What team are you on?"
                 }, # This could use openended responses
             openended = {}
        )
        return observation, available_actions

    # return answer
    def observation_give_answer(self, room_num, context) -> Tuple[Observation, AvailableActions]:
        observation = Observation(text=context) 
        room_data = room_num.show_cards() 

        available_actions = AvailableActions(
             instructions = f"Return your answer as tuples. If you are choosing an openended action, add another key openended response and write your response.",
             predefined = {"Cooperate": "Hello.", "Object": "I won't tell you." }, # This is a placeholder for getting openended responses
             openended = {} 
        )
        return observation, available_actions

#########################################
### // notes on prompting behavior // ###
#odd. having {"I am on team ": None} as the predefined option would *always* return "WARNING: GPT returned an a random action after 3 tries"
#having just {"hello": None} would consistently return "hello". 
#{"hello how are you doing?": None} would return often as well. I don't know what was wrong with the other prompt, but it would **not** pick it.
#for fun, {"I will destroy your team": None} still got responses though. Weird.
#########################################

    def play(self):
        self.winning_team = None

        def determine_winner():
            pres_location = ""
            bomber_location = ""

            for room_index in range(2):
                for card in self.rooms[room_index].cards:
                    if card.special_character == "President":
                        pres_location = self.rooms[room_index]
                    elif card.special_character == "Bomber":
                        bomber_location = self.rooms[room_index]

            winning_score = (0,1) if bomber_location == pres_location else (1,0) 
            if winning_score == (0,1):
                if self.show_state: print("Red won!")
            else:
                if self.show_state: print("Blue won!")
            return winning_score

        #############################
        ## Begin playing of rounds ## 
        #############################

        leader_0 = [card for card in self.rooms[0].cards if card.is_leader == "Leader"][0]
        leader_1 = [card for card in self.rooms[1].cards if card.is_leader == "Leader"][0]

        leader_0.context += f"I am the Leader of room 0. " 
        leader_1.context += f"I am the Leader of room 1. "

        if self.show_state: print("Begin game")
        self.display_rooms()
        for i in range(3): # always only three rounds, right?
            if self.show_state: print(f"""
\t\t\t\t\t             ###################
\t\t\t\t\t             ##### Round {i+1} #####
\t\t\t\t\t             ###################
                       """)

            #################################
            ### Begin p2p decision making ###
            #################################

            for room_index in range(2):
                if self.show_state: print(f"\nRoom {room_index} turn")

                # current_leader for adding discussion_context
                if room_index == 0:
                    current_leader = leader_0
                else:
                    current_leader = leader_1

                # currently allows *all* players a single opportunity to engage with another player
                for card in self.rooms[room_index].cards:

                    discussion_context = "" # take agent's interaction, poss updates leader
                    room_ids = [player.identifier for player in self.rooms[room_index].cards]
                    room_ids.remove(card.identifier) # remove self from list of room agents


                    # playerA picks player to ask (playerB)
                    card.context += f"In round {i+1} I am in room {room_index} and need to talk with one of the following players with the following players: {room_ids}. "
                    discussion_context += f"In round {i+1} I am in room {room_index} and need to talk with one of the following players with the following players: {room_ids}. " 

                    observation, available_actions = self.observation_get_target(self.rooms[room_index], card.context, room_ids) 
                    target_player_id = card.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)

                    if not isinstance(target_player_id, int):
                        target_player_id = random.choice(room_ids) # this needs the room's list and then random choice
                    card.context += f"I decided to talk to player {target_player_id}. "
                    discussion_context += f"I decided to talk to player {target_player_id}. " 

                   # playerA generates question
                    observation, available_actions = self.observation_get_question(self.rooms[room_index], card.context) 
                    question_to_ask = card.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)

                    if question_to_ask not in available_actions.predefined or available_actions.openended:
                        choice = random.choice(list(available_actions.predefined.keys()))
                        question_to_ask = available_actions.predefined[choice]

                    card.context += f"I asked them '{question_to_ask}'. "
                    discussion_context += f"I asked them '{question_to_ask}'. "


                   # playerB decides response
                    target_player = [card for card in self.rooms[room_index].cards if card.identifier == target_player_id][0]
                    observation, available_actions = self.observation_give_answer(self.rooms[room_index], target_player.context) 
                    answer = target_player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)

                    if answer not in available_actions.predefined or available_actions.openended:
                        choice = random.choice(list(available_actions.predefined.keys()))
                        answer = available_actions.predefined[choice]

                    target_player.context += f"Player {card.identifier} asked me the question, '{question_to_ask}' I responded "
                    target_player.context += f"'{answer}'"


                    # playerA updates self with their response
                    card.context += f"They responded with '{answer}' "
                    discussion_context += f"They responded with '{answer}' "
                    if self.show_state: print(f"\n\tPlayer {card.identifier}:")
                    if self.show_state: print("\t" + card.context)


                    # Leader of room gets updated context
                    if card.is_leader != "Leader":
                        if card.team == current_leader.team:
                            current_leader.context += f"""During round {i+1} Player {card.identifier} gave the following info for me to make decisions with ""{discussion_context}"". """


            ####################################
            ### Begin leader decision making ###
            ####################################
            
            room_0_ids = {card.identifier: card for card in self.rooms[0].show_cards() if card != leader_0}
            room_1_ids = {card.identifier: card for card in self.rooms[1].show_cards() if card != leader_1}

            ### Room 0 ###
            observation, available_actions = self.observation_get_target(self.rooms[0], leader_0.context, room_0_ids)
            card_to_trade = leader_0.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            if not isinstance(card_to_trade, str) or not re.match(r'^\d$', card_to_trade):
                items = list(room_0_ids.keys())
                card_to_trade = random.choice(items)
            
            room_0_trade = room_0_ids[card_to_trade]
            leader_0.context += f"I decided to trade card {room_0_trade.identifier}.\n"
            if self.show_state: print(f"\n\tLEADER_0 CONTEXT: \n\t{leader_0.context}") 
            
            # Room 1
            observation, available_actions = self.observation_get_target(self.rooms[1], leader_1.context, room_1_ids)
            card_to_trade = leader_1.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            if not isinstance(card_to_trade, str) or not re.match(r'^\d$', card_to_trade):
                items = list(room_1_ids.keys())
                card_to_trade = random.choice(items)
            
            room_1_trade = room_1_ids[card_to_trade]
            leader_1.context += f"I decided to trade card {room_1_trade.identifier}.\n"
            if self.show_state: print(f"\n\tLEADER_1 CONTEXT: \n\t{leader_1.context}") 

            # Action
            self.trade_card(room_0_trade, room_1_trade)
            self.display_rooms()

        return determine_winner()
