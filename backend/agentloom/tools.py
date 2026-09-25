"""
tools.py

A dispatch table for Python functions the agent is allowed to call.

The idea is simple: instead of the "brain" (an LLM) directly running
code, it can only ask for a registered function by name, with a
dictionary of arguments. The ToolRegistry looks the name up, checks it
exists, and calls it. This is the same basic pattern real tool-calling
frameworks use, just without the extra layers - a name maps to a
function, and that's it.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable


class ToolNotFoundError(Exception):
    """Raised when the agent asks for a tool that was never registered."""


class ToolExecutionError(Exception):
    """Raised when a registered tool raises an exception, or is called
    with the wrong arguments."""


@dataclass
class ToolInfo:
    name: str
    description: str
    func: Callable


class ToolRegistry:
    """Holds every function the agent is allowed to call, keyed by name."""

    def __init__(self):
        self._tools: dict[str, ToolInfo] = {}

    def register(self, name: str | None = None, description: str | None = None):
        """Decorator: @registry.register() or @registry.register("add")"""

        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_description = description or (inspect.getdoc(func) or "").strip() or "No description."
            self._tools[tool_name] = ToolInfo(name=tool_name, description=tool_description, func=func)
            return func

        return decorator

    def call(self, name: str, args: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ToolNotFoundError(f"No tool registered under the name '{name}'")

        func = self._tools[name].func
        try:
            return func(**args)
        except TypeError as exc:
            raise ToolExecutionError(f"Tool '{name}' was called with bad arguments: {exc}") from exc
        except Exception as exc:
            raise ToolExecutionError(f"Tool '{name}' raised an error: {exc}") from exc

    def describe(self) -> list[dict]:
        """A plain list of {name, description} - useful for showing
        available tools to a real LLM in its system prompt, or to the
        dashboard."""
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools.keys())
