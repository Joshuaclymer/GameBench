from api.util import load_json
from collections import defaultdict
import random
import seaborn as sns
import functools

random.seed(0)

import choix
import matplotlib.pyplot as plt
import numpy as np
from rating import *

import pandas as pd

complete_matches = {
    g: get_matches(g) for g in games
} | {"all": get_matches()}
complete_bootstrapped_params = {
    g: bootstrap_params(m) for g, m in complete_matches.items()
} | {"all": bootstrap_params(get_matches())}

################################################################################
################################################################################
################################################################################



sns.set(style='whitegrid')
sns.set_context("paper", font_scale=1.5)

bootstrapped_params = complete_bootstrapped_params["all"]
ratings = bootstrapped_params.mean(0)

sorted_indices = np.argsort(ratings)
sorted_data = bootstrapped_params[:, sorted_indices]
sorted_labels = [players[i] for i in sorted_indices]

fig, ax = plt.subplots(constrained_layout=True, dpi=300)
sns.boxplot(data=sorted_data, whis=(5, 95), fliersize=0, ax=ax)
ax.set_ylabel("Rating")
ax.set_xticks(ticks=range(len(players)), labels=sorted_labels)
#ax.tick_params(axis='x', rotation=30)

plt.savefig("figures/overall_rating.png")

################################################################################

fig, ax = plt.subplots(constrained_layout=True, dpi=300)

matrix = np.zeros((n_players, n_players))
for i in range(n_players):
    for j in range(n_players):
        matrix[i, j] = choix.probabilities([i, j], ratings)[0]

sns.heatmap(matrix, ax=ax, annot=True, xticklabels=players, yticklabels=players, fmt=".2f")
#ax.set_title("Win probabilities")
ax.set_ylabel("Probability this agent...")
ax.set_xlabel("... beats this agent")
ax.tick_params(axis='x', rotation=30)
ax.tick_params(axis='y', rotation=0)
ax.invert_yaxis()

plt.savefig("figures/overall_probabilities.png")

################################################################################

fig, ax = plt.subplots(constrained_layout=True, dpi=300)

n_games = defaultdict(int)
counts = np.array([0] * n_players)
for match in complete_matches["all"]:
    agents = list(match.keys())[1:]
    counts[players.index(agents[0])] += 1
    counts[players.index(agents[1])] += 1

sorted_indices = np.argsort(counts)
sorted_players = [players[i] for i in sorted_indices]
sorted_counts = counts[sorted_indices]
sns.barplot(x=sorted_players, y=sorted_counts, ax=ax)
#ax.tick_params(axis='x', rotation=30)
#ax.set_ylabel("Agent")
#ax.set_xlabel("Number of matches collected")

plt.savefig("figures/num_matches_per_agent.png")

################################################################################

fig, ax = plt.subplots(constrained_layout=True, dpi=300)

n_games = defaultdict(int)
for match in complete_matches["all"]:
    game = match["game"]
    n_games[game] += 1

games, counts = zip(*list(n_games.items()))
counts = np.array(counts)
sorted_indices = np.argsort(counts)
sorted_games = [games[i] for i in sorted_indices]
sorted_counts = counts[sorted_indices]
sns.barplot(x=[shorter_names[g] for g in sorted_games], y=sorted_counts, ax=ax)
labels = ax.get_xticklabels()
#plt.setp(labels, rotation=45, ha="right", rotation_mode="anchor")
#ax.tick_params(axis='x', rotation=30)
#ax.set_ylabel("Game")
#ax.set_xlabel("Number of matches collected")

plt.savefig("figures/num_matches_per_game.png")

################################################################################
sns.set_context("paper", font_scale=2)
categories = games
N = len(categories)

all_ratings = {
    c: complete_bootstrapped_params[c].mean(0) for c in categories
}
for game, ratings in all_ratings.items():
    expd = np.exp(ratings)
    maxd = np.max(expd)
    all_ratings[game] = expd / maxd

x, y, hue = [], [], []
for category in categories:
    ratings = all_ratings[category]
    for agent_idx, score in enumerate(ratings):
        x.append(shorter_names[category])
        y.append(score)
        hue.append(players[agent_idx])

x = np.array(x)
y = np.array(y)
hue = np.array(hue)

fig, ax = plt.subplots(figsize=(10, 7), constrained_layout=True, dpi=300)
sns.scatterplot(x=x, y=y, hue=hue, style=hue, palette='bright', s=300, ax=ax)
#ax.set_ylim(-2.5, 3)
ax.set_ylabel("Proportional rating")
#plt.xticks(rotation=45, ha="right", rotation_mode="anchor")
plt.savefig("figures/rating_scatter.png")

################################################################################

ratings_df = pd.DataFrame(index=players, columns=["Overall"] + [shorter_names[g] for g in games])
scores_df = pd.DataFrame(index=players, columns=["Overall"] + [shorter_names[g] for g in games])

header = "\\begin{tabular}{lcccccccccc}\n\\toprule\nAgent &  & \\multicolumn{9}{c}{Score} \\\\\n\\cmidrule(lr){2-11}\n &  Overall & ALS & ARC & AYT & CN & HV & PT & SN & TRB & SB \\\\\n"

def create_bold_underline_formatter(column):
    sorted_values = column.sort_values(ascending=False).unique()
    if len(sorted_values) >= 2:
        max_value = sorted_values[0]
        second_max_value = sorted_values[1]
    else:
        max_value = sorted_values[0]
        second_max_value = None

    def formatter(x):
        formatted_x = f"{x:.2f}"
        if x == max_value:
            return f"\\textbf{{{formatted_x}}}"
        elif x == second_max_value:
            return f"\\underline{{{formatted_x}}}"
        return formatted_x

    return formatter

def latex(name, df):
    formatters = {col: create_bold_underline_formatter(df[col]) for col in df.columns}
    l = df.to_latex(formatters=formatters)
    l = header + "\n".join(l.split("\n")[3:])
    with open(f"figures/{name}.tex", "w") as f:
        f.write(l)

for game in games:
    matches = complete_matches[game]
    params = complete_bootstrapped_params[game]
    game = shorter_names[game]

    n_matches = defaultdict(int)
    scores = defaultdict(int)
    for m in matches:
        agents = list(m.keys())[1:]
        n_matches[agents[0]] += 1
        n_matches[agents[1]] += 1
        scores[agents[0]] += m[agents[0]]
        scores[agents[1]] += m[agents[1]]


    ratings = params.mean(0)
    ratings_df.loc[:, game] = ratings
    for agent in players:
        scores_df.loc[agent, game] = scores[agent] / n_matches[agent] if n_matches[agent] > 0 else float("nan")

matches = complete_matches["all"]
n_matches = defaultdict(int)
scores = defaultdict(int)
for m in matches:
    agents = list(m.keys())[1:]
    n_matches[agents[0]] += 1
    n_matches[agents[1]] += 1
    scores[agents[0]] += m[agents[0]]
    scores[agents[1]] += m[agents[1]]

params = complete_bootstrapped_params["all"]
ratings = params.mean(0)
ratings_df.loc[:, "Overall"] = ratings
for agent in players:
    scores_df.loc[agent, "Overall"] = scores[agent] / n_matches[agent] if n_matches[agent] > 0 else float("nan")

latex("ratings_table", ratings_df)
latex("scores_table", scores_df)