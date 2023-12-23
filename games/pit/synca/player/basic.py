"""Basic Player class(es) that are functional but not sophisticated.

TODO
 - still consider syncronizing access to cards & other data
"""

import copy
import random
import threading
import time

import config
import util
from synca import gameengine
from synca.player import base


# seconds before withdrawing a binding offer
BINDING_OFFER_LIFETIME = 0.01

# will respond to open offers until hitting this limit
LOCKED_CARDS_LIMIT = 5


class SimplePlayer(base.NullPlayer):
    """A fully functional Pit player, just not very good."""

    def new_round(self, message):
        """Resets state at start of a new round."""
        self.already_rang = False
        self.cards = message.cards
        self.locked_cards = []
        self.open_offers = []
        self.incoming_offers = []
        self.outgoing_offers = []
        super(SimplePlayer, self).new_round(message)

    def make_plays(self):
        """Main game play method makes & responds to offers, etc."""
        if not self.already_rang and util.is_winning_hand(self.cards):
            self.notify(gameengine.Message.RING_BELL)
            self.already_rang = True
            return
        self.clear_outgoing_offers()
        self.check_offers()
        self.make_offers()

    def clear_outgoing_offers(self):
        """Attempts to withdraw any previous binding offers that have expired."""
        now = time.time()
        for added, cards, target_uid in self.outgoing_offers:
            if now - added > BINDING_OFFER_LIFETIME:
                if all([card in self.locked_cards for card in cards]):
                    self.notify(
                        gameengine.Message.WITHDRAW, cards=cards, target_uid=target_uid
                    )
                else:
                    self.outgoing_offers.remove((added, cards, target_uid))

    def check_offers(self):
        """Responds to incoming and open offers"""
        random.shuffle(self.incoming_offers)
        random.shuffle(self.open_offers)
        for offer in self.incoming_offers:
            self.attempt_response(offer)
        if self.open_offers:
            if len(self.locked_cards) < LOCKED_CARDS_LIMIT:
                self.attempt_response(self.open_offers[0])
        self.incoming_offers = []
        self.open_offers = []

    def attempt_response(self, offer):
        """If cards are available, issues a binding offer to match the offer."""
        # because I haven't syncronized access to self.cards and self.locked_cards
        # this will sometimes get a KeyError accessing data that has been deleted
        # by the other thread - ok to just ignore & move on
        try:
            groups = util.available_card_groups(self.cards, self.locked_cards)
            cards = self.get_match(groups, offer.count)
        except KeyError:
            return None
        if cards:
            self.notify(
                gameengine.Message.BINDING_OFFER, cards=cards, target_uid=offer.uid
            )
            self.locked_cards.extend(cards)
            self.outgoing_offers.append((time.time(), cards, offer.uid))
            return True

    def get_match(self, groups, quantity):
        """Returns cards to trade that match the given quantity"""
        match_with = []
        if config.BEAR in self.cards and config.BEAR not in self.locked_cards:
            match_with.append(config.BEAR)
        if config.BULL in self.cards and config.BULL not in self.locked_cards:
            match_with.append(config.BULL)
        matches = util.matching_groups_with(match_with, groups, quantity)
        vanilla_matches = util.matching_groups(groups, quantity)
        matches.extend(vanilla_matches)
        if matches:
            random.shuffle(matches)
            return matches[0]
        else:
            return self.get_match_with_break(groups, quantity)

    def get_match_with_break(self, groups, quantity):
        """Returns a match by breaking up a group, when applicable"""
        if not groups:
            return
        smallest = min(groups.values())
        if smallest > 4:
            for card, count in groups.iteritems():
                if count == smallest:
                    return [card] * quantity

    def make_offers(self):
        """Makes open offers."""
        groups = util.available_card_groups(self.cards, self.locked_cards)
        for count in [4, 3, 2, 1]:
            if count in groups.values():
                self.notify(gameengine.Message.OFFER, count=count)

    def handle_offer(self, message):
        """Called when another player makes an open offer"""
        self.open_offers.append(message)

    def handle_binding_offer(self, message):
        """Called when another player makes a binding offer"""
        self.incoming_offers.append(message)

    def handle_trade(self, message):
        """Called when a trade happens"""
        if message.uid == self.uid:
            for card in message.removed_cards:
                self.cards.remove(card)
                self.locked_cards.remove(card)
            self.cards.extend(message.cards)

    def handle_withdraw(self, message):
        """Called when a binding offer to or from me is withdrawn"""
        if message.uid == self.uid:
            # only remove them if all cards are found in locked_cards
            if all([card in self.locked_cards for card in message.cards]):
                [self.locked_cards.remove(card) for card in message.cards]
