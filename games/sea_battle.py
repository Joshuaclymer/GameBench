from dataclasses import dataclass, field
import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import ast
from itertools import permutations, product, combinations
from pprint import pprint

PLAYERS_PER_TEAM = 3
N_PLAYERS = 2 * PLAYERS_PER_TEAM
BOARD_SIZE = (24, 24)

"""
Remaining features:
- Wind
- Whirlpools
- Different ships (different cannons, different amounts of health, different shooting options)
- Tokens use/regeneration (damage affects regen)
- Carpentry (just gradually remove damage)
- Buoys? Blockade mechanics?

Questions:
- Should I explain all edge cases, simplify the rules, or let the agents learn?
- How many features should I add? Which are just extras?
- Is deliberation necessary? Maybe I give each player a certain number of messages,
and as long as a player hasn't used up all of their messages, they can choose
to send a message instead of submitting a plan. Or maybe it's not necessary
because it's the same agent controlling each member and they all have pretty much
perfect information
- Should the observation report what actions other players took? Maybe give a
play-by-play where it what each ship did per-token. Can build up that play-by-play
as the plans are being executed, and then tack it on next turn. This feels
pretty important, but there's already a lot of text being passed.
"""

def get_plan_description(plan):
    """Converts a movement plan string into a human-readable description."""
    map = {"L": "move left", "F": "move forward", "R": "move right",
        "W": "wait", "l": "shoot left", "r": "shoot right", "b": "shoot both",
        "n": "don't shoot"}

    return ", then ".join([map[token] for token in plan])

@dataclass
class Location:
    position : complex
    heading  : complex = field(default_factory=lambda: random.choice([1, 1j, -1, -1j]))

    def forward(self):
        """Returns location one square in front of this location."""
        return Location(self.position + self.heading, self.heading)

    def turn(self, token):
        """Returns location rotated from this location according to a movement
        token."""
        dir = {"L": 1j, "F": 1, "R": -1j, "W": 1}[token]
        return Location(self.position, self.heading * dir)

    def adjacent(self, token):
        """Returns location adjacent from this location according to a cannon
        token."""
        dir = {"l": 1j, "r": -1j, "n": 99}[token]
        return Location(self.position + self.heading*dir, self.heading)

    def __eq__(self, t):
        return self.position == t.position

@dataclass
class DamageCounter:
    threshold : int
    damage : int = 0

    def sunk(self):
        return self.damage >= self.threshold

    def rock(self):
        self.damage += 0.2

    def cannon(self):
        self.damage += 0.5

