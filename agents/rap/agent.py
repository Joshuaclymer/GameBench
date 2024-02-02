from dataclasses import dataclass, field
from api.classes import Action, Agent, AvailableActions, Observation, Rules
import re
from .reasoners.base import Reasoner, SearchConfig, WorldModel
from .reasoners.algorithm import MCTS
from .chat import *
from .monads import *
from .func import *
from .definitions import *


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
            random_api(),
            human_api(),
            openai_api(),
        ][self.agent_type]

        self._completions = lookup_monad(self._completions, rules)

        if self.transparent_reasoning:
            self._completions = log_monad(self._completions)
            self._probabilities = log_monad(self._probabilities)

        self.completions = (self.context_builder, self._completions)
        self.probabilities = (self.context_builder, self._probabilities)

        self.log(f"Warning: using {['random', 'human', 'OpenAI'][self.agent_type]} API")

        # Construct observation string: combine text description with image description
        obs = observation.text
        if observation.image is not None:
            self.log("Recieved image observation. Requesting text description.")
            obs += "\n" + image_description(observation.image, rules)
        obs += "\n" + available_actions.instructions

        # Add description as openended_response of predefined action. This has
        # the effect of listing the description when showing to GPT, but will
        # be ignored by the game since it's a predefined action.
        predefined = tuple(
            Action(action, openended_response=description)
            for action, description in available_actions.predefined.items()
        )

        # Get openended responses now, and GPT will select from them as if they
        # are a predefined action. TODO: maybe get several possible responses.
        openended = []
        for action, description in available_actions.openended.items():
            temp = Action(action, openended_response=description)
            context = self.context_builder("openended", observation=obs, action=temp)
            c = self._completions(context)
            action = Action(action, openended_response=c)
            openended.append(action)
        openended = tuple(openended)

        self._init_state = GameState(
            observation=obs, depth=0, actions=predefined + openended
        )

        try:
            action = self.reasoner(None).trace[1][0]

            self.log(
                f"Recieved the following observation:\n{observation.text}\nAvailable actions: {available_actions}.\nChoosing the action: {action}"
            )

            return action
        except Exception as e:
            self.log(f"MCTS threw an error: {e=}. Returning default action.")

            return Action(action_id=None)

    def init_state(self) -> GameState:
        """From WorldModel; called by MCTS."""
        self.log("Retrieving initial state")

        return self._init_state

    def step(
        self, state: GameState, action: Action
    ) -> tuple[GameState, dict[str, float]]:
        """From WorldModel; called by MCTS."""
        try:
            oth = others_actions(state, *self.completions)
        except Exception as e:
            self.log(f"Failed to parse others' actions: {e=}")
            oth = "no information about others' actions"

        try:
            nxt = step(state, action, oth, *self.completions)
        except Exception as e:
            self.log(f"Failed to parse new state: {e=}")
            nxt = GameState("no information about current state", state.depth + 1)

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

    def get_actions(self, state: GameState) -> tuple[Action]:
        """From WorldModel; called by MCTS."""
        try:
            actions = get_actions(state, *self.completions)
        except Exception as e:
            self.log(f"Failed to parse actions: {e=}")
            actions = (Action(action_id="do a random action"),)

        self.log(
            f"Retrieving actions for the following state:\n{state.observation}\nActions: {actions}"
        )

        return actions

    def fast_reward(
        self, state: GameState, action: Action
    ) -> tuple[float, dict[str, float]]:
        """From SearchConfig; called by MCTS."""
        actions = get_actions(state, *self.completions)
        int = intuitions(state, actions, *self.probabilities)
        int = int[actions.index(action)]
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
        action: Action,
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
