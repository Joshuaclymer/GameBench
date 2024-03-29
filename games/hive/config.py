from api.classes import Rules

class GameConfig:
    NUM_BEETLE_CARDS = 0
    NUM_SPIDER_CARDS = 2
    NUM_GRASSHOPPER_CARDS = 3
    NUM_SOLDIERANT_CARDS = 3
    NUM_QUEENBEE_CARDS = 1
    MAX_TURNS = 250
    rules = Rules(
        title="Hive", summary="Hive is a bug-themed abstract strategy game. The object of Hive is to capture the opponent's queen bee by allowing it to become completely surrounded by pieces belonging to either player, while avoiding the capture of one's own queen. Tiles can be moved to other positions after being placed according to various rules, much like chess pieces.",  
        additional_details={"Placing the Queen Bee": "Players must place their Queen Bee by their fourth turn. Until then, they cannot move any placed pieces.", 
                            "Queen Bee Movement": "The Queen Bee can only move one space at a time around the hive.",
                            "Spider Movement": "The Spider can move exactly three spaces.",
                            "Ant Movement": "Able to move to any empty space around the hive as long as other movement rules are not violated.",
                            "Grasshopper Movement": "The Grasshopper can jump over over adjacent pieces, landing on the first empty space.",
                            "One Hive Rule": "The tiles must always be connected; you cannot move a piece if it would break the hive into separate groups.",
                            "Freedom to Move": "A piece can only move if it can physically slide to its new position without disturbing other tiles.",
                            "Max Turns": "The game ends after " + str(MAX_TURNS) + " turns."  + "If no Queen Bee is surrounded by the end of the game, the game is a draw."
                            }
    )