"""
state_machine.py

AgentLoom's loop moves through a small, fixed set of states every time
it takes a step. Writing this as an explicit state machine (instead of
just a pile of if/else inside one big loop) makes the allowed flow
obvious, and makes it easy to say exactly why a transition happened.

States:
    THINKING   - asking the "brain" (an LLM, or the demo planner) what
                 to do next.
    ACTING     - calling a registered Python function (a tool) with the
                 arguments the brain asked for.
    OBSERVING  - recording what that tool call returned, so the next
                 THINKING step can see it.
    DONE       - the brain said the task is finished.
    ERROR      - something went wrong (bad JSON, unknown tool, a tool
                 raised an exception) and the loop is stopping early.
    MAX_STEPS  - the loop ran out of steps before finishing.

Only certain transitions make sense (you can't jump straight from
THINKING to DONE without going through ACTING first if a tool was
called, for example). `StateMachine.transition()` checks this and
raises an error if something tries to skip a step it shouldn't.
"""

from __future__ import annotations

import logging
from enum import Enum

logger = logging.getLogger("agentloom")


class AgentState(str, Enum):
    THINKING = "THINKING"
    ACTING = "ACTING"
    OBSERVING = "OBSERVING"
    DONE = "DONE"
    ERROR = "ERROR"
    MAX_STEPS = "MAX_STEPS"


# Map of "from this state, these are the states you're allowed to move to".
_ALLOWED_TRANSITIONS: dict[AgentState, set[AgentState]] = {
    AgentState.THINKING: {AgentState.ACTING, AgentState.DONE, AgentState.ERROR, AgentState.MAX_STEPS},
    AgentState.ACTING: {AgentState.OBSERVING, AgentState.ERROR},
    AgentState.OBSERVING: {AgentState.THINKING, AgentState.ERROR},
    AgentState.DONE: set(),
    AgentState.ERROR: set(),
    AgentState.MAX_STEPS: set(),
}


class InvalidTransitionError(Exception):
    """Raised when the agent tries to move to a state it isn't allowed
    to move to from where it currently is."""


class StateMachine:
    """Tracks the agent's current state and enforces valid transitions."""

    def __init__(self, initial_state: AgentState = AgentState.THINKING):
        self.state = initial_state

    def can_transition(self, to_state: AgentState) -> bool:
        return to_state in _ALLOWED_TRANSITIONS.get(self.state, set())

    def transition(self, to_state: AgentState) -> AgentState:
        if not self.can_transition(to_state):
            raise InvalidTransitionError(f"Cannot move from {self.state} to {to_state}")

        logger.info("State transition: %s -> %s", self.state.value, to_state.value)
        self.state = to_state
        return self.state
