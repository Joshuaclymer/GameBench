from functools import cache
from .definitions import *
import math

@cache
def step(
    state: GameState,
    action: str,
    others: str,
    context_builder: ContextBuilder,
    completions: CompletionsFunction,
) -> GameState:
    """Determines the next state after an action + other players' actions."""
    context = context_builder(
        "state", observation=state.observation, action=action, others=others
    )
    c = completions(context)

    try:
        new_state = re.findall(r"<state>(.*)</state>", c, re.S)[0]
        return GameState(new_state, depth=state.depth + 1)
    except:
        # What to do in this position?
        return GameState(None, depth=DEPTH_LIMIT)


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
) -> tuple[str]:
    """Determine available actions in a state."""
    if state.actions:
        return state.actions

    context = context_builder("actions", observation=state.observation)
    c = completions(context)
    try:
        c = re.findall(r"<actions>(.*)</actions>", c, re.S)[0]
        actions = c.strip().split("\n")
        return tuple(actions)
    except:
        return tuple()


@cache
def others_actions(
    state: GameState, context_builder: ContextBuilder, completions: CompletionsFunction
) -> str:
    """Determines other players' actions in a state."""
    context = context_builder("others", observation=state.observation)
    c = completions(context)
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
    actions: tuple[str],
    context_builder: ContextBuilder,
    probabilities: ProbabilitiesFunction,
) -> dict[str, float]:
    """Determines probabilities of agent selecting each action in a state."""
    context = context_builder(
        "action_select",
        observation=state.observation,
        actions="\n".join(actions),
    )
    ps = probabilities(context, actions, len(actions))
    return ps

@cache
def self_eval(
    state: GameState,
    action: str,
    context_builder: ContextBuilder,
    probabilities: ProbabilitiesFunction,
):
    """Determines probability agent says action is good."""
    context = context_builder(
        "self_eval", observation=state.observation, action=f"{action}"
    )
    ps = probabilities(context)
    return ps["yes"]