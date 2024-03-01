from dataclasses import dataclass
from typing import List, Tuple
import random
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules


@dataclass
class Commodity:
    name: str
    base_value: float
    price_fluctuation: Tuple[float, float]


@dataclass
class Message:
    sender_id: int
    recipient_id: int
    content: str
    message_type: str


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
        self.scores = []
        self.round_number = 0
        self.messages = []  # List to store messages exchanged between agents

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
        self.scores = [0.0] * len(self.agents)

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

    def communicate(
        self, sender_id: int, recipient_id: int, content: str, message_type: str
    ):
        self.messages.append(Message(sender_id, recipient_id, content, message_type))

    def play(self) -> Tuple[float, float]:
        while not self.game_is_over:
            self.round_number += 1
            for agent in self.agents:
                observation, available_actions = self.get_observation(agent)
                # Send message to the other agent
                other_agent = self.agents[1 - self.agents.index(agent)]
                message_content = f"Round {self.round_number}: Interested in trading {random.choice(list(self.stock_pile.keys()))}?"
                message_type = "inquiry"
                agent.send_message(other_agent.agent_id, message_content, message_type)

                received_messages = [
                    message
                    for message in self.messages
                    if message.recipient_id == agent.agent_id
                ]

                # Processing received messages
                for message in received_messages:
                    if message.message_type == "inquiry":
                        interested = random.choice([True, False])
                        if interested:
                            # Send an offer message back to the inquiring agent
                            offer_content = (
                                f"Offering X units of {message.content.split()[-1]}"
                            )
                            self.communicate(
                                agent.agent_id,
                                message.sender_id,
                                offer_content,
                                "offer",
                            )
                    elif message.message_type == "offer":
                        decision = random.choice(["accept", "counter-offer", "reject"])

                        if decision == "accept":
                            # Assuming the offer format is "Offering [quantity] units of [commodity]"
                            _, quantity, _, commodity = message.content.split()
                            quantity = int(quantity)
                            if (
                                commodity in self.stock_pile
                                and self.stock_pile[commodity] >= quantity
                            ):
                                # Calculate the trade value
                                commodity_obj = next(
                                    filter(
                                        lambda x: x.name == commodity, self.commodities
                                    ),
                                    None,
                                )
                                if commodity_obj:
                                    trade_value = (
                                        commodity_obj.base_value
                                        * random.uniform(
                                            *commodity_obj.price_fluctuation
                                        )
                                        * quantity
                                    )
                                    # Apply Bull/Bear market effects randomly
                                    if (
                                        random.random() < 0.1
                                    ):  # 10% chance for market effect
                                        if random.choice(["Bull", "Bear"]) == "Bull":
                                            trade_value *= 1.2  # Increase value by 20%
                                        else:
                                            trade_value *= 0.8  # Decrease value by 20%

                                    # Update the accepting agent's score
                                    self.scores[self.agents.index(agent)] += trade_value

                                    # Update stock piles
                                    self.stock_pile[commodity] -= quantity

                                    acceptance_content = f"Offer for {quantity} units of {commodity} accepted."
                                    self.communicate(
                                        agent.agent_id,
                                        message.sender_id,
                                        acceptance_content,
                                        "acceptance",
                                    )

                                    # Log the trade
                                    if self.show_state:
                                        print(
                                            f"{agent.agent_id} accepted the offer and traded {quantity} units of {commodity} for {trade_value}"
                                        )
                        elif decision == "counter-offer":
                            # Assuming the message content includes the commodity name and quantity, e.g., "Offering 5 Wheat"
                            _, offered_quantity, _, offered_commodity = (
                                message.content.split()
                            )
                            counter_quantity = random.randint(1, int(offered_quantity))
                            counter_commodity = random.choice(
                                list(self.stock_pile.keys())
                            )
                            counter_offer_content = f"Counter-offer: {counter_quantity} units of {counter_commodity}"
                            self.communicate(
                                agent.agent_id,
                                message.sender_id,
                                counter_offer_content,
                                "counter-offer",
                            )
                            if self.show_state:
                                print(
                                    f"{agent.agent_id} made a counter-offer to Agent {message.sender_id}"
                                )
                        else:
                            # Simply reject the offer without making a counter-offer
                            rejection_content = "Offer rejected"
                            self.communicate(
                                agent.agent_id,
                                message.sender_id,
                                rejection_content,
                                "rejection",
                            )
                            if self.show_state:
                                print(
                                    f"{agent.agent_id} rejected the offer from Agent {message.sender_id}"
                                )
                # Take action based on observation and received messages
                action = agent.take_action(
                    self.rules,
                    observation,
                    available_actions,
                    received_messages=received_messages,
                    show_state=self.show_state,
                )
                self.update(action, available_actions, agent)
                if all(value == 0 for value in self.stock_pile.values()):
                    self.game_is_over = True

        total_score = sum(self.scores)
        normalized_scores = [score / total_score for score in self.scores]
        return tuple(normalized_scores)
