from functools import cache
from .definitions import *
import math
from api.classes import Action
import re

import sys

@cache
def step(
    state: GameState,
    action: Action,
    others: str,
    context_builder: ContextBuilder,
    completions: CompletionsFunction,
) -> GameState:
    """Determines the next state after an action + other players' actions."""
    context = context_builder(
        "state", observation=state.observation, action=action, others=others
    )
    c = completions(context)

    new_state = re.findall(r"<state>(.*)</state>", c, re.S)[0]
    return GameState(new_state, depth=state.depth + 1)


@cache
def win_probability(
    state: GameState,
    context_builder: ContextBuilder,
    probabilities: ProbabilitiesFunction,
) -> float:
    """Determines probability of winning in the future from current state."""
    context = context_builder("goal", observation=state.observation)
    ps = probabilities(context)
    return ps["yes"]


@cache
def is_terminal(state: GameState) -> bool:
    """A terminal state must be reached or MCTS will throw out its results."""
    return state.depth >= DEPTH_LIMIT


@cache
def get_actions(
    state: GameState, context_builder: ContextBuilder, completions: CompletionsFunction
) -> tuple[Action]:
    """Determine available actions in a state."""
    # The first state will have preset actions.
    if state.actions:
        return state.actions

    print("\n\n\n\n")

    context = context_builder("actions", observation=state.observation)
    c = completions(context)
    c = re.findall(r"<actions>(.*)</actions>", c, re.S)[0]
    actions = []
    for action in c.strip().split("\n"):
        action = Action(action_id=action)
        actions.append(action)
    return tuple(actions)


@cache
def others_actions(
    state: GameState, context_builder: ContextBuilder, completions: CompletionsFunction
) -> str:
    """Determines other players' actions in a state.

    Notably, GPT4 seems to incorporate others' actions even when this function
    fails parse anything (tested in tic-tac-toe)
    """
    context = context_builder("others", observation=state.observation)
    c = completions(context)
    c = re.findall(r"<others>(.*)</others>", c, re.S)[0]
    return c


@cache
def calculate_reward(
    intuition: float, self_eval: float, win_probability: float = 0.5
) -> float:
    """Reward formula, basically copied from RAP paper."""
    win_probability = 2 * win_probability - 1
    return intuition + self_eval + win_probability


@cache
def intuitions(
    state: GameState,
    actions: tuple[Action],
    context_builder: ContextBuilder,
    probabilities: ProbabilitiesFunction,
) -> dict[str, float]:
    """Determines probabilities of agent selecting each action in a state."""
    context = context_builder(
        "action_select",
        observation=state.observation,
        actions="\n".join(f"{i}. {a}" for i, a in enumerate(actions)),
    )
    ps = probabilities(context, range(len(actions)))
    return ps


@cache
def self_eval(
    state: GameState,
    action: str,
    context_builder: ContextBuilder,
    probabilities: ProbabilitiesFunction,
):
    """Determines probability agent says action is good."""
    context = context_builder("self_eval", observation=state.observation, action=action)
    ps = probabilities(context)
    return ps["yes"]