@dataclass
class SeaBattle(Game):
    id : str = "sea_battle"
    rules : Rules = Rules(
        title="Sea Battle",
        summary="Sink all of your opponent team's ships before they sink all of your team's ships.",
        additional_details={
            "Gameplay": "Gameplay cycles through three phases: deliberation, planning, and execution.",
            "Deliberation phase": "During this time, you will communicate with your teammates to share strategical ideas and form a plan.",
            "Planning phase": "During this phase, all players create a plan.",
            "Execution phase": "All player's plans are executed simultaneously. As in, all players take their first movement according to the first movement token in each plan, then each pauses to shoot according to the cannon token, and so forth.",
            "Plan": "A plan is a sequence of 8 tokens: 4 movement tokens and 4 cannon tokens. These tokens alternate: one movement token, one cannon token, so forth.",
            "Movement token": "There are four options: F = move forward one space; L = move forward one space, spin left, move forward; R = move forward one space, spin right, move forward. W = do not move. You have a limited number of movement tokens each turn, and will have fewer if you have sustained more damage. You will always have 4 W tokens.",
            "Cannon token": "There are four options: l = shoot left; r = shoot right; b = shoot left and right; n = don't shoot. You have a limited number of cannonballs each turn. Token b uses up two cannonballs and token n doesn't use any.",
            "Rock": "If you sail into a rock, you will sustain damage.",
            "Cannonball": "If you are shot by a cannonball, you will sustain damage.",
            "Ramming": "If you sail into another ship, or the same square that another ship is attempting to, you may either both sustain damage or either of you may be blocked from moving.",
            "Damage": "After you sustain enough damage, your ship will sink and you will be unable to play the rest of the game.",
            "Board symbols": ". = open water that you can sail on. R = a rock. A, B, C, X, Y, and Z = all ships. Your team will either be ships A, B, and C, or ships X, Y, and Z.",
        }
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

        all_locations = [Location(x+y*1j) for x in range(1, 23) for y in range(1, 23)]
        random.shuffle(all_locations)

        self.locations = all_locations[:N_PLAYERS]
        self.damages   = [DamageCounter(10) for _ in range(N_PLAYERS)]
        self.plans = [None] * N_PLAYERS
        self.lefts = [4] * N_PLAYERS
        self.forwards = [4] * N_PLAYERS
        self.rights = [4] * N_PLAYERS
        self.cannons = [4] * N_PLAYERS
        self.ship_symbols = list("ABCXYZ") # hardcoded...

        self.rocks = \
            [Location(0 +i*1j) for i in range(24)] + \
            [Location(i + 23j) for i in range(24)] + \
            [Location(23+i*1j) for i in range(24)] + \
            [Location(i +  0j) for i in range(24)] + \
            all_locations[N_PLAYERS:20]

        self.winds = all_locations[N_PLAYERS+20:10]

    def sink(self, *data):
        """Checks damage counters for ships that have just been sunken, and
        deletes their data from the game state as well as any local state
        passed in through *data. Not the prettiest way to do this..."""
        for i in reversed([i for i, dmg in enumerate(self.damages) if dmg.sunk()]):
            for d in data:
                del d[i]
            del self.locations[i]
            del self.damages[i]
            del self.plans[i]
            del self.lefts[i]
            del self.forwards[i]
            del self.rights[i]
            del self.cannons[i]
            del self.ship_symbols[i]

    def get_state_string(self, agent : Agent):
        def xy(loc):
            return 23-int(loc.position.imag), int(loc.position.real)

        directions = {}
        board = [["." for _ in range(24)] for _ in range(24)]
        for agent_id, location in enumerate(self.locations):
            x, y = xy(location)
            symbol = self.ship_symbols[agent_id]
            board[x][y] = symbol
            directions[symbol] = {1: "East", 1j: "North", -1: "West", -1j: "South"}[location.heading]

        for location in self.rocks:
            x, y = xy(location)
            board[x][y] = "R"

        id = agent.agent_id

        board = "\n".join([" ".join(board[i]) for i in range(24)]) + "\n"
        board += ". ".join([f"Ship {symbol} is facing {dir}" for symbol, dir in directions.items()]) + ".\n"
        board += f"You are controlling ship {self.ship_symbols[id]}. Your team's ships are {'A, B, and C' if agent.team_id == 0 else 'X, Y, and Z'}.\n"
        board += f"You have {self.lefts[id]} L tokens, {self.forwards[id]} F tokens, and {self.rights[id]} R tokens.\n"
        board += f"You have {self.cannons[id]} cannonballs.\n"
        board += f"You have {self.damages[id].damage} damage. If you reach {self.damages[id].threshold}, you will sink."

        return board

    def get_available_plans(self, agent : Agent):
        id = agent.agent_id

        movement_plans = [
            p
            for p
            in list(set(combinations("LLLLFFFFRRRRWWWW", r=4)))
            if  p.count("L") <= self.lefts[id]
            and p.count("F") <= self.forwards[id]
            and p.count("R") <= self.rights[id]
        ]
        cannon_plans = [
            p
            for p
            in list(set(combinations("llllrrrrbbbbnnnn", r=4)))
            if p.count("llll") + p.count("rrrr") + 2*p.count("bbbb") <= self.cannons[id]
        ]

        plans = [
            "".join([m + c for m, c in zip(movement, cannon)])
            for movement, cannon
            in product(movement_plans, cannon_plans)
        ]

        return plans

    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        state_string = self.get_state_string(agent)
        observation = Observation(text=state_string)

        if self.show_state:
            print(state_string)

        available_actions = AvailableActions(
            instructions="It is the planning phase. Return your action as a plan consisting of tokens you have available to you. A plan is a sequence of 8 tokens, alternating between movement tokens and cannon tokens.",
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

        self.execute_plans()

    def execute_plans(self):
        for token_i in range(8):
            tokens = [p[token_i] for p in self.plans]

            # Cannon firing
            if token_i % 2:
                for location, token in zip(self.locations, tokens):
                    shots = ["l", "r"] if token == "b" else [token]

                    for shot in shots:
                        target = location
                        for _ in range(3):
                            target = target.adjacent(shot)
                            if target in self.locations:
                                dmg = next(dmg for dmg, location in zip(self.damages, self.locations) if target == location)
                                dmg.cannon()
                                break

                            if target in self.rocks:
                                break

                # Remove sunk ships
                self.sink()

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
                self.sink(new, tokens)

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
                self.sink(actual)

                self.locations = actual

        self.plans = [None] * len(self.plans)

    def play(self) -> Tuple[float, float]:
        while True:
            for player in (agent for agent, dmg in zip(self.agents, self.damages) if not dmg.sunk()):
                observation, available_actions = self.get_observation(player)
                action = player.take_action(self.rules, observation, available_actions, show_state=self.show_state)
                self.update(action, available_actions, player)

            if all(dmg.sunk() for dmg in self.damages):
                return (0.5, 0.5)

            if all(dmg.sunk() for dmg, player in zip(self.damages, self.agents) if player.team_id == 0):
                return (0., 1.)

            if all(dmg.sunk() for dmg, player in zip(self.damages, self.agents) if player.team_id == 1):
                return (1., 0.)