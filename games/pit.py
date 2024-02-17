from dataclasses import dataclass
from typing import List, Tuple
import random
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules


# Define a simple Commodity class for representing commodities in the Pit game
@dataclass
class Commodity:
    name: str


# Define the PitGame class implementing the Game interface
@dataclass
class PitGame(Game):
    rules: Rules = Rules(
        title="Pit",
        summary="""Pit is a commodity trading game where players engage in trading to accumulate points and emerge as the winner.
        The game involves commodity cards representing various goods, with each card holding a specific point value.
        Players shout out their trade offers, attempting to negotiate deals with others to acquire valuable commodities.
        Additionally, Bull and Bear cards periodically influence the market conditions, either boosting or decreasing commodity values.
        The game continues with trading phases, market fluctuations, and scoring until a player or team reaches the agreed-upon point total,
        declaring them the victor in the spirited world of commodity trading.""",
        additional_details=None,
    )
    id: str = "pit"

    def __post_init__(
        self,
        id: str = None,
        rules: Rules = Rules,
        agents: List[Agent] = [],
        show_state: bool = False,
        game_is_over: bool = False,
    ):
        #super().__init__(id, rules, agents, show_state, game_is_over)
        self.commodities = [
            Commodity("Wheat"),
            Commodity("Corn"),
            Commodity("Barley"),
            Commodity("Oats"),
        ]
        self.stock_pile = {
            commodity.name: random.randint(1, 10) for commodity in self.commodities
        }
        self.scores = []  # Initialize scores as an empty list"""

    def init_game(
        self,
        agent_1_cls: Agent,
        agent_2_cls: Agent,
    ):
        agent_1 = agent_1_cls(
            team_id=0,
            agent_id=1,
            agent_type_id=agent_1_cls.agent_type_id,
            **self.agent_1_kwargs,
        )
        agent_2 = agent_2_cls(
            team_id=0,
            agent_id=2,
            agent_type_id=agent_2_cls.agent_type_id,
            **self.agent_2_kwargs,
        )
        self.agents = [agent_1, agent_2]
        self.scores = [0.0] * len(
            self.agents
        )  # Initialize scores with the correct length

    def get_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        observation_text = (
            f"{agent.agent_id}, it's your turn. Stock Pile: {self.stock_pile}"
        )
        available_actions = AvailableActions(
            instructions="Choose a commodity to trade",
            predefined={
                commodity.name: f"Trade {commodity.name}"
                for commodity in self.commodities
            },
            openended={},
        )
        return Observation(text=observation_text), available_actions

    def update(self, action: Action, available_actions: AvailableActions, agent: Agent):
        chosen_commodity = action.action_id
        if chosen_commodity in available_actions.predefined:
            if self.stock_pile[chosen_commodity] > 0:
                self.stock_pile[chosen_commodity] -= 1
                # Increment agent's score by 1
                self.scores[self.agents.index(agent)] += 1
                if self.show_state:
                    print(f"{agent.agent_id} traded {chosen_commodity}")
            else:
                if self.show_state:
                    print(f"No more {chosen_commodity} in stock pile.")
        else:
            if self.show_state:
                print("Invalid action. Choosing a random action instead.")
            chosen_commodity = random.choice(list(available_actions.predefined.keys()))
            if self.stock_pile[chosen_commodity] > 0:
                self.stock_pile[chosen_commodity] -= 1
                # Increment agent's score by 1
                self.scores[self.agents.index(agent)] += 1
                if self.show_state:
                    print(f"{agent.agent_id} traded {chosen_commodity}")
            else:
                if self.show_state:
                    print(f"No more {chosen_commodity} in stock pile.")

    def play(self) -> Tuple[float, float]:
        while not self.game_is_over:
            for agent in self.agents:
                observation, available_actions = self.get_observation(agent)
                action = agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
                self.update(action, available_actions, agent)

                if all(value == 0 for value in self.stock_pile.values()):
                    self.game_is_over = True

        # Normalize scores to sum up to 1
        total_score = sum(self.scores)
        normalized_scores = [score / total_score for score in self.scores]

        return tuple(normalized_scores)
