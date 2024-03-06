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

    # TODO: process covered/uncovered cards
    # each theater needs to keep track of the card that is uncovered
    # all else is covered
    # relevant to targeting convered/uncovered cards

    """
    Air Theater:
    Player 1: [F-35 (5, Ongoing: +1 to adjacent Theaters, uncovered), Face down (2, covered)]
    Player 2: [Face down (2, covered), Tank Buster (4, Instant: Destroy one face-down card, uncovered)]
    """

    def get_theater_string(self):
        # return a string representation of the theater
        theater_name = self.name # no "Theater" at the end
        return f"{theater_name} Theater:\nPlayer 1: {self.player_1_cards}\nPlayer 2: {self.player_2_cards}"


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
