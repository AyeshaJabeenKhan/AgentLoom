import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from agentloom.agent import Agent
from agentloom.tools import ToolRegistry


def make_registry():
    registry = ToolRegistry()

    @registry.register()
    def add(a, b):
        return a + b

    return registry


def scripted_brain(responses):
    """Returns a brain_fn that plays back a fixed list of JSON strings,
    one per call, regardless of what task/history it's given."""
    call_count = {"i": 0}

    def brain_fn(task, history):
        response = responses[call_count["i"]]
        call_count["i"] += 1
        return response

    return brain_fn


def test_single_step_final_answer():
    brain = scripted_brain([json.dumps({"action": "final_answer", "answer": "hello"})])
    agent = Agent(brain_fn=brain, tools=make_registry(), max_steps=5)

    result = agent.run("say hello")

    assert result.status == "done"
    assert result.final_answer == "hello"
    assert len(result.steps) == 2  # THINKING, then DONE


def test_tool_call_then_final_answer():
    responses = [
        json.dumps({"action": "call_tool", "tool": "add", "args": {"a": 2, "b": 3}}),
        json.dumps({"action": "final_answer", "answer": "the sum is 5"}),
    ]
    brain = scripted_brain(responses)
    agent = Agent(brain_fn=brain, tools=make_registry(), max_steps=5)

    result = agent.run("add 2 and 3")

    assert result.status == "done"
    assert result.final_answer == "the sum is 5"
    states = [s.state for s in result.steps]
    assert states == ["THINKING", "ACTING", "OBSERVING", "THINKING", "DONE"]


def test_unknown_tool_ends_in_error():
    responses = [json.dumps({"action": "call_tool", "tool": "does_not_exist", "args": {}})]
    brain = scripted_brain(responses)
    agent = Agent(brain_fn=brain, tools=make_registry(), max_steps=5)

    result = agent.run("do something impossible")

    assert result.status == "error"
    assert result.final_answer is None


def test_malformed_json_ends_in_error():
    brain = scripted_brain(["this is not json at all"])
    agent = Agent(brain_fn=brain, tools=make_registry(), max_steps=5)

    result = agent.run("confuse the agent")

    assert result.status == "error"


def test_max_steps_reached_without_finishing():
    # Always asks to call the same tool, never finishes.
    responses = [json.dumps({"action": "call_tool", "tool": "add", "args": {"a": 1, "b": 1}})] * 10
    brain = scripted_brain(responses)
    agent = Agent(brain_fn=brain, tools=make_registry(), max_steps=3)

    result = agent.run("loop forever")

    assert result.status == "max_steps"
    assert result.final_answer is None
