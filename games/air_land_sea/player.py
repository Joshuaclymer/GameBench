@dataclass
class Player:
    supreme_commander: int
    hand: List[Card]
    victory_points: int
    agent: Agent
    player_id: int