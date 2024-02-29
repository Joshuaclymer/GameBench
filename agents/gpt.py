from dataclasses import dataclass, field
from typing import Any, Dict, List
from api.classes import Agent, AvailableActions, Action, Observation, Rules
import openai
import api.util as util
import ast
import json
from PIL import Image


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

openai_client = openai.Client(
    api_key=util.load_json("credentials.json")["openai_api_key"]
)


@dataclass
class OpenAITextAgent(Agent):
    openai_model : str
    agent_type_id : str
    system_message : str = "You are an agent playing a game. Select the action that maximizes your probability of winning."
    max_retries : int = 3
    transparent_reasoning : bool = False
    mode: int = 0  # 0 = normal, 1 = chain of thought, 2 = babble and prune
    
    def print(self, *args, **kwargs):
        if self.transparent_reasoning:
            print(self.agent_type_id, *args, **kwargs)
            
    def get_user_message_content(self, text_prompt: str, image: Image) -> List[Dict[str, Any]]:
        return [
                {
                    "type": "text",
                    "text": text_prompt
                }
            ]

    def get_request_params(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "model": self.openai_model,
            "messages": messages,
            "response_format": { "type": "json_object" }
        }
    
    def take_action(self, rules: Rules, observation: Observation, available_actions: AvailableActions, show_state : bool) -> Action:
        valid_actions = []
        prompt = f"You are playing a game called {rules.title}. The rules are as follows:\n{rules.summary}\n"
        if rules.additional_details != None:
            prompt += "The following are headings with additional information about the rules that you can expand by taking the action Explain(<heading key>).\n"
            details_dict = {f"H{i+1}": topic + " - " + description for i, (topic, description) in enumerate(rules.additional_details.items())}
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

        if any(
            [
                available_actions.predefined.get(action) != None
                or available_actions.openended.get(action)
                for action in list(available_actions.predefined.keys())
                + list(available_actions.openended.keys())
            ]
        ):
            prompt += "Return the action Explain(<action>) to receive additional info about what any of the above actions do.\n"

        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": self.get_user_message_content(prompt, observation.image)},
        ]

        # Chain of Thought
        if self.mode == 1:
            prompt += "First, let's reason out loud about which action you should take to maximize your probability of winning."
            messages.append({"role": "user", "content": prompt})

            response = (
                openai_client.chat.completions.create(
                    model=self.openai_model, messages=messages
                )
                .choices[0]
                .message.content
            )
            messages.append({"role": "assistant", "content": response})
            prompt = ""

            self.print("GPT reasoned out loud with: " + response)

        # Babble and Prune
        elif self.mode == 2:
            prompt += "\nList your top three choices of actions. Each action should be different. Below are valid actions:"
            prompt += str(list(valid_actions))

            messages.append({"role": "user", "content": prompt})
            response = (
                openai_client.chat.completions.create(
                    model=self.openai_model, messages=messages
                )
                .choices[0]
                .message.content
            )
            messages.append({"role": "assistant", "content": response})
            prompt = ""
            
            self.print(
                f"GPT listed the following actions as possibilities: {response}"
            )

        prompt += "\nTo summarize, if you choose a predefined action, you must return json with an 'action' key which contains one of the following valid actions:\n"
        prompt += str(list(available_actions.predefined))
        prompt += "\nOr if you choose an openended action, you must return json with an 'action' key which contains one of the following valid actions and an 'openeded_response' key which contains your reponse to the prompt:\n"
        prompt += str(list(available_actions.openended))
        #prompt += "\nMake sure to return ONLY a JSON. It should contain nothing outside the curly braces of the JSON."
        messages.append({"role": "user", "content": prompt})
            
        
        #print(prompt)
        result = None
        
        for _ in range(self.max_retries):
            response = openai_client.chat.completions.create(**self.get_request_params(messages)).choices[0].message.content
            messages.append({"role": "assistant", "content": response})
            self.print("GPT responded with", response)

            try:
                action = ast.literal_eval(util.extract_json(response))
            except:
                self.print("GPT returned invalid JSON")
                continue

            if action["action"] in available_actions.openended and "openended_response" not in action:
                self.print("GPT chose openended action but didn't include response", action)
                error_message = "You chose an openended action, and so your json must have an 'openended_response' key."
                messages.append({"role": "user", "content": error_message})
                continue

            
            if action["action"] in valid_actions:
                self.print("GPT chose valid action", action)
                result = action
                break
            
            self.print("GPT returned invalid action", action)
            error_message = f"{action['action']} is not one of the valid actions. "
            error_message += "As a reminder, the valid actions are as follows:\n"
            error_message += f"{str(list(valid_actions))}\n"
            error_message += "Please return a json with the key 'action' with the action you choose and (optionally) the key 'openended_response' if you select openended response action."
            messages.append({"role": "user", "content": error_message})

        if result == None:
            self.print(f"WARNING: GPT returned an a random action after {self.max_retries} tries")
            return Action(action_id=None)
        return Action(action_id=result["action"], openended_response=result.get("openended_response"))

@dataclass
class ChatGPTText(OpenAITextAgent):
    openai_model: str = "gpt-3.5-turbo-1106"
    agent_type_id: str = "gpt-3.5"


@dataclass
class GPT4Text(OpenAITextAgent):
    openai_model: str = "gpt-4-1106-preview"
    agent_type_id: str = "gpt-4"


@dataclass
class ChainOfThought(OpenAITextAgent):
    openai_model: str = "gpt-4-1106-preview"
    agent_type_id: str = "cot"
    mode: int = 1

@dataclass
class BabbleAndPrune(OpenAITextAgent):
    openai_model: str = "gpt-4-1106-preview"
    agent_type_id: str = "b&p"
    mode: int = 2

@dataclass
class GPT4Vision(OpenAITextAgent):
    openai_model : str = "gpt-4-vision-preview"
    agent_type_id : str = "gpt-4-vision"
    is_vision_agent : bool = True
    
    def get_user_message_content(self, text_prompt: str, image: Image) -> List[Dict[str, str]]:
        content = super().get_user_message_content(text_prompt, image)
        if image is not None:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{util.base64_encode_image(image)}",
                    "detail": "low"
                }
            })
        return content
    
    def get_request_params(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "model": self.openai_model,
            "messages": messages,
            # As vision models have a low(but undocumented?) default value for below parameter
            # https://community.openai.com/t/documented-max-token-default-is-incorrect-for-gpt-4-vision-preview/507329
            "max_tokens": 600,
        }