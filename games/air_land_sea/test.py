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
    agent_1 = game.agents[0]
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
    # check theater strengths
    # print(game.board.theaters[0].player_total_strength)
    # print(game.board.theaters[1].player_total_strength)
    # print(game.board.theaters[2].player_total_strength)

    game.board.theaters[2].player_cards[1][-1].flip()
    # print(game.board.get_board_string())
    # check theater strengths
    # print(game.board.theaters[0].player_total_strength)
    # print(game.board.theaters[1].player_total_strength)
    # print(game.board.theaters[2].player_total_strength)

    observation, available_actions = game.get_observation(agent_1)
    print(observation.text)

    print("Test complete")


if __name__ == "__main__":
    test()