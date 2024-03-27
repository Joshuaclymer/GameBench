from api.classes import Agent, Action, Observation, AvailableActions, Rules
from .card import CardType, Card
from .board import Board
from .config import GameConfig as Config
from dataclasses import dataclass, field
from typing import List, Tuple
import random
from api.classes import Game

default_config = Config()

@dataclass
class CodenamesGame(Game):
    config : Config = default_config
    rules : Rules = default_config.codenames_rules
    id : str = "codenames" # Unique identifier in snake_case

    spymaster_1 : Agent = None
    spymaster_2 : Agent = None
    operative_1 : Agent = None
    operative_2 : Agent = None

    spymaster_list : List[Agent] = field(default_factory=list)
    operative_list : List[Agent] = field(default_factory=list)
    red_team_list : List[Agent] = field(default_factory=list)
    blue_team_list : List[Agent] = field(default_factory=list)
    show_state : bool = True
    game_is_over : bool = False
    game_board : Board = None

    def init_game(self, agent_1_class: Agent, agent_2_class: Agent):
        agents = [
            agent_1_class(team_id=1, agent_id=0, **self.agent_1_kwargs),
            agent_1_class(team_id=1, agent_id=1, **self.agent_1_kwargs),
            agent_2_class(team_id=2, agent_id=2, **self.agent_2_kwargs),
            agent_2_class(team_id=2, agent_id=3, **self.agent_2_kwargs)
        ]

        self._validate_agents(agents)
        self._assign_teams(agents)
        self.setup_board()

    def set_config(self, config: Config):
        self.config = config
        self.rules = config.codenames_rules

    def _validate_agents(self, agents):
        if len(agents) != 4:
            raise ValueError("Exactly four agents are required to start the game.")
        teams = [agent.team_id for agent in agents]
        if teams.count(1) != 2 or teams.count(2) != 2:
            raise ValueError("Agents must be evenly split into two teams.")

    def _assign_teams(self, agents):
        team1, team2 = self._split_into_teams(agents)
        self.spymaster_1, self.operative_1 = random.sample(team1, 2)
        self.spymaster_2, self.operative_2 = random.sample(team2, 2)
        self._populate_team_lists()

    def _split_into_teams(self, agents):
        team1 = [agent for agent in agents if agent.team_id == 1]
        team2 = [agent for agent in agents if agent.team_id == 2]
        return team1, team2

    def _populate_team_lists(self):
        self.spymaster_list = [self.spymaster_1, self.spymaster_2]
        self.operative_list = [self.operative_1, self.operative_2]
        self.red_team_list = [self.spymaster_1, self.operative_1]
        self.blue_team_list = [self.spymaster_2, self.operative_2]


    def setup_board(self):
        self.game_board = Board(self.config)
        self.game_board.current_turn = CardType.RED


    def get_agent_team(self, agent: Agent) -> CardType:
        if agent in self.red_team_list:
            return CardType.RED
        elif agent in self.blue_team_list:
            return CardType.BLUE
        else:
            raise ValueError("Agent is not on a team.")

    def _get_observation_text(self, agent: Agent) -> str:
        team_name = self.game_board.current_team_name()
        agent_role = "Spymaster" if agent in self.spymaster_list else "Operative"
        text = f"{team_name} {agent_role}\n\nCurrent board:\n"
        for index, card in enumerate(self.game_board.cards):
            text += f"{card.word} ({card.card_type if agent in self.spymaster_list or self.game_board.revealed[index] else 'UNKNOWN'}) ({'REVEALED' if self.game_board.revealed[index] else 'HIDDEN'})\n"
        return text

    def get_spymaster_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        self._validate_role(agent, self.spymaster_list, "Spymaster")

        text = self._get_observation_text(agent)
        last_hint_info = self._get_last_hint_info(agent)
        text += "\n\n" + last_hint_info

        if self.show_state:
            print(text)

        actions = {"submit_clue": "Submit a clue to help your team guess the cards. In the following format: word,number_of_cards"}
        return Observation(text), AvailableActions("Enter a one-word clue and the number of cards from your team that the clue relates to. In the following format: word,3", {}, actions)

    def get_operative_observation(self, agent: Agent) -> Tuple[Observation, AvailableActions]:
        self._validate_role(agent, self.operative_list, "Operative")

        text = self._get_observation_text(agent)
        current_clue, current_num_guesses = self.game_board.last_hint
        if current_clue:
            text += f"\n\nYour clue is: '{current_clue}' for {current_num_guesses} cards. You have made {self.game_board.guesses_made_during_turn} guesses so far."


        last_hint_info = self._get_last_hint_info(agent)
        text += "\n\n" + last_hint_info

        if self.show_state:
            print(text)

        actions = self._get_operative_actions(current_num_guesses)
        return Observation(text), AvailableActions("Please guess a card based on the given clue.", actions, {})

    def _get_last_hint_info(self, agent: Agent) -> str:
        text = ""
        if self.get_agent_team(agent) == CardType.RED and self.game_board.last_blue_hint:
            last_hint, num_guesses = self.game_board.last_blue_hint
            last_turn_guesses = ', '.join(self.game_board.last_blue_guesses)
            text = f"Last Turn Hint: '{last_hint}', for {num_guesses} cards.\nLast Turn Guesses: {last_turn_guesses}"
        elif self.get_agent_team(agent) == CardType.BLUE and self.game_board.last_red_hint:
            last_hint, num_guesses = self.game_board.last_red_hint
            last_turn_guesses = ', '.join(self.game_board.last_red_guesses)
            text = f"Last Turn Hint: '{last_hint}', for {num_guesses} cards.\nLast Turn Guesses: {last_turn_guesses}"
        return text

    def _get_operative_actions(self, current_num_guesses) -> dict:
        actions = {}
        if self.game_board.guesses_made_during_turn <= current_num_guesses or current_num_guesses == 0:
            for index, card in enumerate(self.game_board.cards):
                if not self.game_board.revealed[index]:
                    actions["guess_" + str(index)] = "Guess the word: " + card.word
        actions["end_turn"] = "End your current turn."
        return actions


    def _validate_role(self, agent: Agent, role_list: List[Agent], role_name: str):
        if agent not in role_list:
            raise ValueError(f"Agent is not a {role_name}.")


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
            try:
                clue, num_guesses = action.openended_response.split(",")
            except ValueError:
                clue = "None"
                num_guesses = 1
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
            if self.game_board.last_hint[1] + 1 == self.game_board.guesses_made_during_turn:
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
                self.game_board.reveal_card(index)
                self.game_board.increment_guesses()
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

    def update(self, action: Action, available_actions: AvailableActions, agent: Agent):
        if agent in self.spymaster_list:
            self.update_spymaster(action, available_actions, agent)
        elif agent in self.operative_list:
            self.update_operative(action, available_actions, agent)
        else:
            raise ValueError("Agent is not in the game.")


    def reset_last_turn_guesses(self):
        if self.game_board.current_turn == CardType.BLUE:
            self.game_board.last_blue_guesses = []
        else:
            self.game_board.last_red_guesses = []

    def _process_spymaster_turn(self, spymaster: Agent):
        if self.game_board.last_hint[0] is None:
            self.reset_last_turn_guesses()
            observation, actions = self.get_spymaster_observation(spymaster)
            action = spymaster.take_action(self.rules, observation, actions, show_state=self.show_state)
            if action.action_id not in actions.predefined and action.action_id not in actions.openended:
                clue = "None"
                num_guesses = 1
                action = Action(f"submit_clue", openended_response=f"{clue},{num_guesses}")

            self.update(action, actions, spymaster)

    def _check_turn_end(self) -> bool:
        return self.game_board.is_turn_over()

    def _process_operative_turn(self, operative: Agent):
        observation, actions = self.get_operative_observation(operative)
        action = operative.take_action(self.rules, observation, actions, show_state=self.show_state)
        if action.action_id not in actions.predefined and action.action_id not in actions.openended:
            action = Action(action_id=random.choice(list(actions.predefined.keys())))
        self.update(action, actions, operative)

        if self._check_turn_end():
            self.game_board.end_turn()

    def _check_game_end(self) -> bool:
        return self.game_is_over or self.game_board.is_game_over()

    def _determine_scores(self) -> Tuple[float, float]:
        winner = self.game_board.winner()
        red_points = sum(1 for i, card in enumerate(self.game_board.cards) if card.card_type == CardType.RED and self.game_board.revealed[i])
        blue_points = sum(1 for i, card in enumerate(self.game_board.cards) if card.card_type == CardType.BLUE and self.game_board.revealed[i])
        assassin_revealed = any(card.card_type == CardType.ASSASSIN and self.game_board.revealed[i] for i, card in enumerate(self.game_board.cards))

        if assassin_revealed:
            if winner == CardType.RED:
                blue_points = 0
            elif winner == CardType.BLUE:
                red_points = 0

        if winner == CardType.RED:
            red_points += 3
        elif winner == CardType.BLUE:
            blue_points += 3

        total_points = red_points + blue_points

        if total_points == 0:
            return 0.5, 0.5

        return red_points / total_points, blue_points / total_points

    def _get_current_team(self) -> Tuple[Agent, Agent]:
        if self.game_board.current_turn == CardType.RED:
            return self.spymaster_1, self.operative_1
        else:
            return self.spymaster_2, self.operative_2


    def play(self) -> Tuple[float, float]:
        while not self.game_is_over:
            current_team = self._get_current_team()
            spymaster, operative = current_team

            self._process_spymaster_turn(spymaster)
            self._process_operative_turn(operative)

            if self._check_game_end():
                return self._determine_scores()