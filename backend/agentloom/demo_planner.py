"""
demo_planner.py

AgentLoom's loop expects a "brain" function: something that looks at
the task and what has happened so far, and returns a JSON decision
(call this tool with these arguments, or here is the final answer).
Normally that brain is a real LLM API call.

To keep this project runnable by anyone with zero setup (no API key
required), this file provides a small stand-in planner. It only
recognizes a few simple patterns (basic arithmetic, asking for the
time, counting words in a quoted phrase) using plain regular
expressions - it is not trying to be smart, just consistent and
demonstrable.

Swapping this for a real LLM call is a one-line change in Agent's
constructor - see agent.py and the README.
"""

from __future__ import annotations

import json
import re

_ADD_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:\+|plus)\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)
_MULTIPLY_RESULT_RE = re.compile(r"multiply.*?result.*?by\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)
_TIME_RE = re.compile(r"\b(current time|what time|time is it)\b", re.IGNORECASE)
_WORD_COUNT_RE = re.compile(r"how many words.*?[\"'](.+?)[\"']", re.IGNORECASE | re.DOTALL)


def _tool_call(tool: str, args: dict) -> str:
    return json.dumps({"action": "call_tool", "tool": tool, "args": args})


def _final_answer(answer: str) -> str:
    return json.dumps({"action": "final_answer", "answer": answer})


def demo_planner(task: str, history: list[dict]) -> str:
    """
    Decide the next step for a task, given what tool calls have already
    happened (`history`, a list of {"tool", "args", "result"} dicts).
    Returns a JSON string, exactly like a real LLM call would.
    """
    if not history:
        add_match = _ADD_RE.search(task)
        if add_match:
            a, b = float(add_match.group(1)), float(add_match.group(2))
            return _tool_call("add", {"a": a, "b": b})

        if _TIME_RE.search(task):
            return _tool_call("get_time", {})

        wc_match = _WORD_COUNT_RE.search(task)
        if wc_match:
            return _tool_call("word_count", {"text": wc_match.group(1)})

        return _final_answer(
            "I don't have a scripted plan for this task. The demo planner only "
            "recognizes simple addition, time requests, and word counts - plug in "
            "a real LLM to handle arbitrary tasks (see the README)."
        )

    last_step = history[-1]

    if last_step["tool"] == "add":
        multiply_match = _MULTIPLY_RESULT_RE.search(task)
        if multiply_match:
            factor = float(multiply_match.group(1))
            return _tool_call("multiply", {"a": last_step["result"], "b": factor})

    return _final_answer(f"The result is {last_step['result']}.")
