from dataclasses import dataclass, field
import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import ast
from itertools import permutations, product, combinations
from pprint import pprint

PLAYERS_PER_TEAM = 1
N_PLAYERS = 2 * PLAYERS_PER_TEAM
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

    def adjacent(self, token):
        dir = {"l": 1j, "r": -1j, "n": 99}[token]
        return Location(self.position + self.heading*dir, self.heading)

    @staticmethod
    def random():
        return Location(
            random.randint(0, 23) + random.randint(0, 23)*1j,
            random.choice([1, 1j, -1, -1j])
        )

    def __eq__(self, t):
        return self.position == t.position

@dataclass
class DamageCounter:
    threshold : int
    damage : int = 0

    def sunk(self):
        return self.damage >= self.threshold

    def rock(self):
        self.damage += 3

    def cannon(self):
        self.damage += 5

@dataclass
class SeaBattle(Game):
    id : str = "sea_battle"
    rules : Rules = Rules(
        title="Sea Battle",
        summary="Sink all of your opponent team's ships before they sink all of your team's ships.",
        additional_details=None
    )

    def init_game(self, agent1 : Agent, agent2 : Agent):
        """The design pattern for the state is to put all agent data spread
        out across several lists, where the index i in each list always
        corresponds to agent i. For state that needs to be modified, objects
        are used in the list so that they may be modified in-place in
        iteration. """
        team1 = [agent1(agent_id=i, team_id=0) for i in range(PLAYERS_PER_TEAM)]
        team2 = [agent2(agent_id=i+PLAYERS_PER_TEAM, team_id=1) for i in range(PLAYERS_PER_TEAM)]
        self.agents = team1 + team2
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
        self.damages   = [DamageCounter(10) for _ in range(N_PLAYERS)]
        self.plans = [None] * N_PLAYERS

        self.rocks = \
            [Location(0 +i*1j) for i in range(24)] + \
            [Location(i + 23j) for i in range(24)] + \
            [Location(23+i*1j) for i in range(24)] + \
            [Location(i +  0j) for i in range(24)] + \
            [Location.random() for _ in range(10)]

        self.winds = [Location.random() for _ in range(10)]

    def remove(self, i):
        del self.locations[i]
        del self.damages[i]
        del self.plans[i]

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
        # Choose a random action if an invalid action was chosen
        action = action.action_id
        if action not in available_actions.predefined:
            action = random.choice(list(available_actions.predefined.keys()))

        # Queue this agent's plan, and return if not every agent has queued yet.
        self.plans[agent.agent_id] = action
        if any(p is None for p in self.plans):
            return

        print("#################\n###################\n################")
        print(self.get_board_string())
        print(self.locations)
        print(self.damages)
        print(self.plans)

        for token_i in range(8):
            tokens = [p[token_i] for p in self.plans]
            print("tokens", tokens)

            # Cannon firing
            if tokens[0] in "lrbn":
                for location, token in zip(self.locations, tokens):
                    shots = ["l", "r"] if token == "b" else [token]

                    for shot in shots:
                        target = location
                        for _ in range(3):
                            target = target.adjacent(shot)
                            if target in self.locations:
                                print("Ship hit")
                                dmg = next(dmg for dmg, location in zip(self.damages, self.locations) if target == location)
                                dmg.cannon()

                                break

                            if target in self.rocks:
                                print("Rock hit")
                                break

                # Remove sunk ships
                sunk = [i for i, dmg in enumerate(self.damages) if dmg.sunk()]
                for i in sunk:
                    self.remove(i)

            # Movement
            else:
                """Movement happens in the following phases:
                1. All moving ships claim their forward spot
                2. If any claimed spot is already occupied, collisions occur
                3. All turning ships rotate in place
                4. All turning ships claim the next forward spot
                5. Collisions again

                Collisions change which spot the ship ends up moving to.
                """

                # 1. For all ships that are moving, claim the forward spot.
                claims = []
                for location, token in zip(self.locations, tokens):
                    if token in "LFR":
                        claims.append(location.forward())
                    else:
                        claims.append(location)

                # 2. Resolve collisions
                actual = []
                for old_location, claim, damage in zip(self.locations, claims, self.damages):
                    if claim in self.rocks:
                        actual.append(old_location)
                        damage.rock()
                    else:
                        actual.append(claim)

                # 3. Turn ships that tried to turn, regardless of collision
                new = []
                for location, token in zip(actual, tokens):
                    new.append(location.turn(token))

                # 3.5 Remove sunk ships
                sunk = [i for i, dmg in enumerate(self.damages) if dmg.sunk()]
                for i in sunk:
                    del new[i]
                    del tokens[i]
                    self.remove(i)

                # 4. For all turning ships, claim the forward spot
                claims = []
                for location, token in zip(new, tokens):
                    if token in "LR":
                        claims.append(location.forward())
                    else:
                        claims.append(location)

                # 5. Resolve collisions again, with slightly different rules.
                actual = []
                for old_location, claim in zip(new, claims):
                    if claim in self.rocks:
                        actual.append(old_location)
                        damage.rock()
                    else:
                        actual.append(claim)

                # 5.5 Remove sunk ships
                sunk = [i for i, dmg in enumerate(self.damages) if dmg.sunk()]
                for i in sunk:
                    del actual[i]
                    self.remove(i)

                self.locations = actual

        print(self.get_board_string())
        print(self.locations)
        print(self.damages)

        self.plans = [None] * len(self.plans)

    def play(self) -> Tuple[float, float]:
        while True:
            for player in (agent for agent, dmg in zip(self.agents, self.damages) if not dmg.sunk()):
                observation, available_actions = self.get_observation(player)
                action = player.take_action(self.rules, observation, available_actions, show_state=self.show_state)
                self.update(action, available_actions, player)

            if all(dmg.sunk() for dmg in self.damages):
                print("All ships sunk.")
                return (0.5, 0.5)

            if all(dmg.sunk() for dmg, player in zip(self.damages, self.agents) if player.team_id == 0):
                print("Team 0 wins.")
                return (0., 1.)

            if all(dmg.sunk() for dmg, player in zip(self.damages, self.agents) if player.team_id == 1):
                print("Team 1 wins.")
                return (1., 0.)