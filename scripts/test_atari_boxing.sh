python api/play_game.py \
    --agent_1_path agents.random_agent.RandomAgent \
    --agent_2_path agents.gpt.GPT4Vision \
    --game_path games.atari.boxing.AtariBoxing \
    --show_state \
    --num_matches 1 \
    --agent_2_kwargs '{"transparent_reasoning": True}'