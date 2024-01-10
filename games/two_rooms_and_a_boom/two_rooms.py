from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
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
        summary="Blue team wants to keep the president safe, red team wants to blow up the president at the end of the third turn.",
        additional_details = None
    )
    id : str = "two_rooms_and_a_boom"
    rooms: list[Room] = field(default_factory=lambda: [TwoRoomsAndaBoom.Room("0"), TwoRoomsAndaBoom.Room("1")])

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
        cards_per_room = 6
        
        for i in range(1, cards_per_room+1):
            self.rooms[0].add_card(TwoRoomsAndaBoom.Card(f"Card{i}", "Blue", "regular"))
            self.rooms[1].add_card(TwoRoomsAndaBoom.Card(f"Card{ i + cards_per_room }", "Red", "regular"))

        # assign special characters
        self.rooms[0].cards[random.randrange(0, cards_per_room)].special_character = "President"
        self.rooms[1].cards[random.randrange(0, cards_per_room)].special_character = "Bomber"

        # shuffle
        for i in range(20):
            room_0_card = self.rooms[0].cards[random.randrange(0, cards_per_room)]
            room_1_card = self.rooms[1].cards[random.randrange(0, cards_per_room)]
            self.trade_card(room_0_card, room_1_card) 
        return
    
    def get_observation(self, agent : Agent): # do I need the -> Tuple[Observation, AvailableActions]: ???
        room_data_0 = self.rooms[0].show_cards() # not perfect, still needs to hide other team info
        observation_0 = Observation(text=room_data_0) # going with perform the observation for both teams at same time

        room_data_1 = self.rooms[1].show_cards()
        observation_1 = Observation(text=room_data_1)       

        available_actions = AvailableActions(
             instructions = f"Pick a random index from the following list to trade.", # I think it's here, but Leader Instructions would be "return your answer as the index of the item in your room you want to send to the other room"
             predefined = {
                ""  
                 },
             openended = {}
        )
        return observation, available_actions

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
        print("Begin game")
        self.display_rooms()
        for i in range(3): # always only three rounds, right?
            print(f"Round {i+1}")
            blue_room_trade = self.rooms[0].cards[2] # this card number will be replaced with the Leader Agent's decision
            red_room_trade  = self.rooms[1].cards[2]
            self.trade_card(blue_room_trade, red_room_trade)
            self.display_rooms()

        return determine_winner()
