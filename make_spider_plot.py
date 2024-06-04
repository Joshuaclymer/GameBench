import functools
from api.util import load_json
from collections import defaultdict
import random

import choix
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from rating import get_params, players, get_matches, better_names

sns.set(style="whitegrid")

categories = ["sea_battle", "two_rooms_and_a_boom", "are_you_the_traitor", "air_land_sea", "santorini", "hive", "pit", "arctic_scavengers", "codenames"]
N = len(categories)

all_ratings = {
    c: get_params(get_matches(c)) for c in categories
}
#for category, ratings in all_ratings.items():
#    expratings = np.exp(ratings)
#    best = np.max(expratings)
#    relative = expratings / best
#    all_ratings[category] = relative

x, y, hue = [], [], []
for category in categories:
    ratings = all_ratings[category]
    for agent_idx, score in enumerate(ratings):
        x.append(better_names[category])
        y.append(score)
        hue.append(players[agent_idx])

x = np.array(x)
y = np.array(y)
hue = np.array(hue)

fig, ax = plt.subplots(figsize=(9, 6), constrained_layout=True, dpi=300)
sns.scatterplot(x=y, y=x, hue=hue, style=hue, palette='bright', s=100, ax=ax)
plt.savefig("figures/rating_scatter.png")

"""
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
#plt.show()"""