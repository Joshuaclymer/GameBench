from dataclasses import dataclass, field
import random
from api.classes import Action, Agent, AvailableActions, Observation, Rules
import api.util as util
from agents.reasoners.base import Reasoner, SearchConfig, WorldModel
from agents.reasoners.algorithm import MCTS
import openai
import math
from functools import partial

# To-do:
# * add support for openeded actions
# * add support for image observations
# * make side-by-side comparison between RAP and LATS, and see how you might
#   borrow ReACT. Or implement LATS separately (ask Josh first)
#   * we want CoT reasoning and ability for agent to lookup rules
# * maybe use unique prompts for emphasizing the unknown of what other
#   players are going to do

openai_client = openai.Client(
    api_key=util.load_json("credentials.json")["openai_api_key"]
)

context_templates = util.load_json("agents\prompt_templates.json")


def context(template, **kwargs) -> list[dict[str, str]]:
    format = partial(str.format, **kwargs)

    return [
        {"role": ("user" if i & 1 == 0 else "assistant"), "content": format(message)}
        for i, message in enumerate(context_templates[template])
    ]


def completion(context: list[dict[str, str]]) -> str:
    """Regular chat completion."""
    for msg in context:
        print(msg["role"].upper(), "::", msg["content"])
    ret = (
        openai_client.chat.completions.create(
            model="gpt-3.5-turbo-1106", messages=context
        )
        .choices[0]
        .message.content
    )
    print(ret)
    return ret


def probability(context: list[dict[str, str]], token: str = "yes", n: int = 2) -> float:
    """Prompt for exactly one token, and return probability that the LLM
    returned 'token' out of 'n' token options."""
    for msg in context:
        print(msg["role"].upper(), "::", msg["content"])
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
    print(p / p_total)
    return p / p_total


@dataclass
class GameState:
    """Wrapper for game state. 'state' is the observation."""

    state: str
    myturn: bool = True
    depth: int = 0
    actions: list[str] = field(default_factory=list)


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

    @property
    def prefix(self) -> list[dict[str, str]]:
        """A prompt prefix with examples showing how to reasond and respond.

        Future:
        * keep running list of past observations and available_actions to
        generate more diversity of prefixes
        * keep track of token count and maybe drop some example interactions
        if we're hitting the context length
        * maybe split the prefix into system, user, and assistant messages
        if it improves performance
        """
        return context(
            "prefix",
            title=self.rules.title,
            summary=self.rules.summary,
            observation=self.observation.text,
            win=random.choice(["yes", "no"]),
            actions="\n".join(
                f"{action}: {description}"
                for action, description in self.available_actions.predefined.items()
            ),
            action=random.choice(list(self.available_actions.predefined.keys())),
            eval=random.choice(["yes", "no"]),
        )

    def take_action(
        self,
        rules: Rules,
        observation: Observation,
        available_actions: AvailableActions,
        show_state: bool,
    ) -> Action:
        self.rules = rules
        self.observation = observation
        self.available_actions = available_actions
        try:
            action_id = self.reasoner(None).trace[1][0]
            #return Action(action_id=action_id)
        except TypeError:
            raise "Depth limit reached on MCTS with no terminal state reached."

    def init_state(self) -> GameState:
        return GameState(
            self.observation.text,
            myturn=True,
            depth=0,
            actions=self.available_actions.predefined.keys(),
        )

    def step(self, state: GameState, action: str) -> GameState:
        """Predict next state from action."""
        prompt = self.prefix + context(
            "state",
            observation=state.state,
            who="You" if state.myturn else "Other players",
            who2="Other players" if state.myturn else "You",
            action=action,
        )
        new_state = completion(prompt)

        prompt = self.prefix + context(
            "goal",
            who="you" if not state.myturn else "other players",
            observation=new_state,
        )
        goal = probability(prompt)
        return GameState(new_state, not state.myturn, state.depth + 1), {
            "goal_reached": goal
        }

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
        """Predict actions from current state."""
        if state.actions:
            return state.actions

        prompt = self.prefix + context(
            "actions",
            observation=state.state,
            who="Your" if state.myturn else "Other players'",
        )
        response = completion(prompt)
        actions = [r.split(":")[0] for r in response.split("\n")]
        state.actions = actions
        return actions

    def calculate_reward(
        self,
        state: GameState,
        intuition: float,
        self_eval: float,
        goal_reached: float = 0.5,
    ) -> float:
        """Calculates reward of taking action.

        goal_reached is always calculated from the player's own perspective
        ("will YOU win"), so we map it from [0, 1] to [-1, 1] to mean that low
        probability of winning == high probability of others' winning.
        """
        goal_reward = 2 * goal_reached - 1
        flip = 1 if state.myturn else -1
        reward = (intuition + self_eval) * self.reward_alpha + goal_reward * (
            1 - self.reward_alpha
        )
        return flip * reward

    def fast_reward(
        self, state: GameState, action: str
    ) -> tuple[float, dict[str, float]]:
        """Get probability of LLM selection action + probability of saying it's
        a good choice."""
        prompt = self.prefix + context(
            "action_select",
            title=self.rules.title,
            summary=self.rules.summary,
            observation=state.state,
            actions="\n".join(
                f"{idx} {action}" for idx, action in enumerate(state.actions)
            ),
            who="you" if state.myturn else "other players",
        )
        idx = next(i for i, a in enumerate(state.actions) if action == a)
        intuition = probability(prompt, str(idx), len(state.actions))

        prompt = self.prefix + context(
            "self_eval",
            title=self.rules.title,
            summary=self.rules.summary,
            observation=state.state,
            action=f"{action}",
            who="you" if state.myturn else "other players",
        )
        self_eval = probability(prompt)

        return self.calculate_reward(state, intuition, self_eval), {
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
            self.calculate_reward(state, intuition, self_eval, goal_reached),
            {"intuition": intuition, "goal_reached": goal_reached},
        )
