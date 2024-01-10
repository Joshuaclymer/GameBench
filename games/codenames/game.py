from api.classes import Agent, Action, Observation, AvailableActions, Rules
from .card import CardType, Card
from .board import Board
from .config import GameConfig as Config
from dataclasses import dataclass, field
from typing import List, Tuple
import random

@dataclass
class CodenamesGame:
    id : str # Unique identifier in snake_case
    rules : Rules # document that agents can reference at any point. 
    spymaster_1 : Agent = None
    spymaster_2 : Agent = None
    operative_1 : Agent = None
    operative_2 : Agent = None

    spymaster_list : List[Agent] = field(default_factory=list)
    operative_list : List[Agent] = field(default_factory=list)
    red_team_list : List[Agent] = field(default_factory=list)
    blue_team_list : List[Agent] = field(default_factory=list)
    show_state : bool = False 
    game_is_over : bool = False 
    game_board : Board = None
    config : Config = None


    def __init__(self, config : Config, agents : List[Agent]):
        if len(agents) != 4:
            raise ValueError("Exactly four agents are required to start the game.")

        self.config = config
        self.rules = self.config.codenames_rules
        self.id = "codenames_game"
        
        team1 = [agent for agent in agents if agent.team_id == 1]
        team2 = [agent for agent in agents if agent.team_id == 2]

        if len(team1) != 2 or len(team2) != 2:
            raise ValueError("Agents must be evenly split into two teams.")

        random.shuffle(team1)
        random.shuffle(team2)

        self.spymaster_1, self.operative_1 = team1
        self.spymaster_2, self.operative_2 = team2

        self.spymaster_list = [self.spymaster_1, self.spymaster_2]
        self.operative_list = [self.operative_1, self.operative_2]

        self.red_team_list = [self.spymaster_1, self.operative_1]
        self.blue_team_list = [self.spymaster_2, self.operative_2]

        self.setup_board()

    def setup_board(self):
        words = self.config.WORD_LIST
        self.game_board = Board(words, self.config)
        self.game_board.current_turn = CardType.RED

    def get_agent_team(self, agent : Agent) -> CardType:
        if agent in self.red_team_list:
            return CardType.RED
        elif agent in self.blue_team_list:
            return CardType.BLUE
        else:
            raise ValueError("Agent is not on a team.")
        
    def get_spymaster_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        if agent not in self.spymaster_list:
            raise ValueError("Agent is not a spymaster.")
        
        team_name = self.game_board.current_team_name()
        text = team_name + " Spymaster\n\n" + "Current board:\n"
        for index, card in enumerate(self.game_board.cards):
            if self.game_board.revealed[index]:
                text += f"{card.word} ({card.card_type}) (REVEALED)\n"
            else:
                text += f"{card.word} ({card.card_type}) (HIDDEN)\n"

        if self.get_agent_team(agent) == CardType.RED and self.game_board.last_blue_hint:
            previous_turn_info = f"Last Turn Hint: '{self.game_board.last_blue_hint[0]}', for {self.game_board.last_blue_hint[1]} cards.\nLast Turn Guesses: {', '.join(self.game_board.last_blue_guesses)}"
            text += "\n\n" + previous_turn_info
        elif self.get_agent_team(agent) == CardType.BLUE and self.game_board.last_red_hint:
            previous_turn_info = f"Last Turn Hint: '{self.game_board.last_red_hint[0]}', for {self.game_board.last_red_hint[1]} cards.\nLast Turn Guesses: {', '.join(self.game_board.last_red_guesses)}"
            text += "\n\n" + previous_turn_info
        
        return Observation(text), AvailableActions("Enter a one-word clue and the number of cards the clue relates to. In the following format: word,3", {}, {"submit_clue": Action("submit_clue")})

    def get_operative_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        if agent not in self.operative_list:
            raise ValueError("Agent is not an operative.")            

        team_name = self.game_board.current_team_name()
        text = team_name + " Operative\n\n" + "Current board:\n"
        for index, card in enumerate(self.game_board.cards):
            if self.game_board.revealed[index]:
                text += f"{card.word} ({card.card_type}) (REVEALED)\n"
            else:
                text += f"{card.word} (HIDDEN)\n"

        current_clue, current_num_guesses = self.game_board.last_hint
        if current_clue:
            clue_text = f"Your clue is: '{current_clue}' for {current_num_guesses} cards."
        text += "\n\n" + clue_text

        # Show last turn info from the opposing team
        if self.get_agent_team(agent) == CardType.RED and self.game_board.last_blue_hint:
            previous_turn_info = f"Last Turn Hint: {self.game_board.last_blue_hint[0]}, for {self.game_board.last_blue_hint[1]} cards.\nLast Turn Guesses: {', '.join(self.game_board.last_blue_guesses)}"
            text += "\n\n" + previous_turn_info
        elif self.get_agent_team(agent) == CardType.BLUE and self.game_board.last_red_hint:
            previous_turn_info = f"Last Turn Hint: {self.game_board.last_red_hint[0]}, for {self.game_board.last_red_hint[1]} cards.\nLast Turn Guesses: {', '.join(self.game_board.last_red_guesses)}"
            text += "\n\n" + previous_turn_info

        possible_actions = {}
        if self.game_board.guesses_made_during_turn <= current_num_guesses or current_num_guesses == 0:
            for index, card in enumerate(self.game_board.cards):
                if not self.game_board.revealed[index]:
                    possible_actions[card.word] = Action("guess_" + str(index))
        if self.game_board.guesses_made_during_turn > 0:
            possible_actions["end_turn"] = Action("end_turn")

        return Observation(text), AvailableActions(clue_text, possible_actions, {})



    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        if agent in self.spymaster_list:
            return self.get_spymaster_observation(agent)
        elif agent in self.operative_list:
            return self.get_operative_observation(agent)
        else:
            raise ValueError("Agent is not in the game.")
        
    def update_spymaster(self, action : Action, available_actions : AvailableActions, agent : Agent):
        if agent not in self.spymaster_list:
            raise ValueError("Agent is not a spymaster.")

        if action.action_id == "submit_clue":
            clue, num_guesses = action.openended_response.split(",")
            num_guesses = int(num_guesses)
            if num_guesses < 0:
                raise ValueError("Number of guesses must be non-negative.")
            self.game_board.last_hint = (clue, num_guesses)
        else:
            raise ValueError("Invalid action for spymaster.")
        
        if self.get_agent_team(agent) == CardType.RED:
            self.game_board.last_red_hint = (clue, num_guesses)
        else:
            self.game_board.last_blue_hint = (clue, num_guesses)

    def handle_turn(self, card, index, expected_card_type):
        if card.card_type == expected_card_type:
            self.game_board.reveal_card(index)
            if self.game_board.last_hint[1] == self.game_board.guesses_made_during_turn:
                self.game_board.end_turn()
        elif card.card_type in [CardType.RED, CardType.BLUE]:
            self.game_board.reveal_card(index)
            self.game_board.end_turn()
        else:
            self.game_is_over = True

        
    def update_operative(self, action : Action, available_actions : AvailableActions, agent : Agent):
        if agent not in self.operative_list:
            raise ValueError("Agent is not an operative.")
        if action.action_id.startswith("guess_"):
            index = int(action.action_id.split("_")[1])
            
            guessed_word = self.game_board.cards[index].word
            card_type = self.game_board.cards[index].card_type
            if self.get_agent_team(agent) == CardType.RED:
                self.game_board.last_red_guesses.append(f"{guessed_word} (guessed) - {card_type}")
            else:
                self.game_board.last_blue_guesses.append(f"{guessed_word} (guessed) - {card_type}")

            card = self.game_board.cards[index]

            if card.card_type == CardType.ASSASSIN:
                self.game_is_over = True
            elif card.card_type == CardType.NEUTRAL:
                self.game_board.reveal_card(index)
                self.game_board.increment_guesses()
                self.game_board.end_turn()
            else:
                self.game_board.reveal_card(index)
                self.game_board.increment_guesses()
                if card.card_type == CardType.ASSASSIN:
                    self.game_is_over = True
                elif self.game_board.current_turn == CardType.RED:
                    self.handle_turn(card, index, CardType.RED)
                else:
                    self.handle_turn(card, index, CardType.BLUE)
        elif action.action_id == "end_turn":
            self.game_board.end_turn()
            self.game_board.guesses_made_during_turn = 0
        else:
            raise ValueError("Invalid action for operative.")

    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        if agent in self.spymaster_list:
            self.update_spymaster(action, available_actions, agent)
        elif agent in self.operative_list:
            self.update_operative(action, available_actions, agent)
        else:
            raise ValueError("Agent is not in the game.")
        
    
    def turn_changed_to_other_team(self, current_team) -> bool:
        # Check if the current team is different from the last turn's team
        if self.last_turn_team and self.last_turn_team != current_team:
            return True
        return False
    
    def play(self) -> Tuple[float, float]:
        while not self.game_is_over:
            # Determine the current team's spymaster and operative
            if self.game_board.current_turn == CardType.RED:
                spymaster = self.spymaster_1
                operative = self.operative_1
            else:
                spymaster = self.spymaster_2
                operative = self.operative_2

            # Spymaster's action
            if self.game_board.last_hint is None:
                spymaster_observation, spymaster_available_actions = self.get_observation(spymaster)
                spymaster_action = spymaster.take_action(self.rules, spymaster_observation, spymaster_available_actions, show_state=True)
                self.update(spymaster_action, spymaster_available_actions, spymaster)

            # Operative's action
            operative_observation, operative_available_actions = self.get_observation(operative)
            operative_action = operative.take_action(self.rules, operative_observation, operative_available_actions, show_state=True)
            self.update(operative_action, operative_available_actions, operative)

            # Check for game end conditions
            possible_winner = self.game_board.winner()
            if self.game_is_over or possible_winner:
                if self.game_board.current_turn == CardType.RED or possible_winner == CardType.BLUE:
                    return (-1, 1)
                else:
                    return (1, -1)