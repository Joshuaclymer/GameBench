from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from typing import List, Dict, Optional, Tuple
from cards.game_cards import *
import random
 
@dataclass
class ArcticScavengers(Game):
    class Player:
        def __init__(self, agent):
            self.agent = agent
            self.cards = {"deck":[], "draw":[], "skirmish":[]} 

        def create_deck(self, deck):
            pass
    class Deck:
        def __init__(self):
            self.contested_resources = []
            self.junkyard = []
            self.mercenaries = [[]] # 8 mercenary piles

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
        self.players = [self.Player(self.agents[0]), self.Player(self.agents[1])]
        self.deck = self.Deck()
        # TODO: Initialise 10 cards for each player (4 refugee, 3 scavenger, 1 brawler, 1 spear, 1 shovel)
        for player in self.players:
            player.create_deck(self.deck)
        self.game_winner = None
    
    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        pass

    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        pass

    def play(self) -> Tuple[float, float]:
        # 14 turns in total, as there are 14 contested resource cards in the pile.
        # DRAWING PHASE: 
        # Both players draw 5 cards from top of their deck. If deck is empty, shuffle discard pile and draw from there.
        count = 0
        while self.deck.contested_resources:
            initiator = count % 2
            # Draw 5 cards automatically for each player. get_observation returns the hand of the player.
            # The available actions are to choose which cards to keep for skirmish.
            # Call get_observation again to decide which resources to gather. Need to use logic to check validity (otherwise call again).
            # Call update again to update the player's deck.
            # Then the skirmish happens, and the top contested resource card goes to the winining player.
            count += 1