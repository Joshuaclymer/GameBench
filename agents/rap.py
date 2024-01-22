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
# * add support for openeded actions
# * add support for image observations
# * maybe caching results between calls to take_action? It's possible the agent
#   will accurately predict a future state, in which case it shouldn't
#   recalculate rewards and all.
# * add support for looking up more info about the rules.

DEPTH_LIMIT = 2

"""A context, based on OpenAI API"""
ContextType = NewType("Context", list[dict[str, str]])

"""Returns the next message in a context."""
CompletionsFunction = NewType("CompletionsFunction", Callable[ContextType, str])

"""Determines the probability of tokens appearing next after a context."""
ProbabilitiesFunction = NewType(
    "ProbabilitiesFunction",
    Callable[[ContextType, list[str], int], dict[str, float]],
)

"""A function that builds a context from a context template and substituions."""
ContextBuilder = NewType("ContextBuilder", Callable[[str, str], ContextType])


def context_builder_factory(rules: Rules) -> Callable[[str, str], ContextType]:
    """Makes a context builder with substitutions for game rules."""
    context_templates = util.load_json("agents\context_templates.json")

    def context_builder(template: str, **kwargs: str) -> ContextType:
        messages = context_templates["prefix"] + context_templates[template]

        if rules.additional_details:
            topics = context_templates["additional_topics"]
            topics = topics.format(topics=", ".join(list(rules.additional_details)) if rules.additional_details else "none")
        else:
            topics = ""
        
        return [
            {
                "role": ("user" if i & 1 == 0 else "assistant"),
                "content": message.format(
                    title=rules.title,
                    summary=rules.summary,
                    topics=topics,
                    **kwargs,
                ),
            }
            for i, message in enumerate(messages)
        ]

    return context_builder


def lookup_monad(completions: CompletionsFunction, rules: Rules) -> CompletionsFunction:
    """Repeatedly asks for a completion until the response is not asking
    for a rules description."""
    rules_lookup_re = re.compile(r"rule\((\w+)\)")

    def new_completions(context) -> str:
        def request(ctx):
            ret = completions(ctx)

            if re.match(rules_lookup_re, ret):
                rule = re.findall(rules_lookup_re, ret)[0]
                if rule in rules.additional_details:
                    context.append({"role": "assistant", "content": ret})
                    context.append(
                        {"role": "user", "content": rules.additional_details[rule]}
                    )

                    return request(ctx)

            return ret

        return request(context)

    return new_completions


def cot_monad(completions: CompletionsFunction) -> CompletionsFunction:
    """Asks for CoT."""
    pass


def expose_openai_api() -> tuple[CompletionsFunction, ProbabilitiesFunction]:
    """Returns a CompletionsFunction and a ProbabilitiesFunction that
    interacts with GPT3.5."""

    openai_client = openai.Client(
        api_key=util.load_json("credentials.json")["openai_api_key"]
    )

    def completions(context: ContextType) -> str:
        return (
            openai_client.chat.completions.create(
                model="gpt-3.5-turbo-1106", messages=context
            )
            .choices[0]
            .message.content
        )

    def probabilities(
        context: ContextType, tokens: list[str] = ["yes", "no"], n: int = 2
    ) -> dict[str, float]:
        context = context_builder(template, **kwargs)
        n = min(n, 5) # OpenAI doesn't allow more than 5

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

        def unnorm_prob(token: str):
            """Return the unnormalized probability of a token."""
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
        return {token: unnorm_prob(token) / p_total for token in tokens}

    return completions, probabilities


def random_replies() -> tuple[CompletionsFunction, ProbabilitiesFunction]:
    """Returns completions and probabilities that return random responses.
    Useful for debugging."""

    def randstr() -> str:
        """There is a probability that this returns the same string in different
        calls which could make debugging confusing."""
        return "".join(
            random.choices("abcdefghijklmnopqrstuvwxyz", k=random.randint(5, 10))
        )

    def completions(context: ContextType) -> str:
        return f"<state>{randstr()}</state><actions>{randstr()}\n{randstr()}\n{randstr()}</actions>"

    def probabilities(
        context: ContextType, tokens: list[str, str] = ["yes", "no"], n: int = 0
    ) -> dict[str, float]:
        return {token: random.random() for token in tokens}

    return completions, probabilities


def human_interaction() -> tuple[CompletionsFunction, ProbabilitiesFunction]:
    """Completions that uses input() or random if nothing is supplied,
    probabilities that is random."""
    r_completions, probabilities = random_replies()

    def completions(context: ContextType) -> str:
        c = input("\n".join([m["content"] for m in context]) + "\n>>> ")

        if not c:
            c = r_completions(context)
            print(c)
            return c

        return c

    return completions, probabilities


