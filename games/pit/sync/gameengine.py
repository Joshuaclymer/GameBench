"""Pit Game Engine

The game is broken into distinct cycles during which each player gets the chance
to perform one action (making an offer, responding to a prior offer, etc.). The
player actions for each cycle are randomized and then executed one at at time.
Therefore, in each cycle, all player actions are based on information known at
the end of the previous cycle, but the order of execution is random, so if two
players attempt to do the same thing (e.g. respond to an offer or ring the
trading bell), luck will determine who does it first.

Performing actions causes the player to be delayed for some number of subsequent
cycles. During the delay the player will not be able to perform actions and
won't be notified of other game events such as offers and trades. The one
exception to this is a delayed player will still be notified if another player
responds directly to them about a previous offer. The delayed player will still
be notified and will still be able to make the trade (causing them to get
delayed yet again).

TODO LIST:
- notification about responses made and rejected
"""

import copy
import itertools
import random

import config
import util

# number of cycles before an offer expires
OFFER_CYCLES = 10
# cycles a player must wait after making an offer
OFFER_DURATION = 1
# cycles a player must wait after making a response (if no trade resulted)
RESPONSE_DURATION = 2
# cycles a player must wait after participating in a trade
TRADE_DURATION = 4


class Action(object):
    def __init__(self, player):
        self.player = player
        self.cycle = -1  # to be set by game engine

    def __str__(self):
        return "Action"

    def __repr__(self):
        return str(self)

    def copy(self):
        """Should return a new instance that is a copy of the action"""
        raise NotImplementedError


class Offer(Action):
    """An offer to trade a certain number of cards, made to anyone/everyone."""

    def __init__(self, player, quantity):
        super(Offer, self).__init__(player)
        if quantity > 4:
            raise Exception("Offers can only be up to four cards")
        self.quantity = quantity

    def __str__(self):
        return "Offer in cycle {2} by {0} for {1}".format(
            self.player, self.quantity, self.cycle
        )

    def copy(self):
        """Returns a copy of this offer"""
        offer = Offer(self.player, self.quantity)
        offer.cycle = self.cycle
        return offer

    def __eq__(self, offer):
        """Returns True iff all fields of this offer equal the other"""
        return self.player == offer.player and self.quantity == offer.quantity

    # def __hash__(self):
    #     return hash(self.player)


class Response(Action):
    """Response to an offer.

    A response is binding - a player issuing one should not make any other
    offers or responses with these cards until this response is confirmed,
    withdrawn, or expired.
    """

    def __init__(self, offer, player, cards):
        """Game engine needs to know the cards so it can execute a trade. They
        will be removed before the response is sent to the target player.
        """
        super(Response, self).__init__(player)
        self.offer = offer
        self.cards = cards

    def __str__(self):
        return "Response in cycle {2} by {0} to {1}".format(
            self.player, self.offer, self.cycle
        )

    def copy(self):
        """Returns a copy of this response"""
        response = Response(self.offer.copy(), self.player, self.cards)
        response.cycle = self.cycle
        return response


class BellRing(Action):
    """The action of ringing the bell to indicate that you have won the round"""

    def __str__(self):
        return "Bell Ring in cycle {1} by {0}".format(self.player, self.cycle)


