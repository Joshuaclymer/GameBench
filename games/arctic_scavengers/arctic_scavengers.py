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

        def draw_hand(self):
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

    def observation_decide_cards(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        # Returns the hand of the player.
        # The available actions are to choose which cards to keep for skirmish.
        pass

    def play_resource_gather(self, player : Player):
        # Configure a while loop until the user says STOP. No need to announce how many cards left for skirmish.
        # Make sure in while loop that actions are not repeated and each one is valid.
        # Once user says STOP the number of cards left for skirmish is determined for them (might have output to announce this).
        observation, available_actions = self.get_observation(player.agent)
        action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
        while action != "STOP":
            self.update(action, available_actions, player.agent)
            observation, available_actions = self.get_observation(player.agent)
            action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)

    def play_skirmish(self, player : Player):
        pass

    def play(self) -> Tuple[float, float]:
        #### DRAWING PHASE #### 
        # 14 turns in total, as there are 14 contested resource cards in the pile.
        # Both players draw 5 cards from top of their deck. If deck is empty, shuffle discard pile and draw from there.
        count = 0
        while self.deck.contested_resources:
            initiator = count % 2
            for player in self.players:
                player.draw_hand()

            #### RESOURCE GATHERING PHASE ####
            player = self.players[initiator]
            self.play_resource_gather(player)
            player = self.players[1 - initiator]
            self.play_resource_gather(player)
            
            #### SKIRMISH PHASE ####
            # Then the skirmish happens, and the top contested resource card goes to the winining player.
            # Use a while loop like before
            player = self.players[initiator]
            self.play_skirmish(player)
            player = self.players[1 - initiator]
            self.play_skirmish(player)
            fight_scores = [self.players[0].calculate_fight_score(), self.players[1].calculate_fight_score()]
            if fight_scores[0] > fight_scores[1]:
                self.players[0].cards["deck"].append(self.deck.contested_resources.pop(0))
            elif fight_scores[0] < fight_scores[1]:
                self.players[1].cards["deck"].append(self.deck.contested_resources.pop(0))
            else:
                people_scores = [self.players[0].calculate_people(), self.players[1].calculate_people()]
                if people_scores[0] > people_scores[1]:
                    self.players[0].cards["deck"].append(self.deck.contested_resources.pop(0))
                elif people_scores[0] < people_scores[1]:
                    self.players[1].cards["deck"].append(self.deck.contested_resources.pop(0))
                else:
                    self.deck.junkyard.append(self.deck.contested_resources.pop(0))
            
            count += 1