from dataclasses import dataclass, field
from api.classes import Agent, AvailableActions, Action, Observation, Rules
import random
import openai
import api.util as util
import ast
import json


action_format_instructions_no_openended = """\
Return actions in json with the following keys.
{
    "action": str,
}
"""

action_format_instructions_with_openended = """\
Return actions in json with the following keys.
{
    "action": str,
    "openended_response": Optional[str],
}
Include the openended response only if you have chosen an openended action.
"""

openai_client = openai.Client(api_key=util.load_json("credentials.json")["openai_api_key"])
@dataclass
class OpenAITextAgent(Agent):
    openai_model : str
    agent_type_id : str
    system_message : str = "You are an agent playing a game. Select the action that maximizes your probability of winning."
    max_retries : int = 3

    def take_action(self, rules: Rules, observation: Observation, available_actions: AvailableActions, show_state : bool):
        valid_actions = []
        prompt = f"You are playing a game called {rules.title}. The rules are as follows:\n{rules.summary}\n"
        if rules.additional_details != None:
            prompt += "The following are headings with additional information about the rules that you can expand by taking the action Explain(<heading key>).\n"
            details_dict = {f"H{i+1}": topic for i, topic in rules.additional_details}
            prompt += json.dumps(details_dict, indent=4)
            valid_actions.extend(f"Explain({h})" for h in list(details_dict.keys()))

        prompt += f"\n# Observation\nThe following describes the current state of the game:\n{observation.text}\n"
        assert available_actions.predefined != {} or available_actions.openended != {}
        prompt += f"\n# Actions\n"
        prompt += f"{available_actions.instructions}\n"

        if len(list(available_actions.openended.keys())) > 0:
            prompt += action_format_instructions_with_openended
            prompt += "The following are openended actions you can take\n"
            prompt += str(list(available_actions.openended.keys())) + "\n"
            valid_actions += list(available_actions.openended)
        else:
            prompt += action_format_instructions_no_openended

        if len(list(available_actions.predefined.keys())) > 0:
            prompt += "The following are predefined actions you can take:\n"
            prompt += str(list(available_actions.predefined)) + "\n"
            valid_actions += list(available_actions.predefined)
        if any([available_actions.predefined[action] != None for action in list(available_actions.predefined.keys()) + list(available_actions.openended.keys())]):
            prompt += "Return the action Explain(<action>) to receive additional info about what any of the above actions do.\n"

        prompt += "\nTo summarize, you must return json with an 'action' key which contains one of the following valid actions:\n"
        prompt += str(list(valid_actions))

        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": prompt},
        ]

        result = None
        for _ in range(self.max_retries):
            response = openai_client.chat.completions.create(
                model=self.openai_model,
                response_format={ "type": "json_object" },
                messages=messages
            ).choices[0].message.content
            messages.append({"role": "assistant", "content": response})
            action = ast.literal_eval(response)
            if action["action"] in valid_actions:
                result = action
                break
            else:
                error_message = f"{action['action']} is not one of the valid actions. "
                error_message += "As a reminder, the valid actions are as follows:\n"
                error_message += f"{str(list(valid_actions))}\n"
                error_message += "Please return a json with the key 'action' with the action you choose and (optionally) the key 'openended_response' if you select openended response action."
                messages.append({"role": "user", "content": error_message})
        if result == None:
            print(f"WARNING: GPT returned an a random action after {self.max_retries} tries")
            return Action(action_id=None)
        return Action(action_id=result["action"], openended_response=result.get("openended_response"))

@dataclass
class ChatGPTText(OpenAITextAgent):
    openai_model : str = "gpt-3.5-turbo-1106"
    agent_type_id : str = "gpt-3.5"

@dataclass
class GPT4Text(OpenAITextAgent):
    openai_model : str = "gpt-4-1106-preview"
    agent_type_id : str = "gpt-4"


