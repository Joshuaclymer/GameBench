python api/play_game.py \
    --agent_1_path agents.gpt.ChainOfThought \
    --agent_2_path agents.gpt.GPT4Text \
    --game_path games.tic_tac_toe.TicTacToe \
    --show_state \
    --num_matches 50 \
    --agent_1_kwargs '{"transparent_reasoning": True}'

# python api/play_game.py \
#     --agent_1_path agents.gpt.BabbleAndPrune \
#     --agent_2_path agents.gpt.GPT4Text \
#     --game_path games.tic_tac_toe.TicTacToe \
#     --show_state \
#     --num_matches 50

# python api/play_game.py \
#     --agent_1_path agents.gpt.BabbleAndPrune \
#     --agent_2_path agents.gpt.GPT4Text \
#     --game_path games.tic_tac_toe.TicTacToe \
#     --show_state \
#     --num_matches 50