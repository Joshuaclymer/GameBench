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
            "Supreme Commander Cards": ("Supreme Commander Cards: The 1st Player Supreme Commander wins tied Theaters and gains the following number of VPs based on the number of cards left in their opponent's hand if their opponent withdraws: 4+ cards = 2 VPs, 2-3 cards = 3 VPs, 1 card = 4 VPs, 0 cards = 6 VPs.\n"
                "The 2nd Player Supreme Commander loses tied Theaters and gains the following number of VPs based on the number of cards left in their opponent’s hand if their opponent withdraws: 5+ cards = 2 VPs, 3-4 cards = 3 VPs, 2 cards = 4 VPs, 0-1 cards = 6 VPs."),
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
    # points opponent gets if the player withdraws based on number of cards in player's hand
    withdrawal_points: Dict[str, Dict[int, int]] = field(default_factory=lambda: {
        "1st": {4: 2, 3: 3, 2: 3, 1: 4, 0: 6},
        "2nd": {5: 2, 4: 3, 3: 3, 2: 4, 0: 6}
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

        observation_text = (
            "Player " + str(player.id + 1) + "\n"
            "Current Hand: " + str(hand) + "\n"
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
            cards_to_play[str(action_id)] = f"Play {card} faceup to {card.theater}."
        # Facedown cards can be played to any theater, make 3 actions for each card for each of the 3 theaters.
        # facedown action_id must increase counting up from len(hand)
        for action_id, card in enumerate(hand, start=len(hand)):
            cards_to_play[str(action_id)] = f"Play {card} facedown to Air. Strength will be 2 while facedown."
        for action_id, card in enumerate(hand, start=len(hand)*2):
            cards_to_play[str(action_id)] = f"Play {card} facedown to Land. Strength will be 2 while facedown."
        for action_id, card in enumerate(hand, start=len(hand)*3):
            cards_to_play[str(action_id)] = f"Play {card} facedown to Sea. Strength will be 2 while facedown."

        # TODO: add action to withdraw

        available_actions = AvailableActions(
            instructions = "Select a card from your hand to play to a theater",
            predefined = cards_to_play,
            openended = {}
        )
        return Observation(text=observation_text), available_actions
    
    def find_card_from_action(self, action : Action, available_actions: AvailableActions) -> Card:
        action_id = action.action_id
        action_desc = available_actions.predefined[action_id]
        # find which card was just played
        # can use name and theater to find the card
        # name will suffice except for Manuever
        # find name in string (comes after "Play" and before the '(')

        # card_name_pattern = r'Play\s+([^(]+)\s+\(' # old
        card_name_pattern = r"(?:Play|Flip)\s+([^(]+)\s+\(" # checks between Play or Flip and the '('
        theater_pattern = r'\d,\s+(\w+)\s*[),]?'
        card_name_match = re.search(card_name_pattern, action_desc)
        if card_name_match:
            card_name = card_name_match.group(1).strip()  # .strip() to remove trailing spaces
        else:
            card_name = None
        theater_match = re.search(theater_pattern, action_desc)
        if theater_match:
            theater = theater_match.group(1)
        else:
            theater = None

        print("inside find_card_from_action")
        print("card name:", card_name + ".end")
        print("theater:", theater + ".end")
        search_deck = Deck()
        for card in search_deck.cards:
            if card.name == card_name and card.theater == theater:
                return card
        return None

    def find_theater_played_from_action(self, action : Action, available_actions: AvailableActions) -> str:
        # returns string of theater name
        action_id = action.action_id
        action_desc = available_actions.predefined[action_id]
        theater_pattern = r'to (\w+)\.' # after the word "to" and before the period
        if action_desc.startswith("Flip"):
            theater_pattern = r'\)\s+in\s+(\w+)' # the word after the ')' and 'in'
        theater_match = re.search(theater_pattern, action_desc)
        if theater_match:
            theater = theater_match.group(1)
        else:
            theater = None
        print("inside find_theater_played_from_action")
        print("theater:", theater)
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
        # checking for Containment, Blockade
        # first check for Containment Effect in any player's effect cards
        if any(card.name == 'Containment' for player_cards in self.effect_manager.effect_cards for card in player_cards):
            # can check the agent output for if they selected an action to play a facedown card
            # how to distinguish between tactical effect usage of 'facedown' and playing a facedown card
            # predefined action output:
                # Action object with "action_id" == "guess_18"
            # openended action output:
                # Action object with action_id == "submit_clue"
                # and openended_response == "conflict,2" # string
            # need to reference available actions using action_id to see if the action was to play a facedown card
            action_id = action.action_id
            action_desc = available_actions.predefined[action_id]
            # if the description does not contain the word faceup then the action was to play a facedown card
            if 'faceup' not in action_desc:
                # destroy the card
                destroy = True
        if any(card.name == 'Blockade' for player_cards in self.effect_manager.effect_cards for card in player_cards):
            just_played_card = self.find_card_from_action(action, available_actions)
            # find location of Blockade card
            blockade = Card('Blockade', 'Sea', 5, 'Ongoing', 'If any player plays a card to an adjacent theater occupied by at least 3 other cards, destroy that card')
            blockade_location = self.board.search_ongoing_effect_location(blockade, self.effect_manager)
            # blockade_location looks like [p1_theater_id, p2_theater_id]
            # doesn't matter which player's it is, just need to find the adjacent theaters of both if they both exist
            # find adjacent theaters to the Blockade card's current position
            adjacent_theaters_p1 = self.board.get_adjacent_theaters(blockade_location[0])
            adjacent_theaters_p2 = self.board.get_adjacent_theaters(blockade_location[1])
            # merge the two lists
            adjacent_theaters = list(set(adjacent_theaters_p1 + adjacent_theaters_p2))
            
            # find location of just_played_card
            just_played_card_location = self.find_theater_played_from_action(action, available_actions) # str

            # access theaters by indices

            for theater_ind in adjacent_theaters:
                if len(self.board.theaters[theater_ind].player_1_cards) + len(self.board.theaters[theater_ind].player_2_cards) >= 3 and self.board.theaters[theater_ind].name == just_played_card_location:
                    destroy = True
        return destroy
    
    # I pass in observation + available actions to agent, then it will choose one
    def update(self, action : Action, available_actions : AvailableActions, agent : Agent):
        #  To make dissapearing and reappearing work for ongoing effects (by flip)
            # on card flip, call add effect and resolve effect
            # this will be done when i we process agent output in update()
        pass
    
    def play_card_from_action(self, action : Action, available_actions : AvailableActions, agent : Agent):
        player = self.get_player_by_agent_id(agent.agent_id)
        # take in action and available action string and turn it into playing a card
        card = self.find_card_from_action(action, available_actions) # Card Object
        theater_played_str = self.find_theater_played_from_action(action, available_actions) # theater name as string
        theater = self.board.get_theater_by_name(theater_played_str)
        faceup_or_facedown = self.find_faceup_or_facedown_from_action(action, available_actions) # string
        is_faceup = True if faceup_or_facedown == 'faceup' else False

        player.play(card, is_faceup, theater)
        return card, theater
    
    def flip_card_from_action(self, action : Action, available_actions : AvailableActions, agent : Agent):
        # find card name
        card = self.find_card_from_action(action, available_actions)
        # find theater
        theater_chosen_str = self.find_theater_played_from_action(action, available_actions) # string
        theater = self.board.get_theater_by_name(theater_chosen_str)
        # apply flip
        for player in self.players:
            for current_card in theater.player_cards[player.id]:
                if current_card == card:
                    current_card.flip()
                    return current_card, theater
        return None, None

    def resolve_effect(self, card : Card, agent : Agent, theater : Theater):
        # takes in the card that was just played, the agent that played it, and the theater it was played to
        player = self.get_player_by_agent_id(agent.agent_id)
        opponent = self.get_player_by_agent_id(1 - agent.agent_id)
        # applies game logic of tactical abilities that happen immediately
        # does not handle
            # Support (calculated at end of game)
            # 6 strength cards (Heavy Bombers, Super Battleship, Heavy Tanks)
            # Containment + Blockade (take effect in post play triggers)
            # Aerodrome + Airdrop (take effect after available actions are generated next turn)
        # Handles
        # Manuever, Ambush, Transport, Redeploy, Reinforce, Disrupt (immediate extra action)

        # normal loop:
            # get_observation
            # modify_available_actions
            # get agent output action
                # check if withdraw
            # check_destroy_triggers
            # apply action
            # add_effect
            # resolve_effect


        # the extra action procedures are to be coded in the game class

        if card.name == 'Manuever':
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
                        uncovered_cards.append((uncovered_card, theater))

            for action_id, (card, theater) in enumerate(uncovered_cards):
                if card.facedown:
                    cards_to_flip[str(action_id)] = f"Flip {card} in {theater.name} faceup."
                elif not card.facedown:
                    # faceup
                    cards_to_flip[str(action_id)] = f"Flip {card} in {theater.name} facedown."
                else:
                    print("error: card is neither faceup nor facedown")

            manuever_available_actions = AvailableActions(
                instructions = "Select an uncovered card from an adjacent theater to flip.",
                predefined = cards_to_flip,
                openended = {}
            )
            print("manuever_available_actions")
            print(manuever_available_actions.predefined)
            # call take action
            agent_output = agent.take_action(self.rules, observation, manuever_available_actions, True)
            flipped_card, target_theater = self.flip_card_from_action(agent_output, manuever_available_actions, agent)
            if flipped_card and not flipped_card.facedown:
                # add effect if flipped faceup
                self.effect_manager.add_effect(flipped_card, player.id)
                # resolve effect (if flipped faceup)
                self.resolve_effect(flipped_card, agent, target_theater)
        elif card.name == 'Ambush':
            # flip any uncovered card
            # get_observation + modified available actions dict
            # get agent output action
            # apply flip
            # add effect
            # resolve effect
            pass
        elif card.name == 'Transport':
            # move 1 of your cards to a different theater
            # get_observation + modified available actions dict
            # get agent output action
            # apply move
            pass
        elif card.name == 'Redeploy':
            # return 1 of your facedown cards to your hand. If you do, play a card
            # Return
                # get_observation + modified available actions dict
                # get agent output action
                # apply return
            # play (normal loop) (maybe this is just calling the update function again on the same player)
                # get_observation
                # modify_available_actions
                # get agent output action
                # check_destroy_triggers
                # apply action
                # add_effect
                # resolve_effect
            pass
        elif card.name == 'Reinforce':
            # draw 1 card and play it facedown to an adjacent theater
            # draw new card
            # play (but only facedown actions)
                # get_observation + modified available actions dict (only facedown)
                # get agent output action
                # check_destroy_triggers
                # apply action
            pass
        elif card.name == 'Disrupt':
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
            pass
        else:
            pass

    # Returns the scores for agent_1 and agent_2 after the game is finished.
    # the high level gameplay loop
    # is run after init_game is ran
    def play(self):
        agent_1 = self.agents[0]
        agent_2 = self.agents[1]

        # while True:
            # Track player characteristics such as 
                # hand, VPs, supreme comamander, current turn, locally within this play function?

            # TODO: there are multiple rounds in one game
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

            
            # normal loop is
                # get_observation
                # modify_available_actions

                # get agent output action

                # apply action (call play)
                # post_play_triggers
                # add_effect
                # resolve_effect

            # player 1
            # observation
            # action
            # update

            # player 2
            # observation
            # action
            # update

        # applies game logic of tactical abilities that happen immediately
        # does not handle
            # Support (calculated at end of game)
            # 6 strength cards (Heavy Bombers, Super Battleship, Heavy Tanks)
            # Containment + Blockade (take effect in post play triggers)
            # Aerodrome + Airdrop (take effect after available actions are generated next turn)
        # Handles
        # Manuever, Ambush, Transport, Redeploy, Reinforce, Disrupt (immediate extra action)

        # the extra action procedures are to be coded in the game class

        pass