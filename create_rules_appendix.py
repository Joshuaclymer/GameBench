import api.util as util

game_paths = [
    "games.arctic_scavengers.arctic_scavengers.ArcticScavengers",
    "games.are_you_the_traitor.aytt.AreYouTheTraitor",
    "games.two_rooms_and_a_boom.two_rooms.TwoRoomsAndaBoom",
    "games.air_land_sea.game.AirLandSea",
    "games.codenames.game.CodenamesGame",
    "games.hive.game.HiveGame",
    "games.santorini.santorini.Santorini",
    "games.pit.pit.PitGame",
    "games.sea_battle.SeaBattle"
]

latex = ""
for path in game_paths:
    game_class = util.import_class(path)
    rules = game_class.rules

    latex += "\\textbf{" + rules.title + "} " + rules.summary + "\n\n"
    if rules.additional_details:
        latex += "\\begin{itemize}"
        for detail, comment in rules.additional_details.items():
            latex += "\n\t\\item \\textbf{" + detail + "} " + comment
        latex += "\n\\end{itemize}\n"

with open("rules_appendix.tex", "w") as f:
    f.write(latex)