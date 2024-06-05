from api.util import load_json
from collections import defaultdict
import random
import seaborn as sns
import functools

import choix
import matplotlib.pyplot as plt
import numpy as np
from rating import bootstrap_params, players, n_players, get_matches, better_names, shorter_names

sns.set(style='whitegrid')

all_matches = get_matches()

bootstrapped_params = bootstrap_params(all_matches)
ratings = bootstrapped_params.mean(0)

fig, ax = plt.subplots()
sns.boxplot(data=bootstrapped_params, whis=(0, 100), ax=ax)
#ax.set_xlabel("Agent")
ax.set_xticks(ticks=range(len(players)), labels=players)

plt.savefig("figures/overall_rating.png")

################################################################################

fig, ax = plt.subplots(constrained_layout=True, dpi=300)

matrix = np.zeros((n_players, n_players))
for i in range(n_players):
    for j in range(n_players):
        matrix[i, j] = choix.probabilities([i, j], ratings)[0]

sns.heatmap(matrix, ax=ax, annot=True, xticklabels=players, yticklabels=players, fmt=".2f")
#ax.set_title("Win probabilities")
ax.set_ylabel("Probability this agent...")
ax.set_xlabel("... beats this agent")
ax.tick_params(axis='x', rotation=30)
ax.tick_params(axis='y', rotation=0)
ax.invert_yaxis()

plt.savefig("figures/overall_probabilities.png")

################################################################################

fig, ax = plt.subplots(constrained_layout=True, dpi=300)

n_games = defaultdict(int)
counts = [0] * n_players
for match in all_matches:
    agents = list(match.keys())[1:]
    counts[players.index(agents[0])] += 1
    counts[players.index(agents[1])] += 1

sns.barplot(x=players, y=counts, ax=ax)
#ax.tick_params(axis='x', rotation=30)
#ax.set_ylabel("Agent")
#ax.set_xlabel("Number of matches collected")

plt.savefig("figures/num_matches_per_agent.png")

################################################################################

fig, ax = plt.subplots(constrained_layout=True, dpi=300)

n_games = defaultdict(int)
for match in all_matches:
    game = match["game"]
    n_games[game] += 1

games, counts = zip(*list(n_games.items()))
sns.barplot(x=[better_names[g] for g in games], y=counts, ax=ax)
labels = ax.get_xticklabels()
plt.setp(labels, rotation=45, ha="right", rotation_mode="anchor")
#ax.tick_params(axis='x', rotation=30)
#ax.set_ylabel("Game")
#ax.set_xlabel("Number of matches collected")

plt.savefig("figures/num_matches_per_game.png")

################################################################################

fig, ax = plt.subplots()

n_matches = defaultdict(int)

for match in all_matches:
    agents = list(match.keys())[1:]
    n_matches[agents[0], agents[1]] += 1
    n_matches[agents[1], agents[0]] += 1

wins = defaultdict(int)
for match in all_matches:
    agents = list(match.keys())[1:]
    game = match["game"]
    wins[agents[0], agents[1]] += match[agents[0]] / n_games[game]
    wins[agents[1], agents[0]] += match[agents[1]] / n_games[game]

for (agent1, agent2), score in wins.items():
    wins[agent1, agent2] = score / n_matches[agent1, agent2]

matrix = np.zeros((len(players), len(players)))
#matrix.fill(np.nan)
for i, player1 in enumerate(players):
    for j, player2 in enumerate(players):
        if player1 == player2:
            continue

        matrix[i, j] = wins[player1, player2]

sns.heatmap(matrix, ax=ax, annot=True, xticklabels=players, yticklabels=players)

ax.set_title("Average score")
ax.set_ylabel("Average points this agent scored...")
ax.set_xlabel("... against this agent")
ax.tick_params(axis='x', rotation=30)
ax.tick_params(axis='y', rotation=0)
ax.invert_yaxis()

plt.savefig("figures/average_score.png")

################################################################################