from games.air_land_sea.game import AirLandSea
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from agents.human_agent import HumanAgent
import api.util as util

def test():
    agent_1_path = "agents.human_agent.HumanAgent"
    agent_2_path = "agents.human_agent.HumanAgent"
    agent_1_class = util.import_class(agent_1_path)
    agent_2_class = util.import_class(agent_2_path)
    game = AirLandSea()
    game.init_game(agent_1_class, agent_2_class)
    agent_1 = game.agents[0] # this is why it thinks the agent is a player
    print("Game id:",game.id)
    # print(game.player1.hand[0])

    # put cards in theater to test, lets just start easy, won't make play function
    card_to_play = game.player1.hand.pop()
    game.board.theaters[0].player_1_cards.append(card_to_play)

    # testing theater string
    # print(game.board.theaters[0].get_theater_string())
    # testing flip function
    # game.board.theaters[0].player_1_cards[0].flip()
    # print(game.board.theaters[0].get_theater_string())
    # test board string function
    # print(game.board.get_board_string())
    # observation, available_actions = game.get_observation(agent_1)


    # TODO: what's the next thing to make?
    # have a player capable of playing a card?
        # TODO: get observation needs to work
    print("Test complete")


if __name__ == "__main__":
    test()