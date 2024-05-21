from api.util import load_json
from collections import defaultdict
import random

import choix
import matplotlib.pyplot as plt
import numpy as np

def get_weighted_rating(game):

    matches = [m for m in load_json("matches.json") if "gpt3-bap" not in m and "gpt4-bap" not in m and m["game"] == game]

    players = set()
    for match in matches:
        agents = list(match.keys())[1:]
        players.update(agents)

    players = ["random", "gpt3", "gpt3-cot", "gpt4", "gpt4-cot", "rap"]#list(players)
    n_players = len(players)
    players.sort()


    ################################################################################

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
    print(bootstrapped_params.shape)
    #ratings = bootstrapped_params.mean(1)
    bootstrapped_params = bootstrapped_params * (1 / len(matches))

    return bootstrapped_params

#ci90s = np.percentile(bootstrapped_params, [5, 95], axis=1)
#ci90s = np.absolute(ratings - ci90s)

bootstrapped_params = None
for game in ["sea_battle", "two_rooms_and_a_boom", "are_you_the_traitor", "air_land_sea", "santorini", "hive", "pit", "arctic_scavengers", "codenames", "atari_boxing"]:
    if bootstrapped_params is None:
        bootstrapped_params = get_weighted_rating(game)
    else:
        bootstrapped_params += get_weighted_rating(game)

ratings = bootstrapped_params.mean(1)
ci90s = np.percentile(bootstrapped_params, [5, 95], axis=1)
ci90s = np.absolute(ratings - ci90s)

fig, ax = plt.subplots()
players = ["random", "gpt3", "gpt3-cot", "gpt4", "gpt4-cot", "rap"]
ax.errorbar(players, ratings, yerr=ci90s, fmt="o")
ax.set_title("Rating")

plt.show()