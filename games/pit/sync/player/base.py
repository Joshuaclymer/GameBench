"""Module for base Player class
"""

import random


class Player(object):
    def __init__(self):
        self.name = "Player {0}".format(random.randint(1, 9999))

    def new_game(self, players, commodities):
        """New game started with list of player names and commodities being used"""

    def new_round(self, hand, card_counts):
        """New round of a game started

        Includes your hand plus dict w/ # of cards each other player is dealt
        """

    def opening_bell(self):
        """Opening bell rung, trades allowed now"""

    def get_action(self, cycle):
        """Return an action for the current cycle or None to pass"""

    def offer_made(self, offer):
        """A player has called out an offer for anyone to respond"""

    def offer_expired(self, offer):
        """Your prior offer has expired without executing"""

    def response_made(self, response):
        """A player has responded to your prior offer

        Should return list of cards if you accept the offer, else None.
        """

    def response_rejected(self, response):
        """Your response to a specific player was rejected"""

    def trade_confirmation(self, response, hand=None):
        """Two players have made a trade

        If you are one of the players in the trade, this includes updated hand.
        """

    def closing_bell(self, player):
        """A player has rung the closing bell"""

    def closing_bell_confirmed(self, player):
        """The game engine has confirmed that a player has won this round"""

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def __eq__(self, player):
        return self.name == player.name

    def __hash__(self):
        return hash(repr(self))