class GameEngine(object):
    def play(self, players, games=1):
        """Primary entry method, plays a number of games of Pit"""
        self.players = players
        results = dict([(player, 0) for player in players])
        for game in range(games):
            dealer = random.randint(0, len(players) - 1)
            winner = self.one_game(starting_dealer=dealer)
            results[winner] += 1
        return results

    def one_game(self, starting_dealer=0):
        """Play one game and returns winning player."""
        self.player_info = {}
        self.dealer = starting_dealer
        # so players can't edit and mess each other up
        players = tuple(self.players)
        for player in players:
            self.player_info[player] = {"score": 0}
            player.new_game(players, config.COMMODITIES[: len(players)])

        self.winner = None
        while not self.winner:
            self.one_round()
            self.next_dealer()
        return self.winner

    def one_round(self):
        """Plays round, updates scores, sets self.winner if anyone won"""
        self.cycle = 0
        self.in_play = True
        self.offers = []
        self.busy_players = {}

        self.deal_cards()

        card_counts = {}
        for player in self.players:
            card_counts[player] = len(self.player_info[player]["cards"])

        for player in self.players:
            hand = copy.copy(self.player_info[player]["cards"])
            player.new_round(hand, card_counts.copy())

        while self.in_play:
            self.one_cycle()

        self.update_scores()

    def one_cycle(self):
        """One cycle gives each player the chance to perform an action"""
        actions = self.collect_actions()
        for action in actions:
            self.process_action(action)
            if not self.in_play:
                return
        self.cycle += 1
        self.end_cycle()

    def collect_actions(self):
        """Collects and randomizes player actions, locking cards as needed"""
        actions = []
        self.locked_cards = {}
        for player in self.available_players():
            action = player.get_action(self.cycle)
            if action:
                action.cycle = self.cycle
                actions.append(action)
                if isinstance(action, Response):
                    self.locked_cards[player] = action.cards
        random.shuffle(actions)
        return actions

    def process_action(self, action):
        """One player makes one action"""
        self.ACTION_METHODS[type(action)](self, action)

    def add_offer(self, offer):
        """Add an offer to the game"""
        offer.cycle = self.cycle
        self.offers.append(offer)
        for player in self.available_players():
            player.offer_made(offer.copy())
        self.delay_player(offer.player, OFFER_DURATION)

    def send_response(self, response):
        """Issue a response to player who made initial offer.

        The initial player immediately accepts or rejects the response, so by
        the end of this method the response is either rejected or the trade is
        confirmed.

        The response will be also rejected under any of these conditions:
        - same player made both offer and response
        - offer no longer present in game state list of offers
        - player making response no longer has these cards

        This also grabs the response's cards & removes them from the response.
        They are saved so they can be used if the trade ends up executing.
        """
        response.cycle = self.cycle
        response_cards = response.cards
        response.cards = None

        if (
            response.offer in self.offers
            and response.player != response.offer.player
            and util.has_cards(
                response_cards, self.player_info[response.player]["cards"], []
            )
        ):
            confirm_cards = response.offer.player.response_made(response)
            if confirm_cards and util.has_cards(
                confirm_cards, self.player_info[response.offer.player]["cards"], []
            ):
                self.confirm(response, response_cards, confirm_cards)
                return
        # player rejected response or offer was already removed
        response.player.response_rejected(response)
        self.delay_player(response.player, RESPONSE_DURATION)

    def confirm(self, response, response_cards, confirm_cards):
        """Confirm a trade between two players

        Sends full hand update to the two players involved in the trade
        """
        self.offers.remove(response.offer)

        util.swap_cards(
            self.player_info[response.player]["cards"],
            response_cards,
            self.player_info[response.offer.player]["cards"],
            confirm_cards,
        )

        # notify players of trade, send full hands to the two involved
        for player in self.players:
            if player == response.player:
                player.trade_confirmation(
                    response.copy(), hand=self.player_info[response.player]["cards"]
                )
            elif player == response.offer.player:
                player.trade_confirmation(
                    response.copy(),
                    hand=self.player_info[response.offer.player]["cards"],
                )
            elif player in self.available_players():
                player.trade_confirmation(response.copy(), hand=None)

        # the two players who trade are now busy for a bit
        self.delay_player(response.player, TRADE_DURATION)
        self.delay_player(response.offer.player, TRADE_DURATION)

    def ring_bell(self, bell_ring):
        """Ring the closing bell"""
        for player in self.players:
            player.closing_bell(bell_ring.player)

        if util.is_winning_hand(self.player_info[bell_ring.player]["cards"]):
            self.in_play = False
            for player in self.players:
                player.closing_bell_confirmed(bell_ring.player)

    ACTION_METHODS = {
        Offer: add_offer,
        Response: send_response,
        BellRing: ring_bell,
    }

    def update_scores(self):
        """Updates player scores at end of a round, sets winner if any."""
        for player in self.players:
            score = util.score_hand(self.player_info[player]["cards"])
            self.player_info[player]["score"] += score
            if self.player_info[player]["score"] >= config.WINNING_SCORE:
                self.winner = player

    def end_cycle(self):
        """Performs bookkeeping at end of a cycle

        - removes any expired offers
        - restores busy players who are done being busy
        """
        expired_offers = list(filter(self.expired_offer, self.offers))
        self.offers = list(itertools.filterfalse(self.expired_offer, self.offers))
        for offer in expired_offers:
            offer.player.offer_expired(offer)

        for player in list(self.busy_players.keys()):
            if self.cycle >= self.busy_players[player]:
                del self.busy_players[player]

    def expired_offer(self, offer):
        """True iff this offer is expired

        An offer added in cycle 0 gets to live through cycle <OFFER_CYCLES>
        """
        return self.cycle - offer.cycle > OFFER_CYCLES

    def deal_cards(self):
        """Sets game_state cards to a new set of shuffled cards"""
        cards = util.deal_cards(len(self.players), self.dealer)
        for index, player in enumerate(self.players):
            self.player_info[player]["cards"] = cards[index]

    def next_dealer(self):
        """Advances dealer"""
        self.dealer = util.next_position(self.dealer, len(self.players))

    def available_players(self):
        """Returns iterable of players not currently busy"""
        return set(self.players) - set(self.busy_players.keys())

    def delay_player(self, player, duration):
        """Adds a player to busy_players for given number of cycles"""
        end_cycle = self.cycle + duration
        self.busy_players[player] = end_cycle

    def debug(self):
        """Helper to print game state and exit game"""
        print("CYCLE {0}".format(self.cycle))
        for player in self.players:
            cards = copy.copy(self.player_info[player]["cards"])
            cards.sort()
            print(
                "PLAYER {0}: score={1} cards={2}".format(
                    str(player), self.player_info[player]["score"], cards
                )
            )
        print("OFFERS {0}".format(self.offers))
        print("IN PLAY? {0}".format(self.in_play))
        print("BUSY? {0}".format(self.busy_players))
        print("---------------")
