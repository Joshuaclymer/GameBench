# This test script is easier to debug in VS Code than the original Bash script.

from api.play_game import play_game

play_game(
    agent_1_path="agents.random_agent.RandomAgent",
    agent_2_path="agents.gpt.GPT4",
    game_path="games.santorini.santorini.Santorini",
    show_state=True,
    num_matches=3,
)
