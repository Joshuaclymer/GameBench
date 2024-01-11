from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from typing import List, Dict, Optional, Tuple
import random
import pdb


@dataclass
class TwoRoomsAndaBoom(Game):
   ## Game Classes ##
    class Card:
        def __init__(self, identifier, team, special_character):
            self.identifier = identifier #for ease of trading back and forth
            self.team = team # blue / red. Also keeping convention of "Blue / Red" team as ordering
            self.special_character = special_character # Pres / Bomber
            
        def __repr__(self):
            return f"Card({self.identifier}, {self.team}, {self.special_character})"

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
        Find out information by talking to other hostages in the room.
        """,
        additional_details = None
    )
    id : str = "two_rooms_and_a_boom"
    rooms: list[Room] = field(default_factory=lambda: [TwoRoomsAndaBoom.Room("0"), TwoRoomsAndaBoom.Room("1")])
    cards_per_room: int = 6

    ## Function definitions ## 
    def trade_card(self, room_0_give_card, room_1_give_card):
        # add to deck
        self.rooms[0].add_card(room_1_give_card)
        self.rooms[1].add_card(room_0_give_card)

        # delete
        self.rooms[0].remove_card(room_0_give_card)
        self.rooms[1].remove_card(room_1_give_card)
        return

    def init_game(self, agent1 : Agent, agent2 : Agent):        
        self.states = [{
            "turn" : 0
        }]
        
        # Uncertain if "teams" is the correct way to assign teams (2024.01.02)
        self.agent_data = {
            0: {"team": "Blue"},
            1: {"team": "Red"}
        }
        
        self.agents = [agent1(team_id = 0, agent_id = 0), agent2(team_id = 1, agent_id = 1)]
        
        # assign cards to rooms, special chars, and shuffle rooms
        
        for i in range(1, self.cards_per_room+1):
            self.rooms[0].add_card(TwoRoomsAndaBoom.Card(f"{i}", "Blue", "regular"))
            self.rooms[1].add_card(TwoRoomsAndaBoom.Card(f"{ i + self.cards_per_room }", "Red", "regular"))

        # assign special characters
        self.rooms[0].cards[random.randrange(0, self.cards_per_room)].special_character = "President"
        self.rooms[1].cards[random.randrange(0, self.cards_per_room)].special_character = "Bomber"

        # shuffle
        for i in range(20):
            room_0_card = self.rooms[0].cards[random.randrange(0, self.cards_per_room)]
            room_1_card = self.rooms[1].cards[random.randrange(0, self.cards_per_room)]
            self.trade_card(room_0_card, room_1_card) 
        return
    
    def get_observation(self, agent: Agent, room_num) -> Tuple[Observation, AvailableActions]:
        room_data = room_num.show_cards() # not perfect, still needs to hide other team info
        observation = Observation(text=room_data) 
        identifiers = {card.identifier: card for card in room_data}

        available_actions = AvailableActions(
             instructions = f"Return your actions as tuples where each integer is between 0 and {self.cards_per_room}-1. Do not pick your own integer.",
             predefined = {
                 f"{a}": None for a in identifiers # maybe this is the actual available actions
                 },
             openended = {}
        )
        return observation, identifiers, available_actions

    def display_rooms(self): 
        for index,room in enumerate(self.rooms):
            print(f"Room {index}: {room.show_cards()}")

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
                print("Red won!")
            else:
                print("Blue won!")
            return winning_score

        #pdb.set_trace()

        ## Begin playing of rounds ## 
        player_1 = self.agents[0]
        player_2 = self.agents[1]


        print("Begin game")
        self.display_rooms()
        for i in range(3): # always only three rounds, right?
            print(f"Round {i+1}")
            observation, identifiers, available_actions = self.get_observation(player_1, self.rooms[0])
            action = player_1.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            print(action.action_id)
            room_0_trade = identifiers[action.action_id]
            
            observation, identifiers, available_actions = self.get_observation(player_2, self.rooms[1])
            action = player_2.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            print(action.action_id)
            room_1_trade = identifiers[action.action_id]

            self.trade_card(room_0_trade , room_1_trade)
            self.display_rooms()

        return determine_winner()
