from api.util import load_json
from collections import defaultdict
import random
import functools
import choix
import numpy as np

################################################################################
################################################################################
################################################################################
# The code contained in this block is copied from choix. It has been modified
# from the original to fit our data better. The original license is included.
# The MIT License (MIT)
#
# Copyright (c) 2015 Lucas Maystre
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
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

################################################################################
################################################################################
################################################################################

players = ["random", "human", "gpt-3", "gpt-3-cot", "gpt-4", "gpt-4-cot", "gpt-4-rap"]
n_players = len(players)

def get_matches(game=None):
    if game:
        return [m for m in load_json("matches.json") if m["game"] == game]
    return load_json("matches.json")

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
                    matches, k=len(matches), weights=[1 / weights[m["game"]] for m in matches]
                )
            )
            for _ in range(1000)
        ]
    )

    return bootstrapped_params

games = ["sea_battle", "two_rooms_and_a_boom", "are_you_the_traitor", "air_land_sea", "santorini", "hive", "pit", "arctic_scavengers", "codenames"]
games.sort()

better_names = {
    "sea_battle": "Sea Battle", "two_rooms_and_a_boom": "Two Rooms and a Boom",
    "are_you_the_traitor": "Are You the Traitor?", "air_land_sea": "Air, Land, and Sea",
    "santorini": "Santorini", "hive": "Hive", "pit": "Pit", "arctic_scavengers": "Arctic Scavengers",
    "codenames": "Codenames"
}

shorter_names = {
    "sea_battle": "SB", "two_rooms_and_a_boom": "TRB", "are_you_the_traitor": "AYT",
    "air_land_sea": "ALS", "santorini": "SN", "hive": "HV", "pit": "PT",
    "arctic_scavengers": "AS", "codenames": "CN"
}