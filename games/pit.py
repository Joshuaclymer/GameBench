from dataclasses import dataclass
from typing import List, Tuple
import random
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules


# Define a simple Commodity class for representing commodities in the Pit game
@dataclass
class Commodity:
    name: str
    base_value: float
    price_fluctuation: Tuple[
        float, float
    ]  # Tuple representing min and max percentage fluctuation


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

    def __post_init__(self):
        self.commodities = [
            Commodity("Wheat", 10.0, (0.9, 1.1)),
            Commodity("Corn", 15.0, (0.8, 1.2)),
            Commodity("Barley", 12.0, (0.85, 1.15)),
            Commodity("Oats", 8.0, (0.95, 1.05)),
        ]
        self.stock_pile = {
            commodity.name: random.randint(1, 10) for commodity in self.commodities
        }
        self.scores = []  # Initialize scores as an empty list
        self.round_number = 0

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
            commodity = next(
                (c for c in self.commodities if c.name == chosen_commodity), None
            )
            if commodity:
                if self.stock_pile[chosen_commodity] > 0:
                    self.stock_pile[chosen_commodity] -= 1
                    # Calculate fluctuated value based on the commodity's base value and price fluctuation
                    fluctuated_value = commodity.base_value * random.uniform(
                        *commodity.price_fluctuation
                    )
                    # Apply Bull or Bear effect
                    if random.random() < 0.1:  # 10% chance of Bull or Bear effect
                        if random.choice(["Bull", "Bear"]) == "Bull":
                            fluctuated_value *= 1.2  # 20% increase for Bull
                            if self.show_state:
                                print(
                                    f"Bull effect! {chosen_commodity} value increased by 20%."
                                )
                        else:
                            fluctuated_value *= 0.8  # 20% decrease for Bear
                            if self.show_state:
                                print(
                                    f"Bear effect! {chosen_commodity} value decreased by 20%."
                                )
                    # Increment agent's score by the fluctuated value
                    self.scores[self.agents.index(agent)] += fluctuated_value
                    if self.show_state:
                        print(
                            f"{agent.agent_id} traded {chosen_commodity} at {fluctuated_value}"
                        )
                else:
                    if self.show_state:
                        print(f"No more {chosen_commodity} in stock pile.")
        else:
            if self.show_state:
                print("Invalid action. Choosing a random action instead.")
            chosen_commodity = random.choice(list(available_actions.predefined.keys()))
            commodity = next(
                (c for c in self.commodities if c.name == chosen_commodity), None
            )
            if commodity:
                if self.stock_pile[chosen_commodity] > 0:
                    self.stock_pile[chosen_commodity] -= 1
                    fluctuated_value = commodity.base_value * random.uniform(
                        *commodity.price_fluctuation
                    )
                    if random.random() < 0.1:
                        if random.choice(["Bull", "Bear"]) == "Bull":
                            fluctuated_value *= 1.2
                            if self.show_state:
                                print(
                                    f"Bull effect! {chosen_commodity} value increased by 20%."
                                )
                        else:
                            fluctuated_value *= 0.8
                            if self.show_state:
                                print(
                                    f"Bear effect! {chosen_commodity} value decreased by 20%."
                                )
                    self.scores[self.agents.index(agent)] += fluctuated_value
                    if self.show_state:
                        print(
                            f"{agent.agent_id} traded {chosen_commodity} at {fluctuated_value}"
                        )
                else:
                    if self.show_state:
                        print(f"No more {chosen_commodity} in stock pile.")

    def play(self) -> Tuple[float, float]:
        while not self.game_is_over:
            self.round_number += 1
            for agent in self.agents:
                observation, available_actions = self.get_observation(agent)
                action = agent.take_action(
                    self.rules,
                    observation,
                    available_actions,
                    show_state=self.show_state,
                )
                self.update(action, available_actions, agent)

                if all(value == 0 for value in self.stock_pile.values()):
                    self.game_is_over = True

        # Normalize scores to sum up to 1
        total_score = sum(self.scores)
        normalized_scores = [score / total_score for score in self.scores]

        return tuple(normalized_scores)
