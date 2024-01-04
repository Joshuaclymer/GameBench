import math
import random
from dataclasses import dataclass, field
from typing import Any, ClassVar
from functools import cached_property
from api.classes import Agent, AvailableActions, Rules, Observation, Action

allstr = set()
def randstr():
    global allstr
    while True:
        ret = "".join(random.choices("abcdefghjijklmnopqrstuvwxyz", k=random.randint(1, 5)))
        if ret in allstr:
            continue

        allstr.add(ret)
        return ret

def viz(root):
    from treelib import Node, Tree
    def rep(n):
        def rep(self):
            return
    tree = Tree()
    tree.create_node("root", root.state)

    def walk(node):
        for child in node.children:
            tree.create_node(f"{child.state}|visits={child.visits}", child.state, parent=node.state)
            if child.score == child.uct:
            #if child.visits > 1:
                walk(child)

    walk(root)
    return tree.show(stdout=False)

def gpt(message, openai_model="gpt3"):
    """return openai_client.chat.completions.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": "You are trying to win a game."},
            {"role": "user", "content": message}
        ]
    ).choices[0].message.content"""
    #return input(message)
    #print()
    ret = randstr()
    print(message, ret)
    return ret

@dataclass
class Node:
    state: str
    parent: "Node" = None
    visits: int = 1
    value: int = 0

    rules: ClassVar[Rules] = None
    available_actions: ClassVar[AvailableActions] = None

    @cached_property
    def children(self) -> list["Node"]:
        """Prompt GPT for actions if at non-root node. Then, prompt GPT to
        guess state."""
        prompt = """You are playing a game called {title}.
        The rules are as follows: {summary}.
        Your current observation of the game state is
        {observation}
        Your available actions are as follows:
        """.format(
            title=Node.rules.title,
            summary=Node.rules.summary,
            observation=self.state
        )
        if self.parent is None:
            actions_string = "\n".join([f"{action}: {description}" for action, description in Node.available_actions.predefined.items()])
            actions = Node.available_actions.predefined.keys()
        else:
            actions_string = gpt(prompt)
            actions = [r.split(":")[0] for r in actions.split("\n")]

        states = []
        for action in actions:
            prompt = prompt + actions_string + """
            Write the action you choose below.
            {action}
            The new state of the game is as follows:
            """.format(action=action)
            state = Node(gpt(prompt), parent=self)
            states.append(state)

        return states

    @cached_property
    def is_terminal(self) -> bool:
        return random.randint(1, 10) in [1, 2, 3]

    @cached_property
    def reward(self) -> float:
        return random.randint(1, 10)

    @cached_property
    def uct(self) -> float:
        return self.value + math.sqrt(math.log(self.parent.visits) / self.visits)

    @property
    def score(self) -> float:
        return self.uct if self.parent.visits > 1 else self.reward

    def mcts(self, n=5) -> str:
        for _ in range(n):
            node = self
            while not node.is_terminal:
                node = max(node.children, key=lambda n: n.score)

            while node:
                node.visits += 1
                node.value += self.reward
                node = node.parent

@dataclass
class ReasoningViaPlanning(Agent):
    agent_type_id: str = "rap"
    rules: Rules = None,
    observation: Observation = None,
    available_actions: AvailableActions = None

    def take_action(
        self,
        rules: Rules,
        observation: Observation,
        available_actions: AvailableActions,
        show_state: bool,
    ) -> Action:
        Node.rules = rules
        Node.available_actions = available_actions
        Node(observation.text).mcts()
