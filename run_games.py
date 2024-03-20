import api.play_game as play_game
from itertools import combinations
import pandas as pd
import json
import api.util as util
import traceback
import sys

game_paths = [
    'games.sea_battle.SeaBattle',
    'games.codenames.game.CodenamesGame',
    'games.two_rooms_and_a_boom.two_rooms.TwoRoomsAndaBoom',
    'games.are_you_the_traitor.aytt.AreYouTheTraitor'
]

gpt3model = 'gpt-3.5-turbo-1106'
gpt4model = 'gpt-4-1106-preview'

agents = [
    ('agents.gpt.ChatGPTText', {}),
    ('agents.gpt.GPT4Text', {}),
    ('agents.gpt.GPT4COT', {}),
    ('agents.gpt.GPT4BAP', {}),
    ('agents.gpt.GPT3ChainOfThought', {}),
    ('agents.gpt.GPT3BabbleAndPrune', {}),
    #('agents.rap.ReasoningViaPlanning', {"agent_type": 2}),
    ('agents.random_agent.RandomAgent', {})
]
agent = "agents.gpt.ChatGPTText"
random_agent_path = 'agents.random_agent.RandomAgent'


games = iter([game for _ in range(5) for game in game_paths])

def play():
    while True:
        game = next(games)
        while True:
            try:
                play_game.play_game("agents.gpt.ChatGPTText", "agents.random_agent.RandomAgent", game, num_matches=1, save_results=True, show_state=True, agent_1_kwargs={"transparent_reasoning": True})
                break
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                while True:
                    i = input("Press ^S[enter] to skip, or [enter] to retry: ")
                    if i == "S":
                        game = next(games)
                        break
                    elif i == "":
                        break

                continue

if not sys.flags.interactive:
    print("Run in interactive mode.")
    sys.exit(1)

play()