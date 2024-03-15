from dataclasses import dataclass, field
from typing import Optional, List
import random

@dataclass
class Card:
    name: str
    theater: str
    strength: int
    tactical_ability_type: Optional[str] = None
    tactical_ability_description: Optional[str] = None
    facedown: bool = False

    def __post_init__(self):
        self.current_strength = self.strength

    def __str__(self):
        card_info = f"{self.name} ({self.strength}"
        tactical_ablity_string = ""
        # if self.tactical_ability_type and not self.facedown:
        if self.tactical_ability_type:
            tactical_ablity_string = f", {self.tactical_ability_type}: {self.tactical_ability_description}"
        # $ represents the covered/uncovered status of the card (it will be manipulated by the theater class)
        return f"{card_info}, {self.theater}{tactical_ablity_string})"

    def __repr__(self):
        return self.__str__()
    
    def flip(self):
        if self.facedown:
            print("flipping faceup")
            # flip faceup
            self.current_strength = self.strength
            self.facedown = False
        else:
            print("flipping facedown")
            # flip facedown
            self.current_strength = 2
            self.facedown = True

@dataclass
class Deck:
    cards: List[Card] = field(default_factory=lambda: [
            Card('Support', 'Air', 1, 'Ongoing', 'You gain +3 strength in each adjacent theater'),
            Card('Air Drop', 'Air', 2, 'Instant', 'The next time you play a card, you may play it to a non-matching theater'),
            Card('Manuever', 'Air', 3, 'Instant', 'Flip an uncovered card in an adjacent theater'),
            Card('Aerodrome', 'Air', 4, 'Ongoing', 'You may play cards of strength 3 or less to non-matching theaters'),
            Card('Containment', 'Air', 5, 'Ongoing', 'If any player plays a facedown card, destroy that card'),
            Card('Heavy Bombers', 'Air', 6),
            Card('Transport', 'Sea', 1, 'Instant', 'You may move 1 of your cards to a different theater'),
            Card('Escalation', 'Sea', 2, 'Ongoing', 'All your facedown cards are now strength 4'),
            Card('Manuever', 'Sea', 3, 'Instant', 'Flip an uncovered card in an adjacent theater'),
            Card('Redeploy', 'Sea', 4, 'Instant', 'You may return 1 of your facedown cards to your hand. If you do, play a card'),
            Card('Blockade', 'Sea', 5, 'Ongoing', 'If any player plays a card to an adjacent theater occupied by at least 3 other cards, destroy that card'),
            Card('Super Battleship', 'Sea', 6),
            Card('Reinforce', 'Land', 1, 'Instant', 'Draw 1 card and play it facedown to an adjacent theater'),
            Card('Ambush', 'Land', 2, 'Instant', 'Flip any uncovered card'),
            Card('Manuever', 'Land', 3, 'Instant', 'Flip an uncovered card in an adjacent theater'),
            Card('Cover Fire', 'Land', 4, 'Ongoing', 'All cards covered by this card are now strength 4'),
            Card('Disrupt', 'Land', 5, 'Ongoing', 'Starting with you, both players choose and flip 1 of their uncovered cards'),
            Card('Heavy Tanks', 'Land', 6)
    ])

    def __post_init__(self):
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()

    def add(self, card: Card):
        self.cards.insert(0, card)

    def deal(self):
        # deal 6 cards from the deck
        return [self.draw() for _ in range(6)]