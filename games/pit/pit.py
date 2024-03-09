from dataclasses import dataclass, field
from typing import Tuple, Dict
import random
from classes import Observation, Action, Agent, AvailableActions, Game, Rules


@dataclass
class Commodity:
    name: str
    value: float


@dataclass
class Observation:
    text: str


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
    player_hands: Dict[int, Dict[str, int]] = field(default_factory=dict)

    def __post_init__(self):
        self.commodities = [
            Commodity("Barley", 85.0),
            Commodity("Coffee", 80.0),
            Commodity("Corn", 75.0),
            Commodity("Oats", 60.0),
            Commodity("Oranges", 50.0),
            Commodity("Soyabeans", 55.0),
            Commodity("Sugar", 65.0),
            Commodity("Wheat", 100.0),
        ]
        self.scores = []
        self.round_number = 0

    def distribute_cards(self):
        for player_id in self.player_hands.keys():
            for _ in range(9):
                selected_commodity = random.choice(self.commodities).name
                self.player_hands[player_id][selected_commodity] += 1

    def init_game(
        self,
        agent_1_cls: Agent,
        agent_2_cls: Agent,
    ):
        # agent_1 = agent_1_cls(
        #     team_id=0,
        #     agent_id=1,
        #     agent_type_id=agent_1_cls.agent_type_id,
        #     **self.agent_1_kwargs,
        # )
        # agent_2 = agent_2_cls(
        #     team_id=1,
        #     agent_id=2,
        #     agent_type_id=agent_2_cls.agent_type_id,
        #     **self.agent_2_kwargs,
        # )
        agent_1 = agent_1_cls
        agent_2 = agent_2_cls
        self.agents = [agent_1, agent_2]

        for agent in self.agents:
            self.player_hands[agent.agent_id] = {
                commodity.name: 0 for commodity in self.commodities
            }

        self.scores = [0.0] * len(self.agents)

    def check_corners_update_score(self):
        print(self.player_hands)
        for agent_id, hand in self.player_hands.items():
            for commodity, count in hand.items():
                if count == 3:
                    commodity_obj = next(
                        (c for c in self.commodities if c.name == commodity), None
                    )
                    if commodity_obj:
                        self.scores[
                            self.agents.index(
                                next(
                                    agent
                                    for agent in self.agents
                                    if agent.agent_id == agent_id
                                )
                            )
                        ] += commodity_obj.value
                        print(
                            f"Agent {agent_id} has cornered the market on {commodity}. Score updated."
                        )

                    self.distribute_cards()
                    return True
        return False

    def get_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        observation_text = (
            f"{agent.agent_id}, it's your turn. Hand: {self.player_hands}"
        )
        available_actions = AvailableActions(
            instructions="Choose a card to trade",
            predefined={
                commodity.name: f"Trade {commodity.name}"
                for commodity in self.commodities
            },
            openended={},
        )
        return (
            Observation(text=observation_text),
            available_actions,
        )

    def update(
        self,
        action: Action,
        available_actions: AvailableActions,
        agent: Agent,
        other_agent: Agent,
    ):
        chosen_commodity = action.action_id
        if chosen_commodity in available_actions.predefined:
            commodity = next(
                (c for c in self.commodities if c.name == chosen_commodity), None
            )
            if commodity:
                print(self.player_hands)
                if self.player_hands[agent.agent_id][chosen_commodity] > 0:
                    self.player_hands[agent.agent_id][chosen_commodity] -= 1
                    self.player_hands[other_agent.agent_id][chosen_commodity] += 1
                    if self.show_state:
                        print(f"{agent.agent_id} traded {chosen_commodity}")
                else:
                    if self.show_state:
                        print(f"No more {chosen_commodity} in hand.")
        else:
            if self.show_state:
                print("Invalid action. Choosing a random action instead.")
            chosen_commodity = random.choice(list(available_actions.predefined.keys()))
            commodity = next(
                (c for c in self.commodities if c.name == chosen_commodity), None
            )
            if self.player_hands[agent.agent_id][chosen_commodity] > 0:
                self.player_hands[agent.agent_id][chosen_commodity] -= 1
                self.player_hands[other_agent.agent_Id][chosen_commodity] += 1

                if self.show_state:
                    print(f"{agent.agent_id} traded {chosen_commodity}")
            else:
                if self.show_state:
                    print(f"No more {chosen_commodity} in hand.")

    def play(self) -> Tuple[float, float]:
        self.distribute_cards()

        while not self.game_is_over:
            self.round_number += 1
            current_agent = self.agents[(self.round_number - 1) % len(self.agents)]
            other_agent = self.agents[1 - ((self.round_number - 1) % len(self.agents))]

            observation, available_actions = self.get_observation(current_agent)

            action = current_agent.take_action(
                self.rules,
                observation,
                available_actions,
                show_state=True,
            )
            self.update(action, available_actions, current_agent, other_agent)
            print(self.scores)
            if self.check_corners_update_score():
                print(f"Round {self.round_number}: Corner detected, scores updated.")
                break

            print(f"End of round {self.round_number}. Scores: {self.scores}")

            if any(score >= 500 for score in self.scores):
                self.game_is_over = True
                break

        print(
            f"Agent {self.agents[self.scores.index(max(self.scores))].agent_id} won with a score of {max(self.scores)}."
        )
        total_score = sum(self.scores)
        normalized_scores = [score / total_score for score in self.scores]
        return tuple(normalized_scores)
