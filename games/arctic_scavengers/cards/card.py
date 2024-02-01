from enum import Enum

class ActionType(Enum):
    STANDARD = 1
    MODIFIER = 2

    def __str__(self):
        return self.name
    
class ActionSymbol(Enum):
    SEARCH = 1
    DRAW = 2
    COMBAT = 3
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
        self.validate_actions()

        self.supply_pile = supply_pile 
        self.cost = cost

        if supply_pile is not None and cost is not None:
            raise ValueError("Card can have either 'supply_pile' or 'cost', not both.")
        
    def validate_actions(self):
        standard_actions = 0
        action_modifiers = 0
        disabled_actions = 0

        for action in self._actions:
            if action.type == ActionType.STANDARD:
                standard_actions += 1
            elif action.type == ActionType.MODIFIER:
                action_modifiers += 1
            elif action.type == ActionType.DISABLED:
                disabled_actions += 1

        if standard_actions > 2 or action_modifiers > 1 or disabled_actions > 1:
            raise ValueError("Invalid action configuration.")

        if not self._actions:
            raise ValueError("At least one action is required.")
