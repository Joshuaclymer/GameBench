from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import random
from games.air_land_sea.cards import Card
from games.air_land_sea.effect_manager import EffectManager

@dataclass
class Theater:
    name: str
    player_1_cards: List[Card] = field(default_factory=list)
    player_2_cards: List[Card] = field(default_factory=list)

    def __post_init__(self):
        self.player_cards = [self.player_1_cards, self.player_2_cards]

    def is_uncovered(self, card: Card, player_id: int) -> bool:
        # the last one in the list is the uncovered card
        return card == self.player_cards[player_id][-1]
        # if player_id == 0:
        #     return card == self.player_1_cards[-1]
        # elif player_id == 1:
        #     return card == self.player_2_cards[-1]
        # else:
        #     raise ValueError("player_id must be 0 or 1")

    """
    Air Theater:
    Player 1: [F-35 (5, Ongoing: +1 to adjacent Theaters, uncovered), Face down (2, covered)]
    Player 2: [Face down (2, covered), Tank Buster (4, Instant: Destroy one face-down card, uncovered)]
    """
    
    def get_theater_string(self):
        # return a string representation of the theater with representation of covered/uncovered cards
        theater_name = self.name  # no "Theater" at the end

        # helper function
        def process_cards(cards, player_id):
            cards_string = ""
            for i, card in enumerate(cards):
                # TODO: apply Escalation, Cover Fire (strength increasing) to str(card)
                # replace $ with "uncovered" or "covered"
                card_status = "uncovered" if self.is_uncovered(card, player_id) else "covered"
                card_string = str(card).replace(")", ", " + card_status + ")")
                # handle commas
                if i == 0:
                    cards_string += card_string
                else:
                    cards_string += f", {card_string}"
            return cards_string

        player_1_cards_string = process_cards(self.player_1_cards, 0)
        player_2_cards_string = process_cards(self.player_2_cards, 1)

        return_string = f"{theater_name} Theater:\nPlayer 1: [{player_1_cards_string}]\nPlayer 2: [{player_2_cards_string}]"
        return return_string

@dataclass
class Board:
    theaters: List[Theater] = field(default_factory=lambda: [
        Theater('Air'),
        Theater('Sea'),
        Theater('Land')
    ])
    ongoing_effects: List[Card] = field(default_factory=list) # ongoing effects that affect the board

    def __post_init__(self):
        # shuffle theaters into random order
        random.shuffle(self.theaters)

    def rotate_theater(self):
        # rotate the theaters clockwise
        self.theater_order.append(self.theaters.pop(0))

    def get_board_string(self):
        # return a string representation of the board
        return_string = ""
        for theater in self.theaters:
            return_string += theater.get_theater_string() + "\n"
        return return_string

    def get_theater(self, theater_id: str):
        # return the theater with the given id
        pass
    
    def search_ongoing_effect_location(self, card: Card, effect_manager: EffectManager) -> List[Optional[int]]:
        target_theater = [None, None]
        # returns a list of size 2
        for player_id in range(2):
            if card in effect_manager.effect_cards[player_id]:
                # if the player has Support, find adjacent theaters
                for index, theater in enumerate(self.theaters):
                    if card in theater.player_cards[player_id]:
                        # if the theater has Support, place its index in the tuple associated with the player
                        target_theater[player_id] = index
        return target_theater

    
    def get_adjacent_theaters(self, theater_index) -> List[int]:
        """
        Calculate the adjacent theaters based on the current theater index.
    
        :param theater_index: Index of the current theater (0, 1, or 2)
        :return: A list of indexes for the adjacent theaters
        """
        # Check for the middle theater, which has both neighbors
        if theater_index == 1:
            return [0, 2]
        # For theaters at the ends (0 and 2), they only have one adjacent theater (1)
        return [1]
    

    def get_theater_strengths(self, effect_manager: EffectManager) -> List[Tuple[int, int]]:
        # return the strength of each theater
                # return the strength of the player in the theater
        # check for Support card
        # then apply to computed adjacent theaters if so
        theater_strengths = [[], [], []]
        support = Card('Support', 'Air', 1, 'Ongoing', 'You gain +3 strength in each adjacent theater')
        support_search = self.search_ongoing_effect_location(support, effect_manager)
        # find adjacent theaters if Support is in play to apply its effect
        # say we get [None, 0] (player 2 has Support in the third theater)
        for player_id in range(2):
            if support_search[player_id] is not None:
                adj_theaters = self.get_adjacent_theaters(support_search[player_id])
            # calculate the strength of each theater based on the cards in it normally
            for index, theater in enumerate(self.theaters):
                strength = 0
                # TODO: apply Escalation, Cover Fire (strength increasing)
                for card in theater.player_cards[player_id]:
                    strength += card.current_strength
                # apply Support effect if necessary
                if index in adj_theaters:
                    strength += 3
                theater_strengths[index].append(strength)
        return theater_strengths