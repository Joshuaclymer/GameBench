from dataclasses import dataclass, field
import random
from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
import ast
from .board import Board, Theater
from .player import Player
from .cards import Card, Deck
import random
from .effect_manager import EffectManager
import re
import pprint

@dataclass
class AirLandSea(Game):
    rules : Rules = Rules(
        title="Air Land and Sea",
        summary=("A strategic card game where two players compete"
            "over a series of battles to control different Theaters"
            "of war: Air, Land, and Sea. Each player is dealt 6 cards"
            "representing various military units and tactics. "
            "Players win a battle by controlling more Theaters than "
            "their opponent or convincing their opponent to withdraw. "
            "Victory Points (VPs) are earned by winning battles, "
            "and the first player to reach 12 VPs wins the game. "
            "Players must carefully manage their hand and strategically deploy cards to outmaneuver their opponent."),
        additional_details = {
            "Battle Structure": ("During a Battle, the players take turns playing one card at a time, trying to control more Theaters than their opponent."
                "You don’t draw cards during a Battle, so be sure to plan carefully and make the most of the 6 cards you are dealt!"),
            "Theaters": ("Each of the three Theater boards creates a 'column' between the players: one for Air, one for Land, and one for Sea. These columns are called Theaters. Cards are always played into these three Theaters. If a card is in a particular Theater’s column, we say that the card is 'in that Theater.'\n"
                "Theaters that are next to each other are called 'adjacent Theaters.'"
                "A player owns all of the cards on their side of the Theater boards. During your turn, you will play cards only on your side of the Theaters."),
            "Battle Cards": ("Cards are played to advance your war effort and how they are played will ultimately determine who wins the war (the game).\n"
                "Strength: Each card has a Strength value. If the total Strength of all the cards on your side of the Theater is higher than the total Strength of all the cards on your opponent’s side of that Theater, you 'control' that Theater.\n"
                "Tactical Abilities: Most cards have a Tactical Ability along with Strength, which takes effect as soon as the card is played 'face up' to a Theater. These abilities are either 'Instant' or 'Ongoing.'"),
            "Type of Battle Cards": ("There are three types of cards: 'Air,' 'Land,' and 'Sea' cards, which relate to the three Theaters. Normally, you may only play a card 'face up' to its matching Theater: Air cards in the Air Theater, and so on."),
            "Facedown Cards": ("Cards can also be played 'facedown' as a 'wild card' in any Theater. Facedown cards always have a Strength of 2. 'Facedown' cards do not have any Tactical Abilities. You may see your own facedown cards at any time, but you may not see your opponent's 'facedown' cards."),
            "Covered Cards": ("When a card is played to a Theater that already contains cards, the newly played card is placed so that it overlaps the previously played card, while still showing the top portion of it. Any card overlapped by another is called a 'covered card.' Similarly, any card that is not overlapped by another card is referred to as 'uncovered.'"),
            "Resolving Battle": ("During a Battle, players take turns starting with the player who has the 1st Player Supreme Commander card.\n"
                "On your turn, you must take only one of these three actions: Deploy, Improvise, Withdraw.\n"
                "Once you have finished your action, your opponent begins their turn. The players continue to alternate taking turns until one of them withdraws or both players have played all of their cards."),
            "Possible actions:": ("Deploy: Play one card from your hand, 'face up.' When you play a card, you must follow these deployment restrictions: You can only play cards on your side of the Theater boards. The card must be the same type as the Theater you play it to. If you have other cards in that Theater already, you must place the new card so that it covers (partially overlaps) those cards.\n"
                "Improvise: Play one card from your hand, 'facedown', to any Theater. 'Facedown' cards are treated as 'wild cards' and can be played to any Theater regardless of which type they are.\n"
                "Withdraw: If you think your chances of winning the current Battle are low, you may withdraw. If you do, your opponent wins the Battle and gains VPs depending on how many cards are left in your hand. See the Supreme Commander cards for more specific information."),
            "Supreme Commander Cards": ("Supreme Commander Cards: The 1st Player Supreme Commander wins tied Theaters and gains the following number of VPs based on the number of cards left in their opponent's hand if their opponent withdraws: 5+ cards = 2 VPs, 3-4 cards = 3 VPs, 2 cards = 4 VPs, 0-1 cards = 6 VPs.\n"
                "The 2nd Player Supreme Commander loses tied Theaters and gains the following number of VPs based on the number of cards left in their opponent’s hand if their opponent withdraws: 4+ cards = 2 VPs, 2-3 cards = 3 VPs, 1 card = 4 VPs, 0 cards = 6 VPs."),
            "Tactical Abilities": ("Most cards have Tactical Abilities described on the card. When you play a card face up from your hand, or if a facedown card is flipped over, its Tactical Ability takes effect immediately. There are two kinds of Tactical Abilities: 'Instant' and 'Ongoing', indicated on the card.\n"
                "You must carry out the effects of a Tactical Ability unless they contain the word 'may'.\n"
                "If a Tactical Ability is impossible to perform, that ability is ignored and has no effect."),
            "Instant Abilities": ("Instant Abilities take effect immediately after the card is played or if the card is revealed by being flipped face up. Once the Instant Ability is resolved, it has no further effect (unless somehow that card is played or revealed again).\n"
                "Note: Because instant abilities take effect when flipped face up, it is possible for multiple instant abilities to take effect around the same time. In these situations, always resolve the instant abilities in the order they happened and fully resolve each ability before moving on to the next.\n"
                "Once an instant ability begins taking effect, it always resolves fully, even if it gets flipped facedown before completing."),
            "Ongoing Abilities": ("These are always in effect as long as the card is face up. If a card with an Ongoing Ability is flipped 'facedown', the ability no longer has any effect (unless that card is revealed again).\n"
                "Example: The Escalation Tactical Ability increases the Strength of all of your facedown cards to 4 as long as the Escalation card remains 'face up'. If that card were flipped over by another Tactical Ability, your 'facedown' cards would go back to being Strength 2."),
            "Tactical Ability Key Terms": 
                ("Flip: Many Tactical Abilities allow you to flip a card. Flipping a card means either turning it 'face up' if it is 'facedown' or turning a 'facedown' card so it is 'face up.'"
                    "Unless the ability states otherwise, you may flip any card — yours or your opponent's.\n"
                "Uncovered/Covered: Many Tactical Abilities only affect uncovered or covered cards. If an ability does not specify uncovered or covered, such as Transport or Redeploy, assume the ability can affect any card.\n"
                "Play: Some Tactical Abilities instruct you to play a card, or only take effect in response to a card being played. The word 'play' describes any time a player takes a card from their hand and places it in a Theater.\n"
                "Non-Matching Theaters: Means that a card is not in the Theater of its type. The card does not suffer any penalty for being in the 'wrong' Theater.\n"
                "Destroy: Some Tactical Abilities instruct you to destroy a card. Destroyed cards are always placed facedown on the bottom of the deck. If a card is destroyed immediately after it is played, such as by Blockade, then that card does not get to use its Tactical Ability.\n"
                "Occupied: When counting the number of cards that occupy a Theater, always count both players' cards towards that total.\n"
                "Move: When a card is moved to a different Theater. It stays on the same side of the Theaters it was already on and remains owned by the same player. Moved cards are placed on top of any cards already in the Theater it was moved to. It covers those cards."),
            "Ending Battles": ("There are two ways a Battle can end: If a player withdraws, their opponent wins the Battle. Or if both players have played all of the cards in their hand. At this point, the player who controls the most Theaters wins the Battle."
                "In order to control a Theater, you must have a higher total Strength there than your opponent has in that Theater. If your Strengths are tied, the 1st Player wins the tie and controls that Theater. If there are no cards on either side of the Theater, the 1st player controls that Theater."),
            "Scoring Victory Points": ("If neither player withdraws, the winner of the Battle scores 6 VPs. If one of the players withdraws, the other player scores VPs based on the number of cards left in the withdrawing player's hand (see the Supreme Commander Cards for details). After scoring VPs, check if the victor has enough VPs to win the game (12 VPs). If they don’t, fight another Battle."),
            "Setting up Battles": ("All cards are collected and shuffled together to create a new deck. Deal each player a new hand of 6 cards. Next, the Theater cards are rotated clockwise so that the rightmost Theater is moved to the far left of the Theater lineup. Lastly, players swap Supreme Commander cards. The player who was 1st in the last battle is now 2nd."),
        }
    )
    id : str = "air_land_sea"
    # first key is the player who won's supreme commander
    # subkey is the number of cards in the loser's hand
    withdrawal_points: Dict[int, Dict[int, int]] = field(default_factory=lambda: {
        0 : {5: 2, 4: 3, 3: 3, 2: 4, 0: 6},
        1 : {4: 2, 3: 3, 2: 3, 1: 4, 0: 6}
    })

    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.effect_manager = EffectManager()
        self.board : Board = Board() # theater_order is randomized on init
        self.deck = Deck() # shuffled on init
        p1_hand = self.deck.deal()
        p2_hand = self.deck.deal()
        p1_supreme_commander = random.choice([0, 1])
        p2_supreme_commander = 1 - p1_supreme_commander
        self.agents = [agent1(team_id = 0, agent_id = 0, **self.agent_1_kwargs), agent2(team_id = 1, agent_id = 1, **self.agent_2_kwargs)]
        self.player1 = Player(id=0, supreme_commander=p1_supreme_commander, agent=self.agents[0], hand=p1_hand)
        self.player2 = Player(id=1, supreme_commander=p2_supreme_commander, agent=self.agents[1], hand=p2_hand)
        self.players = [self.player1, self.player2]

    def get_player_by_agent_id(self, agent_id : int) -> Player:
        for player in self.players:
            if player.id == agent_id:
                return player
        return None

    # generate observation and available actions for the agent
    def get_observation(self, agent : Agent) -> Tuple[Observation, AvailableActions]:
        player = self.get_player_by_agent_id(agent.agent_id)
        # print("player_id", player.id)
        # Observation includes
        hand = player.hand
        supreme_commander = "1st" if player.supreme_commander == 0 else "2nd" if player.supreme_commander == 1 else "error"
        # print("supreme commander:",supreme_commander)
        hand_size = str(len(player.hand))
        opponent = self.get_player_by_agent_id(1 - agent.agent_id)
        opponent_hand_size = str(len(opponent.hand))
        # print("opponent hand size:",opponent_hand_size)
        victory_points = str(player.victory_points)
        # print("victory points:",victory_points)
        # the opponent sees the name as facedown
        # but the player sees the normal card but with "Facedown-" in front of the name and strength set to 2
        board_string = self.board.get_board_string(player.id)
        hand_string = ""
        for card in hand:
            hand_string += "  "+ str(card) + "\n"

        observation_text = (
            "Player " + str(player.id + 1) + "'s action\n"
            "Current Hand: \n" + hand_string + ""
            "Current Supreme Commander: " + supreme_commander + "\n"
            "Current Victory Points: " + victory_points + "\n"
            "Current Hand Size: " + hand_size + "\n"
            "Current Opponent Hand Size: " + opponent_hand_size + "\n"
            "Current Board: \n" + board_string
        )

        # a dictionary formatted like so:
        # { 'Play {card.name}' : 'Play {card} faceup to {card.theater}'}}
        cards_to_play = {}
        for action_id, card in enumerate(hand):
            cards_to_play[str(action_id)] = f"Play {card} faceup to {card.theater}. Deploy."
        # Facedown cards can be played to any theater, make 3 actions for each card for each of the 3 theaters.
        # facedown action_id must increase counting up from len(hand)
        for action_id, card in enumerate(hand, start=len(hand)):
            cards_to_play[str(action_id)] = f"Play {card} facedown to Air. Strength will be 2 while facedown. Improvise."
        for action_id, card in enumerate(hand, start=len(hand)*2):
            cards_to_play[str(action_id)] = f"Play {card} facedown to Land. Strength will be 2 while facedown. Improvise."
        for action_id, card in enumerate(hand, start=len(hand)*3):
            cards_to_play[str(action_id)] = f"Play {card} facedown to Sea. Strength will be 2 while facedown. Improvise."

        cards_to_play[str(len(hand)*4)] = "Withdraw from the battle. Opponent scores VPs based on the number of cards left in your hand."

        available_actions = AvailableActions(
            instructions = "Select a card from your hand to play to a theater",
            predefined = cards_to_play,
            openended = {}
        )
        return Observation(text=observation_text), available_actions
    
    def find_card_from_action(self, action : Action, available_actions: AvailableActions, agent : Agent=None) -> Card:
        # the agent is the one is playing or flipping the card
        action_id = action.action_id
        action_desc = available_actions.predefined[action_id]
        # find which card was just played
        # can use name and theater to find the card
        # name will suffice except for maneuver
        # find name in string (comes after "Play" and before the '(')

        # card_name_pattern = r'Play\s+([^(]+)\s+\(' # old
        card_name_pattern = r"(?:Play|Flip|Move|Return)\s+([^(]+)\s+\(" # checks between Play or Flip and the '('
        theater_pattern = r'\d,\s+(\w+)\s*[),]?' # checks after number and comma and before the the next comma (excluding whitespace)
        card_name_match = re.search(card_name_pattern, action_desc)
        if card_name_match:
            card_name = card_name_match.group(1).strip()  # .strip() to remove trailing spaces
        else:
            card_name = None
        theater_match = re.search(theater_pattern, action_desc)
        if theater_match:
            theater_name = theater_match.group(1)
        else:
            theater_name = None
        

        # print("inside find_card_from_action")
        # print("card name:", card_name + ".end")
        # print("theater:", theater + ".end")
        found_card = None
        if action_desc.startswith("Flip") or action_desc.startswith("Move") or action_desc.startswith("Return"):
            # locate from board
            if card_name == "Facedown":
                # print("inside card_name == Facedown in find card")
                # when card_name is Facedown it's the opponent's facedown card
                # the case where the agent is flipping an unknown (ie. the oppponent's) uncovered facedown card
                theater = self.find_theater_played_from_action(action, available_actions)
                # print("theater found:", theater)
                # choose the opponent's uncovered facedown card
                opponent_id = 1 - agent.agent_id
                found_card = theater.player_cards[opponent_id][-1]
            else:
                if action_desc.startswith("Move") and card_name.startswith("Facedown-<"):
                    # the case where we're moving a facedown card we own looks like "Facedown-<card_name>"
                    card_name = re.search(r"<([^>]+)>", card_name).group(1)
                    theater_name = re.search(r'>,\s*(\w+)', action_desc).group(1)
                    # print("inside find_card_from_action Move Facedown-< format:")
                    # print("card_name:", card_name)
                    # print("theater_name:", theater_name)

                # locate from theater
                # print("using flip to search board for card")
                # print("running board.search_card in find_card")
                found_card = self.board.search_card(card_name, theater_name)
        else:
            # locate from hand if play
            # you need to locate it from their hand not the board
            found_card = self.player1.search_hand(card_name, theater_name)
            if found_card == None:
                found_card = self.player2.search_hand(card_name, theater_name)
            if found_card == None:
                print("error: could not find card from action")
        # print("found card in find_card:", found_card)
        return found_card

    def find_theater_played_from_action(self, action : Action, available_actions: AvailableActions) -> Theater:
        # returns string of theater name
        action_id = action.action_id
        action_desc = available_actions.predefined[action_id]
        theater_pattern = r'to (\w+)\.' # after the word "to" and before the period
        if action_desc.startswith("Flip") or action_desc.startswith("Return"):
            theater_pattern = r'\)\s+in\s+(\w+)' # the word after the ')' and 'in'
        theater_match = re.search(theater_pattern, action_desc)
        if theater_match:
            theater = theater_match.group(1)
        else:
            theater = None
        # print("theater found in find_theater:", theater)
        # print("inside find_theater_played_from_action")
        # print("theater:", theater)
        theater = self.board.get_theater_by_name(theater)
        return theater

    def find_faceup_or_facedown_from_action(self, action : Action, available_actions : AvailableActions) -> bool:
        action_id = action.action_id
        action_desc = available_actions.predefined[action_id]
        if 'faceup' not in action_desc:
            return "facedown"
        else:
            return "faceup"

    def check_destroy_triggers(self, action : Action, available_actions : AvailableActions):
        # returns a flag indicating whether to destroy the card or not
        destroy = False
        action_id = action.action_id
        action_desc = available_actions.predefined[action_id]
        # checking for Containment, Blockade
        # first check for Containment Effect in any player's effect cards
        if any(card.name == 'Containment' for player_cards in self.effect_manager.effect_cards for card in player_cards):
            # if the description does not contain the word faceup then the action was to play a facedown card
            if 'faceup' not in action_desc:
                # destroy the card
                destroy = True
        if any(card.name == 'Blockade' for player_cards in self.effect_manager.effect_cards for card in player_cards):
            # find just_played card its location
            just_played_card = self.find_card_from_action(action, available_actions)
            just_played_card_location = self.find_theater_played_from_action(action, available_actions)

            # print("inside blockade - just_played_card_location = ", just_played_card_location)
            # print("inside blockade - just_played_card = ", just_played_card)

            # find theater of Blockade card by searching for it in every theater            
            for player in self.players:
                for theater in self.board.theaters:
                    for card in theater.player_cards[player.id]:
                        if card.name == 'Blockade':
                            blockade_location = theater
                            break
                            
            # print("inside blockade - blockade_location = ", blockade_location)
            
            # find adjacent theaters to the Blockade card's current theater
            blockade_index = self.board.get_theater_index(blockade_location.name)
            adjacent_theaters_indices = self.board.get_adjacent_theaters(blockade_index)
            adjacent_theaters = []
            for theater_ind in adjacent_theaters_indices:
                adjacent_theaters.append(self.board.theaters[theater_ind])

            # print("inside blockade - adjacent_theaters = ", adjacent_theaters)

            # if the just_played card is in an adjacent theater to the Blockade card, then check if the adjacent theater has 3 or more cards already
            for theater in adjacent_theaters:
                if just_played_card_location == theater:
                    if len(theater.player_1_cards) + len(theater.player_2_cards) >= 3:
                        destroy = True
            
            # print("inside blockade - destroy = ", destroy)

                # old version
                # blockade = Card('Blockade', 'Sea', 5, 'Ongoing', 'If any player plays a card to an adjacent theater occupied by at least 3 other cards, destroy that card')
                # blockade_location = self.board.search_ongoing_effect_location(blockade, self.effect_manager) # a list or none
                # # blockade_location looks like [p1_theater_id, p2_theater_id]
                # # doesn't matter which player's it is, just need to find the adjacent theaters of both if they both exist
                # # find adjacent theaters to the Blockade card's current position
                # adjacent_theaters_p1 = self.board.get_adjacent_theaters(blockade_location[0])
                # adjacent_theaters_p2 = self.board.get_adjacent_theaters(blockade_location[1])
                # # merge the two lists
                # adjacent_theaters = list(set(adjacent_theaters_p1 + adjacent_theaters_p2))
            
                # # find location of just_played_card
                # just_played_card_location = self.find_theater_played_from_action(action, available_actions)

                # # access theaters by indices

                # for theater_ind in adjacent_theaters:
                #     if len(self.board.theaters[theater_ind].player_1_cards) + len(self.board.theaters[theater_ind].player_2_cards) >= 3 and self.board.theaters[theater_ind] == just_played_card_location:
                #         destroy = True
        return destroy
    
    # I pass in observation + available actions to agent, then it will choose one
    def update(self, action : Action, available_actions : AvailableActions, agent : Agent) -> Optional[Agent]:

        # check for withdraw
        if available_actions.predefined[action.action_id].startswith("Withdraw"):
            # how do i signal to the outer function that the battle is over?
            # how do i signal to the outer funciton that a player withdrew?
            return agent

        #  To make dissapearing and reappearing work for ongoing effects (by flip)
            # on card flip, call add effect and resolve effect
            # this will be done when i we process agent output in update()
        if self.check_destroy_triggers(action, available_actions):
            # remove card from hand and end turn
            player = self.get_player_by_agent_id(agent.agent_id)
            played_card = self.find_card_from_action(action, available_actions, agent)
            player.hand.remove(played_card)
            if self.show_state:
                print("Destroyed card:", played_card)
                print(player.hand)
            return None
        played_card, played_to_theater = self.play_card_from_action(action, available_actions, agent)
        # print("played card facedown:",played_card.facedown)
        if not (played_card.name == 'Heavy Bombers' or played_card.name == 'Super Battleship' or played_card.name == 'Heavy Tanks') and not played_card.facedown:
            # print("resolving effect in update")
            self.resolve_effect(played_card, agent, played_to_theater)
        return None
    
    def play_card_from_action(self, action : Action, available_actions : AvailableActions, agent : Agent):
        player = self.get_player_by_agent_id(agent.agent_id)
        # take in action and available action string and turn it into playing a card
        card = self.find_card_from_action(action, available_actions) # Card Object
        theater = self.find_theater_played_from_action(action, available_actions)
        faceup_or_facedown = self.find_faceup_or_facedown_from_action(action, available_actions) # string
        is_faceup = True if faceup_or_facedown == 'faceup' else False

        player.play(card, is_faceup, theater)
        return card, theater
    
    def flip_card_from_action(self, action : Action, available_actions : AvailableActions, agent : Agent) -> Tuple[Card, Theater]:
        # find card name
        card = self.find_card_from_action(action, available_actions, agent)
        # print("found card")
        # print(card)
        # find theater
        theater = self.find_theater_played_from_action(action, available_actions)
        # print(theater)
        # apply flip
        for player in self.players:
            for current_card in theater.player_cards[player.id]:
                # print(id(card))
                # print(card)
                # print(id(current_card))
                # print(current_card)
                if current_card == card:
                    # print("found card")
                    current_card.flip()
                    if (current_card in self.effect_manager.effect_cards[player.id]) and current_card.facedown:
                        self.effect_manager.remove_effect(current_card, player.id)
                    return current_card, theater
        return None, None

    def resolve_effect(self, input_card : Card, agent : Agent, theater : Theater):
        # takes in the card that was just played, the agent that played it, and the theater it was played to
        player = self.get_player_by_agent_id(agent.agent_id)
        opponent = self.get_player_by_agent_id(1 - agent.agent_id)

        self.effect_manager.add_effect(input_card, agent.agent_id)
        if self.show_state:
            print("effect cards")
            print(self.effect_manager.effect_cards)
        # applies game logic of tactical abilities that happen immediately
        # does not handle
            # Support (calculated at end of game)
            # 6 strength cards (Heavy Bombers, Super Battleship, Heavy Tanks)
            # Containment + Blockade (take effect in post play triggers)
            # Aerodrome + Airdrop (take effect after available actions are generated next turn)
        # Handles
        # Maneuver, Ambush, Transport, Redeploy, Reinforce, Disrupt (immediate extra action)

        # normal loop:
            # get_observation
            # modify_available_actions
            # get agent output action
                # check if withdraw
            # update
                # check_destroy_triggers
                # apply action
                # resolve_effect
                    # add_effect
                    # do effect
                    # remove effect


        # the extra action procedures are to be coded in the game class

        if input_card.name == 'Maneuver':
            # flip an uncovered card in an adjacent theater
                # find which theater is adjacent to the theater the card was played in
            # get_observation + modified available actions dict
                # call get observation normally on the player
                # generate available actions for the player that are only to flip an uncovered card in an adjacent theater
            # get agent output action
            # apply flip
            # add effect
            # resolve effect
            observation, _ = self.get_observation(agent)
            # modify available actions to only allow flipping an uncovered card in an adjacent theater
            # generate actions to flip an uncovered card in an adjacent theater
            uncovered_cards = []
            cards_to_flip = {}
            theater_index = self.board.get_theater_index(theater.name)
            adjacent_theaters_indices = self.board.get_adjacent_theaters(theater_index)
            adjacent_theaters = []
            for theater_ind in adjacent_theaters_indices:
                adjacent_theaters.append(self.board.theaters[theater_ind])
            # go through cards in each theater and find uncovered cards
            # uncovered just means it is the last in the list (index is -1)
            for theater in adjacent_theaters:
                for player_id in range(2):
                    if theater.player_cards[player_id]:
                        uncovered_card = theater.player_cards[player_id][-1]
                        uncovered_cards.append((uncovered_card, theater, player_id))

            for action_id, (card, theater, player_id) in enumerate(uncovered_cards):
                if card.facedown:
                    # check if it is player's card or opponent's card
                    if player_id == player.id:
                        # player owns the facedown card and can see its contents
                        cards_to_flip[str(action_id)] = f"Flip {card} in {theater.name} faceup."
                    else:
                        # opponent owns the facedown card and cannot see its contents
                        cards_to_flip[str(action_id)] = f"Flip Facedown (2) in {theater.name} faceup."
                elif not card.facedown:
                    # faceup
                    cards_to_flip[str(action_id)] = f"Flip {card} in {theater.name} facedown."
                else:
                    if self.show_state:
                        print("error: card is neither faceup nor facedown")

            maneuver_available_actions = AvailableActions(
                instructions = "Select an uncovered card from an adjacent theater to flip.",
                predefined = cards_to_flip,
                openended = {}
            )
            if self.show_state:
                print(observation.text)
                print("maneuver_available_actions")
                print(maneuver_available_actions.predefined)
            # call take action
            if len(maneuver_available_actions.predefined) == 0:
                if self.show_state:
                    print("no cards to flip")
                self.effect_manager.remove_effect(input_card, player.id)
                return
            agent_output = agent.take_action(self.rules, observation, maneuver_available_actions, show_state=self.show_state)
            # print("player", player.id + 1)
            flipped_card, target_theater = self.flip_card_from_action(agent_output, maneuver_available_actions, agent)
            # print(input_card)
            # print(id(input_card))
            self.effect_manager.remove_effect(input_card, player.id)
            if flipped_card and not flipped_card.facedown:
                # search target_theater for the card and identify who owns it
                for flipped_owner in self.players:
                    if flipped_card in target_theater.player_cards[flipped_owner.id]:
                        # resolve effect (if flipped faceup) for the player who owns the flipped card
                        self.resolve_effect(flipped_card, flipped_owner.agent, target_theater)
                        break
            return
        elif input_card.name == 'Ambush':
            # flip any uncovered card
            # get_observation + modified available actions dict
            # get agent output action
            # apply flip
            # add effect
            # resolve effect
            observation, _ = self.get_observation(agent)
            # modify available actions to only allow flipping an uncovered card in an adjacent theater
            # generate actions to flip an uncovered card in an adjacent theater
            uncovered_cards = []
            cards_to_flip = {}
            # go through cards in each theater and find uncovered cards
            # uncovered just means it is the last in the list (index is -1)
            for theater in self.board.theaters:
                for player_id in range(2):
                    if theater.player_cards[player_id]:
                        uncovered_card = theater.player_cards[player_id][-1]
                        uncovered_cards.append((uncovered_card, theater, player_id))

            for action_id, (card, theater, player_id) in enumerate(uncovered_cards):
                if card.facedown:
                    # check if it is player's card or opponent's card
                    if player_id == player.id:
                        # player owns the facedown card and can see its contents
                        cards_to_flip[str(action_id)] = f"Flip {card} in {theater.name} faceup."
                    else:
                        # opponent owns the facedown card and cannot see its contents
                        cards_to_flip[str(action_id)] = f"Flip Facedown (2) in {theater.name} faceup."
                elif not card.facedown:
                    # faceup
                    cards_to_flip[str(action_id)] = f"Flip {card} in {theater.name} facedown."
                else:
                    if self.show_state:
                        print("error: card is neither faceup nor facedown")

            ambush_available_actions = AvailableActions(
                instructions = "Select any uncovered card to flip.",
                predefined = cards_to_flip,
                openended = {}
            )
            if self.show_state:
                print(observation.text)
                print("ambush_available_actions")
                print(ambush_available_actions.predefined)
            # call take action
            if len(ambush_available_actions.predefined) == 0:
                if self.show_state:
                    print("no cards to flip")
                self.effect_manager.remove_effect(input_card, player.id)
                return
            agent_output = agent.take_action(self.rules, observation, ambush_available_actions, True)
            # print("player", player.id + 1)
            flipped_card, target_theater = self.flip_card_from_action(agent_output, ambush_available_actions, agent)
            # print(input_card)
            # print(id(input_card))
            if input_card in self.effect_manager.effect_cards[player.id]:
                self.effect_manager.remove_effect(input_card, player.id)
            if flipped_card and not flipped_card.facedown:
                # search target_theater for the card and identify who owns it
                for flipped_owner in self.players:
                    if flipped_card in target_theater.player_cards[flipped_owner.id]:
                        # resolve effect (if flipped faceup) for the player who owns the flipped card
                        self.resolve_effect(flipped_card, flipped_owner.agent, target_theater)
                        break
            return
        elif input_card.name == 'Transport':
            # move 1 of your cards to a different theater
            # get_observation + modified available actions dict
            observation, _ = self.get_observation(agent)
            # generate available actions to move 1 of player's card to a different theater
            player_cards = []
            cards_to_move = {}
            for theater in self.board.theaters:
                for card in theater.player_cards[player.id]:
                    player_cards.append((card, theater))

            action_id = 0
            for target_theater in self.board.theaters:
                for card, theater in player_cards:
                    if target_theater != theater:
                        if card.facedown:
                            card_string = str(card)
                            card_string = re.sub(r' \(\d', f"> (2-<{card.strength}>", card_string)
                            card_string = "Facedown-<" + card_string
                            cards_to_move[str(action_id)] = f"Move {card_string} in {theater.name} to {target_theater.name}."
                        else:
                            cards_to_move[str(action_id)] = f"Move {card} in {theater.name} to {target_theater.name}."
                        action_id += 1
            cards_to_move[str(action_id)] = "Do not move any cards."

            transport_available_actions = AvailableActions(
                instructions = "Select one of your cards to move to a different theater. You may also choose to not move anything.",
                predefined = cards_to_move,
                openended = {}
            )
            if self.show_state:
                print(observation.text)
                print("transport_available_actions")
                pprint.pprint(transport_available_actions.predefined)
            
            # get agent output action
            action = agent.take_action(self.rules, observation, transport_available_actions, show_state=self.show_state)
            # apply move
            found_card = self.find_card_from_action(action, transport_available_actions, agent)
            if not found_card:
                # then we didn't want to move a card or didn't find one
                self.effect_manager.remove_effect(input_card, player.id)
                return
            # move the card to the target theater
            # find the target theater
            target_theater = self.find_theater_played_from_action(action, transport_available_actions)
            # print("moving card")
            # print("target_theater:", target_theater)
            self.board.move_card(found_card, target_theater)
            self.effect_manager.remove_effect(input_card, player.id)
            return
        elif input_card.name == 'Redeploy':
            # you may return 1 of your facedown cards to your hand. If you do, play a card
            # Return
                # get_observation + modified available actions dict
                # get agent output action
                # apply return
            observation, _ = self.get_observation(agent)
            
            # generate available actions to return 1 of player's facedown cards to their hand
            facedown_cards = []
            cards_to_return = {}
            for theater in self.board.theaters:
                for card in theater.player_cards[player.id]:
                    if card.facedown:
                        facedown_cards.append((card, theater))

            action_id = 0
            for card, theater in facedown_cards:
                cards_to_return[str(action_id)] = f"Return {card} in {theater.name} to your hand in order to play a card."
                action_id += 1
            cards_to_return[str(action_id)] = "Do not return any cards."
        
            redeploy_available_actions = AvailableActions(
                instructions = "Select one of your facedown cards to return to your hand. You may also choose to not return anything (not use this tactical ability).",
                predefined = cards_to_return,
                openended = {}
            )
            if self.show_state:
                print(observation.text)
                print("redeploy_available_actions")
                pprint.pprint(redeploy_available_actions.predefined)
            # get agent output action
            action = agent.take_action(self.rules, observation, redeploy_available_actions, show_state=self.show_state)

            # apply return
            if action.action_id == str(action_id):
                # then we didn't want to return a card
                self.effect_manager.remove_effect(input_card, player.id)
                return
            found_card = self.find_card_from_action(action, redeploy_available_actions, agent)
            current_theater = self.find_theater_played_from_action(action, redeploy_available_actions)

            current_theater.player_cards[player.id].remove(found_card)
            player.hand.append(found_card)
            # make it not facedown, when it goes back to hand
            found_card.flip()

            # play (normal loop) (maybe this is just calling the update function again on the same player)
                # get_observation
                # modify_available_actions
                # get agent output action
                # update
                    # check_destroy_triggers
                    # apply action
                    # resolve_effect
                        # add_effect
                        # do effect
                        # remove_effect
            observation, available_actions = self.get_observation(agent)
            # print("\n------------------------\n")
            # print("get observation")
            # print("calling modify available actions on:", player.id)
            modified_actions = self.effect_manager.modify_available_actions(available_actions, player.hand, player.id)
            if self.show_state:
                print(observation.text)
                pprint.pprint(modified_actions.predefined)
            action = agent.take_action(self.rules, observation, modified_actions, show_state=self.show_state)
            self.update(action, modified_actions, agent)
            if input_card in self.effect_manager.effect_cards[player.id]:
                self.effect_manager.remove_effect(input_card, player.id)
            return
        elif input_card.name == 'Reinforce':
            # draw 1 card and play it facedown to an adjacent theater
            # draw new card
            # play (but only facedown actions)
                # get_observation + modified available actions dict (only facedown)
                # get agent output action
                # update
                    # check_destroy_triggers
                    # apply action
            drawn_card = self.deck.draw()
            player.hand.append(drawn_card)
            observation, _ = self.get_observation(agent)

            # generate available actions to play the drawn card facedown to an adjacent theater
            theater_ind = self.board.get_theater_index(theater.name)
            adjacent_theaters_indices = self.board.get_adjacent_theaters(theater_ind)
            adjacent_theaters = []
            for theater_ind in adjacent_theaters_indices:
                adjacent_theaters.append(self.board.theaters[theater_ind])

            places_to_play = {}
            for action_id, target_theater in enumerate(adjacent_theaters):
                places_to_play[str(action_id)] = f"Play {drawn_card} facedown to {target_theater.name}. Strength will be 2 while facedown."

            reinforce_available_actions = AvailableActions(
                instructions = "Select an adjacent theater to play the drawn card facedown.",
                predefined = places_to_play,
                openended = {}
            )
            if self.show_state:
                print(observation.text)
                print("reinforce_available_actions")
                pprint.pprint(reinforce_available_actions.predefined)

            # get agent output action
            action = agent.take_action(self.rules, observation, reinforce_available_actions, show_state=self.show_state)
            # play the drawn card facedown to the target theater
            target_theater = self.find_theater_played_from_action(action, reinforce_available_actions)
            player.play(drawn_card, False, target_theater)
            self.effect_manager.remove_effect(input_card, player.id)
            pass
        elif input_card.name == 'Disrupt':
            # Starting with you, both players choose and flip 1 of their uncovered cards
            # owner -> get_observation + modified available actions dict
            # get agent output action
            # apply flip
            # add effect (if flipped faceup)
            # resolve effect (if flipped faceup)
            # opponent -> get_observation + modified available actions dict
            # get agent output action
            # apply flip
            # add effect (if flipped faceup)
            # resolve effect (if flipped faceup)
            def disrupt_flip(current_player : Player, current_agent : Agent) -> Optional[Tuple[Card, Agent, Theater]]:
                # print("inside disrupt_flip:", self.effect_manager.effect_cards)
                observation, _ = self.get_observation(current_agent)
                # generate available actions for player to flip one of their uncovered cards
                player_uncovered_cards = []
                cards_to_flip = {}
                for theater in self.board.theaters:
                    for card in theater.player_cards[current_player.id]:
                        if theater.is_uncovered(card, current_player.id):
                            player_uncovered_cards.append((card, theater))
            
                action_id = 0
                for card, theater in player_uncovered_cards:
                    if card.facedown:
                        cards_to_flip[str(action_id)] = f"Flip {card} in {theater.name} faceup."
                    else:
                        cards_to_flip[str(action_id)] = f"Flip {card} in {theater.name} facedown."
                    action_id += 1
                disrupt_available_actions = AvailableActions(
                    instructions = "Select one of your uncovered cards to flip.",
                    predefined = cards_to_flip,
                    openended = {}
                )

                if self.show_state:
                    print(observation.text)
                    print("disrupt_available_actions")
                    pprint.pprint(disrupt_available_actions.predefined)
                
                if len(disrupt_available_actions.predefined) == 0:
                    if self.show_state:
                        print("no cards to flip")
                    return None

                # get agent output action
                action = current_agent.take_action(self.rules, observation, disrupt_available_actions, show_state=self.show_state)

                # apply flip
                flipped_card, target_theater = self.flip_card_from_action(action, disrupt_available_actions, current_agent)   
                # add effect (if flipped faceup)
                # move the resolve effect call on flipped card to end
                if not flipped_card.facedown:
                    # return so we can resolve effect later for the player who owns the flipped card
                    # self.resolve_effect(flipped_card, current_agent, target_theater)
                    return flipped_card, current_agent, target_theater
                return None
            
            effect_stack = []
            # Player's flip
            player_param_tuple = disrupt_flip(player, agent)
            if player_param_tuple:
                effect_stack.append(player_param_tuple)
            # opponent's flip
            opponent_param_tuple = disrupt_flip(opponent, opponent.agent)
            if opponent_param_tuple:
                effect_stack.append(opponent_param_tuple)
            
            # finish disrupt effect before resolving flip effects
            if input_card in self.effect_manager.effect_cards[player.id]:
                self.effect_manager.remove_effect(input_card, player.id)

            # process effect stack in order
            for param_tuple in effect_stack:
                self.resolve_effect(*param_tuple)
            return
        else:
            pass

    def take_action_wrapper(self, agent : Agent, observation : Observation, available_actions : AvailableActions) -> Action:
        valid_action = False
        num_tries = 0
        while not valid_action:
            action = agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            num_tries += 1
            if action:
                if action.action_id in available_actions.predefined:
                    valid_action = True
            if num_tries >= 3:
                # make a random choice of the available actions
                action = Action(action_id=random.choice(list(available_actions.predefined.keys())))
        return action

    # def take_action_wrapper(self, agent: Agent, observation: Observation, available_actions: AvailableActions) -> Action:
    #     # check if the action id is in the available actions
    #     # if not, let it try two more times (inside here)
    #     # if third time is invalid, choose randomly
    #     num_tries = 0
    #     while num_tries < 3:
    #         try:
    #             action = agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
    #             if action.action_id in available_actions.predefined:
    #                 # If the action is valid, return it immediately
    #                 return action
    #             else:
    #                 # If the action_id is not in available actions, raise ValueError to trigger except block
    #                 raise ValueError("Invalid action selected.")
    #         except (IndexError, ValueError):
    #             # Handle invalid action selection, either from user input or any other issue
    #             if self.show_state:
    #                 print("Invalid action selected. Please try again.")
    #             num_tries += 1
    #     # If the loop exits due to reaching the maximum number of tries, choose a random action
    #     if self.show_state:
    #         print("Selecting a random action due to repeated invalid selections.")
    #     random_action_id = choice(list(available_actions.predefined.keys()))
    #     return Action(action_id=random_action_id)

    def battle_setup(self):
        # clear board & clear each theater's cards
        self.board.clear_cards()
        self.deck = Deck() 
        self.deck.shuffle() # TODO: shuffled on init
        # clear hands & deal new hands
        for player in self.players:
            player.hand = []
            player.hand = self.deck.deal()
        # switch supreme commander
        self.players[0].supreme_commander, self.players[1].supreme_commander = self.players[1].supreme_commander, self.players[0].supreme_commander
        # new effect manager
        self.effect_manager = EffectManager()
        # rotate theaters
        self.board.rotate_theaters()

    # Returns the scores for agent_1 and agent_2 after the game is finished.
    # the high level gameplay loop
    # is run after init_game is ran
    def play(self) -> Tuple[float, float]:
        if self.show_state:
            print("Starting Game!")
        # Game Setup (already basically done in init_game)
        game_over = False
        while not game_over:
            # Battle Setup
            # we'll need to reset game state for each battle
            self.battle_setup()
            battle_over = False
            # determine who goes first based on supreme commander
            current_agent_turn = None
            for player in self.players:
                if player.supreme_commander == 0:
                    current_agent_turn = player.agent
                    break
            withdrawn_agent = None
            if self.show_state:
                print("Starting Battle!")
            while not battle_over:
                # process player turns
                current_player = self.get_player_by_agent_id(current_agent_turn.agent_id)
                observation, available_actions = self.get_observation(current_agent_turn)
                modified_actions = self.effect_manager.modify_available_actions(available_actions, current_player.hand, current_player.id)
                if self.show_state:
                    print("\n")
                    print(observation.text)
                    pprint.pprint(modified_actions.predefined)
                # action = self.take_action_wrapper(current_agent_turn, observation, modified_actions)
                action = current_agent_turn.take_action(self.rules, observation, modified_actions, show_state=self.show_state)
                withdrawn_agent = self.update(action, modified_actions, current_agent_turn)
                # check if both players have 0 cards in hand or player withdrew to end battle
                if withdrawn_agent or (len(self.players[0].hand) == 0 and len(self.players[1].hand) == 0):
                    battle_over = True
                else:
                    # switch agent turn
                    if current_agent_turn == self.players[0].agent:
                        current_agent_turn = self.players[1].agent
                    else:
                        current_agent_turn = self.players[0].agent
            # battle resolution (add victory points, check for win)
            if self.show_state:
                print(self.board.get_board_string(3)) # 3 is the owner id for spectating
                print("Battle Over!")
            # if a player withdrew
            if withdrawn_agent:
                # decide who won and lost
                victor = self.get_player_by_agent_id(1 - withdrawn_agent.agent_id)
                loser = self.get_player_by_agent_id(withdrawn_agent.agent_id)
                # add victory points to opponent
                loser_hand_size = len(loser.hand)
                victor.victory_points += self.withdrawal_points[victor.supreme_commander][loser_hand_size]
                if self.show_state:
                    print("Player", withdrawn_agent.agent_id + 1, "withdrew!")
                    print("Player", victor.id + 1, "gained", self.withdrawal_points[victor.supreme_commander][loser_hand_size], "VPs!")
            else:
                theater_strengths = self.board.get_theater_strengths(self.effect_manager)
                # find victor and loser
                # theater strengths looks like [[p1_strength, p2_strength], [p1_strength, p2_strength], [p1_strength, p2_strength]]
                player_1_theater_wins = 0
                player_2_theater_wins = 0
                for theater in theater_strengths:
                    if self.player1.supreme_commander == 0:
                        if theater[0] >= theater[1]:
                            player_1_theater_wins += 1
                        else:
                            player_2_theater_wins += 1
                    elif self.player2.supreme_commander == 0:
                        if theater[1] >= theater[0]:
                            player_2_theater_wins += 1
                        else:
                            player_1_theater_wins += 1
                    # victor has the most theater wins
                if player_1_theater_wins > player_2_theater_wins:
                    victor = self.player1
                else:
                    victor = self.player2
                # add victory points to victor
                victor.victory_points += 6
                if self.show_state:
                    print("Both players have no cards in hand!")
                    print(theater_strengths)
                    print("Player 1 won", player_1_theater_wins, "theaters")
                    print("Player 2 won", player_2_theater_wins, "theaters")
                    print("Player", victor.id + 1, "won the battle and gained 6 VPs!")
                    if victor.id == 0:
                        print("Player 1 VPs:", self.player1.victory_points - 6, "-->", self.player1.victory_points)
                        print("Player 2 VPs:", self.player2.victory_points)
                    else:
                        print("Player 2 VPs:", self.player2.victory_points - 6, "-->", self.player2.victory_points)
                        print("Player 1 VPs:", self.player1.victory_points)
            # check for game over
            if victor.victory_points >= 12:
                game_over = True
                if self.show_state:
                    print("Game Over!")
                    print("Player", victor.id + 1, "has won the game!")
        # return scores on game end
        return float(self.players[0].victory_points), float(self.players[1].victory_points)


            # reach 12 victory points to win
            # must track victory points of each player
                # check after each battle if a player has reached 12 victory points
            # must track who is the supreme commander (influences victory points players get from withdrawing)
                # supreme commander goes first and wins ties in theaters
            # must track current position of theaters (in order to rotate them clockwise after each battle)
                # must randomly place 3 theaters in beginning of game
            # must track each player's hand (each gets 6 in beginning of battle)

            # at end of battle, compare strength scores in each theater to determine theater winner and overall battle winner
            # end of battle is when there are no more cards to play

            # normal loop:
                # get_observation
                # modify_available_actions
                # get agent output action
                    # check if withdraw
                # update
                    # check_destroy_triggers
                    # apply action
                    # resolve_effect
                        # add_effect
                        # do effect
                        # remove effect            
        pass