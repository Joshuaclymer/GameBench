from cards.card import *

class Brawler (Card):
    def __init__(self):
        super().__init__(title="Brawler", tribe_members=1,
                    actions={"DIG":Action(ActionType.STANDARD, ActionSymbol.DIG, 1), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 2)}, cost=[Cost(CostType.FOOD, 2)])
        
class Refugee (Card):
    def __init__(self):
        super().__init__(title="Refugee", tribe_members=1,
                   actions={"DIG":Action(ActionType.STANDARD, ActionSymbol.DIG, 0), "HUNT":Action(ActionType.STANDARD, ActionSymbol.HUNT, 0)}, cost=[Cost(CostType.FOOD, 0)])
        
class Scavenger (Card):
    def __init__(self):
        super().__init__(title="Scavenger", tribe_members=1,
                   actions={"DRAW":Action(ActionType.STANDARD, ActionSymbol.DRAW, 1), "DIG":Action(ActionType.STANDARD, ActionSymbol.DIG, 1), "HUNT":Action(ActionType.STANDARD, 
                            ActionSymbol.HUNT, 1), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 1)}, cost=[Cost(CostType.FOOD, 1)])

class Hunter (Card):
    def __init__(self):
        super().__init__(title="Hunter", tribe_members=1,
                   actions={"HUNT":Action(ActionType.STANDARD, ActionSymbol.HUNT, 2), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 1)}, cost=[Cost(CostType.MEDICINE, 1)])
        
class Saboteur (Card):
    def __init__(self):
        super().__init__(title="Saboteur", tribe_members=1, special_instruction="Disarm one tool card, forcing it to be discarded.",
                   actions={"DIG":Action(ActionType.STANDARD, ActionSymbol.DIG, 1), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 1)}, cost=[Cost(CostType.MEDICINE, 1), Cost(CostType.FOOD, 1)])
        
class Scout(Card):
    def __init__(self):
        super().__init__(title="Scout", tribe_members=1,
                     actions={"DRAW":Action(ActionType.STANDARD, ActionSymbol.DRAW, 2), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 2)}, cost=[Cost(CostType.MEDICINE, 1), Cost(CostType.FOOD, 2)])
        
class GroupLeaders(Card):
    def __init__(self):
        super().__init__(title="Group Leaders", tribe_members=2, special_instruction="Any action may be enhanced by both Group Leaders and a tool.",
                     actions={"DRAW":Action(ActionType.MODIFIER, ActionSymbol.DRAW, 2), "DIG":Action(ActionType.MODIFIER, ActionSymbol.DIG, 2), "HUNT":Action(ActionType.MODIFIER, ActionSymbol.HUNT, 2), 
                              "FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 2)}, cost=[Cost(CostType.MEDICINE, 2), Cost(CostType.FOOD, 2)])

class SniperTeam(Card):
    def __init__(self):
        super().__init__(title="Sniper Team", tribe_members=2, special_instruction="Snipe one tribe member, forcing it to be discarded.",
                    cost=[Cost(CostType.MEDICINE, 2), Cost(CostType.FOOD, 2)])
        
#Is cost of Thugs 6 food + 6 medicine or 6 food or 6 medicine?
class Thug(Card):
    def __init__(self):
        super().__init__(title="Thug", tribe_members=3,
                     actions={"DIG":Action(ActionType.STANDARD, ActionSymbol.DIG, 1), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 3)}, cost=[Cost(CostType.MEDICINE, 6), Cost(CostType.FOOD, 6)])
        
class TribeFamily(Card):
    def __init__(self):
        super().__init__(title="Tribe Family", tribe_members=5,
                     actions={"HUNT":Action(ActionType.STANDARD, ActionSymbol.HUNT, 0), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 0)}, supply_pile=SupplyPileType.CONTESTED_RESOURCES)
        
