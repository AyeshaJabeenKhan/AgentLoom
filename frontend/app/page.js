"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const SAMPLE_TASKS = [
  "What is 12 plus 30, then multiply the result by 2?",
  "What is the current time?",
  'How many words are in "the quick brown fox jumps over the lazy dog"?',
  "Write me a poem about the ocean.",
];

function formatDetail(step) {
  const d = step.detail;
  if (step.state === "THINKING") {
    const decision = d.decision;
    if (decision.action === "call_tool") {
      return (
        <span>
          decided to call <code>{decision.tool}</code> with <code>{JSON.stringify(decision.args)}</code>
        </span>
      );
    }
    return <span>decided the task is finished</span>;
  }
  if (step.state === "ACTING") {
    return (
      <span>
        calling <code>{d.tool}</code> with <code>{JSON.stringify(d.args)}</code>
      </span>
    );
  }
  if (step.state === "OBSERVING") {
    return (
      <span>
        <code>{d.tool}</code> returned <code>{JSON.stringify(d.result)}</code>
      </span>
    );
  }
  if (step.state === "DONE") {
    return <span>final answer: {d.answer}</span>;
  }
  if (step.state === "ERROR") {
    return <span>{d.error}</span>;
  }
  return <span>{JSON.stringify(d)}</span>;
}

export default function Home() {
  const [task, setTask] = useState(SAMPLE_TASKS[0]);
  const [maxSteps, setMaxSteps] = useState(8);
  const [tools, setTools] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);

  async function loadTools() {
    try {
      const res = await fetch(`${API_URL}/tools`);
      const data = await res.json();
      setTools(data);
    } catch (err) {
      // Non-fatal - the tools list is just informational.
    }
  }

  useEffect(() => {
    loadTools();
  }, []);

  async function handleRun(e) {
    e.preventDefault();
    setError("");
    setResult(null);
    setRunning(true);

    try {
      const res = await fetch(`${API_URL}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, max_steps: Number(maxSteps) }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "The agent run failed.");
      setResult(data);
    } catch (err) {
      setError(err.message === "Failed to fetch" ? "Could not reach the API at " + API_URL : err.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="page">
      <div className="header">
        <h1>AgentLoom</h1>
        <p>Give it a task. Watch it think, call tools, and observe results until it's done.</p>
      </div>

      <form className="card" onSubmit={handleRun}>
        <h2>1. Give it a task</h2>
        <textarea rows={2} value={task} onChange={(e) => setTask(e.target.value)} />

        <div className="sample-tasks">
          {SAMPLE_TASKS.map((t) => (
            <span key={t} className="sample-chip" onClick={() => setTask(t)}>
              {t.length > 42 ? t.slice(0, 42) + "..." : t}
            </span>
          ))}
        </div>

        <div className="actions">
          <label style={{ fontSize: 12, color: "var(--text-soft)" }}>
            Max steps:{" "}
            <input
              type="number"
              style={{ width: 60, display: "inline-block" }}
              value={maxSteps}
              onChange={(e) => setMaxSteps(e.target.value)}
            />
          </label>
          <button className="primary" type="submit" disabled={running}>
            {running ? "Running..." : "Run agent"}
          </button>
        </div>

        {error && <div className="error-box">{error}</div>}
      </form>

      <div className="card">
        <h2>2. Registered tools</h2>
        <div className="tools-list">
          {tools.map((t) => (
            <span key={t.name} className="tool-chip">
              <b>{t.name}</b> &mdash; {t.description}
            </span>
          ))}
        </div>
      </div>

      {result && (
        <div className="card">
          <h2>3. Trace</h2>
          <div className="status-row">
            <span className={`badge ${result.status}`}>{result.status}</span>
            {result.final_answer && <span style={{ fontSize: 13, color: "var(--text-soft)" }}>{result.final_answer}</span>}
          </div>

          <div className="timeline">
            {result.steps.map((step, i) => (
              <div className="step-row" key={i}>
                <span className={`step-marker ${step.state.toLowerCase()}`}>{step.state}</span>
                <div className="step-body">{formatDetail(step)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="footer-note">
        AgentLoom: A project demonstrating a tool-calling agent loop, built completely without an agent framework.
      </div>
    </div>
  );
}
