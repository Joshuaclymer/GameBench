from dataclasses import dataclass, field
import random
from api.classes import Action, Agent, AvailableActions, Observation, Rules
import api.util as util
import openai
import math
from functools import partial
import re

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
# * maybe caching results? It's possible the agent will accurately predict
#   a future state, in which case it shouldn't recalculate rewards and all.

openai_client = openai.Client(
    api_key=util.load_json("credentials.json")["openai_api_key"]
)

context_templates = util.load_json("agents\context_templates.json")

def completion(context: list[dict[str, str]]) -> str:
    """Regular chat completion."""
    ret = (
        openai_client.chat.completions.create(
            model="gpt-3.5-turbo-1106", messages=context
        )
        .choices[0]
        .message.content
    )
    return ret


def probabilities(
    context: list[dict[str, str]], tokens: list[str] = ["yes", "no"], n: int = 2
) -> dict[str, float]:
    """Prompt for exactly one token, and return probabilities of each token
    in tokens."""
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

    def prior(token):
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


def make_context_builder() -> Callable:
    def context_builder(template, **kwargs):
        messages = context_templates["prefix"] + context_templates[template]
        return [
            {"role": ("user" if i & 1 == 0 else "assistant"), "content": message.format(**kwargs)}
            for i, message in enumerate(messages)
        ]

    return context_builder


@dataclass
class GameState:
    observation: str
    depth: int = 0
    actions: list[str] = None


@cache
def step(state: GameState, action: str, context_builder: Callable) -> GameState:
    prompt = context_builder(
        "state", observation=state.observation, action=action, others=state.others
    )
    new_state = completion(prompt)
    new_state = re.findall(r"<state>(.*)</state>", new_state, re.S)[0]
    return GameState(new_state, depth=state.depth + 1)


@cache
def win_probability(state: GameState, context_builder: Callable) -> float:
    prompt = context_builder("goal", observation=state.observation)
    goal = probabilities(prompt)["yes"]
    return goal


@cache
def is_terminal(state: GameState) -> bool:
    return state.depth >= DEPTH_LIMIT


@cache
def get_actions(state: GameState) -> list[str]:
    if state.actions:
        return state.actions

    prompt = build_context(
        "actions",
        observation=state.observation,
    )
    response = completion(prompt)
    response = re.findall(r"<actions>(.*)</actions>", response, re.S)[0]
    actions = response.strip().split("\n")
    return actions


@cache
def calculate_reward(
    state: GameState, goal_reached: float, intuition: float, self_eval: float
) -> float:
    goal_reward = 2 * goal_reached - 1
    return intuition + self_eval + goal_reward


@cache
def intuitions(state: GameState) -> dict[str, float]:
    prompt = self.context_builder(
        "action_select",
        observation=state.observation,
        actions="\n".join(state.actions),
    )
    ints = probabilities(prompt, action[0], len(state.actions))
    return ints


class ReasoningViaPlanning(Agent, WorldModel, SearchConfig):
    agent_type_id: str = "rap"
    transparent_reasoning: bool = False

    context_builder: Callable = None
    _init_state: GameState = None

    def take_action(
        self,
        rules: Rules,
        observation: Observation,
        available_actions: AvailableActions,
        show_state: bool,
    ) -> Action:
        self.context_builder = make_context_builder(rules)
        self._init_state = GameState(
            observation=observation.text,
            depth=0,
            actions=available_actions.predefined.keys(),
        )

    def init_state(self) -> GameState:
        if self.transparent_reasoning:
            print("RAP: Retrieving initial state")
        
        return self._init_state

    def step(
        self, state: GameState, action: str
    ) -> tuple[GameState, dict[str, float]]:
        next = step(state, action, self.context_builder)
        goal = win_probability(next, self.context_builder)
        info = {"goal_reached": goal}

        if self.transparent_reasoning:
            print(f"RAP: Stepping from\n{state.observation}\nwith action {action}. New state looks like\n{next.observation}")

        return next, info

    def is_terminal(self, state: GameWrapper.State) -> bool:
        term = is_terminal(state, self.context_builder)

        if self.transparent_reasoning:
            print(f"RAP: Determining if the follow state is terminal\n{state.observation}\nResult: {term}")

        return term

    def get_actions(self, state: GameWrapper.State) -> list[str]:
        actions = get_actions(state, self.context_builder)

        if self.transparent_reasoning:
            print(f"RAP: Retreiving actions for the following state:\n{state.observation}\nActions: {actions}")

        return actions

    def fast_reward(
        self, state: GameState, action: str
    ) -> tuple[float, dict[str, float]]:
        int = intuitions(state, self.context_builder)[action]
        sev = self_eval(state, action, self.context_builder)
        rew = calculate_reward(int, sev, goal_reached)

        if self.transparent_reasoning:
            print(f"RAP: Calculating fast reward for the following state:\n{state.observation}\nAction: {action}\nIntuition: {int}, Self-eval: {sev}, Reward: {reward}")

        return rew

    def reward(
        self,
        state: GameState,
        action: str,
        intuition: float,
        self_eval: float,
        goal_reached: float,
    ) -> tuple[float, dict[str, float]]:
        rew = calculate_reward(intuition, self_eval, goal_reached)
        info = {"intuition": intuition, "goal_reached": goal_reached}

        if self.transparent_reasoning:
            print(f"RAP: Calculating fast reward for the following state:\n{state.observation}\nAction: {action}\nIntuition: {int}, Self-eval: {sev}, Goal-reached: {goal_reached}, Reward: {reward}")

        return rew, info