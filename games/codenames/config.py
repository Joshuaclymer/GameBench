from api.classes import Rules

class GameConfig:
    FIRST_TEAM_CARDS = 9
    SECOND_TEAM_CARDS = 8
    ASSASSIN_CARDS = 1
    NEUTRAL_CARDS = 7
    TOTAL_CARDS = FIRST_TEAM_CARDS + SECOND_TEAM_CARDS + ASSASSIN_CARDS + NEUTRAL_CARDS
    NUM_WORDS = 25
    WORD_LIST = ["AGENT",
    "AFRICA",
    "AIR",
    "ALIEN",
    "ALPS",
    "AMAZON",
    "AMBULANCE",
    "AMERICA",
    "ANGEL",
    "ANTARCTICA",
    "APPLE",
    "ARM",
    "ATLANTIS",
    "AUSTRALIA",
    "AZTEC",
    "BACK",
    "BALL",
    "BAND",
    "BANK",
    "BAR",
    "BARK",
    "BAT",
    "BATTERY",
    "BEACH",
    "BEAR",
    "BEAT",
    "BED",
    "BEIJING",
    "BELL",
    "BELT",
    "BERLIN",
    "BERMUDA",
    "BERRY",
    "BILL",
    "BLOCK",
    "BOARD",
    "BOLT",
    "BOMB",
    "BOND",
    "BOOM",
    "BOOT",
    "BOTTLE",
    "BOW",
    "BOX",
    "BRIDGE",
    "BRUSH",
    "BUCK",
    "BUFFALO",
    "BUG",
    "BUGLE",
    "BUTTON",
    "CALF",
    "CANADA",
    "CAP",
    "CAPITAL",
    "CAR",
    "CARD",
    "CARROT",
    "CASINO",
    "CAST",
    "CAT",
    "CELL",
    "CENTAUR",
    "CENTER",
    "CHAIR",
    "CHANGE",
    "CHARGE",
    "CHECK",
    "CHEST",
    "CHICK",
    "CHINA",
    "CHOCOLATE",
    "CHURCH",
    "CIRCLE",
    "CLIFF",
    "CLOAK",
    "CLUB",
    "CODE",
    "COLD",
    "COMIC",
    "COMPOUND",
    "CONCERT",
    "CONDUCTOR",
    "CONTRACT",
    "COOK",
    "COPPER",
    "COTTON",
    "COURT",
    "COVER",
    "CRANE",
    "CRASH",
    "CRICKET",
    "CROSS",
    "CROWN",
    "CYCLE",
    "CZECH",
    "DANCE",
    "DATE",
    "DAY",
    "DEATH",
    "DECK",
    "DEGREE",
    "DIAMOND",
    "DICE",
    "DINOSAUR",
    "DISEASE",
    "DOCTOR",
    "DOG",
    "DRAFT",
    "DRAGON",
    "DRESS",
    "DRILL",
    "DROP",
    "DUCK",
    "DWARF",
    "EAGLE",
    "EGYPT",
    "EMBASSY",
    "ENGINE",
    "ENGLAND",
    "EUROPE",
    "EYE",
    "FACE",
    "FAIR",
    "FALL",
    "FAN",
    "FENCE",
    "FIELD",
    "FIGHTER",
    "FIGURE",
    "FILE",
    "FILM",
    "FIRE",
    "FISH",
    "FLUTE",
    "FLY",
    "FOOT",
    "FORCE",
    "FOREST",
    "FORK",
    "FRANCE",
    "GAME",
    "GAS",
    "GENIUS",
    "GERMANY",
    "GHOST",
    "GIANT",
    "GLASS",
    "GLOVE",
    "GOLD",
    "GRACE",
    "GRASS",
    "GREECE",
    "GREEN",
    "GROUND",
    "HAM",
    "HAND",
    "HAWK",
    "HEAD",
    "HEART",
    "HELICOPTER",
    "HIMALAYAS",
    "HOLE",
    "HOLLYWOOD",
    "HONEY",
    "HOOD",
    "HOOK",
    "HORN",
    "HORSE",
    "HORSESHOE",
    "HOSPITAL",
    "HOTEL",
    "ICE",
    "ICE CREAM",
    "INDIA",
    "IRON",
    "IVORY",
    "JACK",
    "JAM",
    "JET",
    "JUPITER",
    "KANGAROO",
    "KETCHUP",
    "KEY",
    "KID",
    "KING",
    "KIWI",
    "KNIFE",
    "KNIGHT",
    "LAB",
    "LAP",
    "LASER",
    "LAWYER",
    "LEAD",
    "LEMON",
    "LEPRECHAUN",
    "LIFE",
    "LIGHT",
    "LIMOUSINE",
    "LINE",
    "LINK",
    "LION",
    "LITTER",
    "LOCH NESS",
    "LOCK",
    "LOG",
    "LONDON",
    "LUCK",
    "MAIL",
    "MAMMOTH",
    "MAPLE",
    "MARBLE",
    "MARCH",
    "MASS",
    "MATCH",
    "MERCURY",
    "MEXICO",
    "MICROSCOPE",
    "MILLIONAIRE",
    "MINE",
    "MINT",
    "MISSILE",
    "MODEL",
    "MOLE",
    "MOON",
    "MOSCOW",
    "MOUNT",
    "MOUSE",
    "MOUTH",
    "MUG",
    "NAIL",
    "NEEDLE",
    "NET",
    "NEW YORK",
    "NIGHT",
    "NINJA",
    "NOTE",
    "NOVEL",
    "NURSE",
    "NUT",
    "OCTOPUS",
    "OIL",
    "OLIVE",
    "OLYMPUS",
    "OPERA",
    "ORANGE",
    "ORGAN",
    "PALM",
    "PAN",
    "PANTS",
    "PAPER",
    "PARACHUTE",
    "PARK",
    "PART",
    "PASS",
    "PASTE",
    "PENGUIN",
    "PHOENIX",
    "PIANO",
    "PIE",
    "PILOT",
    "PIN",
    "PIPE",
    "PIRATE",
    "PISTOL",
    "PIT",
    "PITCH",
    "PLANE",
    "PLASTIC",
    "PLATE",
    "PLATYPUS",
    "PLAY",
    "PLOT",
    "POINT",
    "POISON",
    "POLE",
    "POLICE",
    "POOL",
    "PORT",
    "POST",
    "POUND",
    "PRESS",
    "PRINCESS",
    "PUMPKIN",
    "PUPIL",
    "PYRAMID",
    "QUEEN",
    "RABBIT",
    "RACKET",
    "RAY",
    "REVOLUTION",
    "RING",
    "ROBIN",
    "ROBOT",
    "ROCK",
    "ROME",
    "ROOT",
    "ROSE",
    "ROULETTE",
    "ROUND",
    "ROW",
    "RULER",
    "SATELLITE",
    "SATURN",
    "SCALE",
    "SCHOOL",
    "SCIENTIST",
    "SCORPION",
    "SCREEN",
    "SCUBA DIVER",
    "SEAL",
    "SERVER",
    "SHADOW",
    "SHAKESPEARE",
    "SHARK",
    "SHIP",
    "SHOE",
    "SHOP",
    "SHOT",
    "SINK",
    "SKYSCRAPER",
    "SLIP",
    "SLUG",
    "SMUGGLER",
    "SNOW",
    "SNOWMAN",
    "SOCK",
    "SOLDIER",
    "SOUL",
    "SOUND",
    "SPACE",
    "SPELL",
    "SPIDER",
    "SPIKE",
    "SPINE",
    "SPOT",
    "SPRING",
    "SPY",
    "SQUARE",
    "STADIUM",
    "STAFF",
    "STAR",
    "STATE",
    "STICK",
    "STOCK",
    "STRAW",
    "STREAM",
    "STRIKE",
    "STRING",
    "SUB",
    "SUIT",
    "SUPERHERO",
    "SWING",
    "SWITCH",
    "TABLE",
    "TABLET",
    "TAG",
    "TAIL",
    "TAP",
    "TEACHER",
    "TELESCOPE",
    "TEMPLE",
    "THEATER",
    "THIEF",
    "THUMB",
    "TICK",
    "TIE",
    "TIME",
    "TOKYO",
    "TOOTH",
    "TORCH",
    "TOWER",
    "TRACK",
    "TRAIN",
    "TRIANGLE",
    "TRIP",
    "TRUNK",
    "TUBE",
    "TURKEY",
    "UNDERTAKER",
    "UNICORN",
    "VACUUM",
    "VAN",
    "VET",
    "WAKE",
    "WALL",
    "WAR",
    "WASHER",
    "WASHINGTON",
    "WATCH",
    "WATER",
    "WAVE",
    "WEB",
    "WELL",
    "WHALE",
    "WHIP",
    "WIND",
    "WITCH",
    "WORM",
    "YARD"]

    codenames_rules = Rules(
    title="Codenames",
    summary=("A strategic game of guessing and deduction where two teams, Red and Blue, compete "
             "to identify their respective words on a grid based on one-word clues given by their "
             "Spymasters. The game ends when all words of one team are guessed, the assassin word "
             "is chosen, or there are no more legal moves possible."),
    additional_details=[
        ("Game Setup", "Teams: Two teams (Red and Blue), each with a Spymaster and an Operative. "
                       "Board: A grid of words, some belonging to each team, one assassin, and neutral words. "
                       "Word Distribution: Randomly assigned, with a specific number for each team and the assassin."),
        ("Roles", "Spymaster: Knows which words correspond to which team / the assassin. Gives one-word clues that relate to any number of their team's words on the board. "
                  "Operative: Guesses the words based on the Spymaster's clues. Aims to guess all the words only related to their team."),
        ("Turn Structure", "Spymaster's Turn: Give a clue to their operative and a number indicating how many words relate to that clue. "
                           "Operative's Turn: Guess words, aiming to find all their team's words. After each guess, the Spymaster will indicate whether the word is correct or not. If the word belongs to their team, the Operative can continue guessing. If the word belongs to the other team, the turn ends but the other team has been advantaged. If the word is neutral, the turn ends with no penalty. If the word is the assassin, the game ends immediately. Operatives can also end their turn prematurely after at least one guess."),
        ("Winning Conditions", "A team wins by correctly guessing all their words. "
                               "Game ends immediately if the assassin word is guessed and the team who guessed it loses."),
        ("Forbidden Actions", "Spymasters cannot use part or any form of the words on the board in their clues. "
                              "Spymasters cannot use words that sound like words on the board in their clues. "
                              "Clues must be exactly one word and one number."
                              "Operatives must only guess; they cannot pass extra information to the Spymaster or vice versa."),
        ("Scoring", "Points are awarded to the team who correctly guesses all their words or to the other team if one team guesses the assassin word."),
        ("Special Rules", "If zero words are related to the clue, the Spymaster can give a clue of '0' and the Operative can guess an unlimited number of words."),
    ]
)