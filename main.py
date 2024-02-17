from api.play_game import play_game

play_game(
    "agents.random_agent.RandomAgent",
    "agents.gpt.GPT4Text",
    "games.pit.PitGame",
    show_state=True
)