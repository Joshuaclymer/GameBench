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
sns.scatterplot(x=x, y=y, hue=hue, style=hue, palette='bright', s=300, ax=ax)
ax.set_ylim(-2.5, 3)
plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
plt.savefig("figures/rating_scatter.png")