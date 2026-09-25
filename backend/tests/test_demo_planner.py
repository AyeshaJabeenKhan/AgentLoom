import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from agentloom.demo_planner import demo_planner


def test_recognizes_simple_addition():
    decision = json.loads(demo_planner("What is 12 plus 30?", []))
    assert decision["action"] == "call_tool"
    assert decision["tool"] == "add"
    assert decision["args"] == {"a": 12.0, "b": 30.0}


def test_multi_step_add_then_multiply():
    first = json.loads(demo_planner("What is 12 plus 30, then multiply the result by 2?", []))
    assert first["tool"] == "add"

    history = [{"tool": "add", "args": first["args"], "result": 42.0}]
    second = json.loads(demo_planner("What is 12 plus 30, then multiply the result by 2?", history))
    assert second["action"] == "call_tool"
    assert second["tool"] == "multiply"
    assert second["args"] == {"a": 42.0, "b": 2.0}


def test_time_request_recognized():
    decision = json.loads(demo_planner("What is the current time?", []))
    assert decision["tool"] == "get_time"


def test_word_count_request_recognized():
    decision = json.loads(demo_planner('How many words are in "the quick brown fox"?', []))
    assert decision["tool"] == "word_count"
    assert decision["args"]["text"] == "the quick brown fox"


def test_unrecognized_task_gives_final_answer_explaining_limits():
    decision = json.loads(demo_planner("Write me a poem about the ocean.", []))
    assert decision["action"] == "final_answer"


def test_add_without_followup_gives_final_answer():
    history = [{"tool": "add", "args": {"a": 1, "b": 1}, "result": 2.0}]
    decision = json.loads(demo_planner("What is 1 plus 1?", history))
    assert decision["action"] == "final_answer"
    assert "2.0" in decision["answer"]
