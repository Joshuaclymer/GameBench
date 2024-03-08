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

    # TODO: play card function, which class should that be?
    # player?
    # called in update function of game class
    # info we need
        # player playing the card
        # card being played
        # facedown or faceup
        # which theater (some effects will let people play to other theaters than normal)
    # does not return anything
    # plays the card to the theater, removes it from the hand, changes theater strength, adds effect to Effect Manager if applicable
    def play(self, card: Card, faceup: bool, theater: Theater):
        # TODO: change to theater object instead of int id
        self.hand.remove(card)
        if not faceup:
            card.flip()
        theater.player_total_strength[self.id] += card.current_strength
        theater.player_cards[self.id].append(card)

    # TODO: make a function that outputs where a card can be played?
    # we need to handle a few effects
        # play to an adjacent theater Reinforce, 
        # play to any theater Air Drop

    # handle restraints to where a card can be played when generating available actions

    # def get_hand_string(self):
    #     hand_string = ""
    #     for i, card in enumerate(self.hand):
    #         if i == 0:
    #             hand_string += str(card)
    #         else:
    #             hand_string += f", {str(card)}"
    #     return hand_string