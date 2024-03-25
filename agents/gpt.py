from collections import defaultdict
from dataclasses import dataclass, field
from api.classes import Agent, AvailableActions, Action, Observation, Rules
import random
import openai
import api.util as util
import ast
import json
from PIL import Image
import base64
from io import BytesIO
import re


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

tokens = defaultdict(int)
def completions(*args, **kwargs):
    ret = openai_client.chat.completions.create(*args, **kwargs)

    model = kwargs["model"]
    tokens[f"{model}_input"] += ret.usage.prompt_tokens
    tokens[f"{model}_output"] += ret.usage.completion_tokens
    print("*******************", tokens)
    return ret

@dataclass
class OpenAITextAgent(Agent):
    openai_model: str
    agent_type_id: str
    system_message: str = "You are an agent playing a game. Select the action that maximizes your probability of winning."
    max_retries: int = 3
    transparent_reasoning: bool = False
    mode: int = 0  # 0 = normal, 1 = chain of thought, 2 = babble and prune

    def print(self, *args, **kwargs):
        if self.transparent_reasoning:
            print(self.agent_type_id, *args, **kwargs)

    def take_action(
        self,
        rules: Rules,
        observation: Observation,
        available_actions: AvailableActions,
        show_state: bool,
    ):
        messages = [{"role": "system", "content": self.system_message}]
        valid_actions = []
        prompt = f"You are playing a game called {rules.title}. The rules are as follows:\n{rules.summary}\n"
        if rules.additional_details != None:
            prompt += "The following are headings with additional information about the rules that you can expand by taking the action Explain(<heading key>).\n"
            details_dict = {
                f"H{i+1}": topic for i, topic in enumerate(rules.additional_details)
            }
            prompt += json.dumps(details_dict, indent=4)
            valid_actions.extend(f"Explain({h})" for h in list(details_dict.keys()))

        prompt += f"\n# Observation\nThe following describes the current state of the game:\n{observation.text}\n"
        if observation.image is not None:
            if self.openai_model == "gpt-4-1106-preview":
                self.print("Image observation recieved.")
                buffered = BytesIO()
                observation.image.save(buffered, format="JPEG")
                base64_image = base64.b64encode(buffered.getvalue())
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                )
                prompt = ""
            else:
                self.print("Image observation recieved. Using GPT4 to generate text description.")
                buffered = BytesIO()
                image.save(buffered, format="JPEG")
                base64_image = base64.b64encode(buffered.getvalue())

                imagedesc = completions(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                },
                            ],
                        }
                    ],
                ).choices[0].message.content
                prompt += imagedesc
                observation.image = None

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

        # Chain of Thought
        if self.mode == 1:
            prompt += "First, let's reason out loud about which action you should take to maximize your probability of winning."
            messages.append({"role": "user", "content": prompt})

            response = (
                completions(
                    model=self.openai_model
                    if observation.image is None
                    else "gpt-4-vision-preview",
                    messages=messages,
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
                completions(
                    model=self.openai_model
                    if observation.image is None
                    else "gpt-4-vision-preview",
                    messages=messages,
                )
                .choices[0]
                .message.content
            )
            messages.append({"role": "assistant", "content": response})
            prompt = ""

            self.print(f"GPT listed the following actions as possibilities: {response}")

        prompt += "\nTo summarize, if you choose a predefined action, you must return json with an 'action' key which contains one of the following valid actions:\n"
        prompt += str(list(available_actions.predefined))
        prompt += "\nOr if you choose an openended action, you must return json with an 'action' key which contains one of the following valid actions and an 'openended_response' key which contains your response to the prompt:\n"
        prompt += str(list(available_actions.openended))
        messages.append({"role": "user", "content": prompt})

        result = None
        for _ in range(self.max_retries):
            response = (
                completions(
                    model=self.openai_model
                    if observation.image is None
                    else "gpt-4-vision-preview",
                    response_format={"type": "json_object"},
                    messages=messages,
                )
                .choices[0]
                .message.content
            )
            messages.append({"role": "assistant", "content": response})
            self.print("GPT responded with", response)

            try:
                action = ast.literal_eval(response.strip())
                action["action"]
            except:
                self.print("GPT returned invalid JSON")
                continue

            if (
                action["action"] in available_actions.openended
                and "openended_response" not in action
            ):
                self.print(
                    "GPT chose openended action but didn't include response", action
                )
                error_message = "You chose an openended action, and so your json must have an 'openended_response' key."
                messages.append({"role": "user", "content": error_message})
                continue

            if action["action"] in valid_actions:
                self.print("GPT chose valid action", action)
                explain = re.findall(r"Explain\((H\d+)\)", action["action"])
                if len(explain):
                    self.print("GPT is asking for explanation.")
                    rule = details_dict[explain[0]]
                    desc = rules.additional_details[rule]
                    messages.append({"role": "user", "content": desc})
                    continue

                explain = re.findall(r"Explain\((\d+)\)", action["action"])
                if len(explain):
                    self.print("GPT is asking for explanation.")
                    rule = details_dict["H" + explain[0]]
                    desc = rules.additional_details[rule]
                    messages.append({"role": "user", "content": desc})
                    continue

                explain = re.findall(r"Explain\((.+)\)", action["action"])
                if len(explain):
                    self.print("GPT is asking for explanation.")
                    desc = rules.additional_details[explain[0]]
                    messages.append({"role": "user", "content": desc})
                    continue
                result = action
                break

            self.print("GPT returned invalid action", action)
            error_message = f"{action['action']} is not one of the valid actions. "
            error_message += "As a reminder, the valid actions are as follows:\n"
            error_message += f"{str(list(valid_actions))}\n"
            error_message += "Please return a json with the key 'action' with the action you choose and (optionally) the key 'openended_response' if you select openended response action."
            messages.append({"role": "user", "content": error_message})
        if result == None:
            self.print(
                f"WARNING: GPT returned an a random action after {self.max_retries} tries"
            )
            return Action(action_id=None)

        return Action(
            action_id=result["action"],
            openended_response=result.get("openended_response"),
        )


@dataclass
class GPT3(OpenAITextAgent):
    openai_model: str = "gpt-3.5-turbo-1106"
    agent_type_id: str = "gpt3"
    mode: int = 0

@dataclass
class GPT3CoT(OpenAITextAgent):
    openai_model: str = "gpt-3.5-turbo-1106"
    agent_type_id: str = "gpt3-cot"
    mode: int = 1

@dataclass
class GPT3BaP(OpenAITextAgent):
    openai_model: str = "gpt-3.5-turbo-1106"
    agent_type_id: str = "gpt3-bap"
    mode: int = 2

@dataclass
class GPT4(OpenAITextAgent):
    openai_model: str = "gpt-4-1106-preview"
    agent_type_id: str = "gpt4"
    mode: int = 0

@dataclass
class GPT4CoT(OpenAITextAgent):
    openai_model: str = "gpt-4-1106-preview"
    agent_type_id: str = "gpt4-cot"
    mode: int = 1

@dataclass
class GPT4BaP(OpenAITextAgent):
    openai_model: str = "gpt-4-1106-preview"
    agent_type_id: str = "gpt4-bap"
    mode: int = 2