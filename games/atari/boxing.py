
#%%
import threading
from time import sleep
from atariari.benchmark.wrapper import ram2label
from pettingzoo.atari import boxing_v2
from dataclasses import dataclass
from typing import List, Dict, Tuple
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from PIL import Image
import logging
import random
import asyncio
import matplotlib.pyplot as plt
import threading

# %%
 
boxing_rules = Rules(
    title= "Atari 2600: Boxing",
    summary="""
    Boxing is an adversarial game where precise control and appropriate responses to your opponent are key.
    The players have two minutes (around 1200 steps) to duke it out in the ring. Each step, they can move and punch.
    """,
    additional_details={"Scoring": """
    Scoring hinges on landing punches on the opponent's head, with precision in aligning your punches crucial for effectiveness. Long-range jabs score one point, while power punches at closer range score two. Defensive blocking is achieved by positioning your gloves against the opponent's punches.

    The key to scoring and defense is maintaining the correct distance and ensuring your fist aligns with the opponent's head. Misalignment leads to hitting the opponent's gloves, which doesn't score points. A knockout results in 100 points and ends the game; otherwise, the highest scorer at the round's end is declared the winner, with ties possible.

    Strategic gameplay involves cornering the opponent against the ropes to restrict their movement and increase scoring opportunities. By forcing the opponent into a corner, they have fewer escape routes, allowing for a barrage of scoring punches. Players must also be wary of being cornered themselves, as this limits defensive and offensive maneuvers.

    In terms of scoring, each successful punch not only scores points but also pushes the opponent back slightly, enhancing control over the ring. Dominating by driving the opponent to the ropes can lead to a series of scoring punches. However, players must avoid being trapped against the ropes to maintain the upper hand.
    """,
})

actions_explanation_text = """
Your choice of actions are:
    - 0 - No operation
    - 1 - Fire
    - 2 - Move up
    - 3 - Move right
    - 4 - Move left
    - 5 - Move down
    - 6 - Move upright
    - 7 - Move upleft
    - 8 - Move downright
    - 9 - Move downleft
    - 10 - Fire up
    - 11 - Fire right
    - 12 - Fire left
    - 13 - Fire down
    - 14 - Fire upright
    - 15 - Fire upleft
    - 16 - Fire downright
    - 17 - Fire downleft

    Each action is preceded by its index, and each index-action pair is separated by a newline.
    You can choose:
    1. Which direction to move (8 directions, plus stay put)
    2. Whether to punch or not
    - The no-punch actions are prefixed with Move, and the punch actions are prefixed with "Fire".
    - "No Operation" means stay where you are and don't punch.
"""

observation_explanation_text = """Game state: {state}. The explanations of the keys are:
    - player_x, player_y: The coordinates of the your player
    - enemy_x, enemy_y: The coordinates of the enemy
    - enemy_score, player_score: The current scores of the enemy and player
    - clock: The number of seconds left in the game.
    (0,0) is the top left corner. (30,4) is the topleftmost you can be. (109,87) is the bottom rightmost you can be.
    An image of the game board is also provided. Your player's colour is {player_colour}
"""
# %%
actions = {
    "no operation": "0",
    "fire": "1",
    "move up": "2",
    "move right": "3",
    "move left": "4",
    "move down": "5",
    "move upright": "6",
    "move upleft": "7",
    "move downright": "8",
    "move downleft": "9",
    "fire up": "10",
    "fire right": "11",
    "fire left": "12",
    "fire down": "13",
    "fire upright": "14",
    "fire upleft": "15",
    "fire downright": "16",
    "fire downleft": "17"
}


# Takes an action string and returns an int corresponding to the action if valid.
# If invalid, returns 0(no-op)
def parse_action(act: str) -> int:
    try:
        # Try to convert the action to an integer
        act_int = int(act)
        # If the conversion is successful and the integer is within the desired range, return it
        if 0 <= act_int <= 17:
            return act_int
        # If the integer is not a valid action, return no-op
        else:
            return 0
    except ValueError:
        # If the action can't be converted to an integer, treat it as an action description
        return int(actions.get(act.lower(), "0"))

# %%
def switch_player_enemy_keys(dictionary: Dict[str, int])-> Dict[str, int]:
    new_dict = {}
    for key, value in dictionary.items():
        if 'player' in key:
            new_key = key.replace('player', 'enemy')
        elif 'enemy' in key:
            new_key = key.replace('enemy', 'player')
        else:
            new_key = key
        new_dict[new_key] = value
    return new_dict

