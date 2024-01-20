from dataclasses import dataclass, field
import random
from api.classes import Action, Agent, AvailableActions, Observation, Rules
import api.util as util
import openai
import math
from functools import cache
import re
from typing import NewType, Callable

# These dependencies come from: https://github.com/Ber666/llm-reasoners/tree/main/reasoners
from agents.reasoners.base import Reasoner, SearchConfig, WorldModel
from agents.reasoners.algorithm import MCTS

# To-do:
# * move intuition calculation elsewhere; only needs to be calculated once
#   per state, but is currently called once per action.
# * likely could use a refactor
# * add support for openeded actions
# * add support for image observations
# * make side-by-side comparison between RAP and LATS, and see how you might
#   borrow ReACT. Or implement LATS separately (ask Josh first)
#   * we want CoT reasoning and ability for agent to lookup rules
# * maybe caching results between calls to take_action? It's possible the agent
#   will accurately predict a future state, in which case it shouldn't
#   recalculate rewards and all.

# Todo: tell MCTS to go to this depth
DEPTH_LIMIT = 2

"""A context, based on OpenAI API"""
ContextType = NewType("Context", list[dict[str, str]])

"""Returns the next message in a context."""
CompletionsFunction = NewType(
    "CompletionsFunction", Callable[[str, dict[str, str]], str]
)

"""Determines the probability of tokens appearing next after a context."""
ProbabilitiesFunction = NewType(
    "ProbabilitiesFunction",
    Callable[[str, list[str], int, dict[str, str]], dict[str, float]],
)


def random_replies() -> tuple[CompletionsFunction, ProbabilitiesFunction]:
    """Returns completions and probabilities that return random responses.
    Useful for debugging."""

    def randstr():
        """There is a probability that this returns the same string in different
        calls which could make debugging confusing."""
        return "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=random.randint(5, 10)))

    def completions(template: str, **kwargs) -> str:
        return f"<state>{randstr()}</state><actions>{randstr()}</actions>"

    def probabilities(
        template: str, tokens: list[str, str] = ["yes", "no"], n: int = 0, **kwargs
    ) -> dict[str, float]:
        return {token: random.random() for token in tokens}

    return completions, probabilities


def expose_openai_api(
    rules: Rules,
) -> tuple[CompletionsFunction, ProbabilitiesFunction]:
    """Returns a CompletionsFunction and a ProbabilitiesFunction that
    interacts with GPT3.5."""

    openai_client = openai.Client(
        api_key=util.load_json("credentials.json")["openai_api_key"]
    )
    context_templates = util.load_json("agents\context_templates.json")

    def context_builder(template: str, **kwargs) -> ContextType:
        messages = context_templates["prefix"] + context_templates[template]
        return [
            {
                "role": ("user" if i & 1 == 0 else "assistant"),
                "content": message.format(
                    title=rules.title, summary=rules.summary, **kwargs
                ),
            }
            for i, message in enumerate(messages)
        ]

    def completion(template: str, **kwargs):
        context = context_builder(template, **kwargs)
        ret = (
            openai_client.chat.completions.create(
                model="gpt-3.5-turbo-1106", messages=context
            )
            .choices[0]
            .message.content
        )
        return ret

    def probabilities(
        template: str, tokens: list[str] = ["yes", "no"], n: int = 2, **kwargs
    ) -> dict[str, float]:
        context = context_builder(template, **kwargs)
        n = min(n, 5)  # OpenAI doesn't allow more than 5

        top_logprobs = (
            openai_client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=context,
                logprobs=True,
                top_logprobs=n,
                max_tokens=1,
            )
            .choices[0]
            .logprobs.content[0]
            .top_logprobs
        )

        def prior(token: str):
            return math.exp(
                next(
                    (
                        tlp.logprob
                        for tlp in top_logprobs
                        if tlp.token.lower() == token.lower()
                    ),
                    -100,
                )
            )

        p_total = sum(math.exp(tlp.logprob) for tlp in top_logprobs)
        return {token: prior(token) / p_total for token in tokens}

    return completion, probabilities


@dataclass(frozen=True)
class GameState:
    observation: str
    depth: int = 0
    actions: tuple[str] = None


@cache
def step(state: GameState, action: str, others: str, completions: CompletionsFunction) -> GameState:
    new_state = completions(
        "state", observation=state.observation, action=action, others=others
    )
    new_state = re.findall(r"<state>(.*)</state>", new_state, re.S)[0]
    return GameState(new_state, depth=state.depth + 1)


@cache
def win_probability(state: GameState, probabilities: ProbabilitiesFunction) -> float:
    winp = probabilities("goal", observation=state.observation)["yes"]
    return winp


@cache
def is_terminal(state: GameState) -> bool:
    return state.depth >= DEPTH_LIMIT


