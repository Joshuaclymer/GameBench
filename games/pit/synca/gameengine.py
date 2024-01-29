"""Pit game engine

TODO:
 - add validation check that offer cards are legal (all same plus bull/bear)
"""

import copy
import multiprocessing
from queue import Queue
import random
import threading
import time

import games.pit.config as config
import games.pit.util as util


class Message(object):
    """A message sent between game engine and player(s)."""

    # control messages from game engine to players
    NEW_GAME = "new game"  # new game starting
    NEW_ROUND = "new round"  # new round starting, cards included
    ROUND_OVER = "round over"  # round has just ended
    GAME_OVER = "game over"  # game has just ended
    DONE = "done"  # all games are finished, close all threads

    # acknowledgements from players to game engine
    ALL_SET = "all set"  # player has set up and is ready to go
    GAME_READY = "game ready"  # player is ready for a new game
    ROUND_READY = "round ready"  # player is ready for a new round
    ROUND_DONE = "round done"  # acknowledge round is over
    GAME_DONE = "game done"  # acknowledge game is over

    # game action messages (possibly sent in either direction)
    # when broadcast from game engine, specific cards will be removed
    OFFER = "offer"  # non-binding offer, includes # of cards
    BINDING_OFFER = "binding offer"  # binding offer, includes actual cards
    WITHDRAW = "withdraw"  # withdraw offer, includes actual cards
    TRADE = "trade"  # trade executed, includes players & count
    # includes cards for players involved
    RING_BELL = "ring bell"  # ring bell to win the round

    def __init__(
        self, text, uid=None, cards=[], count=0, target_uid=None, removed_cards=[]
    ):
        """Initialize a Message with the needed info

        Note on trades: cards and removed_cards sent only to players involved
                        in the trade. removed_cards will always be the cards for
                        the player to remove from own hand.
        """
        self.text = text
        self.uid = uid
        self.cards = cards
        self.count = len(cards) or count
        self.target_uid = target_uid
        self.removed_cards = removed_cards

    def __str__(self):
        msg = "MESSAGE {text} {cards} {count} from {uid} to {target_uid}"
        return msg.format(**self.__dict__)


class Player(object):
    """The structure of a Pit player class.

    This is basically an interface definition. There are very few requirements
    for a Pit player. It only need to provide a set_up method that can take a
    Pipe connection and a Queue instance.
    """

    def __init__(self, name):
        """Player names should be unique and are used to report who won, etc."""
        self.name = name

    def set_up(self, conn, queue):
        """Set up player a connection to the game engine.

        This method is called in a new Process and provides the connection to
        receive updates from the game engine and the queue to put new messages
        that the game engine will process.
        """
        raise NotImplemented


