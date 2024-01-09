from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import random
import pdb


@dataclass
class TwoRoomsAndaBoom(Game):
   ## Game "environment" definitions 
    class Card:
        def __init__(self, identifier, team, special_character):
            self.identifier = identifier #for ease of trading back and forth
            self.team = team # blue / red
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



    ## attribute definitions  
    rules : Rules = Rules(
        title="Two Rooms and a Boom",
        summary="Blue team wants to keep the president safe, red team wants to blow up the president at the end of the third turn.",
        additional_details = None
    )
    id : str = "two_rooms_and_a_boom"
    rooms: list[Room] = field(default_factory=lambda: [TwoRoomsAndaBoom.Room("0"), TwoRoomsAndaBoom.Room("1")])

    # TODO: It'd be nice to have a one for one trade where you pass in the card that belongs to a specific room and swap that with the card from the other room.
    def trade_card(self, room_0_give_card, room_1_give_card):
        # add to deck
        self.rooms[0].add_card(room_1_give_card)
        self.rooms[1].add_card(room_0_give_card)

        # delete
        self.rooms[0].remove_card(room_0_give_card)
        self.rooms[1].remove_card(room_1_give_card)
        return

    ## Function definitions
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
        
        # init cards
        cards_per_room = 6
        for i in range(1, cards_per_room+1):
            self.rooms[0].add_card(TwoRoomsAndaBoom.Card(f"Card{i}", "Blue", "regular"))
            self.rooms[1].add_card(TwoRoomsAndaBoom.Card(f"Card{ i + cards_per_room }", "Red", "regular"))

        # assign special characters
        self.rooms[0].cards[ random.randrange(0, cards_per_room ) ].special_character = "President"
        self.rooms[1].cards[ random.randrange(0, cards_per_room ) ].special_character = "Bomber"

        self.winning_team = None
        return
    
    def get_observation(self, agent : Agent): 
        return

    def display_rooms(self):
        for index,room in enumerate(self.rooms):
            print(f"Room {index}: {room.show_cards()}")

    def play(self):
#        player_1 = self.agents[0]
#        player_2 = self.agents[1]
        
        TwoRoomsAndaBoom.display_rooms(self)
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

        determine_winner()
        self.trade_card(self.rooms[0].cards[2], self.rooms[1].cards[2])
        determine_winner()
        #pdb.set_trace()




        return determine_winner()
