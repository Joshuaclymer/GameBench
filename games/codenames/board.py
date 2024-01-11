from .card import Card, CardType
from dataclasses import dataclass, field
from typing import List, Tuple
import random

class Board:
    cards: List[Card] = field(default_factory=list)
    revealed: List[bool] = field(default_factory=list)
    last_hint: Tuple[str, int] = (None, 0)
    current_turn: CardType = CardType.RED
    guesses_made_during_turn: int = 0
    last_red_hint: Tuple[str, int] = None
    last_blue_hint: Tuple[str, int] = None
    last_red_guesses: List[str] = field(default_factory=list)
    last_blue_guesses: List[str] = field(default_factory=list)

    def __init__(self, config):
        self.config = config
        self.initialize_board()
        self.revealed = [False for _ in self.cards]
        self.current_turn = CardType.RED
        self.last_red_hint = None
        self.last_blue_hint = None
        self.last_red_guesses = []
        self.last_blue_guesses = []

    def increment_guesses(self):
        self.guesses_made_during_turn += 1

    def initialize_board(self):
        words = random.sample(self.config.WORD_LIST, self.config.TOTAL_CARDS)
        self.cards = Board.cards_from_words(self.config, words, CardType.RED, CardType.BLUE)
        self.revealed = [False] * len(self.cards)

    @staticmethod
    def cards_from_words(config, words, first_team: CardType, second_team: CardType) -> List[Card]:
        cards = [Card(word, CardType.NEUTRAL) for word in words]
        cards[:config.FIRST_TEAM_CARDS] = [Card(word, first_team) for word in words[:config.FIRST_TEAM_CARDS]]
        start_second_team = config.FIRST_TEAM_CARDS
        end_second_team = config.FIRST_TEAM_CARDS + config.SECOND_TEAM_CARDS
        cards[start_second_team:end_second_team] = [Card(word, second_team) for word in words[start_second_team:end_second_team]]
        cards[end_second_team] = Card(words[end_second_team], CardType.ASSASSIN)
        random.shuffle(cards)
        return cards

    def current_team_name(self) -> str:
        return "Red Team" if self.current_turn == CardType.RED else "Blue Team"

    def is_turn_over(self) -> bool:
        if self.last_hint[1] == 0:
            return False
        return self.guesses_made_during_turn >= self.last_hint[1] + 1


    def end_turn(self):
        self.current_turn = CardType.BLUE if self.current_turn == CardType.RED else CardType.RED
        self.guesses_made_during_turn = 0
        self.last_hint = (None, 0)


    def reveal_card(self, index: int) -> CardType:
        if 0 <= index < len(self.cards) and not self.revealed[index]:
            self.revealed[index] = True
            return self.cards[index].card_type
        return None

    def winner(self) -> CardType:
        red_cards_revealed = sum(1 for i, card in enumerate(self.cards) if card.card_type == CardType.RED and self.revealed[i])
        blue_cards_revealed = sum(1 for i, card in enumerate(self.cards) if card.card_type == CardType.BLUE and self.revealed[i])
        if red_cards_revealed == self.config.FIRST_TEAM_CARDS:
            return CardType.RED
        elif blue_cards_revealed == self.config.SECOND_TEAM_CARDS:
            return CardType.BLUE
        assassin_revealed = any(card.card_type == CardType.ASSASSIN and self.revealed[i] for i, card in enumerate(self.cards))
        if assassin_revealed:
            return CardType.BLUE if self.current_turn == CardType.RED else CardType.RED
        return None

    def is_game_over(self) -> bool:
        return self.winner() is not None or any(card.card_type == CardType.ASSASSIN and self.revealed[i] for i, card in enumerate(self.cards))

    def update_last_turn_info(self, hint: str, num_guesses: int):
        if self.current_turn == CardType.RED:
            self.last_red_hint = (hint, num_guesses)
            self.last_red_guesses.append(f"{num_guesses} guesses with hint '{hint}'")
        else:
            self.last_blue_hint = (hint, num_guesses)
            self.last_blue_guesses.append(f"{num_guesses} guesses with hint '{hint}'")