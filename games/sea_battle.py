from dataclasses import dataclass, field
import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import ast
from itertools import permutations, product, combinations
from pprint import pprint

def get_plan_description(plan):
    """Converts a movement plan string into a human-readable description."""
    map = {"L": "move left", "F": "move forward", "R": "move right",
        "W": "wait", "l": "shoot left", "r": "shoot right", "b": "shoot both",
        "n": "don't shoot"}

    return ", ".join([map[token] for token in plan])

@dataclass
class Location:
    position : complex
    heading  : complex

    def move(self, step, turn):
        return Location(self.position + step*self.heading, turn*self.heading)

    @staticmethod
    def random():
        return Location(
            random.randint(-12, 12) + random.randint(-12, 12)*1j,
            random.choice([1, 1j, -1, -1j])
        )

    def __eq__(self, t):
        return self.position == t.position

@dataclass
class SeaBattle(Game):
    id : str = "sea_battle"
    rules : Rules = Rules(
        title="Sea Battle",
        summary="Sink all of your opponent team's ships before they sink all of your team's ships.",
        additional_details=None
    )

    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.agents = [agent1(agent_id=0, team_id=0)]#, agent2(agent_id=1, team_id=1)]
        self.winning_team = None

        self.agent_data = {
            i: {
                "damage": 0,
                "water": 0,
                "cannon_tokens": 4,
                "left_tokens": 4,
                "forward_tokens": 4,
                "right_tokens": 4,
            } for i in range(1)
        }
        self.locations = [Location.random() for _ in range(1)]
        self.damages = [0] * 1

        self.rocks = [Location.random() for _ in range(10)]
        self.winds = [Location.random() for _ in range(10)]

        self.plans = [None] * 1

    def get_board_string(self):
        """Ideas
        - the grid is 2d, so return a 2d grid of symbols
        - a list of objects and their coordinates
        """
        board = [["." for _ in range(24)] for _ in range(24)]
        for agent_id, location in enumerate(self.locations):
            x = int(location.position.real + 12) % 24
            y = int(location.position.imag + 12) % 24
            board[x][y] = str(agent_id)

        return "\n".join(["".join(board[i]) for i in range(24)])

    def get_available_plans(self, agent : Agent):
        data = self.agent_data[agent.agent_id]

        movement_plans = [
            p
            for p
            in list(set(combinations("LLLLFFFFRRRRWWWW", r=4)))
            if  p.count("L") <= data["left_tokens"]
            and p.count("F") <= data["forward_tokens"]
            and p.count("R") <= data["right_tokens"]
        ]
        cannon_plans = [
            p
            for p
            in list(set(combinations("llllrrrrbbbbnnnn", r=4)))
            if p.count("llll") + p.count("rrrr") + 2*p.count("bbbb") <= data["cannon_tokens"]
        ]

        plans = [
            "".join([m + c for m, c in zip(movement, cannon)])
            for movement, cannon
            in product(movement_plans, cannon_plans)
        ]

        return plans

    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        board_string = self.get_board_string()
        observation = Observation(text=board_string)

        available_actions = AvailableActions(
            instructions="desc.",
            predefined={
                plan: get_plan_description(plan) for plan in self.get_available_plans(agent)
            },
            openended={}
        )

        print("Current location: ", self.locations[0])

        return observation, available_actions

    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        action = action.action_id
        if action not in available_actions.predefined:
            action = random.choice(list(available_actions.predefined.keys()))
        self.plans[agent.agent_id] = action

        if any(p is None for p in self.plans):
            return

        print(self.plans[0])

        # Map movement tokens to position and heading "deltas"
        token_move = {
            "L": [(1,  1j), (1, 1)],
            "F": [(1,  1 ), (0, 1)],
            "R": [(1, -1j), (1, 1)],
            "W": [(0,  1 ), (0, 1)]
        }

        cannon_move = {
            "l": [1j, 1],
            "r": [-1j, 1],
            "b": [1j, 1],
            "n": [99, 1]
        }

        for token_i in range(8):
            if token_i % 2:
                for p in self.plans:
                    token = p[token_i]
                    target = self.locations[agent_id].move(*cannon_move[token])

                    if target in self.locations:
                        self.damages[self.locations.index(target)] += 1

                for agent_id, damage in enumerate(self.damages):
                    if damage >= 10:
                        pass

            else:
                moves = [token_move[p[token_i]] for p in self.plans]

                claimed = []
                for agent_id in range(1):
                    move = moves[agent_id]
                    claimed.append(self.locations[agent_id].move(*move[0]))

                # check collisions
                self.locations = claimed

                claimed = []
                for agent_id in range(1):
                    move = moves[agent_id]
                    claimed.append(self.locations[agent_id].move(*move[1]))

                # check collisions
                self.locations = claimed

        self.plans = [None] * 1

    def play(self) -> Tuple[float, float]:
        while True:
            for player in self.agents:
                observation, available_actions = self.get_observation(player)
                action = player.take_action(self.rules, observation, available_actions, show_state=self.show_state)
                self.update(action, available_actions, player)

            if self.game_is_over:
                break

        return (1., 0.) if self.winning_team == 0 else (0., 1.)