"""Basic player(s) for the Pit game
"""

import copy
import itertools
import random

import config
import util
from sync import gameengine
from sync.player import base


class BasicPlayer(base.Player):
    """A basic player for the Pit game engine.

    This player has no real strategy. It will always make a trade if one is
    available, regardless of which player is offering the trade, etc.

    TODO LIST
    - do not accept a response if cards already locked up in own response
    - if I have exactly 5 and 5 of two commodities, be able to break one
      of them up and trade less than 5 cards
    """

    # number of cycles to let an offer exist before ignoring it forever
    OFFER_EXPIRATION = 2

    def __init__(self, name):
        super(BasicPlayer, self).__init__()
        self.name = name

    def new_round(self, hand, card_counts):
        """New round of a game started, includes player's cards"""
        self.hand = hand
        self.offers = []
        self.my_offers = []

    def get_action(self, cycle):
        """Returns action for this cycle

        1. randomly do nothing just to mix it up
        2. update internal game state
        3. if winning hand, ring the bell
        4. try to respond to an open offer
        5. make a new offer
        """
        if random.randrange(0, 5) == 4:
            return None

        self.cycle = cycle
        self.offers = self._active_offers(self.offers)
        self._group_cards()

        if util.is_winning_hand(self.hand):
            return gameengine.BellRing(self)

        random.shuffle(self.offers)
        for offer in self.offers:
            cards = self._get_response(offer)
            if cards:
                self.offers.remove(offer)
                return gameengine.Response(offer, self, cards)

        return self._make_offer()

    def offer_made(self, offer):
        """A player has called out an offer for anyone to respond"""
        if offer.player != self:
            self.offers.append(offer)

    def response_made(self, response):
        """Confirms (if possible) or rejects a response to a previous offer

        Returns list of cards if offer is accepted, else None.
        """
        self._group_cards()
        return self._matching_cards(response.offer)

    def trade_confirmation(self, response, hand=None):
        """Two players have made a trade, including new hand if I'm involved."""
        if hand and (response.player == self or response.offer.player == self):
            if response.offer in self.my_offers:
                self.my_offers.remove(response.offer)
            self.hand = hand

    def offer_expired(self, offer):
        """A prior offer has expired without executing, remove from list"""
        self.my_offers.remove(offer)

    def _get_response(self, offer):
        """Returns list of cards if response can be made to this offer, or None"""
        return self._matching_cards(offer)

    def _matching_cards(self, offer):
        """Helper returns cards matching quantity of this offer, if possible

        Randomly chooses cards to see if quantity matches for a trade. Also
        tries to add the bull/bear/both cards to make the quantity match.
        """
        bull = config.BULL
        bear = config.BEAR
        commodities = list(self.card_groups.keys())
        random.shuffle(commodities)
        for commodity in commodities:
            quantity = self.card_groups[commodity]
            if quantity == offer.quantity:
                return [commodity] * quantity
            elif commodity not in [bull, bear]:
                if bull in self.hand and offer.quantity == quantity + 1:
                    return [commodity] * quantity + [bull]
                elif bear in self.hand and offer.quantity == quantity + 1:
                    return [commodity] * quantity + [bear]
                elif (
                    bull in self.hand
                    and bear in self.hand
                    and offer.quantity == quantity + 2
                ):
                    return [commodity] * quantity + [bull, bear]
        return None

    def _make_offer(self):
        """Returns a new Offer

        Max of 4 cards can be part of an offer
        """
        existing_quantities = [offer.quantity for offer in self.my_offers]
        quantities = list(self.card_groups.values())
        random.shuffle(quantities)
        for quantity in quantities:
            if quantity <= 4 and quantity not in existing_quantities:
                offer = gameengine.Offer(self, quantity)
                self.my_offers.append(offer)
                return offer

    def _group_cards(self):
        """Breaks cards into groups keyed by type, count as values"""
        self.card_groups = {}
        for card in set(self.hand):
            self.card_groups[card] = self.hand.count(card)

    def _active_offers(self, offers):
        """Return list of offers that have not expired"""
        exp = lambda offer: self.cycle - offer.cycle > self.OFFER_EXPIRATION
        return list(itertools.filterfalse(exp, offers))
