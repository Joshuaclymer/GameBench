"""Base Player class(es) to provide useful functionality for subclasses.
"""

import random
import threading

from synca import gameengine


class NullPlayer(gameengine.Player):
    """A Pit player class with messaging structure that makes no plays.

    This could be a useful superclass for an actual Pit player. It handles
    threading and messaging to/from the game engine, but never makes any
    actual plays (i.e. making & responding to offers). It also breaks most game
    events into separate methods for easy overriding.
    """

    def set_up(self, conn, queue, uid):
        """Initializes internal state and starts listener thread."""
        self.conn = conn
        self.queue = queue
        self.uid = uid
        self.done_event = threading.Event()
        self.round_over_event = threading.Event()
        self.game_over_event = threading.Event()
        self.notify(gameengine.Message.ALL_SET)
        self.listen()

    def new_game(self, message):
        """Resets state at the start of a new game."""
        self.game_over_event.clear()
        self.notify(gameengine.Message.GAME_READY)

    def new_round(self, message):
        """Resets state at start of a new round."""
        self.round_over_event.clear()
        round_loop = threading.Thread(target=self.round_loop, args=())
        round_loop.daemon = True
        round_loop.start()
        self.notify(gameengine.Message.ROUND_READY)

    def round_loop(self):
        """Main game loop, examines game state and puts actions on the queue.

        This is meant to be run once per round.
        """
        while not self.round_over_event.is_set():
            self.make_plays()

            # this will block, allowing the current thread to release the cpu
            # without this, sometimes the thread never ends
            self.round_over_event.wait(0.0001)
        self.notify(gameengine.Message.ROUND_DONE)

    def make_plays(self):
        """Does nothing (but would be a good place to put actions on the queue)"""

    def round_over(self, message):
        """Called when round over message received

        Sets round over event so round_loop will complete.
        """
        self.round_over_event.set()

    def game_over(self, message):
        """Called when game over message received"""
        self.game_over_event.set()
        self.notify(gameengine.Message.GAME_DONE)

    def done(self, message):
        """Called when done message received"""
        self.done_event.set()

    def handle_offer(self, message):
        """Called when another player makes an open offer"""

    def handle_binding_offer(self, message):
        """Called when another player makes a binding offer

        The binding offer might be made to us!
        """

    def handle_trade(self, message):
        """Called when two players trade cards"""

    def handle_withdraw(self, message):
        """Called when binding offer (to or from me) is withdrawn"""

    def listen(self):
        """Listens for messages from the game engine and update internal state."""
        actions = {
            # gameplay events
            gameengine.Message.NEW_GAME: self.new_game,
            gameengine.Message.NEW_ROUND: self.new_round,
            gameengine.Message.ROUND_OVER: self.round_over,
            gameengine.Message.GAME_OVER: self.game_over,
            gameengine.Message.DONE: self.done,
            # player actions
            gameengine.Message.OFFER: self.handle_offer,
            gameengine.Message.BINDING_OFFER: self.handle_binding_offer,
            gameengine.Message.TRADE: self.handle_trade,
            gameengine.Message.WITHDRAW: self.handle_withdraw,
        }

        while not self.done_event.is_set():
            message = self.conn.recv()
            if message.text in actions:
                actions[message.text](message)

    def notify(self, message, cards=[], count=0, target_uid=None):
        """Helper to put a message on the queue"""
        self.queue.put(
            gameengine.Message(
                message, uid=self.uid, cards=cards, count=count, target_uid=target_uid
            )
        )
