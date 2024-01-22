from typing import NewType, Callable
from dataclasses import dataclass

DEPTH_LIMIT = 2

"""A context, based on OpenAI API"""
ContextType = NewType("Context", list[dict[str, str]])

"""Returns the next message in a context."""
CompletionsFunction = NewType("CompletionsFunction", Callable[ContextType, str])

"""Determines the probability of tokens appearing next after a context."""
ProbabilitiesFunction = NewType(
    "ProbabilitiesFunction",
    Callable[[ContextType, list[str], int], dict[str, float]],
)

"""A function that builds a context from a context template and substituions."""
ContextBuilder = NewType("ContextBuilder", Callable[[str, str], ContextType])

@dataclass(frozen=True)
class GameState:
    """Immutable wrapper for observations, essentially."""

    observation: str
    depth: int = 0
    actions: tuple[str] = None