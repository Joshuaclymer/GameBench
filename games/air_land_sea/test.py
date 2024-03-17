from games.air_land_sea.game import AirLandSea
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from agents.human_agent import HumanAgent
import api.util as util
from games.air_land_sea.cards import Card, Deck
import pprint

def test():
    agent_1_path = "agents.human_agent.HumanAgent"
    agent_2_path = "agents.human_agent.HumanAgent"
    agent_1_class = util.import_class(agent_1_path)
    agent_2_class = util.import_class(agent_2_path)
    game = AirLandSea()
    game.init_game(agent_1_class, agent_2_class)
    agent_1 = game.agents[0]
    agent_2 = game.agents[1]
    # print("Game id:",game.id)

    # constant testing environment
    game.player1.hand = [Card('Redeploy', 'Sea', 4, 'Instant', 'You may return 1 of your facedown cards to your hand. If you do, play a card'),
                            Card('Air Drop', 'Air', 2, 'Instant', 'The next time you play a card, you may play it to a non-matching theater'),
                            Card('Maneuver', 'Sea', 3, 'Instant', 'Flip an uncovered card in an adjacent theater'),
                            # Card('Aerodrome', 'Air', 4, 'Ongoing', 'You may play cards of strength 3 or less to non-matching theaters'),
                            Card('Containment', 'Air', 5, 'Ongoing', 'If any player plays a facedown card, destroy that card'),
                            # Card('Reinforce', 'Land', 1, 'Instant', 'Draw 1 card and play it facedown to an adjacent theater'),
                            # Card("Heavy Bombers", "Air", 6),
                            Card('Disrupt', 'Land', 5, 'Ongoing', 'Starting with you, both players choose and flip 1 of their uncovered cards'),
                            Card('Transport', 'Sea', 1, 'Instant', 'You may move 1 of your cards to a different theater')]
    
    game.player2.hand = [Card('Ambush', 'Land', 2, 'Instant', 'Flip any uncovered card'),
                            Card('Escalation', 'Sea', 2, 'Ongoing', 'All your facedown cards are now strength 4'),
                            Card('Maneuver', 'Sea', 3, 'Instant', 'Flip an uncovered card in an adjacent theater'),
                            Card('Blockade', 'Sea', 5, 'Ongoing', 'If any player plays a card to an adjacent theater occupied by at least 3 other cards, destroy that card'),
                            # Card('Reinforce', 'Land', 1, 'Instant', 'Draw 1 card and play it facedown to an adjacent theater'),
                            Card('Support', 'Air', 1, 'Ongoing', 'You gain +3 strength in each adjacent theater'),]

    game.player1.play(game.player1.hand[1], False, game.board.theaters[0])
    game.player2.play(game.player2.hand[2], False, game.board.theaters[1])
    # after a card is played faceup or flipped faceup its tactical ability takes effect immediately
    # aka the effect manager is called
    # the effect manager is also called when a card is flipped facedown too (to get rid of it)

    # Testing Specific Cards
    target = Card('Maneuver', 'Sea', 3, 'Instant', 'Flip an uncovered card in an adjacent theater')
    # target1 = Card('Aerodrome', 'Air', 4, 'Ongoing', 'You may play cards of strength 3 or less to non-matching theaters')
    # target2 = Card('Redeploy', 'Sea', 4, 'Instant', 'You may return 1 of your facedown cards to your hand. If you do, play a card')
    # game.player1.hand.append(target1)
    # game.player2.hand.append(target2)
    # game.player1.hand.append(target)
    # print("Player 1 hand")
    # print(game.player1.hand)
    # play to second theater
    # print("playing to second theater for p1")
    # game.player1.play(target1, False, game.board.theaters[1])
    # print("Player 1 hand after play")
    # print(game.player1.hand)
    # game.effect_manager.add_effect(target1, game.player1.id)
    # play to third theater for p2
    # print("playing to third theater for p2")
    # game.player2.play(target2, False, game.board.theaters[2])
    # game.effect_manager.add_effect(target2, game.player2.id)
    # print(game.board.get_board_string(game.player1.id))
    # print("Effect cards")
    # print(game.effect_manager.effect_cards)
    # print(game.board.search_ongoing_effect_location(support, game.effect_manager))

    # print("testing get_adjacent_theaters")
    # print(game.board.get_adjacent_theaters(1))

    # print("testing get_theater_strengths")
    # print(game.board.get_theater_strengths(game.effect_manager))
    
    # analyzing the bug:
    """
    player 1 plays redeploy to return air drop to their hand
    player 1 then plays maneuver faceup to land
    player 1 flips redeploy facedown
    """

    current_agent_turn = agent_1
    while True:
        current_player = game.get_player_by_agent_id(current_agent_turn.agent_id)
        print("current agent turn")
        print(current_agent_turn.agent_id)
        print("effects in play")
        print(game.effect_manager.effect_cards)
        # testing get observation
        observation, available_actions = game.get_observation(current_agent_turn)
        # observation, available_actions = game.get_observation(agent_2)
        print("\n------------------------\n")
        print("get observation")
        pprint.pprint(available_actions.predefined)
        print(observation.text)

        # testing modify_available_actions
        # print("testing modify_available_actions")
        # # pprint.pprint(available_actions.predefined)
        print("calling modify available actions on:", current_player.id)
        modified_actions = game.effect_manager.modify_available_actions(available_actions, current_player.hand, current_player.id)
        # print("modified actions")
        # pprint.pprint(modified_actions.predefined)

        # testing find_card_from_action
        # action = Action(action_id="0")
        # card = game.find_card_from_action(action, modified_actions)
        # print("card from action")
        # print(card)

        # Pick an action
        # action = Action(action_id="5")
        action = current_agent_turn.take_action(game.rules, observation, modified_actions, True)
        game.update(action, modified_actions, current_agent_turn)
        # switch players
        if current_agent_turn == agent_1:
            print("changing turn from p1 to p2")
            current_agent_turn = agent_2
        else:
            print("changing turn from p2 to p1")
            current_agent_turn = agent_1


    # testing check destroy trigger
    # print("testing check destroy trigger")
    # print(game.check_destroy_triggers(action, available_actions))

    # testing find faceup or facedown status
    # print("testing find faceup or facedown status")
    # print(game.find_faceup_or_facedown_from_action(action, available_actions))

    # test play_card_from_action
    # print("testing play_card_from_action")
    # played_card, played_to_theater = game.play_card_from_action(action, available_actions, agent_1)
    # game.effect_manager.add_effect(played_card, agent_1.agent_id)
    # print("observation of next player")
    # next_observation, next_available_actions = game.get_observation(agent_2)
    # # pprint.pprint(next_available_actions.predefined)
    # print(next_observation.text)

    # Testing resolve effect
    # print("testing resolve effect")
    # game.resolve_effect(played_card, agent_1, played_to_theater)

        print(game.board.get_board_string(agent_1.agent_id))
    
            # predefined action output:
                # Action object with "action_id" == "guess_18"
            # openended action output:
                # Action object with action_id == "submit_clue"
                # and openended_response == "conflict,2" # string
            # need to reference available actions using action_id to see if the action was to play a facedown card

    print("Test complete")


if __name__ == "__main__":
    test()