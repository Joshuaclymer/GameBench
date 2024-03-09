from games.air_land_sea.game import AirLandSea
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from agents.human_agent import HumanAgent
import api.util as util
from games.air_land_sea.cards import Card, Deck

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

    # testing theater string
    # print(game.board.theaters[0].get_theater_string())
    # testing flip function
    # game.board.theaters[0].player_cards[1][-1].flip()
    # test board string function
    # print(game.board.get_board_string())

    # print("hand sizes")
    # print(len(game.player1.hand))
    # print(len(game.player2.hand))

    game.player1.play(game.player1.hand[0], True, game.board.theaters[0])
    game.player2.play(game.player2.hand[0], True, game.board.theaters[0])
    game.player2.play(game.player2.hand[0], True, game.board.theaters[0])
    game.player2.play(game.player2.hand[0], True, game.board.theaters[1])
    game.player2.play(game.player2.hand[0], True, game.board.theaters[2])
    game.player2.play(game.player2.hand[0], False, game.board.theaters[2])
    # print(game.board.get_board_string())

    game.board.theaters[2].player_cards[1][-1].flip()
    # print(game.board.get_board_string())

    observation, available_actions = game.get_observation(agent_2)
    print(observation.text)
    print(available_actions.predefined)
    # print(observation.text)

    # after a card is played faceup or flipped faceup its tactical ability takes effect immediately
    # aka the effect manager is called
    # the effect manager is also called when a card is flipped facedown too (to get rid of it)

    # first we need a way to always play the Support card in order to test it
    # give player 1 a Support card regardless of what else is going on

    # support = Card('Support', 'Air', 1, 'Ongoing', 'You gain +3 strength in each adjacent theater')
    # game.player1.hand.append(support)
    # game.player2.hand.append(support)
    # # print(game.player1.hand)
    # # play to first theater
    # game.player1.play(support, True, game.board.theaters[1])
    # game.effect_manager.add_effect(support, game.player1.id)
    # # play to second theater for p2
    # game.player2.play(support, True, game.board.theaters[2])
    # game.effect_manager.add_effect(support, game.player2.id)
    # print(game.board.get_board_string())
    # print("Effect cards")
    # print(game.effect_manager.effect_cards)
    # # print(game.board.search_ongoing_effect_location(support, game.effect_manager))

    # # print("testing get_adjacent_theaters")
    # # print(game.board.get_adjacent_theaters(1))

    # print("testing get_theater_strengths")
    # print(game.board.get_theater_strengths(game.effect_manager))


    print("Test complete")


if __name__ == "__main__":
    test()