class GameEngine(object):
    """This is the Pit game engine. More details to come..."""

    def play(self, players, games=1):
        """Will play some number of games with the given set of players"""
        self.players = players
        self.set_up()
        self.wait_for_players(Message.ALL_SET)
        for game in range(games):
            winner = self.one_game()
            print("{0} won this game".format(self.player_data[winner]["name"]))
            self.debug()
        self.tear_down()

    def set_up(self):
        """Sets up players, game state, etc."""
        self.start_time = time.time()

        self.message_queue = multiprocessing.Queue()
        self.player_data = {}
        for player in self.players:
            uid = id(player.name)
            parent_conn, child_conn = multiprocessing.Pipe()
            proc = multiprocessing.Process(
                target=self.set_up_player, args=(player, child_conn, uid)
            )
            self.player_data[uid] = {
                "name": player.name,
                "conn": parent_conn,
                "proc": proc,
                "cards": [],
                "binding_offers": [],
                "score": 0,
            }
            proc.start()

    def set_up_player(self, player, conn, uid):
        """Creates a new process for a player"""
        player.set_up(conn, self.message_queue, uid)

    def one_game(self, starting_dealer=0):
        """Plays one full game"""
        self.broadcast(Message(Message.NEW_GAME))
        for uid, data in self.player_data.iteritems():
            data.update(
                {
                    "score": 0,
                }
            )
        self.dealer = starting_dealer
        self.game_winner = None

        self.wait_for_players(Message.GAME_READY)

        # begin game loop and play until someone wins
        while not self.game_winner:
            self.one_round()
            self.dealer = self.next_player(self.dealer)
        self.end_game()
        return self.game_winner

    def one_round(self):
        """Plays one round of the game and updates scores"""
        self.round_winner = None
        for uid, data in self.player_data.iteritems():
            data.update(
                {
                    "cards": [],
                    "binding_offers": [],
                }
            )
        self.deal_cards()
        self.wait_for_players(Message.ROUND_READY)

        while not self.round_winner:
            message = self.message_queue.get()
            self.process_message(message)
        self.broadcast(Message(Message.ROUND_OVER))
        self.wait_for_players(Message.ROUND_DONE)
        self.update_scores()

    def deal_cards(self):
        """Notifies players of new game, sends them their cards"""
        cards = util.deal_cards(len(self.players), self.dealer)
        for index, (uid, data) in enumerate(self.player_data.iteritems()):
            data["cards"] = cards[index]
            message = Message(Message.NEW_ROUND, cards=cards[index])
            data["conn"].send(message)

    def next_player(self, player):
        """Returns index of next player"""
        return 0 if player == len(self.players) - 1 else player + 1

    def process_offer(self, message):
        """Processes an open offer, rebroadcasting it to all other players"""
        self.broadcast(message, exclude=[message.uid])

    def process_binding_offer(self, message):
        """Processes a binding offer, locks up cards until traded or withdrawn.

        If rebroadcasting the offer, the specific cards will be removed.
        """
        # only take action if the player has the cards in this offer
        data = self.player_data[message.uid]
        if util.has_cards(message.cards, data["cards"], data["binding_offers"]):
            match = self.get_matching_offer(message)
            if match:
                self.execute_trade(message, match)
            else:
                data["binding_offers"].append(message)
                # make a copy of the offer without the specific cards
                binding_offer = copy.copy(message)
                binding_offer.count = len(binding_offer.cards)
                binding_offer.cards = None
                self.broadcast(binding_offer, exclude=[message.uid])

    def process_withdraw(self, message):
        """Removes a binding offer if it still exists"""
        data = self.player_data[message.uid]
        for offer in data["binding_offers"]:
            if offer.cards == message.cards:
                data["binding_offers"].remove(offer)
                withdraw = Message(
                    Message.WITHDRAW,
                    uid=message.uid,
                    count=len(message.cards),
                    target_uid=message.target_uid,
                )
                self.player_data[message.target_uid]["conn"].send(withdraw)
                withdraw = copy.copy(withdraw)
                withdraw.cards = message.cards
                data["conn"].send(withdraw)
                break

    def process_bell_ring(self, message):
        """Broadcasts when a player rings the bell, checks if round over."""
        data = self.player_data[message.uid]
        if util.is_winning_hand(data["cards"]):
            self.round_winner = message.uid

    def process_message(self, message):
        """Processes player messages, updates state, checks if anyone won."""
        actions = {
            Message.OFFER: self.process_offer,
            Message.BINDING_OFFER: self.process_binding_offer,
            Message.WITHDRAW: self.process_withdraw,
            Message.RING_BELL: self.process_bell_ring,
        }
        if message.text in actions:
            actions[message.text](message)

    def get_matching_offer(self, message):
        """Returns matching binding offer, if one exists (to complete a trade)."""
        for offer in self.player_data[message.target_uid]["binding_offers"]:
            if offer.count == message.count:
                return offer
        return None

    def execute_trade(self, offer, match):
        """Trades cards between two players, notifies other players."""
        util.swap_cards(
            self.player_data[offer.uid]["cards"],
            offer.cards,
            self.player_data[match.uid]["cards"],
            match.cards,
        )
        self.broadcast_trade(offer, match)
        # only match was actually stored in binding_offers
        self.player_data[match.uid]["binding_offers"].remove(match)

    def update_scores(self):
        """Updates player scores, checks if there is a game winner."""
        for uid, data in self.player_data.iteritems():
            data["score"] += util.score_hand(data["cards"])
            if data["score"] >= config.WINNING_SCORE:
                self.game_winner = self.round_winner
        print("ROUND WINNER IS {0}".format(self.player_data[self.round_winner]["name"]))
        self.debug()

    def end_game(self):
        """Runs through steps to end a game, notifies players."""
        self.broadcast(Message(Message.GAME_OVER))
        self.wait_for_players(Message.GAME_DONE)

    def tear_down(self):
        """Steps to close down player processes & threads."""
        self.broadcast(Message(Message.DONE))
        for uid, data in self.player_data.iteritems():
            data["proc"].join()

    def broadcast(self, message, exclude=[]):
        """Send a message to all players except optional excluded uid"""
        for uid, data in self.player_data.iteritems():
            if uid not in exclude:
                data["conn"].send(message)

    def broadcast_trade(self, offer, match):
        """Broadcasts TRADE message to all players, including those involved"""
        message = Message(
            Message.TRADE,
            uid=offer.uid,
            cards=match.cards,
            count=len(offer.cards),
            target_uid=match.uid,
            removed_cards=offer.cards,
        )
        self.player_data[offer.uid]["conn"].send(message)

        message = Message(
            Message.TRADE,
            uid=match.uid,
            cards=offer.cards,
            count=len(offer.cards),
            target_uid=offer.uid,
            removed_cards=match.cards,
        )
        self.player_data[match.uid]["conn"].send(message)

        # make a copy to send to other players, but without specific cards
        message = copy.copy(message)
        message.cards = message.removed_cards = []
        self.broadcast(message, exclude=[offer.uid, match.uid])

    def wait_for_players(self, expected_message):
        """Loops and reads queue until message is received from all players.

        Discards any message from queue that is not the expected one.
        """
        received = set()
        while len(received) < len(self.players):
            message = self.message_queue.get()
            if message.text == expected_message:
                received.add(message.uid)

    def debug(self):
        msg = "{name} {uid}: {score} {cards} {binding_offers}"
        print("---------------------------")
        for uid, data in self.player_data.iteritems():
            offers = []
            for offer in data["binding_offers"]:
                offers.append(
                    "BO: {cards} TO {to}".format(
                        to=offer.target_uid, cards=sorted(offer.cards)
                    )
                )
            print(
                msg.format(
                    name=data["name"],
                    uid=uid,
                    score=data["score"],
                    cards=sorted(data["cards"]),
                    binding_offers=offers,
                )
            )
        print("---------------------------")
        print("")
        print("")
