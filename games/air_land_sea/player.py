from dataclasses import dataclass, field
from typing import List
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from games.air_land_sea.cards import Card
from games.air_land_sea.board import Theater

@dataclass
class Player:
    id: int # either 0 or 1
    supreme_commander: int
    agent: Agent = None
    hand: List[Card] = field(default_factory=list)
    victory_points: int = 0

    def play(self, card: Card, faceup: bool, theater: Theater):
        self.hand.remove(card)
        if not faceup:
            card.flip()
        theater.player_cards[self.id].append(card)