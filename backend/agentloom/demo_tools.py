"""
demo_tools.py

A handful of small, safe Python functions for the agent to call, so
this project is demonstrable without needing to plug in any real
external service. Register your own functions the same way for real
use - see tools.py and the README.
"""

from __future__ import annotations

import datetime

from .tools import ToolRegistry

registry = ToolRegistry()


@registry.register("add")
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@registry.register("multiply")
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b


@registry.register("get_time")
def get_time() -> str:
    """Return the current UTC time as a string."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@registry.register("word_count")
def word_count(text: str) -> int:
    """Count how many words are in a piece of text."""
    return len(text.split())
