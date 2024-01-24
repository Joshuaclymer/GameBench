from api.classes import Rules
import api.util as util
import openai
import random
from .definitions import *
import math

from PIL import Image
import base64
from io import BytesIO

openai_client = openai.Client(
    api_key=util.load_json("credentials.json")["openai_api_key"]
)


def context_builder_factory(rules: Rules) -> ContextBuilder:
    """Makes a context builder with substitutions for game rules."""
    context_templates = util.load_json("agents/rap/context_templates.json")

    def context_builder(template: str, **kwargs: str) -> ContextType:
        messages = context_templates["prefix"] + context_templates[template]

        if rules.additional_details:
            topics = context_templates["additional_topics"]
            topics = topics.format(
                topics=", ".join(list(rules.additional_details))
                if rules.additional_details
                else "none"
            )
        else:
            topics = ""

        return [
            {
                "role": ("user" if i & 1 == 0 else "assistant"),
                "content": message.format(
                    title=rules.title,
                    summary=rules.summary,
                    topics=topics,
                    **kwargs,
                ),
            }
            for i, message in enumerate(messages)
        ]

    return context_builder


def openai_api() -> tuple[CompletionsFunction, ProbabilitiesFunction]:
    """Returns a CompletionsFunction and a ProbabilitiesFunction that
    interacts with GPT3.5."""

    def completions(context: ContextType) -> str:
        return (
            openai_client.chat.completions.create(
                model="gpt-3.5-turbo-1106", messages=context
            )
            .choices[0]
            .message.content
        )

    def probabilities(
        context: ContextType, tokens: list[str] = ["yes", "no"]
    ) -> dict[str, float]:
        n = min(len(tokens), 5)  # OpenAI doesn't allow more than 5

        top_logprobs = (
            openai_client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=context,
                logprobs=True,
                top_logprobs=n,
                max_tokens=1,
            )
            .choices[0]
            .logprobs.content[0]
            .top_logprobs
        )

        def unnorm_prob(token: str):
            """Return the unnormalized probability of a token."""
            return math.exp(
                next(
                    (
                        tlp.logprob
                        for tlp in top_logprobs
                        if tlp.token.lower() == str(token).lower()
                    ),
                    -100,
                )
            )

        p_total = sum(math.exp(tlp.logprob) for tlp in top_logprobs)
        return {token: unnorm_prob(token) / p_total for token in tokens}

    return completions, probabilities


def random_api() -> tuple[CompletionsFunction, ProbabilitiesFunction]:
    """Returns completions and probabilities that return random responses.
    Useful for debugging."""

    def randstr() -> str:
        """There is a probability that this returns the same string in different
        calls which could make debugging confusing."""
        return "".join(
            random.choices("abcdefghijklmnopqrstuvwxyz", k=random.randint(5, 10))
        )

    def completions(context: ContextType) -> str:
        return f"<state>{randstr()}</state><actions>0 {randstr()}\n1 {randstr()}\n2 {randstr()}</actions>"

    def probabilities(
        context: ContextType, tokens: list[str, str] = ["yes", "no"]
    ) -> dict[str, float]:
        return {token: random.random() for token in tokens}

    return completions, probabilities


def human_api() -> tuple[CompletionsFunction, ProbabilitiesFunction]:
    """Completions that uses input() or random if nothing is supplied,
    probabilities that is random."""
    r_completions, probabilities = random_api()

    def completions(context: ContextType) -> str:
        c = input("\n".join([m["content"] for m in context]) + "\n>>> ")

        if not c:
            c = r_completions(context)
            print(c)
            return c

        return c

    return completions, probabilities


def image_description(image: Image, rules: Rules) -> str:
    """Gets GPT4 description of image. Doesn't need to fit with rest of code
    so it's kinda a standalone function."""
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    base64_image = base64.b64encode(buffered.getvalue())

    c = openai_client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You are playing a game called {rules.title}. The rules are as follows: {rules.summary}.\nThis image is your observation of the game. Describe what's going on in the image.",
                    },
                    {
                        "type": "image",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )

    return c.choices[0].message.content
