from dataclasses import dataclass, field
import random
from api.classes import Action, Agent, AvailableActions, Observation, Rules
import api.util as util
from agents.reasoners.base import Reasoner, SearchConfig, WorldModel
from agents.reasoners.algorithm import MCTS
import openai

# todo:
# - make prompt manager probably
# - generate examples from gameplay to show as prefixes in prompts
# - include probabilities of position being terminal and prob of it being winning in reward, maybe
# - include probabilitiy of position being terminal in is_terminal maybe

openai_client = openai.Client(api_key=util.load_json("credentials.json")["openai_api_key"])

@dataclass
class GameState:
    state: str
    myturn: bool = True
    depth: int = 0
    actions: list[str] = field(default_factory=list)

def gpt(prompt):
    return openai_client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "You are trying to win a game."},
            {"role": "user", "content": prompt}
        ]
    ).choices[0].message.content

def probability(prompt, token, n):
    top_logprobs = openai_client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "system", "content": "You are trying to win a game."},
            {"role": "user", "content": prompt}
        ],
        logprobs=True,
        top_logprobs=n,
        max_tokens=1
    ).logprobs.content[0].top_logprobs
    p_total = sum(math.exp(tlp.logprob) for tlp in top_logprobs)
    p = math.exp(next((tlp.logprob for tlp in top_logprobs if tlp.token == token), -100))
    return p / p_total

actions_template = """You are playing a game called {title}.
The rules are as follows: {summary}.
Your current observation of the game state is
{observation}
{who} available actions are as follows:
"""

state_template = """You are playing a game called {title}.
The rules are as follows: {summary}.
Your current observation of the game state is
{observation}
{who} are taking the following action
{action}
As a result, the new game state is as follows:
"""

action_select_template = """You are playing a game called {title}.
The rules are as follows: {summary}.
Your current observation of the game state is
{observation}
{who} available actions are as follows:
{actions}
Choose an action by writing the exactly number at the start of the line corresponding to the action you think {who} will take.
"""

self_eval_template = """You are playing a game called {title}.
The rules are as follows: {summary}.
Your current observation of the game state is
{observation}
{who} are taking the following action
{action}
Say exactly either good or bad if you think this is a good or a bad move.
"""

@dataclass
class ReasoningViaPlanning(Agent, WorldModel, SearchConfig):
    agent_type_id: str = "rap"
    reward_alpha: float = 0.5
    goal_reward_default: float = 0.
    goal_reached_reward: float = 100

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
        self.rules = rules
        self.observation = observation
        self.available_actions = available_actions
        try:
            action_id = self.reasoner(None).trace[1][0]
            return Action(action_id=action_id)
        except TypeError:
            raise "Depth limit reached on MCTS with no terminal state reached."
            # Options: try again at greater depth, change output_strategy,
            # or we modify the MCTS code to handle this situation better
            # (why does it throw everything out??)

    def init_state(self) -> GameState:
        return GameState(self.observation.text, True, 0, actions=self.available_actions.predefined.keys())

    def step(self, state: GameState, action: str) -> GameState:
        """Predict next state from action."""
        prompt = state_template.format(
            title=self.rules.title,
            summary=self.rules.summary,
            observation=state.state,
            who="You" if state.myturn else "Other players",
            action=action
        )
        response = gpt(prompt)
        return GameState(response, not state.myturn, state.depth + 1), {}

    def is_terminal(self, state: GameState) -> bool:
        """Temporary terminal calculation. Maybe in the future ask LLM if the
        game is over."""
        return state.depth > 4

    def get_actions(self, state: GameState) -> list[str]:
        """Prediction actions from current state."""
        if state.actions:
            return state.actions

        prompt = actions_template.format(
            title=self.rules.title,
            summary=self.rules.summary,
            observation=state.state,
            who="Your" if state.myturn else "Other players'"
        )
        response = gpt(prompt)
        actions = [r.split(":")[0] for r in response.split("\n")]
        state.actions = actions
        return actions

    def calculate_reward(self, state: GameState, intuition: float, self_eval: float) -> float:
        """Calculates reward of taking action."""
        goal_reward = self.goal_reward_default
        flip = 1 if state.myturn else -1
        reward = (intuition + self_eval) * self.reward_alpha + goal_reward * (1 - self.reward_alpha)
        return flip * reward

    def fast_reward(self, state: GameState, action: str) -> tuple[float, dict[str, float]]:
        """Get probability of LLM selection action + probability of saying it's
        a good choice."""
        prompt = action_select_template.format(
            title=self.rules.title,
            summary=self.rules.summary,
            observation=state.state,
            actions="\n".join(f"{idx} {action}" for idx, action in enumerate(state.actions)),
            who="you" if state.myturn else "other players"
        )
        idx = next(i for i, a in enumerate(state.actions) if action == a)
        intuition = probability(prompt, idx, len(state.actions))

        prompt = self_eval_template.format(
            title=self.rules.title,
            summary=self.rules.summary,
            observation=state.state,
            action=f"{action}",
            who="you" if state.myturn else "other players"
        )
        self_eval = probability(prompt, "good", 2)

        return self.calculate_reward(state, intuition, self_eval), {"intuition": intuition, "self_eval": self_eval}

    def reward(self, state: GameState, action: str, intuition:float=None, self_eval:float=None) -> tuple[float, dict[str, float]]:
        assert intuition is not None
        assert self_eval is not None
        return (
            self.calculate_reward(state, intuition, self_eval),
            {"intuition": intuition},
        )