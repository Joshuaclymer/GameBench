from api.util import load_json
from collections import defaultdict

import choix
import matplotlib.pyplot as plt
import numpy as np

"""
Todo:
- Add confidence interval to rating plot
- Maybe use different algorithm that accepts ratio of wins/losses instead
- Why is .text do (j, i)?
- Add indiciator when win probabilities are inferred from no match data
"""

wins = defaultdict(int)
players = set()

matches = load_json("matches.json")
for match in matches:
    agents = list(match.keys())[1:]
    players.update(agents)

    wins[agents[0], agents[1]] += match[agents[0]]
    wins[agents[1], agents[0]] += match[agents[1]]

matrix = np.zeros((len(players), len(players)))
players = list(players)
n_players = len(players)
players.sort()
for i, player1 in enumerate(players):
    for j, player2 in enumerate(players):
        if player1 == player2:
            continue

        matrix[i][j] = wins[player1, player2]

fig, ax = plt.subplots(1, 3)
im = ax[0].imshow(matrix)

ax[0].set_xticks(np.arange(n_players), labels=players)
ax[0].set_yticks(np.arange(n_players), labels=players)
plt.setp(ax[0].get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

for i in range(n_players):
    for j in range(n_players):
         text = ax[0].text(j, i, matrix[i, j].round(1), ha="center", va="center", color="w")

ax[0].set_title("Scores")

wins = []
for match in matches:
    agents = list(match.keys())[1:]
    if match[agents[0]] == match[agents[1]]:
        continue

    i = players.index(agents[0])
    j = players.index(agents[1])

    if match[agents[0]] > match[agents[1]]:
        wins.append((i, j))
    else:
        wins.append((j, i))

params = choix.ilsr_pairwise(len(players), wins, alpha=0.01)

ax[2].scatter(players, params)
ax[2].set_title("Rating")

matrix = np.zeros((n_players, n_players))
for i in range(n_players):
    for j in range(n_players):
        matrix[i, j] = choix.probabilities([i, j], params)[0]

im = ax[1].imshow(matrix)

ax[1].set_xticks(np.arange(n_players), labels=players)
ax[1].set_yticks(np.arange(n_players), labels=players)
plt.setp(ax[1].get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

for i in range(n_players):
    for j in range(n_players):
         text = ax[1].text(j, i, matrix[i, j].round(1), ha="center", va="center", color="w")

ax[1].set_title("Win probabilities")

plt.show()