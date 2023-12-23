"""Some basic settings for the game

This isn't meant to be a complex configuration management, just some settings.
"""

WINNING_SCORE = 500

COMMODITIES = [
    "wheat",
    "barley",
    "coffee",
    "corn",
    "sugar",
    "oats",
    "soybeans",
    "oranges",
]

COMMODITY_VALUES = {
    COMMODITIES[0]: 100,
    COMMODITIES[1]: 85,
    COMMODITIES[2]: 80,
    COMMODITIES[3]: 75,
    COMMODITIES[4]: 65,
    COMMODITIES[5]: 60,
    COMMODITIES[6]: 55,
    COMMODITIES[7]: 50,
}

COMMODITIES_PER_HAND = 9

BULL = "bull"
BULL_PENALTY = 20
BEAR = "bear"
BEAR_PENALTY = 20
