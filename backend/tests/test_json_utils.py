import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from agentloom.json_utils import JSONParseError, extract_json


def test_plain_json_parses():
    result = extract_json('{"action": "final_answer", "answer": "42"}')
    assert result == {"action": "final_answer", "answer": "42"}


def test_json_wrapped_in_code_fence():
    text = '```json\n{"action": "call_tool", "tool": "add", "args": {"a": 1, "b": 2}}\n```'
    result = extract_json(text)
    assert result["tool"] == "add"


def test_json_with_surrounding_text():
    text = 'Sure, here is my decision:\n{"action": "final_answer", "answer": "done"}\nHope that helps!'
    result = extract_json(text)
    assert result["answer"] == "done"


def test_nested_braces_are_handled():
    text = '{"action": "call_tool", "tool": "add", "args": {"a": 1, "b": {"nested": true}}}'
    result = extract_json(text)
    assert result["args"]["b"]["nested"] is True


def test_no_json_raises_error():
    with pytest.raises(JSONParseError):
        extract_json("I don't know what to do.")


def test_malformed_json_raises_error():
    with pytest.raises(JSONParseError):
        extract_json('{"action": "final_answer", "answer": }')


def test_non_object_json_raises_error():
    with pytest.raises(JSONParseError):
        extract_json("[1, 2, 3]")
