from dataclasses import dataclass, field
from api.classes import Observation, Action, Agent, AvailableActions, Game, Rules
from typing import List, Dict, Optional, Tuple
from games.arctic_scavengers.cards.game_cards import *
import random
import ast

@dataclass
class ArcticScavengers(Game):
    class Player:
        def __init__(self, agent):
            self.agent = agent
            self.cards = {"deck":[], "draw":[]}
            self.actions = {"DIG": 0, "DRAW": 0, "HUNT": 0, "HIRE": 0, "TRASH":0, "SNIPER":0, "SABOTEUR":0}
            self.food = 0

        def create_deck(self, deck):
            self.cards["deck"] = [Refugee()] * 4 + [Scavenger()] * 3 + [Brawler()] + [Spear()] + [Shovel()]
            random.shuffle(self.cards["deck"])

        def draw_hand(self):
            if len(self.cards["deck"]) > 0:
                self.cards["deck"] += self.cards["draw"]
                self.cards["draw"] = []
            random.shuffle(self.cards["deck"])
            self.cards["draw"] = self.cards["deck"][:5]
            self.cards["deck"] = self.cards["deck"][5:]

        def reset_actions(self):
            self.food = 0
            for action in self.actions:
                self.actions[action] = 0

        def calculate_fight_score(self):
            score = 0
            for card in self.cards["draw"]:
                if card.actions:
                    for action in card.actions:
                        if action == "FIGHT":
                            score += card.actions[action].value
            return score

        def calculate_people(self):
            score = 0
            for card in self.cards["draw"]:
                if card.tribe_members:
                    score += card.tribe_members
            return score
    class Deck:
        def __init__(self):
            self.contested_resources = [WolfPack()] * 1 + [Grenade()] * 1 + [SledTeam()] * 1 + [FieldCrew()] * 1 + [TribeFamily()] * 1
            random.shuffle(self.contested_resources)
            self.junkyard = [Junk()] * 7 + [MultiTool()] * 4 + [Net()] * 4 + [Spear()] * 4 + [Pickaxe()] * 4 + [Shovel()] * 4 + [Medkit()] * 6 + [Pills()] * 9
            random.shuffle(self.junkyard)
            self.mercenaries = [[Brawler()]*8, [Hunter()]*8, [Saboteur()]*8, [Scout()]*8, [GroupLeaders()]*5, [SniperTeam()]*5, [Thug()]*5, [Scavenger()]*14] # 8 mercenary piles

    rules : Rules = Rules(
        title="Arctic Scavengers",
        summary="""
        The game is played in 6 rounds, with each round consisting of a resource gathering phase and a skirmish phase.
        In the resource gathering phase, players draw cards from their deck and take actions to gather resources from the mercenary piles and the junkyard pile.
        In the skirmish phase, players compare the strength of their tribes and the winner of the skirmish gains a contested resource card.
        The game ends when all contested resource cards have been won, and the player with the largest tribe is the winner.
        """,
        # Each tribe member card has the number of people it represents shown on the card.
        # During the resource gathering phase, you can interrupt your opponent's actions by playing a sniper or saboteur card from your hand, then the card you play is discarded.
        # During the skirmish phase, you can play a sniper or saboteur card to interrupt your opponent's actions, but the card you play remains in your hand.
        # """,
        additional_details = None
    )
    id : str = "arctic_scavengers"

    def init_game(self, agent1 : Agent, agent2 : Agent):
        self.agents = [agent1(team_id = 0, agent_id = 0, **self.agent_1_kwargs), agent2(team_id = 1, agent_id = 1, **self.agent_2_kwargs)]
        self.players = [self.Player(self.agents[0]), self.Player(self.agents[1])]
        self.deck = self.Deck()
        # Initialise 10 cards for each player (4 refugee, 3 scavenger, 1 brawler, 1 spear, 1 shovel)
        for player in self.players:
            player.create_deck(self.deck)
        self.game_winner = None

    def observation_resource_gather(self, player : Player) -> Tuple[Observation, AvailableActions]:
        context = "This is your draw hand, and the information on your cards."
        for card in player.cards["draw"]:
            context += "\n" + str(card)
        context += f"\nYou have {player.food} FOOD currency."
        context += "\nThe contested resources pile has " + str(len(self.deck.contested_resources)) + " cards and the junkyard pile has " + str(len(self.deck.junkyard)) + " cards."
        context += "\nYou have already performed the following actions: "
        for a in player.actions:
            if player.actions[a] > 0:
                context += a + " "
        for pile in self.deck.mercenaries:
            if pile:
                context += "\nThe " + pile[0].title + " pile has " + str(len(pile)) + " cards."
                context += "\n" + str(pile[0])
        context += "\nThe HUNT action allows you to generate food during a single round, that can be used as currency for hiring a single mercenary card."
        context += "\nAny card you play of type MODIFIER must be combined with a STANDARD card. The MODIFIER card will add to the score of the STANDARD card."
        observation = Observation(text=context)
        s = "Choose cards to use and discard in an action, otherwise say STOP and your current hand will remain for the skirmish. Remember that each of the actions DIG, DRAW, HIRE, HUNT, TRASH can only be used once."
        # s += "\nThe DIG action allows you to draw one or more cards from the top of the junkyard pile, determined by the sum of DIG values you play. You may choose a maximum of one card to place in your reserve deck, and return any other cards to the bottom of the junkyard pile."
        # s += "\nThe DRAW action allows you to draw one or more cards from your reserve deck, adding them to your playing hand. The number is determined by the sum of the DRAW values you play."
        # s += "\nThe HIRE action allows you to hire one mercenary and add it to your reserve deck. The MEDICINE and FOOD currency you play must equal the cost of the mercenary card."
        # s += "\nThe HUNT action allows you to generate FOOD currency that is equal to the sum of the HUNT values you play. This currency can be used to hire mercenaries."
        # s += "\nThe TRASH action allows you to choose one or more cards from your playing hand to add to the junkyard pile, which is shuffled after each new card added."
        s += "\nFor the actions DIG, DRAW, HUNT or TRASH, return as an openended response a list of the action name and a list of the card titles you are using for this action."
        s += "\nFor example, [\"DIG\", [\"Brawler\", \"Shovel\"]]."
        s += "\nFor the action HIRE, return as an openended response a list of the action, a list of the MEDICINE card titles you are using for this action, and the title of the mercenary you want to hire. You must have gathered enough FOOD currency gained by HUNTing for this action."
        s += "\nFor example, [\"HIRE\", [\"Pills\"], \"Saboteur\"]."
        s += "\nFor STOP, return [\"STOP\", []]"
        available_actions = AvailableActions(
             instructions = s,
             openended = {
                    "DIG": "Draw one or more cards from the top of the junkyard pile, determined by the sum of DIG values you play. You may choose a maximum of one card to place in your reserve deck, and return any other cards to the bottom of the junkyard pile.",
                    "DRAW": "Draw one or more cards from your reserve deck, adding them to your playing hand. The number is determined by the sum of the DRAW values you play.",
                    "HIRE": "Hire one mercenary and add it to your reserve deck. The MEDICINE and FOOD currency you play must equal the cost of the mercenary card.",
                    "HUNT": "Generate FOOD currency that is equal to the sum of the HUNT values you play. This currency can be used to hire mercenaries.",
                    "TRASH": "Choose one or more cards from your playing hand to add to the junkyard pile, which is shuffled after each new card added.",
                    "STOP": "Stop gathering resources and move to the skirmish phase."
             },
             predefined = {}
        )
        return observation, available_actions

    def observation_skirmish(self, player : Player, other : int) -> Tuple[Observation, AvailableActions]:
        context = "This is the hand you have brought to the skirmish. Your opponent can see your hand."
        for card in player.cards["draw"]:
            context += "\n" + str(card)
        context += "\n This is the hand your opponent has brought to the skirmish. You can see their hand."
        for card in self.players[other].cards["draw"]:
            context += "\n" + str(card)
        observation = Observation(text=context)
        s = "Choose whether to perform a SNIPE or SABOTEUR action towards your opponent, if you have the cards in your hand. Otherwise, say STOP and your skirmish actions will end."
        s += "\nThe winner of the round is determined by the highest fight value, and if there is a tie then the biggest tribe. Otherwise the contested resource is shuffled in the junkyard pile."
        # s += "\nThe SNIPER action allows you to snipe one tribe member, forcing it to be discarded."
        # s += "\nThe SABOTEUR action allows you to disarm one tool card, forcing it to be discarded."
        s += "\nFor the actions SNIPER or SABOTEUR, return as an openended response a list of the action name and the card title of your opponent that you are performing this action on. Both list values must be strings."
        s += "\nFor the action STOP, return [\"STOP\", ""]"
        available_actions = AvailableActions(
             instructions = s,
             openended = {
                    "SNIPER": "Snipe one tribe member, forcing it to be discarded.",
                    "SABOTEUR": "Disarm one tool card, forcing it to be discarded.",
                    "STOP": "Stop taking further actions in the skirmish."
             },
             predefined = {}
        )
        return observation, available_actions

    def observation_respond_to_action(self, player : Player, action : Action) -> Tuple[Observation, AvailableActions]:
        context = "Your opponent has announced that they are taking the following action."
        context += "\n" + str(action.action_id) + " " + str(action.openended_response)
        observation = Observation(text=context)
        s = "You have the option to perform a SNIPER or SABOTEUR action then discard any cards that you play."
        s += "\nThe SNIPER action allows you to snipe one tribe member, forcing it to be discarded by the opponent."
        s += "\nThe SABOTEUR action allows you to disarm one tool card, forcing it to be discarded by the opponent."
        s += "\nIf you are unable or don't want to take these actions, take the action STOP and return [\"STOP\", ""]."
        s += "\nOtherwise, for the actions SNIPER or SABOTEUR, return as an openended response a list of the action name and the card title of your opponent that you are performing this action on. You must ensure that the list value is a string."
        s += "\nFor example, [\"Brawler\"]."
        available_actions = AvailableActions(
             instructions = s,
             openended = {
                    "SNIPER": "Snipe one tribe member, forcing it to be discarded.",
                    "SABOTEUR": "Disarm one tool card, forcing it to be discarded.",
                    "STOP": "Stop taking further actions in the skirmish."
             },
             predefined = {}
        )
        return observation, available_actions

    def observation_dig_cards(self, dig_cards : List[Card], player : Player) -> Tuple[Observation, AvailableActions]:
        context = "These are the cards you have drawn from the junkyard pile after taking the DIG action."
        for card in dig_cards:
            context += "\n" + str(card)
        observation = Observation(text=context)
        s = "Choose a card to place in your reserve deck, and return the rest to the bottom of the junkyard pile."
        available_actions = AvailableActions(
             instructions = s,
             predefined = {
                  f"{card.title}" : None for card in dig_cards
             },
             openended = {}
        )
        return observation, available_actions

    def update_resource_gather(self, action : Action,  available_actions : AvailableActions, player : Player, action2 : Action, player2 : Player):
        if self.show_state:
            print(action.action_id)
            print(action.openended_response)
            if action2:
                print(action2.action_id)
                print(repr(action2.openended_response))
            print("Player 1 cards: " + str(player.cards))
            print("Player 2 cards: " + str(player2.cards))
        #### Check if a snipe/sabotage is being performed ####
        id2 = action2.action_id
        action2_items = []
        if id2 in ["SNIPER", "SABOTEUR"]: # This is an optional move, so if they play an invalid move then this move is skipped
            action2_items = [action2.openended_response]
            valid = True
            player2_cards = [c.title for c in player2.cards["draw"]]
            if id2 == "SNIPER" and "Sniper" not in player2_cards:
                valid = False
            if id2 == "SABOTEUR" and "Saboteur" not in player2_cards:
                valid = False
            player_cards = [c.title for c in player.cards["draw"]]
            if action2_items[0] not in player_cards:
                valid = False
            for card in player.cards["draw"]:
                if card.title == action2_items[0]:
                    if id2 == "SNIPER" and card.tribe_members == None:
                        valid = False
                    if id2 == "SABOTEUR" and card.tribe_members != None:
                        valid = False
                    break
            if valid:
                for card in player.cards["draw"]:
                    if card.title == action2_items[1]:
                        player.cards["draw"].remove(card)
                        player.cards["deck"].append(card)
                        for c in player2.cards["draw"]:
                            if id2 == "SNIPER" and card.title == "Sniper":
                                player2.cards["draw"].remove(c)
                                player2.cards["deck"].append(c)
                                break
                            if id2 == "SABOTEUR" and card.title == "Saboteur":
                                player2.cards["draw"].remove(c)
                                player2.cards["deck"].append(c)
                                break
                        break
                return # Player 1's action can no longer be performed

        #### Perform Player 1's action ####
        # If selected action is not valid, choose a random action out of DIG, DRAW, HUNT, TRASH and a single card from the player's hand.
        id = action.action_id
        action_items = []
        if id not in available_actions.openended:
            action_items = [[random.choice(player.cards["draw"])]]
            types = [a for a in action_items[0][0].actions.keys()]
            action_items.insert(0, random.choice(types + ["TRASH"])) # No random hiring or stopping
        else:
            try:
                action_items = list(ast.literal_eval(str(action.openended_response)))
                if len(action_items) == 0:
                    raise ValueError
            except:
                choice = random.choice(player.cards["draw"])
                action_items = [[choice]]
                types = [a for a in choice.actions.keys()] if choice.actions else []
                action_items.insert(0, random.choice(types + ["TRASH"])) # No random hiring or stopping


        valid = True
        player_cards = [c.title for c in player.cards["draw"]]
        if id in ["DIG", "DRAW", "HUNT"]:
            standard = 0
            modifier = 0
            for card in action_items[-1]:
                if card not in player_cards:
                    valid = False
                    if self.show_state: print("Card not in player_cards")
                    break
                for c in player.cards["draw"]:
                    if c.title == card:
                        if id not in c.actions:
                            valid = False
                            ("id not in c.actions")
                            break
                        for a in c.actions:
                            if c.actions[a].type == ActionType.MODIFIER:
                                modifier += 1
                            else:
                                standard += 1
            if modifier > 0 and standard == 0:
                valid = False
                if self.show_state: print("modifier > 0 and standard == 0")
            if self.show_state: print(modifier, standard)
        if id == "HIRE":
            food_cost = 0
            med_cost = 0
            med_currency = 0
            if len(action_items) < 3:
                valid = False
            else:
                for c in player2.cards["draw"]:
                    if c.title == action_items[2]:
                        for d in c.cost:
                            if d.type == CostType.FOOD:
                                food_cost += d.value
                            else:
                                med_cost += d.value
                for card_name in action_items[1]:
                    if card_name not in player_cards:
                        valid = False
                        break
                    for card in player.cards["draw"]:
                        if card.title == card_name:
                            if card.actions != None and "MEDICINE" in card.actions:
                                med_currency += card.actions["MEDICINE"].value
                if food_cost > player.food or med_cost > med_currency:
                    valid = False
                mercenary_names = []
                for m in self.deck.mercenaries:
                    if m:
                        mercenary_names.append(m[0].title)
                if action_items[2] not in mercenary_names:
                    valid = False
        if id not in player.actions or player.actions[id] > 0: # If action has already been taken
            valid = False
            if self.show_state: print("Action already taken")
        if self.show_state: print(valid)
        if not valid:
            i = 0
            n = len(player.cards["draw"])
            while i < n and player.cards["draw"][i].tribe_members == None:
                i += 1
            if i == n:
                action_items = ["TRASH", [player.cards["draw"][0]]]
            else:
                action_items = [[player.cards["draw"][i]]]
                types = [a for a in action_items[0][0].actions.keys()]
                for a in player.actions:
                    if a in types and player.actions[a] > 0:
                        types.remove(a)
                action_items.insert(0, random.choice(types + ["TRASH"]))
            id = action_items[0]
            if self.show_state: print(action_items)
        else: # Transform strings into Card objects
            for i in range(len(action_items[1])):
                for card in player.cards["draw"]:
                    if card.title == action_items[1][i]:
                        action_items[1][i] = card
                        break
            if id == "HIRE":
                for mercenary in self.deck.mercenaries:
                    if mercenary and mercenary[0].title == action_items[2]:
                        action_items[-1] = mercenary[0]
                        break

        if id == "DRAW":
            draw_value = 0
            for card in action_items[-1]:
                for c in player.cards["draw"]:
                    if c.title == card.title:
                        player.cards["draw"].remove(c)
                        player.cards["deck"].append(c)
                        draw_value += card.actions["DRAW"].value
                        break
            player.cards["draw"] += player.cards["deck"][:draw_value]
            player.cards["deck"] = player.cards["deck"][draw_value:]
            player.actions["DRAW"] += 1

        if id == "DIG":
            dig_value = 0
            for card in action_items[-1]:
                for c in player.cards["draw"]:
                    if c.title == card.title:
                        player.cards["draw"].remove(c)
                        player.cards["deck"].append(c)
                        dig_value += card.actions["DIG"].value
                        break
            if dig_value > 0:
                dig_cards = self.deck.junkyard[:dig_value]
                observation_dig, available_actions_dig = self.observation_dig_cards(dig_cards, player)
                dig_action = player.agent.take_action(self.rules, observation_dig, available_actions_dig, show_state=self.show_state)
                dig_choice = dig_action.action_id
                if dig_choice not in available_actions_dig.predefined:
                    dig_choice = random.choice(list(available_actions_dig.predefined.keys()))
                dig_card = None
                for card in dig_cards:
                    if card.title == dig_choice:
                        player.cards["deck"].append(card)
                        dig_card = card
                        break
                self.deck.junkyard = self.deck.junkyard[dig_value:]
                dig_cards.remove(dig_card)
                self.deck.junkyard += dig_cards
            player.actions["DIG"] += 1

        if id == "HIRE":
            mercenary = action_items[2]
            food_cost = 0
            for c in mercenary.cost:
                if c.type == CostType.FOOD:
                    food_cost += c.value
            player.food -= food_cost
            for card in action_items[1]:
                for c in player.cards["draw"]:
                    if c.title == card.title:
                        player.cards["draw"].remove(c)
                        player.cards["deck"].append(c)
                        break
            for pile in self.deck.mercenaries:
                if pile and pile[0].title == mercenary.title:
                    pile.pop(0)
            player.cards["deck"].append(mercenary)
            player.actions["HIRE"] += 1

        if id == "HUNT":
            food_value = 0
            for card in action_items[-1]:
                for c in player.cards["draw"]:
                    if c.title == card.title:
                        player.cards["draw"].remove(c)
                        player.cards["deck"].append(c)
                        food_value += card.actions["HUNT"].value
                        break
            player.food += food_value
            player.actions["HUNT"] += 1

        if id == "TRASH":
            for card in action_items[-1]:
                for c in player.cards["draw"]:
                    if c.title == card.title:
                        player.cards["draw"].remove(c)
                        self.deck.junkyard.insert(random.choice(range(len(self.deck.junkyard))), c)
            player.actions["TRASH"] += 1

    def update_skirmish(self, action : Action, available_actions : AvailableActions, player : Player, player2 : Player):
        # If you snipe/sabotage during the skirmish phase, the sniper/saboteur card remains in your hand.
        id = action.action_id
        action_items = []
        if id in available_actions.openended: # This is an optional move, so if they play an invalid move then this move is skipped
            action_items = [action.openended_response]
            valid = True
            player_cards = [c.title for c in player.cards["draw"]]
            if id == "SNIPER" and "Sniper" not in player_cards:
                valid = False
            if id == "SABOTEUR" and "Saboteur" not in player_cards:
                valid = False
            player2_cards = [c.title for c in player2.cards["draw"]]
            if action_items[-1] not in player2_cards:
                valid = False
            for card in player2.cards["draw"]:
                if card.title == action_items[-1]:
                    if id == "SNIPER" and card.tribe_members == None:
                        valid = False
                    if id == "SABOTEUR" and card.tribe_members != None:
                        valid = False
                    break
            if valid:
                if id == "SNIPER":
                    for card in player2.cards["draw"]:
                        if card.title == action_items[-1]:
                            player2.cards["draw"].remove(card)
                            player2.cards["deck"].append(card)
                            break
                if id == "SABOTEUR":
                    for card in player2.cards["draw"]:
                        if card.title == action_items[-1]:
                            player2.cards["draw"].remove(card)
                            player2.cards["deck"].append(card)
                            break

    def play_resource_gather(self, player : Player, other : int):
        observation, available_actions = self.observation_resource_gather(player)
        action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
        can_have_another_turn = False
        for a in player.actions:
            if player.actions[a] == 0:
                can_have_another_turn = True
                break
        while can_have_another_turn and action.action_id != "STOP" and len(player.cards["draw"]) > 0:
            observation2, available_actions2 = self.observation_respond_to_action(self.players[other], action)
            action2 = self.players[other].agent.take_action(self.rules, observation2, available_actions2, show_state=self.show_state)
            self.update_resource_gather(action, available_actions, player, action2, self.players[other])
            observation, available_actions = self.observation_resource_gather(player)
            action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
            can_have_another_turn = False
            for a in player.actions:
                if player.actions[a] == 0:
                    can_have_another_turn = True
                    break

    def play_skirmish(self, player : Player, other : int):
        observation, available_actions = self.observation_skirmish(player, other)
        action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)
        while action.action_id != "STOP":
            self.update_skirmish(action, available_actions, player, self.players[other])
            observation, available_actions = self.observation_skirmish(player, other)
            action = player.agent.take_action(self.rules, observation, available_actions, show_state=self.show_state)

    def play(self) -> Tuple[float, float]:
        count = 0
        while self.deck.contested_resources:
            if self.show_state:
                print("Size of contested resources deck: " + str(len(self.deck.contested_resources)))
            initiator = count % 2
            #### DRAWING PHASE ####
            for player in self.players:
                player.reset_actions()
                player.draw_hand()

            #### RESOURCE GATHERING PHASE ####
            player = self.players[initiator]
            self.play_resource_gather(player, 1-initiator)
            player = self.players[1 - initiator]
            self.play_resource_gather(player, initiator)

            #### SKIRMISH PHASE ####
            player = self.players[initiator]
            self.play_skirmish(player, 1-initiator)
            player = self.players[1 - initiator]
            self.play_skirmish(player, initiator)
            fight_scores = [self.players[0].calculate_fight_score(), self.players[1].calculate_fight_score()]
            if fight_scores[0] > fight_scores[1]:
                self.players[0].cards["deck"].append(self.deck.contested_resources.pop(0))
            elif fight_scores[0] < fight_scores[1]:
                self.players[1].cards["deck"].append(self.deck.contested_resources.pop(0))
            else:
                people_scores = [self.players[0].calculate_people(), self.players[1].calculate_people()]
                if people_scores[0] > people_scores[1]:
                    self.players[0].cards["deck"].append(self.deck.contested_resources.pop(0))
                elif people_scores[0] < people_scores[1]:
                    self.players[1].cards["deck"].append(self.deck.contested_resources.pop(0))
                else:
                    self.deck.junkyard.append(self.deck.contested_resources.pop(0))

            count += 1
        return (1, 0) if self.players[0].calculate_people() > self.players[1].calculate_people() else (0, 1)