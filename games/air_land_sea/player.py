from dataclasses import dataclass, field
from typing import List
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from games.air_land_sea.cards import Card
from games.air_land_sea.board import Theater

@dataclass
class Player:
    id: int # either 0 or 1
    supreme_commander: int # either 0 or 1
    agent: Agent = None
    hand: List[Card] = field(default_factory=list)
    victory_points: int = 0

    def play(self, card: Card, faceup: bool, theater: Theater, show_state: bool):
        self.hand.remove(card)
        if not faceup:
            card.flip()
        theater.player_cards[self.id].append(card)
        if show_state:
            if faceup:
                print("Player", self.id + 1, "played", card, "to", theater.name, "faceup.")
            else:
                print("Player", self.id + 1, "played", card, "to", theater.name, "facedown.")

    # i have theater type and card name
    def search_hand(self, card_name: str, theater_name: str) -> Card:
        for card in self.hand:
            if card.name == card_name and card.theater == theater_name:
                return card
        return None