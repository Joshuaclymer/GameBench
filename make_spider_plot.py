import functools
from api.util import load_json
from collections import defaultdict
import random

import choix
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

sns.set(style="whitegrid")

def get_ratings(game):
    matches = [m for m in load_json("matches.json") if m["game"] == game]

    players = ["random", "gpt3", "gpt3-cot", "gpt4", "gpt4-cot", "rap"]
    players.sort()

    def lsr_pairwise(n_items, data, alpha=0.0, initial_params=None):
        weights, chain = choix.lsr._init_lsr(n_items, alpha, initial_params)
        for p1, p2, p1score, p2score in data:
            chain[p1, p2] += float(p2score) / (weights[p1] + weights[p2])
            chain[p2, p1] += float(p1score) / (weights[p1] + weights[p2])
        chain -= np.diag(chain.sum(axis=1))
        return choix.utils.log_transform(choix.utils.statdist(chain))

    def ilsr_pairwise(n_items, data, alpha=0.0, initial_params=None, max_iter=100, tol=1e-8):
        fun = functools.partial(
                lsr_pairwise, n_items=n_items, data=data, alpha=alpha)
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

    return get_params(matches)

categories = ["sea_battle", "two_rooms_and_a_boom", "are_you_the_traitor", "air_land_sea", "santorini", "hive", "pit", "arctic_scavengers", "codenames"]
N = len(categories)

all_ratings = {
    c: get_ratings(c) for c in categories
}
for category, ratings in all_ratings.items():
    expratings = np.exp(ratings)
    best = np.max(expratings)
    relative = expratings / best
    all_ratings[category] = relative
players = ["random", "gpt3", "gpt3-cot", "gpt4", "gpt4-cot", "rap"]
players.sort()

angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True), dpi=300, constrained_layout=True)


ax.set_theta_offset(np.pi / 2)
ax.set_theta_direction(-1)

better_name = {
    "sea_battle": "Sea Battle", "two_rooms_and_a_boom": "Two Rooms and a Boom",
    "are_you_the_traitor": "Are You the Traitor?", "air_land_sea": "Air, Land, and Sea",
    "santorini": "Santorini", "hive": "Hive", "pit": "Pit", "arctic_scavengers": "Arctic Scavengers",
    "codenames": "Codenames"
}

plt.xticks(angles[:-1], [better_name[c] for c in categories])

ax.set_rscale('linear')
plt.ylim(0, 1)

# Plot each model
for i, player in enumerate(players):
    value = [r[i] for _, r in all_ratings.items()]
    data = value + value[:1]
    ax.plot(angles, data, linewidth=1, linestyle='solid', label=player)
    ax.fill(angles, data, alpha=0.1)

# Add a legend
plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
plt.savefig("figures/spider_plot.png")
#plt.show()