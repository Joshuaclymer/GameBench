from api.util import load_json
from collections import defaultdict
import random

import choix
import matplotlib.pyplot as plt
import numpy as np
import functools
import seaborn as sns

import pandas as pd

from rating import *


ratings_df = pd.DataFrame(index=players, columns=[shorter_names[g] for g in games])
probs_df = pd.DataFrame(index=players, columns=[shorter_names[g] for g in games])
scores_df = pd.DataFrame(index=players, columns=pd.MultiIndex.from_product(
    [[shorter_names[g] for g in games], ["# matches", "score", "avg."]],
    names=["games", "metrics"]
))

for game in games:
    matches = get_matches(game)
    game = shorter_names[game]

    n_matches = defaultdict(int)
    scores = defaultdict(int)
    for m in matches:
        agents = list(m.keys())[1:]
        n_matches[agents[0]] += 1
        n_matches[agents[1]] += 1
        scores[agents[0]] += m[agents[0]]
        scores[agents[1]] += m[agents[1]]

    params = bootstrap_params(matches)
    ratings = params.mean(0)

    ratings_df.loc[:, game] = ratings
    probs_df.loc[:, game] = choix.probabilities(range(n_players), ratings)

    for agent in players:
        scores_df.loc[agent, (game, "# matches")] = n_matches[agent]
        scores_df.loc[agent, (game, "score")] = scores[agent]
        scores_df.loc[agent, (game, "avg.")] = scores[agent] / n_matches[agent] if n_matches[agent] > 0 else 0