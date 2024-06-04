from api.util import load_json
from collections import defaultdict
import random
import seaborn as sns


import functools

import choix
import matplotlib.pyplot as plt
import numpy as np

sns.set(style='whitegrid')

all_matches = [
    m
    for m in load_json("matches.json")
]

players = ["random", "gpt3", "gpt3-cot", "gpt4", "gpt4-cot", "rap"]
n_players = len(players)


def lsr_pairwise(n_items, data, alpha=0.0, initial_params=None):
    weights, chain = choix.lsr._init_lsr(n_items, alpha, initial_params)
    for p1, p2, p1score, p2score in data:
        chain[p1, p2] += float(p2score) / (weights[p1] + weights[p2])
        chain[p2, p1] += float(p1score) / (weights[p1] + weights[p2])
    chain -= np.diag(chain.sum(axis=1))
    return choix.utils.log_transform(choix.utils.statdist(chain))


def ilsr_pairwise(
    n_items, data, alpha=0.0, initial_params=None, max_iter=100, tol=1e-8
):
    fun = functools.partial(lsr_pairwise, n_items=n_items, data=data, alpha=alpha)
    return choix.lsr._ilsr(fun, initial_params, max_iter, tol)


def get_params(matches):
    wins = []
    for match in matches:
        agents = list(match.keys())[1:]
        if match[agents[0]] == match[agents[1]]:
            continue

        i = players.index(agents[0])
        j = players.index(agents[1])

        wins.append((i, j, match[agents[0]], match[agents[1]]))

    params = ilsr_pairwise(len(players), wins, alpha=0.001)
    return params


def boostrap_params():
    weights = defaultdict(int)
    for match in all_matches:
        weights[match["game"]] += 1

    bootstrapped_params = np.array(
        [
            get_params(
                random.choices(
                    all_matches, k=len(all_matches), weights=[1 / weights[m["game"]] for m in all_matches]
                )
            )
            for _ in range(100)
        ]
    ).transpose((1, 0))

    return bootstrapped_params


bootstrapped_params = boostrap_params()
ratings = bootstrapped_params.mean(1)
ci90s = np.percentile(bootstrapped_params, [5, 95], axis=1)
ci90s = np.absolute(ratings - ci90s)

fig, ax = plt.subplots()
sns.barplot(x=players, y=ratings, ax=ax)
ax.errorbar(players, ratings, yerr=ci90s, fmt="none", color="k", capsize=5)
ax.set_title("Rating")
ax.set_xlabel("Agent")
ax.set_ylabel("Exponential Score")
ax.tick_params(axis='x', rotation=30)

plt.savefig("figures/overall_rating.png")

################################################################################

fig, ax = plt.subplots(constrained_layout=True, dpi=300)

matrix = np.zeros((n_players, n_players))
for i in range(n_players):
    for j in range(n_players):
        matrix[i, j] = choix.probabilities([i, j], ratings)[0]

sns.heatmap(matrix, ax=ax, annot=True, xticklabels=players, yticklabels=players, fmt=".2f")
ax.set_title("Win probabilities")
ax.set_ylabel("Probability this agent...")
ax.set_xlabel("... beats this agent")
ax.tick_params(axis='x', rotation=30)
ax.tick_params(axis='y', rotation=0)
ax.invert_yaxis()

plt.savefig("figures/overall_probabilities.png")

################################################################################

fig, ax = plt.subplots()

n_games = defaultdict(int)
for match in all_matches:
    agents = list(match.keys())[1:]
    n_games[agents[0]] += 1
    n_games[agents[1]] += 1

agents, counts = zip(*list(n_games.items()))
ax.barh(agents, counts)
ax.set_ylabel("Agent")
ax.set_xlabel("Number of matches collected")

plt.savefig("figures/num_matches_per_agent.png")

################################################################################

fig, ax = plt.subplots()

n_games = defaultdict(int)
for match in all_matches:
    game = match["game"]
    n_games[game] += 1

games, counts = zip(*list(n_games.items()))
ax.barh(games, counts)
ax.set_ylabel("Game")
ax.set_xlabel("Number of matches collected")

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
