from dataclasses import dataclass, field
import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple, ClassVar
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
- Should I explain all the collision edge cases, simplify the rules, or let the agents learn?
- How many features should I add? Which are just extras?
- Is deliberation necessary? Maybe I give each player a certain number of messages,
and as long as a player hasn't used up all of their messages, they can choose
to send a message instead of submitting a plan.
- Should the observation report what actions other players took? Maybe give a
play-by-play where it what each ship did per-token. Can build up that play-by-play
as the plans are being executed, and then tack it on next turn. This feels
pretty important, but there's already a lot of text being passed. I think
there are a number of unique interactions in this game and extra mechanics

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

    @property
    def xy(self):
        return 23-int(self.position.imag), int(self.position.real)

    @property
    def cardinal(self):
        return {1: "East", 1j: "North", -1: "West", -1j: "South"}[self.heading]

    def __eq__(self, t):
        return self.position == t.position

@dataclass
class DamageCounter:
    threshold : int = 10
    damage : int = 0

    def sunk(self):
        return self.damage >= self.threshold
    def rock(self):
        self.damage += 1
    def cannon(self):
        self.damage += 2
    def ram(self):
        self.damage += 1

@dataclass
class Player:
    agent    : Agent
    location : Location
    symbol   : str
    damage   : DamageCounter = field(default_factory=lambda: DamageCounter())
    plan     : str = None
    tokens   : List = field(default_factory=lambda: list("LLLFFFRRRCCCCCC"))

    def will_collide(self, t):
        return self.claim == t.claim

    def count(self, t):
        return self.tokens.count(t)

    def reset(self):
        self.plan = None

    def __eq__(self, t):
        return self.location == t.location

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
            "Plan": "A plan is a sequence of 6 tokens: 3 movement tokens and 3 cannon tokens. These tokens alternate: one movement token, one cannon token, so forth.",
            "Movement token": "There are four options: F = move forward one space; L = move forward one space, spin left, move forward; R = move forward one space, spin right, move forward. W = do not move. You have a limited number of movement tokens each turn, and will have fewer if you have sustained more damage. You will always have 4 W tokens.",
            "Cannon token": "There are four options: l = shoot left; r = shoot right; b = shoot left and right; n = don't shoot. You have a limited number of cannonballs each turn. Token b uses up two cannonballs and token n doesn't use any.",
            "Rock": "If you sail into a rock, you will sustain damage.",
            "Cannonball": "If you are shot by a cannonball, you will sustain damage.",
            "Ramming": "If two ships attempt to sail into the same spot, neither will end up in that spot, and both may take damage.",
            "Damage": "After you sustain enough damage, your ship will sink and you will be unable to play the rest of the game.",
            "Board symbols": ". = open water that you can sail on. R = a rock. A, B, C, X, Y, and Z = all ships. Your team will either be ships A, B, and C, or ships X, Y, and Z.",
        }
    )

    def init_game(self, agent1 : Agent, agent2 : Agent):
        team1 = [agent1(agent_id=i, team_id=0) for i in range(PLAYERS_PER_TEAM)]
        team2 = [agent2(agent_id=i+PLAYERS_PER_TEAM, team_id=1) for i in range(PLAYERS_PER_TEAM)]
        self.agents = team1 + team2

        all_locations = [Location(x+y*1j) for x in range(1, 23) for y in range(1, 23)]
        random.shuffle(all_locations)

        self._players = [
            Player(agent, location, symbol)
            for _, agent, location, symbol
            in zip(range(N_PLAYERS), self.agents, all_locations, list("ABCXYZ"))
        ]

        self.rocks = \
            [Location(0 +i*1j) for i in range(24)] + \
            [Location(i + 23j) for i in range(24)] + \
            [Location(23+i*1j) for i in range(24)] + \
            [Location(i +  0j) for i in range(24)] + \
            all_locations[N_PLAYERS:20]

    @property
    def players(self):
        """Return only non-sunk players."""
        return [p for p in self._players if not p.damage.sunk()]

    def player_from_agent(self, agent : Agent):
        """Used by functions that are called per-agent."""
        return self._players[agent.agent_id]

    def get_board_string(self):
        directions = {}
        board = [["." for _ in range(24)] for _ in range(24)]
        for p in self.players:
            x, y = p.location.xy()
            board[x][y] = p.symbol
            directions[p.symbol] = {1: "East", 1j: "North", -1: "West", -1j: "South"}[p.location.heading]

        for location in self.rocks:
            x, y = location.xy()
            board[x][y] = "R"

        board = "\n".join([" ".join(board[i]) for i in range(24)]) + "\n"
        board += ". ".join([f"Ship {symbol} is facing {dir}" for symbol, dir in directions.items()]) + ".\n"
        return board

    def get_available_plans(self, agent : Agent):
        player = self.player_from_agent(agent)

        movement_plans = [
            p
            for p
            in list(set(combinations("LLLLFFFFRRRRWWWW", r=3)))
            if  p.count("L") <= player.count("L")
            and p.count("F") <= player.count("F")
            and p.count("R") <= player.count("R")
        ]
        cannon_plans = [
            p
            for p
            in list(set(combinations("llllrrrrbbbbnnnn", r=3)))
            if p.count("llll") + p.count("rrrr") + 2*p.count("bbbb") <= player.count("C")
        ]

        plans = [
            "".join([m + c for m, c in zip(movement, cannon)])
            for movement, cannon
            in product(movement_plans, cannon_plans)
        ]

        return plans

    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        player = self.player_from_agent(agent)
        s = "Rocks line the border of the 24 by 24 board.\n"
        for p in self.players:
            q = 'you' if p.agent == agent else ('your teammate' if p.agent.team_id == agent.team_id else 'your opponent')
            s += f"Ship {p.symbol} ({q}) is located at {p.location.xy} facing {p.location.cardinal}.\n"
        s += "There are more rocks located at " + ", ".join([str(r.xy) for r in self.rocks[-20:]]) + "\n"
        s += f"You have {player.count('L')} L tokens, {player.count('F')} F tokens, and {player.count('R')} R tokens.\n"
        s += f"You have {player.count('C')} cannonballs.\n"
        s += f"You have {player.damage.damage} damage. If you reach {player.damage.threshold}, you will sink."

        observation = Observation(text=s)

        if self.show_state:
            print(s)

        available_actions = AvailableActions(
            instructions="It is the planning phase. Return your action as a plan consisting of tokens you have available to you. A plan is a sequence of 6 tokens, alternating between movement tokens and cannon tokens.",
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

        # Queue this agent's plan, and return if not every agent has finishing planning yet.
        self.player_from_agent(agent).plan = action
        if any(p.plan is None for p in self.players):
            return

        self.execute_plans()

        for player in self.players:
            player.reset()

    def execute_plans(self):
        # break this function up a bit probably
        for plan_i in range(6):
            if plan_i % 2:
                for player in self.players:
                    token = player.plan[plan_i]
                    shots = ["l", "r"] if token == "b" else [token]

                    for shot in shots:
                        target = player.location

                        # Cannons travel for 3 squares
                        for _ in range(3):
                            target = target.adjacent(shot)

                            if target in self.rocks:
                                break

                            hit = next((p for p in self.players if target == p.location), False)
                            if hit:
                                hit.damage.cannon()
                                break

            else:
                # 1. For all ships that are moving, claim the forward spot.
                for player in self.players:
                    if player.plan[plan_i] in "LFR":
                        player.claim = player.location.forward()
                    else:
                        player.claim = player.location

                # 2. Resolve collisions
                for player in self.players:
                    if player.claim in self.rocks:
                        player.damage.rock()
                    elif any(player.will_collide(t) for t in self.players if t != player):
                        player.damage.ram()
                    else:
                        player.location = player.claim


                # 3. Turn ships that tried to turn, regardless of collision
                for player in self.players:
                    player.location = player.location.turn(player.plan[plan_i])

                # 4. For all turning ships, claim the forward spot
                for player in self.players:
                    if player.plan[plan_i] in "LR":
                        player.claim = player.location.forward()
                    else:
                        player.claim = player.location

                # 5. Resolve collisions again, with slightly different rules.
                for player in self.players:
                    if player.claim in self.rocks:
                        player.damage.rock()

                    elif not any(player.will_collide(t) for t in self.players if t != player):
                        player.location = player.claim

    def play(self) -> Tuple[float, float]:
        while True:
            for player in self.players:
                observation, available_actions = self.get_observation(player.agent)
                action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
                self.update(action, available_actions, player.agent)

            if len(self.players) == 0:
                return (0.5, 0.5)

            if all(player.agent.team_id == 0 for player in self.players):
                return (1., 0.)

            if all(player.agent.team_id == 1 for player in self.players):
                return (0., 1.)