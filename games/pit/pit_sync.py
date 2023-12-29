"""Runs a synchronous Pit game using the Game Engine and Player from pit.sync
"""

from sync import gameengine
from sync.player import basic


engine = gameengine.GameEngine()

players = []
players.append(basic.BasicPlayer("bob"))
players.append(basic.BasicPlayer("joe"))
players.append(basic.BasicPlayer("sue"))
players.append(basic.BasicPlayer("tim"))
players.append(basic.BasicPlayer("ned"))
players.append(basic.BasicPlayer("deb"))
players.append(basic.BasicPlayer("pat"))

games = 10

results = engine.play(players, games=games)
print(results)
