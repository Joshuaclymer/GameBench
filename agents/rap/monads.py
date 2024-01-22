from .chat import *
import re

def lookup_monad(completions: CompletionsFunction, rules: Rules) -> CompletionsFunction:
    """Repeatedly asks for a completion until the response is not asking
    for a rules description."""
    rules_lookup_re = re.compile(r"rule\((\w+)\)")

    def new_completions(context) -> str:
        def request(ctx):
            ret = completions(ctx)

            if re.match(rules_lookup_re, ret):
                rule = re.findall(rules_lookup_re, ret)[0]
                if rule in rules.additional_details:
                    context.append({"role": "assistant", "content": ret})
                    context.append(
                        {"role": "user", "content": rules.additional_details[rule]}
                    )

                    return request(ctx)

            return ret

        return request(context)

    return new_completions


def cot_monad(completions: CompletionsFunction) -> CompletionsFunction:
    """Asks for CoT."""
    pass