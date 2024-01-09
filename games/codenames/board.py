# board for codenames game
from .card import Card, CardType
from .config import GameConfig as config
import random

class Board:
    cards_remaining : int = 0
    guesses_made_during_turn : int = 0
    last_hint : (str, int) = None
    current_turn : CardType = None

    def increment_guesses(self):
        self.guesses_made_during_turn += 1

    @staticmethod
    def cards_from_words(words, first_team: CardType, second_team: CardType):
        total_cards = config.FIRST_TEAM_CARDS + config.SECOND_TEAM_CARDS + config.ASSASSIN_CARDS + config.NEUTRAL_CARDS
        if len(words) != total_cards:
            raise ValueError("Wrong number of words for board")
        
        cards = []
        for word in words:
            cards.append(Card(word, CardType.NEUTRAL))

        random.shuffle(cards)
        # place first team cards
        cards[0:config.FIRST_TEAM_CARDS] = [Card(word, first_team) for word in words[0:config.FIRST_TEAM_CARDS]]
        # place second team cards
        cards[config.FIRST_TEAM_CARDS:config.FIRST_TEAM_CARDS + config.SECOND_TEAM_CARDS] = [Card(word, second_team) for word in words[config.FIRST_TEAM_CARDS:config.FIRST_TEAM_CARDS + config.SECOND_TEAM_CARDS]]
        # place assassin card
        cards[config.FIRST_TEAM_CARDS + config.SECOND_TEAM_CARDS] = Card(words[config.FIRST_TEAM_CARDS + config.SECOND_TEAM_CARDS], CardType.ASSASSIN)        
        random.shuffle(cards)
        return cards
        
    def current_team_name(self):
        if self.current_turn == CardType.RED:
            return "Red Team"
        else:
            return "Blue Team"

    def __init__(self, words, game_config):
        num_cards = game_config.FIRST_TEAM_CARDS + game_config.SECOND_TEAM_CARDS + game_config.ASSASSIN_CARDS + game_config.NEUTRAL_CARDS
        self.cards_remaining = num_cards
        random_words = random.sample(words, num_cards)
        print(len(words) == len(set(words)))
        self.cards = Board.cards_from_words(random_words, CardType.RED, CardType.BLUE)
        self.revealed = [False for _ in self.cards]
        self.current_turn = CardType.RED

        
    def end_turn(self):
        if self.current_turn == CardType.RED:
            self.current_turn = CardType.BLUE
        else:
            self.current_turn = CardType.RED
        self.guesses_made_during_turn = 0
        self.last_hint = None

    def winner(self):
        if self.cards_remaining != 0:
            return None
        
        red_cards = 0
        blue_cards = 0
        for index, card in enumerate(self.cards):
            if self.revealed[index]:
                if card.card_type == CardType.RED:
                    red_cards += 1
                elif card.card_type == CardType.BLUE:
                    blue_cards += 1
        if red_cards == config.FIRST_TEAM_CARDS:
            return CardType.RED
        elif blue_cards == config.SECOND_TEAM_CARDS:
            return CardType.BLUE
        else:
            return None
        
    def reveal_card(self, index):
        self.revealed[index] = True
        return self.cards[index].card_type
    

    

