"""
agent.py

The orchestration loop. This is the part that makes AgentLoom an
"agent" rather than just a single function call: it keeps asking the
brain what to do next, runs whatever tool it asks for, feeds the
result back in, and repeats - until the brain says the task is done,
something goes wrong, or it runs out of steps.

The brain is just a function: `brain_fn(task: str, history: list[dict]) -> str`
that returns a JSON string. In this project that's `demo_planner`
(see demo_planner.py), but a real deployment would swap that for an
actual call to an LLM API. Nothing else in this file needs to change
for that swap - the loop doesn't care where the JSON came from.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable

from .json_utils import JSONParseError, extract_json
from .state_machine import AgentState, InvalidTransitionError, StateMachine
from .tools import ToolExecutionError, ToolNotFoundError, ToolRegistry

logger = logging.getLogger("agentloom")


@dataclass
class StepLog:
    step_number: int
    state: str
    detail: dict

    def to_dict(self) -> dict:
        return {"step_number": self.step_number, "state": self.state, "detail": self.detail}


@dataclass
class AgentResult:
    status: str  # "done", "error", "max_steps"
    final_answer: str | None
    steps: list[StepLog] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "final_answer": self.final_answer,
            "steps": [s.to_dict() for s in self.steps],
        }


class Agent:
    """Runs the think -> act -> observe loop for a single task."""

    def __init__(self, brain_fn: Callable[[str, list[dict]], str], tools: ToolRegistry, max_steps: int = 8):
        self.brain_fn = brain_fn
        self.tools = tools
        self.max_steps = max_steps

    def run(self, task: str) -> AgentResult:
        machine = StateMachine(initial_state=AgentState.THINKING)
        history: list[dict] = []  # completed tool calls: [{"tool", "args", "result"}, ...]
        steps: list[StepLog] = []

        logger.info("Starting task: %s", task)

        for step_number in range(1, self.max_steps + 1):
            # --- THINKING ---
            raw_response = self.brain_fn(task, history)

            try:
                decision = extract_json(raw_response)
            except JSONParseError as exc:
                machine.transition(AgentState.ERROR)
                steps.append(StepLog(step_number, AgentState.ERROR.value, {"error": str(exc)}))
                logger.error("Could not parse brain response: %s", exc)
                return AgentResult(status="error", final_answer=None, steps=steps)

            steps.append(StepLog(step_number, AgentState.THINKING.value, {"decision": decision}))
            action = decision.get("action")

            if action == "final_answer":
                machine.transition(AgentState.DONE)
                answer = decision.get("answer", "")
                steps.append(StepLog(step_number, AgentState.DONE.value, {"answer": answer}))
                logger.info("Task finished: %s", answer)
                return AgentResult(status="done", final_answer=answer, steps=steps)

            if action != "call_tool":
                machine.transition(AgentState.ERROR)
                steps.append(
                    StepLog(step_number, AgentState.ERROR.value, {"error": f"Unknown action '{action}'"})
                )
                return AgentResult(status="error", final_answer=None, steps=steps)

            # --- ACTING ---
            machine.transition(AgentState.ACTING)
            tool_name = decision.get("tool")
            tool_args = decision.get("args", {})
            steps.append(StepLog(step_number, AgentState.ACTING.value, {"tool": tool_name, "args": tool_args}))

            try:
                result = self.tools.call(tool_name, tool_args)
            except (ToolNotFoundError, ToolExecutionError) as exc:
                machine.transition(AgentState.ERROR)
                steps.append(StepLog(step_number, AgentState.ERROR.value, {"error": str(exc)}))
                logger.error("Tool call failed: %s", exc)
                return AgentResult(status="error", final_answer=None, steps=steps)

            # --- OBSERVING ---
            machine.transition(AgentState.OBSERVING)
            steps.append(StepLog(step_number, AgentState.OBSERVING.value, {"tool": tool_name, "result": result}))
            history.append({"tool": tool_name, "args": tool_args, "result": result})

            try:
                machine.transition(AgentState.THINKING)
            except InvalidTransitionError as exc:
                # Should not normally happen, but fail loudly and clearly if it does.
                steps.append(StepLog(step_number, AgentState.ERROR.value, {"error": str(exc)}))
                return AgentResult(status="error", final_answer=None, steps=steps)

        logger.warning("Task stopped: reached max_steps (%s) without finishing", self.max_steps)
        return AgentResult(status="max_steps", final_answer=None, steps=steps)
