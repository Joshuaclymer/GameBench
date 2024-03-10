from dataclasses import dataclass, field
from typing import List, Dict
from games.air_land_sea.cards import Card
from api.classes import AvailableActions, Action

@dataclass
class EffectManager:
    player_1_effect_cards : List[Card] = field(default_factory=list)
    player_2_effect_cards : List[Card] = field(default_factory=list)


    def __post_init__(self):
        self.effect_cards = [self.player_1_effect_cards, self.player_2_effect_cards]
    
    def non_matching_theaters(self, current_theater: str) -> List[str]:
        # returns a list of theater names that are not the same as the input theater
        theaters = ['Air', 'Sea', 'Land']
        theaters.remove(current_theater)
        return theaters

    def modify_available_actions(self, available_actions : AvailableActions, player_hand : List[Card], player_id : int) -> AvailableActions:
        # modifies the available actions based on the effects in play
        # Aerodrome (3 strength or less to non matching theaters)
        # Airdrop (1 time to non matching theater)
        # called right after available actions are generated

        # first check for Aerodrome Effect in player's effect cards
        if 'Aerodrome' in [card.name for card in self.effect_cards[player_id]]:
            # allow player to play cards of strength 3 or less faceup to non matching theaters
            # what does available actions look like?
            # if n = number of cards there are 3n actions (n play faceup + 3n facedown for each theater)
            # if 1 card is strength 3 or less, add 2 actions to play it faceup to non matching theaters
            three_or_less = [card for card in player_hand if card.strength <= 3]
            if len(three_or_less) > 0:
                # if not empty, add the actions 
                num_available_actions = len(available_actions.predefined)
                print(f"num available actions: {num_available_actions}")
                for ind, card in enumerate(three_or_less):
                    # identify non matching theaters of the card
                    non_matching_theaters = self.non_matching_theaters(card.theater)
                    for nm_ind, theater in enumerate(non_matching_theaters):
                        available_actions.predefined[str(num_available_actions + ind*2 + nm_ind)] = f"Play {card} faceup to {theater}."

        # next check for Airdrop Effect in player's effect cards
        if 'Airdrop' in [card.name for card in self.effect_cards[player_id]]:
            # allow player to play 1 card faceup to non matching theater
            num_available_actions = len(available_actions.predefined)
            # make sure to remove effect after it is used, how?
            # if n cards to play, add 2n actions (faceup play in all non matching theaters)
            for ind, card in enumerate(player_hand):
                non_matching_theaters = self.non_matching_theaters(card.theater)
                for nm_ind, theater in enumerate(non_matching_theaters):
                    available_actions.predefined[str(num_available_actions + ind*2 + nm_ind)] = f"Play {card} faceup to {theater}."
            # after this function is called, the effect is removed
            airdrop = Card('Airdrop', 'Air', 2, 'Instant', 'The next time you play a card, you may play it to a non-matching theater')
            self.remove_effect(airdrop, player_id)

        return available_actions

    def add_effect(self, card : Card, player_id : int):
        # happens after post play triggers are checked
        self.effect_cards[player_id].append(card)
        pass

    def remove_effect(self, card : Card, player_id : int):
        self.effect_cards[player_id].remove(card)
        pass

    # TODO: how do i say which player the effect is affecting? (can be one or both)
    # how do i store is answered by
    # how do we know which theater is affected
    # access which theater the card is in, then use logic to determine theaters affected

    # lets calculate modified theater strength at the end of the game rather than at all times