# Test the function
# dictionary = {'player_x': 31, 'player_y': 5, 'enemy_x': 109, 'enemy_y': 87, 'enemy_score': 0, 'clock': 89, 'player_score': 0}
# print(switch_player_enemy_keys(dictionary))
# %%
@dataclass
class AtariBoxing(Game):
    rules : Rules = boxing_rules
    id :str = "atari_boxing"
    
    #env = boxing_v2.env(render_mode='ansi',obs_type='ram')
    env = boxing_v2.env(render_mode='rgb_array',obs_type='ram', max_cycles=1000)
    # The higher this number, the more reaction speed matters. And the more disadvantage high-latency agents are at.
    moves_per_second_per_agent = 120.0
    # The probability of the graphical state being shown to the agent
    show_state = False
    logger = logging.getLogger("atari.boxing")
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.WARN)
    if(show_state):
        logger.setLevel(logging.INFO)
        
    def init_game(self, agent_1: Agent, agent_2: Agent):
        # Each agent is a tuple (pettingzoo agent ID, GameBench agent, stored action)
        # A player keeps executing its stored action until it receives a new one
        self.agents = [["first_0",agent_1(team_id=0, agent_id=0, **self.agent_1_kwargs),0], ["second_0",agent_2(team_id=1, agent_id=0, **self.agent_2_kwargs),0]]
        self.game_is_over = False        
        self.env.reset()
        
    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        atari_observation, _, _, _, _ = self.env.last()
        # Interpret the RAM state
        state = ram2label('boxing',atari_observation)
        obs = Observation()
        player_colour = 'grey'
        if agent ==  self.agents[0][1]:
            player_colour = 'white'        
        elif agent == self.agents[1][1]:
            player_colour = 'black'
            state = switch_player_enemy_keys(state)
            
        obs.text = observation_explanation_text.format(state=str(state), player_colour=player_colour)
        obs.image = Image.fromarray(self.env.render())

        acts = AvailableActions(
            instructions = actions_explanation_text,
            predefined = actions,
            openended={}
        )
        #self.logger.info(f"Agent {agent} observation={obs.text}")
        return (obs, acts)
    
    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        self.agents[agent.team_id][2] = parse_action(action.action_id)
        # print(f'stored action {self.agents[agent.team_id][2]} for agent {agent.team_id}')
    

    def agent_loop(self, agent: int):
        self.logger.info(f"Agent {agent} task entered")
        last_observation = None
        while not self.game_is_over:
            observation, available_actions = self.get_observation(self.agents[agent][1])
            if (last_observation == observation):
                # If nothing changed since last observations, no need to act just now
                self.logger.debug(f"Agent {agent} going to sleep")
                #self.logger.info(f"observation={observation.text}")
                last_observation = observation
                sleep(1)
                self.logger.debug(f"Agent {agent} has awoken")
                continue
            last_observation = observation
            #self.logger.info(f"Agent {agent} got observation {observation.text}")
            # Query the agent for what action should be taken
            action = self.agents[agent][1].take_action(rules=self.rules, observation=observation, available_actions=available_actions, show_state = self.show_state)
            self.logger.info(f"Agent {agent} selected action {action.action_id}")
            # Update the stored action
            self.update(action, available_actions, self.agents[agent][1])
        
        self.logger.info(f"Agent {agent} task exiting; Game is over")

    def play(self) -> Tuple[float, float]:
        self.env.render()
        # # Create an event loop
        # loop = asyncio.new_event_loop()

        # # Set the event loop for the new thread
        # asyncio.set_event_loop(loop)

        # # Fire and forget the agent threads
        # for agent in range(2):
        #     loop.create_task(self.agent_loop(agent))

        # # Start the event loop in a new thread
        # threading.Thread(target=loop.run_forever).start()
        
        agentthreads = []

        for agent in range(2):
            agentthreads.append(threading.Thread(target=self.agent_loop, args=(agent,)))
            agentthreads[-1].start()

        self.logger.info("Agent processes fired and forgotten")

        
        # Create the matplotlib image
        fig, ax = plt.subplots()
        img = ax.imshow(self.env.render())
        plt.ion()
        plt.show()

        for agent in self.env.agent_iter():
            observation, _, termination, truncation, _ = self.env.last()
            
            # Display graphical board state
            img.set_data(self.env.render())
            #plt.figure()
            fig.canvas.draw()
            fig.canvas.flush_events()
            
            if termination or truncation:
                self.game_is_over = True
                self.env.close()
                # Parse the state to get the scores
                state = ram2label('boxing',observation)
                return float(state['player_score']), float(state['enemy_score'])
            
            # Fetch the stored action for this agent
            if agent == "first_0":
                action = self.agents[0][2]
            elif agent == "second_0":
                action = self.agents[1][2]
            
            # Execute the stored action
            self.env.step(action)
            self.logger.debug(f'Took action {action} for agent {agent}')
            #self.env.step(parse_action("move downright"))
            
            # Show the board
            # if self.show_state:
            #     state = ram2label('boxing',observation)
            #     print(state)

            # Sleep for a bit to make the game playable
            sleep(1.0/self.moves_per_second_per_agent/2)
        
        plt.ioff()
        self.env.close()
        
        for proc in agentthreads:
            proc.join()
# %%
