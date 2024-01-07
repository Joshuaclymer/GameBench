from enum import Enum

class CardType(Enum):
    RED = 1
    BLUE = 2
    NEUTRAL = 3
    ASSASSIN = 4

class Card:
    def __init__(self, word: str, card_type: Enum):
        self.word = word
        self.card_type = card_type

    def __str__(self):
        return self.word
    