@cache
def get_actions(state: GameState, completions: CompletionsFunction) -> tuple[str]:
    if state.actions:
        return state.actions

    response = completions("actions", observation=state.observation)
    response = re.findall(r"<actions>(.*)</actions>", response, re.S)[0]
    actions = response.strip().split("\n")
    return tuple(actions)

@cache
def others_actions(state: GameState, completions: CompletionsFunction) -> str:
    others = completions("others", observation=state.observation)
    return others


@cache
def calculate_reward(
    intuition: float, self_eval: float, win_probability: float = 0.5
) -> float:
    win_probability = 2 * win_probability - 1
    return intuition + self_eval + win_probability


@cache
def intuitions(
    state: GameState, actions: tuple[str], probabilities: ProbabilitiesFunction
) -> dict[str, float]:
    ints = probabilities(
        "action_select",
        actions,
        len(actions),
        observation=state.observation,
        actions="\n".join(actions),
    )
    return ints


@cache
def self_eval(state: GameState, action: str, probabilities: ProbabilitiesFunction):
    val = probabilities("self_eval", observation=state.observation, action=f"{action}")
    val = val["yes"]
    return val


@dataclass
class ReasoningViaPlanning(Agent, WorldModel, SearchConfig):
    agent_type_id: str = "rap"
    transparent_reasoning: bool = False
    use_openai: bool = False

    completions: CompletionsFunction = None
    probabilities: ProbabilitiesFunction = None
    _init_state: GameState = None

    def __post_init__(self):
        mcts = MCTS()
        self.reasoner = Reasoner(world_model=self, search_config=self, search_algo=mcts)

    def take_action(
        self,
        rules: Rules,
        observation: Observation,
        available_actions: AvailableActions,
        show_state: bool,
    ) -> Action:
        self.completions, self.probabilities = (
            expose_openai_api(rules) if self.use_openai else random_replies()
        )

        self._init_state = GameState(
            observation=observation.text,
            depth=0,
            actions=tuple(available_actions.predefined.keys()),
        )

        # try:
        action_id = self.reasoner(None).trace[1][0]

        if self.transparent_reasoning:
            print(
                f"RAP: Recieved the following observation:\n{observation.text}\nAvailable actions: {available_actions}.\nChoosing the action: {action_id}"
            )

        return Action(action_id=action_id)
        """except Exception as e:
            if self.transparent_reasoning:
                print(
                    f"RAP: MCTS threw an error: {e}. Likely, the internal depth limit was reached and no terminal state was found."
                )

            actions = list(available_actions.predefined.keys())
            return Action(action_id=random.choice(actions))"""

    def init_state(self) -> GameState:
        if self.transparent_reasoning:
            print("RAP: Retrieving initial state")

        return self._init_state

    def step(self, state: GameState, action: str) -> tuple[GameState, dict[str, float]]:
        oth = others_actions(state, self.completions)
        nxt = step(state, action, oth, self.completions)
        winp = win_probability(nxt, self.probabilities)
        info = {"win_probability": winp}

        if self.transparent_reasoning:
            print(
                f"RAP: Stepping from\n{state.observation}\nwith action {action}. New state looks like\n{nxt.observation}"
            )

        return nxt, info

    def is_terminal(self, state: GameState) -> bool:
        term = is_terminal(state)

        if self.transparent_reasoning:
            print(
                f"RAP: Determining if the follow state is terminal\n{state.observation}\nResult: {term}"
            )

        return term

    def get_actions(self, state: GameState) -> list[str]:
        actions = get_actions(state, self.completions)

        if self.transparent_reasoning:
            print(
                f"RAP: Retreiving actions for the following state:\n{state.observation}\nActions: {actions}"
            )

        return actions

    def fast_reward(
        self, state: GameState, action: str
    ) -> tuple[float, dict[str, float]]:
        actions = get_actions(state, self.completions)
        int = intuitions(state, actions, self.probabilities)[action]
        sev = self_eval(state, action, self.probabilities)
        rew = calculate_reward(int, sev)
        info = {"intuition": int, "self_eval": sev}

        if self.transparent_reasoning:
            print(
                f"RAP: Calculating fast reward for the following state:\n{state.observation}\nAction: {action}\nIntuition: {int}, Self-eval: {sev}, Reward: {rew}"
            )

        return rew, info

    def reward(
        self,
        state: GameState,
        action: str,
        intuition: float,
        self_eval: float,
        win_probability: float,
    ) -> tuple[float, dict[str, float]]:
        rew = calculate_reward(intuition, self_eval, win_probability)
        info = {"intuition": intuition, "win_probability": win_probability}

        if self.transparent_reasoning:
            print(
                f"RAP: Calculating fast reward for the following state:\n{state.observation}\nAction: {action}\nIntuition: {intuition}, Self-eval: {self_eval}, Win-probability: {win_probability}, Reward: {rew}"
            )

        return rew, info
