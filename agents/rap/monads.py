from .chat import *
import re


def lookup_monad(completions: CompletionsFunction, rules: Rules) -> CompletionsFunction:
    """Repeatedly asks for a completion until the response is not asking
    for a rules description."""
    rules_lookup_re = re.compile(r"rule\((\w+)\)")

    def new_completions(context: ContextType) -> str:
        def request(ctx: ContextType):
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


def log_monad(
    fn: CompletionsFunction | ProbabilitiesFunction,
) -> CompletionsFunction | ProbabilitiesFunction:
    """Prints context and response."""

    def new_fn(context, *args, **kwargs):
        for message in context:
            content = message["content"].replace("\n", "\n\t\t")
            print(f"\t{message['role']}: {content}")

        ret = fn(context, *args, **kwargs)
        print("\t>>> " + str(ret).replace("\n", "\n\t\t"))
        print("\n\n")
        return ret

    return new_fn
