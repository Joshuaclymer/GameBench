import api.play_game as play_game
from itertools import combinations
import pandas as pd
import json

game_paths = [
    'games.sea_battle.SeaBattle',
    'games.codenames.Codenames',
    'games.two_rooms_and_a_boom.TwoRoomsAndABoom',
    'games.are_you_the_traitor.AreYouTheTraitor'
]

gpt3model = 'gpt-3.5-turbo-1106'
gpt4model = 'gpt-4-1106-preview'

agents = [
    ('agents.gpt.ChatGPTText', {}),
    ('agents.gpt.GPT4Text', {}),
    ('agents.gpt.ChainOfThought', {}),
    ('agents.gpt.BabbleAndPrune', {}),
    ('agents.gpt.GPT3ChainOfThought', {}),
    ('agents.gpt.GPT3BabbleAndPrune', {}),
    ('agents.rap.ReasoningViaPlanning', {"agent_type": 2}),
]

random_agent_path = 'agents.random_agent.RandomAgent'


# Generate all 2-combinations
combinations = list(combinations(agents, 2))

def run_game(game_path:str, agent1_path:str, agent2_path:str, agent_1_kwargs:dict, agent_2_kwargs:dict, num_games=1) -> None:
    for i in range(num_games):
        play_game.play_game(agent1_path, agent2_path, game_path, num_matches=num_games, save_results=True, show_state=True, agent_1_kwargs=agent_1_kwargs, agent_2_kwargs=agent_2_kwargs)

def run_all_games() -> None:
    for game in game_paths:
        # Play all agent combinations against each other
        for agent_combination in combinations:
            run_game(game, agent_combination[0][0], agent_combination[1][0], agent_combination[0][1], agent_combination[1][1],  num_games=5)
        # Play all agents against random agent
        for agent in agents:
            run_game(game, agent, random_agent_path, agent[1], {},num_games=5)

def generate_elo_table():
    # Load the data
    with open('elo_ratings.json', 'r') as f:
        data = json.load(f)
    # Convert the data to a DataFrame
    df = pd.DataFrame(data)
    # Write the DataFrame to a CSV file
    df.to_csv('elo_ratings.csv')

run_all_games()
generate_elo_table()