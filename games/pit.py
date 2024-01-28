from dataclasses import dataclass
from typing import List, Tuple
import random
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules


# Define a simple Commodity class for representing commodities in the Pit game
@dataclass
class Commodity:
    name: str


# Define the PitGame class implementing the Game interface
class PitGame(Game):
    def __init__(
        self,
        id: str,
        rules: Rules,
        agents: List[Agent] = None,
        show_state: bool = False,
        game_is_over: bool = False,
    ):
        super().__init__(id, rules, agents, show_state, game_is_over)
        self.commodities = [
            Commodity("Wheat"),
            Commodity("Corn"),
            Commodity("Barley"),
            Commodity("Oats"),
        ]
        self.stock_pile = {
            commodity.name: random.randint(1, 10) for commodity in self.commodities
        }

    def init_game(self, agent_1: Agent, agent_2: Agent):
        self.agents = [agent_1, agent_2]

    def get_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        observation_text = (
            f"{agent.agent_id}, it's your turn. Stock Pile: {self.stock_pile}"
        )
        available_actions = AvailableActions(
            instructions="Choose a commodity to trade",
            predefined={
                commodity.name: commodity.name for commodity in self.commodities
            },
            openended={},
        )
        return Observation(text=observation_text), available_actions

    def update(self, action: Action, available_actions: AvailableActions, agent: Agent):
        chosen_commodity = action.action_id
        if chosen_commodity in available_actions.predefined:
            if self.stock_pile[chosen_commodity] > 0:
                self.stock_pile[chosen_commodity] -= 1
                agent.team_id += 1  # Increment team score for simplicity
            else:
                print(f"No more {chosen_commodity} in stock pile.")
        else:
            action = random.choice(list(available_actions.keys()))

    def play(self) -> Tuple[float, float]:
        while not self.game_is_over:
            for agent in self.agents:
                observation, available_actions = self.get_observation(agent)
                action_id = agent.take_action({}, observation, available_actions)
                action = Action(action_id)
                self.update(action, available_actions, agent)

                if all(value == 0 for value in self.stock_pile.values()):
                    self.game_is_over = True

        scores = tuple(agent.team_id for agent in self.agents)
        return scores


# Example usage:
agent1 = Agent(team_id=0, agent_id=1, agent_type_id="Trader1")
agent2 = Agent(team_id=0, agent_id=2, agent_type_id="Trader2")

pit_game = PitGame(
    id="Pit",
    rules=Rules(
        title="Pit Game Rules",
        summary="""
        Pit is a commodity trading game where players engage in trading to accumulate points and emerge as the winner. 
        The game involves commodity cards representing various goods, with each card holding a specific point value. 
        Players shout out their trade offers, attempting to negotiate deals with others to acquire valuable commodities. 
        Additionally, Bull and Bear cards periodically influence the market conditions, either boosting or decreasing commodity values. 
        The game continues with trading phases, market fluctuations, and scoring until a player or team reaches the agreed-upon point total, 
        declaring them the victor in the spirited world of commodity trading."
        """,
    ),
)
pit_game.init_game(agent_1=agent1, agent_2=agent2)
scores = pit_game.play()

print(f"Final Scores: {scores}")
