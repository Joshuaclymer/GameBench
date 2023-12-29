import time

from synca import gameengine
from synca.player import base, basic

if __name__ == "__main__":
    start_time = time.time()
    ge = gameengine.GameEngine()
    players = [
        basic.SimplePlayer("joe"),
        basic.SimplePlayer("kim"),
        basic.SimplePlayer("deb"),
        basic.SimplePlayer("bob"),
        basic.SimplePlayer("sue"),
        basic.SimplePlayer("ted"),
        basic.SimplePlayer("han"),
        basic.SimplePlayer("jen"),
    ]

    games = 1
    print("STARTING {0} GAME(S)".format(games))
    ge.play(players, games=games)
    print("TOTAL TIME: {0} SECONDS".format(time.time() - start_time))
