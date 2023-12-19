from dataclasses import dataclass, field
import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import ast
from itertools import permutations, product, combinations
from pprint import pprint

PLAYERS_PER_TEAM = 1
N_PLAYERS = 1#2 * PLAYERS_PER_TEAM
BOARD_SIZE = (24, 24)

def get_plan_description(plan):
    """Converts a movement plan string into a human-readable description."""
    map = {"L": "move left", "F": "move forward", "R": "move right",
        "W": "wait", "l": "shoot left", "r": "shoot right", "b": "shoot both",
        "n": "don't shoot"}

    return ", ".join([map[token] for token in plan])

@dataclass
class Location:
    position : complex
    heading  : complex = 1

    def forward(self):
        return Location(self.position + self.heading, self.heading)

    def turn(self, token):
        dir = {"L": 1j, "F": 1, "R": -1j, "W": 1}[token]
        return Location(self.position, self.heading * dir)

    @staticmethod
    def random():
        return Location(
            random.randint(0, 23) + random.randint(0, 23)*1j,
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
        team1 = [agent1(agent_id=i, team_id=0) for i in range(PLAYERS_PER_TEAM)]
        #team2 = [agent2(agent_id=i+PLAYERS_PER_TEAM, team_id=1) for i in range(PLAYERS_PER_TEAM)]
        self.agents = team1# + team2
        self.winning_team = None

        self.agent_data = {
            i: {
                "damage": 0,
                "water": 0,
                "cannon_tokens": 4,
                "left_tokens": 4,
                "forward_tokens": 4,
                "right_tokens": 4,
            } for i in range(N_PLAYERS)
        }
        self.locations = [Location.random() for _ in range(N_PLAYERS)]
        self.damages = [0] * N_PLAYERS

        self.rocks = \
            [Location(0 +i*1j) for i in range(24)] + \
            [Location(i + 23j) for i in range(24)] + \
            [Location(23+i*1j) for i in range(24)] + \
            [Location(i +  0j) for i in range(24)] + \
            [Location.random() for _ in range(10)]

        self.winds = [Location.random() for _ in range(10)]
        self.plans = [None] * N_PLAYERS

    def get_board_string(self):
        def xy(loc):
            return 23-int(loc.position.imag), int(loc.position.real)

        board = [["." for _ in range(24)] for _ in range(24)]
        for agent_id, location in enumerate(self.locations):
            x, y = xy(location)
            board[x][y] = str(agent_id)

        for location in self.rocks:
            x, y = xy(location)
            board[x][y] = "R"

        return "\n".join([" ".join(board[i]) for i in range(24)])

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

        return observation, available_actions

    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        action = action.action_id
        if action not in available_actions.predefined:
            action = random.choice(list(available_actions.predefined.keys()))
        self.plans[agent.agent_id] = action

        if any(p is None for p in self.plans):
            return

        print("#################\n###################\n################")
        print(self.get_board_string())
        print(self.locations)

        # Arguments to Location.move()
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
            tokens = [p[token_i] for p in self.plans]

            if token_i % 2:
                """for p in self.plans:
                    token = p[token_i]
                    target = self.locations[agent_id].move(*cannon_move[token])

                    if target in self.locations:
                        self.damages[self.locations.index(target)] += 1

                for agent_id, damage in enumerate(self.damages):
                    if damage >= 10:
                        pass"""

            else:
                """Movement happens in the following phases:
                1. All moving ships claim their forward spot
                2. If any claimed spot is already occupied, collisions occur
                3. All turning ships rotate in place
                4. All turning ships claim the next forward spot
                5. Collisions again

                Collisions change which spot the ship ends up moving to.
                """
                print("Tokens:", [p[token_i] for p in self.plans])

                # For all ships that are moving, claim the forward spot.
                claims = []
                for location, token in zip(self.locations, tokens):
                    if token in "LFR":
                        claims.append(location.forward())
                    else:
                        claims.append(location)

                # Resolve collisions
                actual = []
                for old_location, claim in zip(self.locations, claims):
                    if claim in self.rocks:
                        actual.append(location)
                    else:
                        actual.append(claim)

                # Turn ships that tried to turn, regardless of collision
                new = []
                for location, token in zip(actual, tokens):
                    new.append(location.turn(token))

                # For all turning ships, claim the forward spot
                claims = []
                for location, token in zip(new, tokens):
                    if token in "LR":
                        claims.append(location.forward())
                    else:
                        claims.append(location)

                # Resolve collisions again, with slightly different rules.
                actual = []
                for old_location, claim in zip(new, claims):
                    if claim in self.rocks:
                        actual.append(location)
                    else:
                        actual.append(claim)

                # No more turning

                self.locations = actual

        print(self.get_board_string())
        print(self.locations)

        self.plans = [None] * N_PLAYERS

    def play(self) -> Tuple[float, float]:
        while True:
            for player in self.agents:
                observation, available_actions = self.get_observation(player)
                action = player.take_action(self.rules, observation, available_actions, show_state=self.show_state)
                self.update(action, available_actions, player)

            if self.game_is_over:
                break

        return (1., 0.) if self.winning_team == 0 else (0., 1.)