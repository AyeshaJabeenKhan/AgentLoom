import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from agentloom.tools import ToolExecutionError, ToolNotFoundError, ToolRegistry


def test_register_and_call_a_tool():
    registry = ToolRegistry()

    @registry.register()
    def add(a, b):
        """Add two numbers."""
        return a + b

    assert registry.call("add", {"a": 2, "b": 3}) == 5


def test_register_with_custom_name():
    registry = ToolRegistry()

    @registry.register(name="sum_two")
    def add(a, b):
        return a + b

    assert "sum_two" in registry.names()
    assert registry.call("sum_two", {"a": 1, "b": 1}) == 2


def test_unknown_tool_raises_not_found():
    registry = ToolRegistry()
    with pytest.raises(ToolNotFoundError):
        registry.call("does_not_exist", {})


def test_wrong_arguments_raise_execution_error():
    registry = ToolRegistry()

    @registry.register()
    def add(a, b):
        return a + b

    with pytest.raises(ToolExecutionError):
        registry.call("add", {"a": 1})  # missing 'b'


def test_tool_that_raises_is_wrapped_in_execution_error():
    registry = ToolRegistry()

    @registry.register()
    def divide(a, b):
        return a / b

    with pytest.raises(ToolExecutionError):
        registry.call("divide", {"a": 1, "b": 0})


def test_describe_lists_registered_tools():
    registry = ToolRegistry()

    @registry.register()
    def add(a, b):
        """Add two numbers."""
        return a + b

    described = registry.describe()
    assert described == [{"name": "add", "description": "Add two numbers."}]
