import fire
import api.util as util
import random

K = 32

def play_game(agent_1_path, agent_2_path, game_path, num_matches = 1, save_results = True, show_state=False, agent_1_kwargs = {}, agent_2_kwargs = {}):
    agent_1_class = util.import_class(agent_1_path)
    agent_2_class = util.import_class(agent_2_path)
    agent_1_id = agent_1_class.agent_type_id
    agent_2_id = agent_2_class.agent_type_id

    save_results = True
    if agent_1_id == agent_2_id:
        print("You have passed the same class for both agents. No results will be saved.")
        save_results = False

    game_class = util.import_class(game_path)

    player_1_total = 0
    player_2_total = 0
    all_ratings = util.load_json("elo_ratings.json")
    game_elos = all_ratings[game_class.id]

    if agent_1_id not in game_elos:
        game_elos[agent_1_id] = 1500
    if agent_2_id not in game_elos:
        game_elos[agent_2_id] = 1500
    
    agent_1_rating = game_elos[agent_1_id]
    agent_2_rating = game_elos[agent_2_id]
    print(f"{agent_1_id} elo: ", agent_1_rating)
    print(f"{agent_2_id} elo: ", agent_2_rating)

    # Get historical win percentage
    matches = util.load_json("matches.json")
    agent_1_total = 0
    total_matches = 0
    for m in matches:
        if agent_1_id in m and agent_2_id in m:
            agent_1_total += m[agent_1_id]
            total_matches += 1

    if total_matches > 0:
        print(f"Historical average scores for these two agents across {num_matches} matches:")
        print(f'{agent_1_id} avg score: ', agent_1_total/num_matches)
        print(f'{agent_2_id} avg score: ', 1 - agent_1_total / num_matches)
    
    Q1 = 10**(agent_1_rating / 400)
    Q2 = 10**(agent_2_rating / 400)

    agent_1_expected_score = Q1 / (Q1 + Q2)
    agent_2_expected_score = Q2 / (Q1 + Q2)

    for _ in range(num_matches):
        game = game_class(show_state=show_state, agent_1_kwargs=agent_1_kwargs, agent_2_kwargs=agent_2_kwargs)
        if random.choice([0,1]):
            game.init_game(agent_1_class, agent_2_class)
            player_1_score, player_2_score = game.play()
        else:
            game.init_game(agent_2_class, agent_1_class)
            player_2_score, player_1_score = game.play()
        
        print(f"{agent_1_id} score: ", player_1_score)
        print(f"{agent_2_id} score: ", player_2_score)

        player_1_total += player_1_score
        player_2_total += player_2_score

        if save_results:
            matches = util.load_json(f"matches.json")
            matches.append(
                {
                    "game": game_class.id,
                    agent_1_id: player_1_score,
                    agent_2_id: player_2_score,
                }
            )
            util.save_json(matches, "matches.json")
            print("Saved match information")

            agent_1_rating = agent_1_rating + K * (player_1_score - agent_1_expected_score) 
            agent_2_rating = agent_2_rating + K * (player_2_score - agent_2_expected_score) 
            all_ratings[game_class.id][agent_1_id] = agent_1_rating
            all_ratings[game_class.id][agent_2_id] = agent_2_rating
            print("Updated elos:")
            print(f"{agent_1_id}: ", agent_1_rating)
            print(f"{agent_2_id}: ", agent_2_rating)
            util.save_json(all_ratings, "elo_ratings.json")
    
    print("")
    print(f"Agent 1 ({agent_1_id}) average score: ", player_1_total/num_matches)
    print(f"Agent 2 ({agent_2_id}) average score: ", player_2_total/num_matches)

if __name__ == "__main__":
    fire.Fire(play_game)