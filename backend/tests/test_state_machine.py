import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from agentloom.state_machine import AgentState, InvalidTransitionError, StateMachine


def test_starts_in_thinking_by_default():
    machine = StateMachine()
    assert machine.state == AgentState.THINKING


def test_valid_transition_sequence():
    machine = StateMachine()
    machine.transition(AgentState.ACTING)
    machine.transition(AgentState.OBSERVING)
    machine.transition(AgentState.THINKING)
    machine.transition(AgentState.DONE)
    assert machine.state == AgentState.DONE


def test_invalid_transition_raises_error():
    machine = StateMachine()
    with pytest.raises(InvalidTransitionError):
        machine.transition(AgentState.OBSERVING)  # can't observe before acting


def test_terminal_states_have_no_way_out():
    machine = StateMachine()
    machine.transition(AgentState.DONE)
    with pytest.raises(InvalidTransitionError):
        machine.transition(AgentState.THINKING)


def test_can_transition_check_does_not_mutate_state():
    machine = StateMachine()
    assert machine.can_transition(AgentState.OBSERVING) is False
    assert machine.state == AgentState.THINKING  # unchanged
