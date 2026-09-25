"""
api.py

A small FastAPI app that lets the Next.js dashboard run a task through
the agent and see every step it took.

Run it with:
    uvicorn api:app --reload --port 8000

Note on the demo planner: to keep this project runnable with zero
setup (no API key required), /run uses `demo_planner` from
agentloom/demo_planner.py, a simple regex-based stand-in for a real
LLM call. Swap it for your own function that calls a real LLM API to
use this for real - see the README.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agentloom import Agent, configure_logging, demo_planner, demo_tool_registry

configure_logging()

app = FastAPI(title="AgentLoom API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunTaskRequest(BaseModel):
    task: str = Field(..., min_length=1)
    max_steps: int = Field(8, ge=1, le=20)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/tools")
def list_tools() -> list:
    return demo_tool_registry.describe()


@app.post("/run")
def run_task(request: RunTaskRequest) -> dict:
    agent = Agent(brain_fn=demo_planner, tools=demo_tool_registry, max_steps=request.max_steps)
    try:
        result = agent.run(request.task)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error running the agent: {exc}") from exc

    return result.to_dict()
