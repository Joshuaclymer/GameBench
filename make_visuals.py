from api.util import load_json
from collections import defaultdict
import random

import choix
import matplotlib.pyplot as plt
import numpy as np

"""
Todo:
- Why is .text do (j, i)?
- Add indiciator when win probabilities are inferred from no match data
- Maybe make a average score plot? First plot is heavily influenced by
how much data was collected.
"""

def make_figures(game):
    matches = [m for m in load_json("matches.json") if "gpt3-bap" not in m and "gpt4-bap" not in m and m["game"] == game]

    players = set()
    for match in matches:
        agents = list(match.keys())[1:]
        players.update(agents)

    players = list(players)
    n_players = len(players)
    players.sort()

    ################################################################################
    fig, ax = plt.subplots()

    n_matches = defaultdict(int)

    for match in matches:
        agents = list(match.keys())[1:]
        n_matches[agents[0], agents[1]] += 1
        n_matches[agents[1], agents[0]] += 1

    matrix = np.zeros((n_players, n_players))
    for i, player1 in enumerate(players):
        for j, player2 in enumerate(players):
            if player1 == player2:
                continue

            matrix[i][j] = n_matches[player1, player2]

    im = ax.imshow(matrix)

    ax.set_xticks(np.arange(n_players), labels=players)
    ax.set_yticks(np.arange(n_players), labels=players)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for i in range(n_players):
        for j in range(n_players):
            text = ax.text(
                j, i, matrix[i, j].round(1), ha="center", va="center", color="w"
            )

    ax.set_title("Number of matches")

    #plt.show()
    plt.savefig(f"images/{game}_nummatches.jpg")
    plt.close()

    ################################################################################

    fig, ax = plt.subplots()

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

    im = ax.imshow(matrix)

    ax.set_xticks(np.arange(n_players), labels=players)
    ax.set_yticks(np.arange(n_players), labels=players)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for i in range(n_players):
        for j in range(n_players):
            text = ax.text(
                j, i, matrix[i, j].round(1), ha="center", va="center", color="w"
            )

    ax.set_title("Average score")
    ax.set_ylabel("How many points this agent earned...")
    ax.set_xlabel("... playing against this agent")

    #plt.show()
    plt.savefig(f"images/{game}_averagescore.jpg")
    plt.close()

    ################################################################################
    fig, ax = plt.subplots()

    def rank_centrality(n_items, data, alpha=0.0):
        # https://choix.lum.li/en/latest/_modules/choix/lsr.html#rank_centrality
        _, chain = choix.lsr._init_lsr(n_items, alpha, None)
        for p1, p2, p1score, p2score in data:
            chain[p1, p2] += float(p2score)
            chain[p2, p1] += float(p1score)
        idx = chain > 0
        chain[idx] = chain[idx] / (chain + chain.T)[idx]
        chain -= np.diag(chain.sum(axis=-1))
        return choix.utils.log_transform(choix.utils.statdist(chain))

    def get_params(matches):
        wins = []
        for match in matches:
            agents = list(match.keys())[1:]
            if match[agents[0]] == match[agents[1]]:
                continue

            i = players.index(agents[0])
            j = players.index(agents[1])

            wins.append((i, j, match[agents[0]], match[agents[1]]))

        params = rank_centrality(len(players), wins, alpha=0.001)
        return params


    bootstrapped_params = np.array(
        [get_params(random.choices(matches, k=len(matches))) for _ in range(100)]
    ).transpose((1, 0))
    ratings = bootstrapped_params.mean(1)
    ci90s = np.percentile(bootstrapped_params, [5, 95], axis=1)
    ci90s = np.absolute(ratings - ci90s)

    #ax.scatter(players, params)
    ax.errorbar(players, ratings, yerr=ci90s, fmt="o")
    ax.set_title("Rating")

    #plt.show()
    plt.savefig(f"images/{game}_rating.jpg")
    plt.close()

    ################################################################################
    fig, ax = plt.subplots()

    matrix = np.zeros((n_players, n_players))
    for i in range(n_players):
        for j in range(n_players):
            matrix[i, j] = choix.probabilities([i, j], ratings)[0]

    im = ax.imshow(matrix)

    ax.set_xticks(np.arange(n_players), labels=players)
    ax.set_yticks(np.arange(n_players), labels=players)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for i in range(n_players):
        for j in range(n_players):
            text = ax.text(
                j, i, matrix[i, j].round(2), ha="center", va="center", color="w"
            )

    ax.set_title("Win probabilities")
    ax.set_ylabel("Probability that this agent...")
    ax.set_xlabel("... beats this agent")

    #plt.show()
    plt.savefig(f"images/{game}_probabilities.jpg")
    plt.close()

    ################################################################################

for game in ["sea_battle", "two_rooms_and_a_boom", "are_you_the_traitor", "air_land_sea", "santorini", "hive", "pit", "arctic_scavengers", "codenames", "atari_boxing"]:
    make_figures(game)