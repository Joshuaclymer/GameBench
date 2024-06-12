from api.util import load_json
from collections import defaultdict
import random

import choix
import matplotlib.pyplot as plt
import numpy as np
import functools
import seaborn as sns
from rating import bootstrap_params, get_params, players, n_players

sns.set(style='whitegrid')

def make_figures(game, matches):

    fig, axs = plt.subplots(2, 2, figsize=(9.5, 7.8), constrained_layout=True, dpi=300)
    ax_nmatches = axs[0, 0]
    ax_score = axs[0, 1]
    ax_prob = axs[1, 0]
    ax_rating = axs[1, 1]
    fig.suptitle(game)

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

    sns.heatmap(matrix, ax=ax_nmatches, annot=True, xticklabels=players, yticklabels=players)
    ax_nmatches.tick_params(axis='x', rotation=30)
    ax_nmatches.tick_params(axis='y', rotation=0)
    ax_nmatches.invert_yaxis()
    #plt.xticks(rotation=30)

    ax_nmatches.set_title("Number of matches")

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

    sns.heatmap(matrix, ax=ax_score, annot=True, xticklabels=players, yticklabels=players)

    ax_score.set_title("Average score")
    ax_score.set_ylabel("Average points this agent scored...")
    ax_score.set_xlabel("... against this agent")
    ax_score.tick_params(axis='x', rotation=30)
    ax_score.tick_params(axis='y', rotation=0)
    ax_score.invert_yaxis()

    ################################################################################

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
                for _ in range(1000)
            ]
        )
    else:
        bootstrapped_params = np.array(
            [
                get_params(
                    random.choices(
                        matches, k=len(matches)
                    )
                )
                for _ in range(1000)
            ]
        ).transpose((1, 0))
    ratings = bootstrapped_params.mean(1)
    ci90s = np.percentile(bootstrapped_params, [5, 95], axis=1)
    ci90s = np.absolute(ratings - ci90s)

    sns.boxplot(data=bootstrapped_params, whis=(0, 100), ax=ax_rating)
    ax_rating.set_title("Bradley-Terry Model Rating")
    ax_rating.set_xlabel("Agent")
    ax_rating.set_ylabel("Exponential rating")
    ax_rating.set_xticks(ticks=range(len(players)), labels=players)
    ax_rating.tick_params(axis='x', rotation=30)

    ################################################################################

    matrix = np.zeros((n_players, n_players))
    for i in range(n_players):
        for j in range(n_players):
            matrix[i, j] = choix.probabilities([i, j], ratings)[0]

    sns.heatmap(matrix, ax=ax_prob, annot=True, xticklabels=players, yticklabels=players, fmt=".2f")
    ax_prob.set_title("Win probabilities")
    ax_prob.set_ylabel("Probability this agent...")
    ax_prob.set_xlabel("... beats this agent")
    ax_prob.tick_params(axis='x', rotation=30)
    ax_prob.tick_params(axis='y', rotation=0)
    ax_prob.invert_yaxis()


    ################################################################################

    plt.savefig(f"figures/{game}.jpg")
    plt.close()

for game in ["sea_battle", "two_rooms_and_a_boom", "are_you_the_traitor", "air_land_sea", "santorini", "hive", "pit", "arctic_scavengers", "codenames"]:
    matches = [m for m in load_json("matches.json") if m["game"] == game]
    make_figures(game, matches)

make_figures("overall", load_json("matches.json"))
