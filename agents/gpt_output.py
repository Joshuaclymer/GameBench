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
            details_dict = {f"H{i+1}": topic + " - " + description for i, (topic, description) in enumerate(rules.additional_details)}
            prompt += json.dumps(details_dict, indent=4)
        
        prompt += f"\n# Observation\nThe following describes the current state of the game:\n{observation.text}\n"
        assert available_actions.predefined != {} or available_actions.openended != {}
        prompt += f"\n# Actions\n"
        prompt += f"{available_actions.instructions}\n"

        print(f"\n# Observation\nThe following describes the current state of the game:\n{observation.text}\n")
        
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
        action_id = result["action"]
        if action_id in available_actions.predefined:
            print(f"Selected predefined action {available_actions.predefined[action_id]}")
            return available_actions.predefined[action_id]
        elif action_id in available_actions.openended:
            print(f"Selected openended action {result.get('openended_response')}")
            return Action(action_id=available_actions.openended[action_id].action_id, openended_response=result.get("openended_response"))
        else:
            raise ValueError(f"Invalid action {action_id}")

@dataclass
class ChatGPTText(OpenAITextAgent):
    openai_model : str = "gpt-3.5-turbo-1106"
    agent_type_id : str = "gpt-3.5"

@dataclass
class GPT4Text(OpenAITextAgent):
    openai_model : str = "gpt-4-1106-preview"
    agent_type_id : str = "gpt-4"