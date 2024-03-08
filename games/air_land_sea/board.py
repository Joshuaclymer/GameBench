from dataclasses import dataclass, field
from typing import List
import random
from games.air_land_sea.cards import Card

@dataclass
class Theater:
    name: str
    player_1_total_strength: int = 0
    player_2_total_strength: int = 0
    player_1_cards: List[Card] = field(default_factory=list)
    player_2_cards: List[Card] = field(default_factory=list)

    def __post_init__(self):
        self.player_cards = [self.player_1_cards, self.player_2_cards]
        self.player_total_strength = [self.player_1_total_strength, self.player_2_total_strength]

    def is_uncovered(self, card: Card, player_id: int) -> bool:
        # the last one in the list is the uncovered card
        return card == self.player_cards[player_id][-1]
        # if player_id == 0:
        #     return card == self.player_1_cards[-1]
        # elif player_id == 1:
        #     return card == self.player_2_cards[-1]
        # else:
        #     raise ValueError("player_id must be 0 or 1")

    """
    Air Theater:
    Player 1: [F-35 (5, Ongoing: +1 to adjacent Theaters, uncovered), Face down (2, covered)]
    Player 2: [Face down (2, covered), Tank Buster (4, Instant: Destroy one face-down card, uncovered)]
    """
    
    def get_theater_string(self):
        # return a string representation of the theater with representation of covered/uncovered cards
        theater_name = self.name  # no "Theater" at the end

        # helper function
        def process_cards(cards, player_id):
            cards_string = ""
            for i, card in enumerate(cards):
                # replace $ with "uncovered" or "covered"
                card_status = "uncovered" if self.is_uncovered(card, player_id) else "covered"
                card_string = str(card).replace("$", card_status)
                # handle commas
                if i == 0:
                    cards_string += card_string
                else:
                    cards_string += f", {card_string}"
            return cards_string

        player_1_cards_string = process_cards(self.player_1_cards, 0)
        player_2_cards_string = process_cards(self.player_2_cards, 1)

        return_string = f"{theater_name} Theater:\nPlayer 1: [{player_1_cards_string}]\nPlayer 2: [{player_2_cards_string}]"
        return return_string

    def get_strength(self, player_id: int):
        # return the strength of the player in the theater
        pass

@dataclass
class Board:
    theaters: List[Theater] = field(default_factory=lambda: [
        Theater('Air'),
        Theater('Sea'),
        Theater('Land')
    ])
    ongoing_effects: List[Card] = field(default_factory=list) # ongoing effects that affect the board

    def __post_init__(self):
        # shuffle theaters into random order
        random.shuffle(self.theaters)

    def rotate_theater(self):
        # rotate the theaters clockwise
        self.theater_order.append(self.theaters.pop(0))

    def get_board_string(self):
        # return a string representation of the board
        return_string = ""
        for theater in self.theaters:
            return_string += theater.get_theater_string() + "\n"
        return return_string

    def get_theater(self, theater_id: str):
        # return the theater with the given id
        pass
