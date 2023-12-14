from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from abc import abstractmethod
from PIL import Image


@dataclass
class Observation:
    image : Image
    text : str

@dataclass
class AvailableActions:
    predefined : Dict[str, str] = {}
    openended : Dict[str, str] = {}

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
    def take_action(self, observation: Observation, available_actions : AvailableActions):
        pass

# Each game involves two teams. A team involves includes 1 or more agents.
@dataclass
class Game:
    id : str = None # Unique identifier in snake_case
    title : str = None # Displayable title of the game
    rules = None # Multimodal document that agents can reference at any point
    game_is_over : bool = False # indicates that no more actions should be taken and the scores should be computed.
    agents : List[Agent] # agents in the game. Should be initialized in init_game. Can be more than 2 agents because there can be copies playing on a team.
    show_state : False # whether to e.g. print the board

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
    def get_team_scores(self) -> Tuple(float, float):
        pass

    @abstractmethod
    def game_loop(self) -> Tuple(float, float):
        pass


@dataclass
class TwoPlayerTurnBasedGame(Game):
    def game_loop(self, player_1 : Agent, player_2: Agent):
        self.init_game()
        while True:
            # Player 1 moves
            observation, available_actions = self.get_observation(player_1)
            action = player_1.take_action(observation, available_actions, show_state=self.show_state)
            self.update(action, available_actions, player_1)
            if self.game_is_over:
                break

            # Player 2 moves
            observation, available_actions = self.get_observation(player_2)
            action = player_2.take_action(observation, available_actions, show_state=self.show_state)
            self.update(action, available_actions, player_2)
            if self.game_is_over:
                break

        return self.get_team_scores()