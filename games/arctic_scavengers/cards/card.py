from enum import Enum

class ActionType(Enum):
    STANDARD = 1
    MODIFIER = 2

    def __str__(self):
        return self.name
    
class ActionSymbol(Enum):
    DIG = 1
    DRAW = 2
    FIGHT = 3
    HUNT = 4
    MEDICINE = 5
    BUILD_TIME = 6
    FOOD = 7
    TRIBE_MEMBERS = 8
    TOOL = 9

class Action:
    def __init__(self, type:Enum, symbol:Enum, value:int = 0):
        self.type = type
        self.symbol = symbol
        self.value = value
        
class CostType(Enum):
    FOOD = 1
    MEDICINE = 2

    def __str__(self):
        return self.name

class Cost:
    def __init__(self, type:Enum, value:int = 1):
        self.value = value
        self.type = type 

class SupplyPileType(Enum):
    JUNKYARD = 1
    CONTESTED_RESOURCES = 2

    def __str__(self):
        return self.name

class Card:
    def __init__(self, title: str, tribe_members: int = None, special_instruction: str = None, 
                 actions: list = None, supply_pile: Enum = None, cost: list = None):
        self.title = title
        self.special_instruction = special_instruction
        self.tribe_members = tribe_members

        self.actions = actions

        self.supply_pile = supply_pile 
        self.cost = cost
        
    def __str__(self):
        s = ""
        s += f"{self.title}\n"
        if self.tribe_members:
            s += f"Tribe Members: {self.tribe_members}\n"
        if self.special_instruction:
            s += f"Special Instruction: {self.special_instruction}\n"
        if self.actions:
            s += "Actions:\n"
            for action in self.actions:
                s += f"{self.actions[action].symbol}, {self.actions[action].type}: {self.actions[action].value}\n"
        if self.supply_pile:
            s += f"Supply Pile: {self.supply_pile}\n"
        if self.cost:
            s += "Cost:\n"
            for cost in self.cost:
                s += f"{cost.type}: {cost.value}\n"
        return s

