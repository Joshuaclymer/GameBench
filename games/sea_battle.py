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

# maybe generate image?
# in actions, maybe say what coordinates they will end up at
# maybe say something like: last turn you were at xy, chose this action, and etc happened as result

@dataclass
class Location:
    position : complex
    heading  : complex = field(default_factory=lambda: random.choice([1, 1j, -1, -1j]))

    def forward(self):
        """Returns location one square in front of this location."""
        return Location(self.position + self.heading, self.heading)

    def turn(self, direction):
        return Location(self.position, self.heading * direction)

    def adjacent(self, direction):
        return Location(self.position + self.heading*direction, self.heading)

    @property
    def xy(self):
        return int(self.position.real), int(self.position.imag)

    @property
    def cardinal(self):
        # Alternatively, maybe say "increasing X", "increasing Y", etc.
        return {1: "direction of increasing X coordinates", 1j: "direction of increasing Y coordinates", -1: "direction of decreasing X coordinates", -1j: "direction of decreasing Y coordinates"}[self.heading]

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
    damage   : DamageCounter = field(default_factory=lambda: DamageCounter())
    plan     : List[str] = None

    def will_collide(self, t):
        return self.claim == t.claim

    def reset(self):
        self.plan = None

    def __eq__(self, t):
        return self.location == t.location

@dataclass
class SeaBattle(Game):
    id : str = "sea_battle"
    rules : Rules = Rules(
        title="Sea Battle",
        summary="Sink all of your opponent team's ships before they sink all of your team's ships. Players can be damaged in three ways: (1) by getting shot at by another player, (2) by sailing into a rock, (3) by colliding with another ship. After a player has sustained enough damage, they sink and cannot play the rest of the round. A team wins if they have at least one live ship when all of their opponents have sunken. The board is a 24x24 grid. Some squares are occupied by rocks and some are occupied by players' ships. Each turn, all players choose how they want to move and how they want to shoot. All players' choices are executed simultaneously. At the start of the game, there are three players on each team.",
        additional_details={
            "Damage": "Players can be damaged in three ways: (1) by getting shot at by another player, (2) by sailing into a rock, (3) by colliding with another ship.",
            "Sinking": "After a player has sustained enough damage, they sink and cannot play the rest of the round.",
            "Winning": "A team wins if they have at least one live ship when all of their opponents have sunken.",
            "Board": "The board is a 24x24 grid. Some squares are occupied by rocks and some are occupied by players' ships.",
            "Gameplay": "Each turn, all players choose how they want to move and how they want to shoot. All players' choices are executed simultaneously.",
            "Teams": "At the start of the game, there are three players on each team."
        }
    )

    def init_game(self, agent1 : Agent, agent2 : Agent):
        team1 = [agent1(agent_id=i, team_id=0) for i in range(PLAYERS_PER_TEAM)]
        team2 = [agent2(agent_id=i+PLAYERS_PER_TEAM, team_id=1) for i in range(PLAYERS_PER_TEAM)]
        self.agents = team1 + team2

        all_locations = [Location(x+y*1j) for x in range(1, 23) for y in range(1, 23)]
        random.shuffle(all_locations)

        self._players = [
            Player(agent, location)
            for _, agent, location
            in zip(range(N_PLAYERS), self.agents, all_locations)
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

    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        player = self.player_from_agent(agent)
        s = "Rocks line the border of the 24 by 24 board.\n"
        for p in self.players:
            q = 'Your ship' if p.agent == agent else ('A teammate\'s ship' if p.agent.team_id == agent.team_id else 'An opponent\'s ship')
            s += f"{q} is located at {p.location.xy} facing {p.location.cardinal}.\n"
        s += "There are more rocks located at " + ", ".join([str(r.xy) for r in self.rocks[-20:]]) + "\n"
        s += f"You've sustained {player.damage.damage} damage. If you reach {player.damage.threshold}, you will sink."
        observation = Observation(text=s)

        if self.show_state:
            print(s)

        available_actions = AvailableActions(
            instructions="Choose your action for the next turn.",
            predefined={
                "move left and shoot left"    : "Move forward one square, rotate left, move forward another square, then shoot to your left.",
                "move left and shoot right"   : "Move forward one square, rotate left, move forward another square, then shoot to your right.",
                "move forward and shoot left" : "Move forward one square, then shoot to your left.",
                "move forward and shoot right": "Move forward one square, then shoot to your right.",
                "move right and shoot left"   : "Move forward one square, rotate right, move forward another square, then shoot to your left.",
                "move right and shoot right"  : "Move forward one square, rotate right, move forward another square, then shoot to your right.",
                "don't move and shoot left"   : "Don't move, then shoot to your left.",
                "don't move and shoot right"  : "Don't move, then shoot to your right.",
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
        self.player_from_agent(agent).plan = action.split(" and ")
        if any(p.plan is None for p in self.players):
            return

        self.move_ships()
        self.fire_cannons()

        for player in self.players:
            player.reset()

    def move_ships(self):
        for player in self.players:
            print("Player", player.agent.agent_id, player.plan[0])
        # 1. For all ships that are moving, claim the forward spot.
        for player in self.players:
            if player.plan[0] in ["move left", "move forward", "move right"]:
                player.claim = player.location.forward()
            else:
                player.claim = player.location

        # 2. Resolve collisions
        for player in self.players:
            if player.claim in self.rocks:
                print("Ram rock!", player.agent.agent_id)
                player.damage.rock()
            elif any(player.will_collide(t) for t in self.players if t != player):
                print("Collision!", player.agent.agent_id)
                player.damage.ram()
            else:
                player.location = player.claim

        # 3. Turn ships that tried to turn, regardless of collision
        for player in self.players:
            direction = {"move left": 1j, "move right": -1j, "move forward": 1, "don't move": 1}
            player.location = player.location.turn(direction[player.plan[0]])

        # 4. For all turning ships, claim the forward spot
        for player in self.players:
            if player.plan[0] in ["move left", "move right"]:
                player.claim = player.location.forward()
            else:
                player.claim = player.location

        # 5. Resolve collisions again, with slightly different rules.
        for player in self.players:
            if player.claim in self.rocks:
                print("Ram rock!", player.agent.agent_id)
                player.damage.rock()

            elif not any(player.will_collide(t) for t in self.players if t != player):
                player.location = player.claim

    def fire_cannons(self):
        for player in self.players:
            print("Player", player.agent.agent_id, player.plan[1])
            direction = 1j if player.plan[1] == "shoot left" else -1j

            target = player.location
            for _ in range(3):
                target = target.adjacent(direction)

                if target in self.rocks:
                    break

                hit = next((p for p in self.players if target == p.location), False)
                if hit:
                    print("Cannon hit!", hit.agent.agent_id)
                    hit.damage.cannon()
                    break

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