from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from typing import List, Dict, Optional, Tuple
from cards.game_cards import *

@dataclass
class ArcticScavengers(Game):
    rules : Rules = Rules(
        title="Arctic Scavengers",
        summary="""
        Players work to build their tribes as large as possible by hiring mercenaries, scavenging junk piles and winning skirmishes against other players' tribes.
        Each tribe member card in a tribe represents the number of people shown on the card.
        The player with the largest tribe at the end of the game is the winner.
        """,
        additional_details = None
    )
    id : str = "arctic_scavengers"

    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.agents = [agent1(team_id = 0, agent_id = 0, **self.agent_1_kwargs), agent2(team_id = 1, agent_id = 1, **self.agent_2_kwargs)]
        
        self.cards_player0 = {"deck":[], "draw":[], "skirmish":[]}
        self.cards_player1 = {"deck":[], "draw":[], "skirmish":[]}

        # TODO: Initialise 10 cards for each player (4 refugee, 3 scavenger, 1 brawler, 1 spear, 1 shovel)
        # Shuffle deck for each player. Randomly choose player 0 or 1 to be initiator.
        # Create remaining piles for: contested resources, junkyard, and 8 mercenary piles.

        self.game_winner = None
    
    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        pass

    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        pass

    def play(self) -> Tuple[float, float]:
        # 14 turns in total, as there are 14 contested resource cards in the pile.
        # DRAWING PHASE: 
        # Both players draw 5 cards from top of their deck. If deck is empty, shuffle discard pile and draw from there.
