from dataclasses import dataclass, field
from typing import List
from games.air_land_sea.cards import Card

@dataclass
class EffectManager:
    player_1_effect_cards : List[Card] = field(default_factory=list)
    player_2_effect_cards : List[Card] = field(default_factory=list)


    def __post_init__(self):
        self.effect_cards = [self.player_1_effect_cards, self.player_2_effect_cards]

    def modify_available_actions(self, available_actions : List[str], player_id : int):
        # modifies the available actions based on the effects in play
        # Aerodrome (3 strength or less to non matching theaters)
        # Airdrop (1 time to non matching theater)
        # called right after available actions are generated
        # TODO: get it working for Aerodrome first
        pass

    def post_play_triggers(self, card : Card, player_id : int):
        # checking for Containment, Blockade
        # TODO: happens before effect is added
        pass

    def add_effect(self, card : Card, player_id : int):
        # happens after post play triggers are checked
        self.effect_cards[player_id].append(card)
        self.resolve_effect(card, player_id)
        pass

    def resolve_effect(self, card : Card, player_id : int):
        # applies game logic of tactical abilities that happen immediately
        # does not handle
            # Support (calculated at end of game)
            # 6 strength cards (Heavy Bombers, Super Battleship, Heavy Tanks)
            # Containment + Blockade (take effect in post play triggers)
            # Aerodrome + Airdrop (take effect after available actions are generated next turn)
        # Handles
        # Manuever, Ambush, Transport, Redeploy, Reinforce, Disrupt (immediate extra action)
        # how do we give the extra action
        pass

    def remove_effect(self, card : Card, player_id : int):
        self.effect_cards[player_id].remove(card)
        pass





    # TODO: how do i say which player the effect is affecting? (can be one or both)
    # how do i store is answered by
    # how do we know which theater is affected
    # access which theater the card is in, then use logic to determine theaters affected

    # lets calculate modified theater strength at the end of the game rather than at all times
