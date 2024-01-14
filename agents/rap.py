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


def context_builder(template, **kwargs) -> list[dict[str, str]]:
    """Build a context from a template to be sent to OpenAI API

    Context templates are in context_templates.json. Each template is a list
    of messages, alternating between role: user and role: assistant messages.
    Fill-ins are indicated with curly brackets and a label. The fill-ins
    values are given in **kwargs.
    """
    format = partial(str.format, **kwargs)

    return [
        {"role": ("user" if i & 1 == 0 else "assistant"), "content": format(message)}
        for i, message in enumerate(context_templates[template])
    ]


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


def probability(context: list[dict[str, str]], token: str = "yes", n: int = 2) -> float:
    """Prompt for exactly one token, and return probability that the LLM
    returned 'token' out of 'n' token options.

    Todo: this needs to be changed to return probabilites of multiple tokens.
    """
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
    p_total = sum(math.exp(tlp.logprob) for tlp in top_logprobs)
    p = math.exp(
        next(
            (tlp.logprob for tlp in top_logprobs if tlp.token.lower() == token.lower()),
            -100,
        )
    )
    return p / p_total


@dataclass
class GameState:
    observation: str
    depth: int = 0
    actions: list[str] = field(default_factory=list)
    others: str = None


@dataclass
class ReasoningViaPlanning(Agent, WorldModel, SearchConfig):
    agent_type_id: str = "rap"
    reward_alpha: float = 0.5

    reasoner: Reasoner = None
    rules: Rules = None
    observation: Observation = None
    available_action: AvailableActions = None

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
        self.context_builder = partial(
            context_builder, title=rules.title, summary=rules.summary
        )
        self._init_state = GameState(
            observation=observation.text, actions=list(available_actions.predefined.keys())
        )

        try:
            action_id = self.reasoner(None).trace[1][0]
            return Action(action_id=action_id)
        except TypeError:
            raise "Likely: depth limit reached on MCTS with no terminal state reached."

    def init_state(self) -> GameState:
        return self._init_state

    def step(self, state: GameState, action: str) -> GameState:
        """Predict next state from action."""
        prompt = self.context_builder(
            "state", observation=state.observation, action=action, others=state.others
        )
        new_state = completion(prompt)
        new_state = re.findall(r"<state>(.*)</state>", new_state, re.S)[0]

        prompt = self.context_builder(
            "goal",
            observation=new_state,
        )
        goal = probability(prompt)
        return GameState(new_state, depth=state.depth + 1), {"goal_reached": goal}

    def is_terminal(self, state: GameState) -> bool:
        """Terminal calculation

        If MCTS doesn't reach a terminal state, it won't return any information
        about the best path. Strategies to overcome:
        * Increase depth (maybe dynamically) for MCTS
        * Declare states terminal if they are at the end MCTS depth
        * Modify MCTS to return best trace even if it's not terminal
        * Use different MCTS output_strategy that will always return a trace

        Future: maybe ask agent if the state is terminal, then return True
        with probability that agent says yes.
        """
        return state.depth > 1

    def get_actions(self, state: GameState) -> list[str]:
        """Predict actions from current state. And also about others' actions
        because it's convenient to do that here."""
        prompt = self.context_builder("others", observation=state.observation)
        others = completion(prompt)
        state.others = others

        if state.actions:
            return state.actions

        prompt = self.context_builder(
            "actions",
            observation=state.observation,
        )
        response = completion(prompt)
        response = re.findall(r"<actions>(.*)</actions>", response, re.S)[0]
        actions = response.strip().split("\n")
        state.actions = actions
        return actions

    def calculate_reward(
        self,
        intuition: float,
        self_eval: float,
        goal_reached: float = 0.5,
    ) -> float:
        """Calculates reward of taking action."""
        goal_reward = 2 * goal_reached - 1
        reward = (intuition + self_eval) * self.reward_alpha + goal_reward * (
            1 - self.reward_alpha
        )
        return reward

    def fast_reward(
        self, state: GameState, action: str
    ) -> tuple[float, dict[str, float]]:
        """Get probability of LLM selection action + probability of saying it's
        a good choice.

        Todo: move intuition calculation out of here. The prompt does not
        depend on the action, only the state, so calling once per action is
        wasteful (and leads to probabilites that don't sum to 1).
        """
        prompt = self.context_builder(
            "action_select",
            observation=state.observation,
            actions="\n".join(state.actions),
        )
        intuition = probability(prompt, action[0], len(state.actions))

        prompt = self.context_builder(
            "self_eval", observation=state.observation, action=f"{action}"
        )
        self_eval = probability(prompt)

        return self.calculate_reward(intuition, self_eval), {
            "intuition": intuition,
            "self_eval": self_eval,
        }

    def reward(
        self,
        state: GameState,
        action: str,
        intuition: float,
        self_eval: float,
        goal_reached: float,
    ) -> tuple[float, dict[str, float]]:
        return (
            self.calculate_reward(intuition, self_eval, goal_reached),
            {"intuition": intuition, "goal_reached": goal_reached},
        )