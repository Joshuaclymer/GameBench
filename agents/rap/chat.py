from api.classes import Rules
import api.util as util
import openai
import random
from .definitions import *

def context_builder_factory(rules: Rules) -> ContextBuilder:
    """Makes a context builder with substitutions for game rules."""
    context_templates = util.load_json("agents/rap/context_templates.json")

    def context_builder(template: str, **kwargs: str) -> ContextType:
        messages = context_templates["prefix"] + context_templates[template]

        if rules.additional_details:
            topics = context_templates["additional_topics"]
            topics = topics.format(topics=", ".join(list(rules.additional_details)) if rules.additional_details else "none")
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

    openai_client = openai.Client(
        api_key=util.load_json("credentials.json")["openai_api_key"]
    )

    def completions(context: ContextType) -> str:
        return (
            openai_client.chat.completions.create(
                model="gpt-3.5-turbo-1106", messages=context
            )
            .choices[0]
            .message.content
        )

    def probabilities(
        context: ContextType, tokens: list[str] = ["yes", "no"], n: int = 2
    ) -> dict[str, float]:
        context = context_builder(template, **kwargs)
        n = min(n, 5) # OpenAI doesn't allow more than 5

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
                        if tlp.token.lower() == token.lower()
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
        return f"<state>{randstr()}</state><actions>{randstr()}\n{randstr()}\n{randstr()}</actions>"

    def probabilities(
        context: ContextType, tokens: list[str, str] = ["yes", "no"], n: int = 0
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