from api.util import load_json
from collections import defaultdict
import random

import choix
import matplotlib.pyplot as plt
import numpy as np
import functools
import seaborn as sns

sns.set(style='white')

def make_figures(game, matches):

    players = set()
    for match in matches:
        agents = list(match.keys())[1:]
        players.update(agents)

    players = ["random", "gpt3", "gpt3-cot", "gpt4", "gpt4-cot", "rap"]#list(players)
    n_players = len(players)
    #players.sort()

    fig, axs = plt.subplots(2, 2, figsize=(9.5, 7.8), constrained_layout=True)
    pos_nmatches = 0, 0
    pos_score = 0, 1
    pos_prob = 1, 0
    pos_rating = 1, 1

    ################################################################################

    n_matches = defaultdict(int)

    for match in matches:
        agents = list(match.keys())[1:]
        n_matches[agents[0], agents[1]] += 1
        n_matches[agents[1], agents[0]] += 1

    matrix = np.zeros((n_players, n_players), dtype="int")
    for i, player1 in enumerate(players):
        for j, player2 in enumerate(players):
            if player1 == player2:
                continue

            matrix[i][j] = n_matches[player1, player2]

    sns.heatmap(matrix, ax=axs[pos_nmatches], annot=True, xticklabels=players, yticklabels=players)
    axs[pos_nmatches].tick_params(axis='x', rotation=30)
    axs[pos_nmatches].tick_params(axis='y', rotation=0)
    axs[pos_nmatches].invert_yaxis()
    #plt.xticks(rotation=30)

    axs[pos_nmatches].set_title("Number of matches")

    ################################################################################


    wins = defaultdict(int)
    for match in matches:
        agents = list(match.keys())[1:]
        wins[agents[0], agents[1]] += match[agents[0]]
        wins[agents[1], agents[0]] += match[agents[1]]

    for (agent1, agent2), score in wins.items():
        wins[agent1, agent2] = score / n_matches[agent1, agent2]

    matrix = np.empty((len(players), len(players)))
    matrix.fill(np.nan)
    for i, player1 in enumerate(players):
        for j, player2 in enumerate(players):
            if player1 == player2:
                continue

            matrix[i, j] = wins[player1, player2]

    sns.heatmap(matrix, ax=axs[pos_score], annot=True, xticklabels=players, yticklabels=players)

    axs[pos_score].set_title("Average score")
    axs[pos_score].set_ylabel("Average points this agent scored...")
    axs[pos_score].set_xlabel("... against this agent")
    axs[pos_score].tick_params(axis='x', rotation=30)
    axs[pos_score].tick_params(axis='y', rotation=0)
    axs[pos_score].invert_yaxis()

    ################################################################################

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


    if game == "overall":
        weights = defaultdict(int)
        for match in matches:
            weights[match["game"]] += 1
        weights = [1 / weights[m["game"]] for m in matches]
        bootstrapped_params = np.array(
            [
                get_params(
                    random.choices(
                        matches, k=len(matches), weights=weights
                    )
                )
                for _ in range(100)
            ]
        ).transpose((1, 0))
    else:
        bootstrapped_params = np.array(
            [
                get_params(
                    random.choices(
                        matches, k=len(matches)
                    )
                )
                for _ in range(100)
            ]
        ).transpose((1, 0))
    ratings = bootstrapped_params.mean(1)
    ci90s = np.percentile(bootstrapped_params, [5, 95], axis=1)
    ci90s = np.absolute(ratings - ci90s)

    axs[pos_rating].errorbar(players, ratings, yerr=ci90s, fmt="o")
    axs[pos_rating].set_title("Rating")
    axs[pos_rating].set_xlabel("Agent")
    axs[pos_rating].set_ylabel("Exponential Score")
    axs[pos_rating].tick_params(axis='x', rotation=30)

    ################################################################################

    matrix = np.zeros((n_players, n_players))
    for i in range(n_players):
        for j in range(n_players):
            matrix[i, j] = choix.probabilities([i, j], ratings)[0]

    sns.heatmap(matrix, ax=axs[pos_prob], annot=True, xticklabels=players, yticklabels=players, fmt=".2f")
    axs[pos_prob].set_title("Win probabilities")
    axs[pos_prob].set_ylabel("Probability this agent...")
    axs[pos_prob].set_xlabel("... beats this agent")
    axs[pos_prob].tick_params(axis='x', rotation=30)
    axs[pos_prob].tick_params(axis='y', rotation=0)
    axs[pos_prob].invert_yaxis()


    ################################################################################

    plt.savefig(f"figures/{game}.jpg")
    plt.close()

for game in ["sea_battle", "two_rooms_and_a_boom", "are_you_the_traitor", "air_land_sea", "santorini", "hive", "pit", "arctic_scavengers", "codenames"]:
    matches = [m for m in load_json("matches.json") if m["game"] == game]
    make_figures(game, matches)

make_figures("overall", load_json("matches.json"))