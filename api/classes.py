from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from abc import abstractmethod
from PIL import Image


@dataclass
class Observation:
    text : str
    image : Image = None

@dataclass
class AvailableActions:
    instructions : str
    predefined : Dict[str, str]
    openended : Dict[str, str]

@dataclass
class Action:
    action_id: str
    openended_response: Optional[List] = None

@dataclass
class Agent:
    team_id : int 
    agent_id : int
    agent_type_id : str 

    @abstractmethod
    def take_action(self, rules : dict, observation: Observation, available_actions : AvailableActions):
        pass

@dataclass
class Rules:
    title: str
    summary : str
    additional_details : Optional[dict] # Includes additional details by topic that can be 'expanded' by the language model.

# Each game involves two teams. A team involves includes 1 or more agents.
@dataclass
class Game:
    id : str # Unique identifier in snake_case
    rules : Rules # document that agents can reference at any point. 
    agents : List[Agent] = None # agents in the game. Should be initialized in init_game. Can be more than 2 agents because there can be copies playing on a team.
    show_state : bool = False # whether to e.g. print the board
    game_is_over : bool = False # indicates that no more actions should be taken and the scores should be computed.
    agent_1_kwargs : dict = field(default_factory=dict) # kwargs to pass to the agent 1 class when initializing.
    agent_2_kwargs : dict = field(default_factory=dict) # kwargs to pass to the agent 2 class when initializing.

    @abstractmethod
    def init_game(self, agent_1: Agent, agent_2: Agent):
        pass
        
    @abstractmethod
    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        pass

    @abstractmethod
    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        pass

    @abstractmethod
    def play(self) -> Tuple[float, float]:
        # Returns the scores for agent_1 and agent_2 after the game is finished.
        pass