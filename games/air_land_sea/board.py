from dataclasses import dataclass, field
from typing import List
import random

@dataclass
class Board:
    theater_order: List[Theater] = field(default_factory=lambda: [
        Theater('Air'),
        Theater('Sea'),
        Theater('Land')
    ])
    ongoing_effects: List[Card] = field(default_factory=list) # ongoing effects that affect the board

    def __post_init__(self):
        # shuffle theaters into random order
        random.shuffle(self.theater_order)

    def rotate_theater(self):
        # rotate the theaters clockwise
        self.theater_order.append(self.theater_order.pop(0))

    def get_board_string(self):
        # return a string representation of the board
        pass
    def get_theater(self, theater_id: str):
        # return the theater with the given id
        pass

@dataclass
class Theater:
    name: str
    player_1_total_strength: int = 0
    player_2_total_strength: int = 0
    player_1_cards: List[Card] = field(default_factory=list)
    player_2_cards: List[Card] = field(default_factory=list)

    def get_theater_string(self):
        # return a string representation of the theater
        pass
    def get_strength(self, player_id: int):
        # return the strength of the player in the theater
        pass