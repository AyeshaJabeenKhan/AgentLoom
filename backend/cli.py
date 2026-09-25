"""
cli.py

Run a task through the agent from the command line, without needing
the API or dashboard.

Example:
    python cli.py "What is 12 plus 30, then multiply the result by 2?"
"""

from __future__ import annotations

import argparse
import json

from agentloom import Agent, configure_logging, demo_planner, demo_tool_registry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a task through the AgentLoom demo agent.")
    parser.add_argument("task", type=str, help="The task to give the agent")
    parser.add_argument("--max-steps", type=int, default=8, help="Max loop iterations before giving up (default: 8)")
    parser.add_argument("--json", action="store_true", help="Print the full JSON trace instead of a readable summary")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging()

    agent = Agent(brain_fn=demo_planner, tools=demo_tool_registry, max_steps=args.max_steps)
    result = agent.run(args.task)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    print(f"Task: {args.task}\n")
    for step in result.steps:
        print(f"[step {step.step_number}] {step.state}: {step.detail}")

    print()
    if result.status == "done":
        print(f"Final answer: {result.final_answer}")
    elif result.status == "max_steps":
        print("Stopped: ran out of steps before finishing.")
    else:
        print("Stopped: an error occurred (see the ERROR step above).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