@dataclass
class ChainOfThought(Agent):
    """A direct copy of the code above but with added chain of thought prompting."""
    openai_model : str = "gpt-3.5-turbo-1106"#"gpt-4-1106-preview"
    agent_type_id : str = "cot"
    system_message : str = "You are an agent playing a game. Select the action that maximizes your probability of winning."
    max_retries : int = 3

    def take_action(self, rules: Rules, observation: Observation, available_actions: AvailableActions, show_state : bool):
        valid_actions = []
        prompt = f"You are playing a game called {rules.title}. The rules are as follows:\n{rules.summary}\n"
        if rules.additional_details != None:
            prompt += "The following are headings with additional information about the rules that you can expand by taking the action Explain(<heading key>).\n"
            details_dict = {f"H{i+1}": topic for i, topic in rules.additional_details}
            prompt += json.dumps(details_dict, indent=4)
            valid_actions.extend(f"Explain({h})" for h in list(details_dict.keys()))

        prompt += f"\n# Observation\nThe following describes the current state of the game:\n{observation.text}\n"
        assert available_actions.predefined != {} or available_actions.openended != {}
        prompt += f"\n# Actions\n"
        prompt += f"{available_actions.instructions}\n"

        if len(list(available_actions.openended.keys())) > 0:
            prompt += action_format_instructions_with_openended
            prompt += "The following are openended actions you can take\n"
            prompt += str(list(available_actions.openended.keys())) + "\n"
            valid_actions += list(available_actions.openended)
        else:
            prompt += action_format_instructions_no_openended

        if len(list(available_actions.predefined.keys())) > 0:
            prompt += "The following are predefined actions you can take:\n"
            prompt += str(list(available_actions.predefined)) + "\n"
            valid_actions += list(available_actions.predefined)
        if any([available_actions.predefined[action] != None for action in list(available_actions.predefined.keys()) + list(available_actions.openended.keys())]):
            prompt += "Return the action Explain(<action>) to receive additional info about what any of the above actions do.\n"

        prompt += "First, let's reason out loud about which action you should take to maximize your probability of winning."
        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": prompt},
        ]
        response = openai_client.chat.completions.create(
            model=self.openai_model,
            messages=messages
        ).choices[0].message.content
        messages.append({"role": "assistant", "content": response})

        prompt = "Now, choose your action. To summarize, you must return json with an 'action' key which contains one of the following valid actions:\n"
        prompt += str(list(valid_actions))
        messages.append({"role": "user", "content": prompt})

        result = None
        for _ in range(self.max_retries):
            response = openai_client.chat.completions.create(
                model=self.openai_model,
                response_format={ "type": "json_object" },
                messages=messages
            ).choices[0].message.content
            messages.append({"role": "assistant", "content": response})
            action = ast.literal_eval(response)
            if action["action"] in valid_actions:
                result = action
                break
            else:
                error_message = f"{action['action']} is not one of the valid actions. "
                error_message += "As a reminder, the valid actions are as follows:\n"
                error_message += f"{str(list(valid_actions))}\n"
                error_message += "Please return a json with the key 'action' with the action you choose and (optionally) the key 'openended_response' if you select openended response action."
                messages.append({"role": "user", "content": error_message})
        if result == None:
            print(f"WARNING: GPT returned an a random action after {self.max_retries} tries")
            return Action(action_id=None)

        return Action(action_id=result["action"], openended_response=result.get("openended_response"))


@dataclass
class BabbleAndPrune(Agent):
    """Direct copy of code above but with a prompt to ask agent if they agree with the action.

    There is probably a better way to do a simple babble and prune; I think the
    agent usually only returns yes here.
    """
    openai_model : str = "gpt-3.5-turbo-1106"
    agent_type_id : str = "bap"
    system_message : str = "You are an agent playing a game. Select the action that maximizes your probability of winning."
    max_retries : int = 3

    def take_action(self, rules: Rules, observation: Observation, available_actions: AvailableActions, show_state : bool):
        valid_actions = []
        prompt = f"You are playing a game called {rules.title}. The rules are as follows:\n{rules.summary}\n"
        if rules.additional_details != None:
            prompt += "The following are headings with additional information about the rules that you can expand by taking the action Explain(<heading key>).\n"
            details_dict = {f"H{i+1}": topic for i, topic in rules.additional_details}
            prompt += json.dumps(details_dict, indent=4)
            valid_actions.extend(f"Explain({h})" for h in list(details_dict.keys()))

        prompt += f"\n# Observation\nThe following describes the current state of the game:\n{observation.text}\n"
        assert available_actions.predefined != {} or available_actions.openended != {}
        prompt += f"\n# Actions\n"
        prompt += f"{available_actions.instructions}\n"

        if len(list(available_actions.openended.keys())) > 0:
            prompt += action_format_instructions_with_openended
            prompt += "The following are openended actions you can take\n"
            prompt += str(list(available_actions.openended.keys())) + "\n"
            valid_actions += list(available_actions.openended)
        else:
            prompt += action_format_instructions_no_openended

        if len(list(available_actions.predefined.keys())) > 0:
            prompt += "The following are predefined actions you can take:\n"
            prompt += str(list(available_actions.predefined)) + "\n"
            valid_actions += list(available_actions.predefined)
        if any([available_actions.predefined[action] != None for action in list(available_actions.predefined.keys()) + list(available_actions.openended.keys())]):
            prompt += "Return the action Explain(<action>) to receive additional info about what any of the above actions do.\n"

        prompt += "\nTo summarize, you must return json with an 'action' key which contains one of the following valid actions:\n"
        prompt += str(list(valid_actions))

        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": prompt},
        ]

        result = None
        for _ in range(self.max_retries):
            while True:
                response = openai_client.chat.completions.create(
                    model=self.openai_model,
                    response_format={ "type": "json_object" },
                    messages=messages
                ).choices[0].message.content
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": "Evaluate this action. If you agree it is a good action, respond with exactly 'yes'. If you don't agree, respond with exactly 'no'"})
                critique = openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=messages
                ).choices[0].message.content
                messages.append({"role": "assistant", "content": critique})

                if critique == "yes":
                    break

            action = ast.literal_eval(response)
            if action["action"] in valid_actions:
                result = action
                break
            else:
                error_message = f"{action['action']} is not one of the valid actions. "
                error_message += "As a reminder, the valid actions are as follows:\n"
                error_message += f"{str(list(valid_actions))}\n"
                error_message += "Please return a json with the key 'action' with the action you choose and (optionally) the key 'openended_response' if you select openended response action."
                messages.append({"role": "user", "content": error_message})
        if result == None:
            print(f"WARNING: GPT returned an a random action after {self.max_retries} tries")
            return Action(action_id=None)

        return Action(action_id=result["action"], openended_response=result.get("openended_response"))