class WolfPack(Card):
    def __init__(self):
        super().__init__(title="Wolf Pack",
                     actions={"HUNT":Action(ActionType.MODIFIER, ActionSymbol.HUNT, 3), "FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 2)}, supply_pile=SupplyPileType.CONTESTED_RESOURCES)
        
class Grenade(Card):
    def __init__(self):
        super().__init__(title="Grenade",
                     actions={"FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 3)}, supply_pile=SupplyPileType.CONTESTED_RESOURCES)
        
class SledTeam(Card):
    def __init__(self):
        super().__init__(title="Sled Team", tribe_members=2,
                     actions={"DRAW":Action(ActionType.STANDARD, ActionSymbol.DRAW, 2), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 1)}, supply_pile=SupplyPileType.CONTESTED_RESOURCES)
        
class FieldCrew(Card):
    def __init__(self):
        super().__init__(title="Field Crew", tribe_members=4,
                     actions={"DIG":Action(ActionType.STANDARD, ActionSymbol.DIG, 2), "HUNT":Action(ActionType.STANDARD, ActionSymbol.HUNT, 2), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 2)}, 
                     supply_pile=SupplyPileType.CONTESTED_RESOURCES)
        
class Junk(Card):
    def __init__(self):
        super().__init__(title="Junk", supply_pile=SupplyPileType.JUNKYARD)

class MultiTool(Card):
    def __init__(self):
        super().__init__(title="Multitool", 
                         actions={"DIG":Action(ActionType.MODIFIER, ActionSymbol.DIG, 1), "HUNT":Action(ActionType.MODIFIER, ActionSymbol.HUNT, 1), "FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 1)}, supply_pile=SupplyPileType.JUNKYARD)
        
class Net(Card):
    def __init__(self):
        super().__init__(title="Net", 
                         actions={"HUNT":Action(ActionType.MODIFIER, ActionSymbol.HUNT, 2), "FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 1)}, supply_pile=SupplyPileType.JUNKYARD)
        
class Spear(Card):
    def __init__(self):
        super().__init__(title="Spear", 
                         actions={"HUNT":Action(ActionType.MODIFIER, ActionSymbol.HUNT, 1), "FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 2)}, supply_pile=SupplyPileType.JUNKYARD)
        
class Pickaxe(Card):
    def __init__(self):
        super().__init__(title="Pickaxe", 
                         actions={"DIG":Action(ActionType.MODIFIER, ActionSymbol.DIG, 1), "FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 2)}, supply_pile=SupplyPileType.JUNKYARD)
        
class Shovel(Card):
    def __init__(self):
        super().__init__(title="Shovel", 
                         actions={"DIG":Action(ActionType.MODIFIER, ActionSymbol.DIG, 2), "FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 1)}, supply_pile=SupplyPileType.JUNKYARD)
        
class Medkit(Card):
    def __init__(self):
        super().__init__(title="Medkit", 
                         actions={"MEDICINE":Action(ActionType.STANDARD, ActionSymbol.MEDICINE, 2)}, supply_pile=SupplyPileType.JUNKYARD)
        
class Pills(Card):
    def __init__(self):
        super().__init__(title="Pills", 
                         actions={"MEDICINE":Action(ActionType.STANDARD, ActionSymbol.MEDICINE, 1)}, supply_pile=SupplyPileType.JUNKYARD)
        
# class TheGearheads(Card):
#     def __init__(self):
#         super().__init__(title="The Gearheads", tribe_members=5, special_instruction="At game end this gang joins whichever tribe has accumulated the most tools.")

# class TheMasons(Card):
#     def __init__(self):
#         super().__init__(title="The Gearheads", tribe_members=5, special_instruction="At game end this gang joins whichever tribe has accumulated the most buildings.")

# class TheGearheads(Card):
#     def __init__(self):
#         super().__init__(title="The Gearheads", tribe_members=5, special_instruction="At game end this gang joins whichever tribe has accumulated the most meds.")

# class HydroponicGarden(Card):
#     def __init__(self):
#         super().__init__(
#             title="Hydroponic Garden",
#             special_instruction="Generates 1 food each round to assist with hiring mercenaries. Food does not accumulate.",
#             actions={Action(ActionType.STANDARD, ActionSymbol.BUILD_TIME, 4), Action(ActionType.STANDARD, ActionSymbol.FOOD, 1)}
#         )

# class Bunker(Card):
#     def __init__(self):
#         super().__init__(
#             title="Bunker",
#             special_instruction="Allows tribe members to be stored and then retrieved prior to the skirmish.",
#             actions={Action(ActionType.STANDARD, ActionSymbol.BUILD_TIME, 4), Action(ActionType.STANDARD, ActionSymbol.TRIBE_MEMBERS, 3)}
#         )

# class Engineer(Card):
#     def __init__(self):
#         super().__init__(title="Engineer", tribe_members=1, special_instruction="Builds one building by digging in the schematics pile.",
#                      actions={"DRAW":Action(ActionType.STANDARD, ActionSymbol.DRAW, 1), "DIG":Action(ActionType.STANDARD, ActionSymbol.DIG, 2)}, 
#                      cost=[Cost(CostType.MEDICINE, 1), Cost(CostType.FOOD, 2)])
        
# class Medic(Card):
#     def __init__(self):
#         super().__init__(title="Medic", tribe_members=1, special_instruction="Saves one tribe member from the effects of a snipe.",
#                      actions={"DRAW":Action(ActionType.STANDARD, ActionSymbol.DRAW, 1), "MEDICINE":Action(ActionType.STANDARD, ActionSymbol.MEDICINE, 1)}, 
#                      cost=[Cost(CostType.FOOD, 3)])

# class Rifle(Card):
#     def __init__(self):
#         super().__init__(title="Rifle", 
#                          actions={"HUNT":Action(ActionType.MODIFIER, ActionSymbol.HUNT, 2), "FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 2)}, supply_pile=SupplyPileType.JUNKYARD)

# class Toolkit(Card):
#     def __init__(self):
#         super().__init__(title="Toolkit", special_instruction="Increases a tribe members's build by +2 cards.",
#                          actions={"DIG":Action(ActionType.MODIFIER, ActionSymbol.DIG, 2)}, supply_pile=SupplyPileType.JUNKYARD)
        
# class Assassin(Card):
#     def __init__(self):
#         super().__init__(title="Assassin", tribe_members=1, special_instruction="Snipe any single-unit tribe member.",
#                          actions={"DRAW":Action(ActionType.STANDARD, ActionSymbol.DRAW, 1)}, cost=[Cost(CostType.MEDICINE, 2)])

# class Courier(Card):
#     def __init__(self):
#         super().__init__(title="Courier", tribe_members=1, special_instruction="When you perform a draw, you must discard 2 of the drawn cards per Courier played.",
#                          actions={"DRAW":Action(ActionType.STANDARD, ActionSymbol.DRAW, 3), "FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 1)}, cost=[Cost(CostType.MEDICINE, 1), Cost(CostType.FOOD, 1)])

# class DrillSergeant(Card):
#     def __init__(self):
#         super().__init__(title="Drill Sergeant", tribe_members=1, special_instruction="May choose up to 2 cards from your discard pile and shuffle them into your deck. Then draw two cards.",
#                          actions={"DIG":Action(ActionType.STANDARD, ActionSymbol.DIG, 2), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 1)}, cost=[Cost(CostType.MEDICINE, 1), Cost(CostType.FOOD, 2)])

# class Guard(Card):
#     def __init__(self):
#         super().__init__(title="Guard", tribe_members=1, special_instruction="May cancel 1 pre-skirmish action targeting your card(s). Then, draw 1 card.",
#                          actions={"FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 2)}, cost=[Cost(CostType.FOOD, 2)])
        
# class HardyScavenger(Card):
#     def __init__(self):
#         super().__init__(title="Hardy Scavenger", tribe_members=1, special_instruction="If you don't win the Skirmish, return any Hardy Scavengers back to your hand. You still draw a normal starting hand.",
#                          actions={"DRAW":Action(ActionType.STANDARD, ActionSymbol.DRAW, 0), "DIG":Action(ActionType.STANDARD, ActionSymbol.DIG, 1), "HUNT":Action(ActionType.STANDARD, ActionSymbol.HUNT, 1), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 0)}, cost=[Cost(CostType.FOOD, 1)])
        
# class Provocateur(Card):
#     def __init__(self):
#         super().__init__(title="Provocateur", tribe_members=1, special_instruction="May use your tribe member count in place of your fight score.",
#                          actions={"DRAW":Action(ActionType.STANDARD, ActionSymbol.DRAW, 1), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 1)}, cost=[Cost(CostType.MEDICINE, 1)])

# class Rogue(Card):
#     def __init__(self):
#         super().__init__(title="Rogue", tribe_members=1, special_instruction="If there is a tie for the highest fight score, you win the skirmish. The first Rogue played in a tied skirmish wins.",
#                          actions={"DRAW":Action(ActionType.STANDARD, ActionSymbol.DRAW, 1), "FIGHT":Action(ActionType.STANDARD, ActionSymbol.FIGHT, 1)}, cost=[Cost(CostType.MEDICINE, 1)])

# class ScoutingRefugee(Card):
#     def __init__(self):
#         super().__init__(title="ScoutingRefugee", tribe_members=1, special_instruction="May cancel a Recon action. Then, draw 1 card.",
#                          actions={"DIG":Action(ActionType.MODIFIER, ActionSymbol.DIG, 1), "HUNT":Action(ActionType.MODIFIER, ActionSymbol.HUNT, 1), "FIGHT":Action(ActionType.MODIFIER, ActionSymbol.FIGHT, 1)}, cost=[Cost(CostType.FOOD, 1)])