@dataclass(frozen=True)
class GameState:
    """Immutable wrapper for observations, essentially."""

    observation: str
    depth: int = 0
    actions: tuple[str] = None


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
        return GameState(None, depth=DEPTH_LIMIT),


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


@dataclass
class ReasoningViaPlanning(Agent, WorldModel, SearchConfig):
    """Inherents Agent from api.classes, and WorldModel and SearchConfig
    from the llm-agents library."""

    agent_type_id: str = "rap"
    transparent_reasoning: bool = False
    agent_type: int = 0  # 0 = random replies, 1 = human interaction, 2 = openai

    context_builder: Callable[[str, str], ContextType] = None
    completions: CompletionsFunction = None
    probabilities: ProbabilitiesFunction = None
    _init_state: GameState = None

    def __post_init__(self):
        """MCTS only needs to be instantiated once."""
        mcts = MCTS(depth_limit=DEPTH_LIMIT)
        self.reasoner = Reasoner(world_model=self, search_config=self, search_algo=mcts)

    def log(self, s):
        """print() to console only with transparent reasoning."""
        if self.transparent_reasoning:
            print("RAP: " + s)

    def take_action(
        self,
        rules: Rules,
        observation: Observation,
        available_actions: AvailableActions,
        show_state: bool,
    ) -> Action:
        self.context_builder = context_builder_factory(rules)
        self._completions, self._probabilities = [
            random_replies(),
            human_interaction(),
            expose_openai_api(),
        ][self.agent_type]

        # Maybe make monad composition an agent kwarg.
        self._completions = lookup_monad(self._completions, rules)

        self.completions = (self.context_builder, self._completions)
        self.probabilities = (self.context_builder, self._probabilities)

        self.log(
            "Warning: using "
            + ["random replies", "human interaction", "GPT3.5"][self.agent_type]
        )

        self._init_state = GameState(
            observation=observation.text,
            depth=0,
            actions=tuple(available_actions.predefined.keys()),
        )

        #try:
        action_id = self.reasoner(None).trace[1][0]

        self.log(
            f"Recieved the following observation:\n{observation.text}\nAvailable actions: {available_actions}.\nChoosing the action: {action_id}"
        )

        return Action(action_id=action_id)
        #except Exception as e:
        #    self.log(f"MCTS threw an error: {e}. Returning random action.")
#
#            actions = list(available_actions.predefined.keys())
#            return Action(action_id=random.choice(actions))

    def init_state(self) -> GameState:
        """From WorldModel; called by MCTS."""
        self.log("Retrieving initial state")

        return self._init_state

    def step(self, state: GameState, action: str) -> tuple[GameState, dict[str, float]]:
        """From WorldModel; called by MCTS."""
        oth = others_actions(state, *self.completions)
        nxt = step(state, action, oth, *self.completions)
        win = win_probability(nxt, *self.probabilities)
        info = {"win_probability": win}

        self.log(
            f"Stepping with state/action:\n{state.observation}\nAction: {action}. New state looks like\n{nxt.observation}"
        )

        return nxt, info

    def is_terminal(self, state: GameState) -> bool:
        """From WorldModel; called by MCTS."""
        term = is_terminal(state)

        self.log(
            f"Determining if the follow state is terminal\n{state.observation}\nResult: {term}"
        )

        return term

    def get_actions(self, state: GameState) -> list[str]:
        """From WorldModel; called by MCTS."""
        actions = get_actions(state, *self.completions)

        self.log(
            f"Retrieving actions for the following state:\n{state.observation}\nActions: {actions}"
        )

        return actions

    def fast_reward(
        self, state: GameState, action: str
    ) -> tuple[float, dict[str, float]]:
        """From SearchConfig; called by MCTS."""
        actions = get_actions(state, *self.completions)
        int = intuitions(state, actions, *self.probabilities)
        int = int[action]
        sev = self_eval(state, action, *self.probabilities)
        rew = calculate_reward(int, sev)
        info = {"intuition": int, "self_eval": sev}

        self.log(
            f"Calculating fast reward for the following state/action:\n{state.observation}\nAction: {action}\nIntuition: {int}, Self-eval: {sev}, Reward: {rew}"
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
        """From SearchConfig, called by MCTS."""
        rew = calculate_reward(intuition, self_eval, win_probability)
        info = {"intuition": intuition, "win_probability": win_probability}

        self.log(
            f"Calculating regular reward for the following state/action:\n{state.observation}\nAction: {action}\nIntuition: {intuition}, Self-eval: {self_eval}, Win-probability: {win_probability}, Reward: {rew}"
        )

        return rew, info
