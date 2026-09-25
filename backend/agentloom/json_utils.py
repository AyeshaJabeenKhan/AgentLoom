"""
json_utils.py

LLMs rarely return perfectly clean JSON on the first try. They wrap it
in markdown code fences, add a sentence before or after it, or use
smart quotes. This module pulls a JSON object out of whatever text the
brain returned, so the rest of AgentLoom can just work with a plain
Python dict.

The strategy, in order:
    1. Strip common markdown code fences (```json ... ``` or ``` ... ```).
    2. Find the first '{' and the matching closing '}' by counting
       brace depth, so extra text before/after the JSON is ignored.
    3. Parse that substring with the standard json module.

If none of that works, we raise a clear error instead of silently
guessing, since silently guessing wrong here means the agent might
call the wrong tool with the wrong arguments.
"""

from __future__ import annotations

import json
import re

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class JSONParseError(Exception):
    """Raised when no valid JSON object could be found in the text."""


def _strip_code_fences(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text.strip())


def _find_balanced_braces(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return None  # never balanced out - unterminated JSON


def extract_json(text: str) -> dict:
    """Pull the first JSON object out of `text` and parse it into a dict."""
    cleaned = _strip_code_fences(text)
    candidate = _find_balanced_braces(cleaned)

    if candidate is None:
        raise JSONParseError(f"Could not find a JSON object in the response: {text!r}")

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise JSONParseError(f"Found something that looked like JSON, but it didn't parse: {exc}") from exc

    if not isinstance(parsed, dict):
        raise JSONParseError(f"Expected a JSON object ({{...}}), got: {type(parsed).__name__}")

    return parsed
