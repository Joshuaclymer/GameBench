@dataclass
class Card:
    card_type: str
    card_name: str
    card_id: int
    strength: int
    tactical_ability: str
    

@dataclass
class Deck:
    cards: List[Card]

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()

    def add(self, card: Card):
        self.cards.append(card)
    
    def remove(self, card: Card):
        self.cards.remove(card)

class Config:
    # includes the card list
    # includes number of each card that should be in deck
    # includes supreme commander card rules
    pass
