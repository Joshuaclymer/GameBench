from api.util import load_json
from collections import defaultdict
import random

import choix
import matplotlib.pyplot as plt
import numpy as np
import functools
import seaborn as sns

import pandas as pd

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


def bootstrap_params(matches):
    weights = defaultdict(int)
    for match in matches:
        weights[match["game"]] += 1

    bootstrapped_params = np.array(
        [
            get_params(
                random.choices(
                    matches, k=len(all_matches), weights=[1 / weights[m["game"]] for m in matches]
                )
            )
            for _ in range(100)
        ]
    )

    return bootstrapped_params

games = ["sea_battle", "two_rooms_and_a_boom", "are_you_the_traitor", "air_land_sea", "santorini", "hive", "pit", "arctic_scavengers", "codenames"]

columns = pd.MultiIndex.from_product(
    [
        games,
        ["# matches", "P(win)", "rating"]
    ],
    names=["game", "metric"]
)
df = pd.DataFrame(index=players, columns=columns)

for game in games:
    matches = [m for m in all_matches if m["game"] == game]

    n_matches = defaultdict(int)
    for m in matches:
        agents = list(m.keys())[1:]
        n_matches[agents[0]] += 1
        n_matches[agents[1]] += 1

    params = bootstrap_params(matches)
    ratings = params.mean(0)
    df.loc[:, (game, "rating")] = ratings
    df.loc[:, (game, "P(win)")] = choix.probabilities(range(len(players)), ratings)
    for agent, n in n_matches.items():
        df[agent, (game, "# matches")] = n

with open("total_table.tex", "w") as f:
    tex = df.to_latex()
    f.write(tex)