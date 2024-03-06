from dataclasses import dataclass, field
from typing import List
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from games.air_land_sea.cards import Card

@dataclass
class Player:
    player_id: int
    supreme_commander: int
    agent: Agent = None
    hand: List[Card] = field(default_factory=list)
    victory_points: int = 0
