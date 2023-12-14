import fire
import api.util as util

K = 4

def play_game(agent_1_path, agent_2_path, game_path, num_matches = 1):
    agent_1_class = util.import_class(agent_1_path)
    agent_2_class = util.import_class(agent_2_path)
    agent_1_id = agent_1_class.agent_type_id
    agent_2_id = agent_2_class.agent_type_id

    game_class = util.import_class(game_path)
    player_1_total = 0
    player_2_total = 0
    all_ratings = util.load_json("elo_ratings.json")
    game_elos = all_ratings[game_class.game_id]

    if agent_1_id not in game_elos:
        game_elos[agent_1_id] = 1500
    if agent_2_id not in game_elos:
        game_elos[agent_2_id] = 1500
    
    agent_1_rating = game_elos[agent_1_id]
    agent_2_rating = game_elos[agent_2_id]
    print(f"{agent_1_id} elo: ", agent_1_rating)
    print(f"{agent_2_id} elo: ", agent_2_rating)
    
    Q1 = 10**(agent_1_rating / 400)
    Q2 = 10**(agent_2_rating / 400)

    agent_1_expected_score = Q1 / (Q1 + Q2)
    agent_2_expected_score = Q2 / (Q1 + Q2)

    for _ in range(num_matches):
        game = game_class()
        game.init_game(agent_1_class, agent_2_class)
        player_1_score, player_2_score = game.game_loop()
        player_1_total += player_1_score
        player_2_total += player_2_score
        matches = util.load_json(f"matches.json")
        matches.append(
            {
                "game": game_class.game_id,
                agent_1_id: player_1_score,
                agent_2_id: player_2_score,
            }
        )
        util.save_json(matches, "matches.json")
        print("Saved match information")

        agent_1_rating = agent_1_expected_score + K * (player_1_score - agent_1_expected_score) 
        agent_2_rating = agent_2_expected_score + K * (player_2_score - agent_2_expected_score) 
        all_ratings[game_class.game_id][agent_1_id] = agent_1_rating
        all_ratings[game_class.game_id][agent_2_id] = agent_2_rating
        print("Updated elos:")
        print(f"{agent_1_id}: ", agent_1_rating)
        print(f"{agent_2_id}: ", agent_2_rating)

if __name__ == "__main__":
    fire.Fire(play_game)