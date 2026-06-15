# ADR 0001: Agent orchestration approach

- **Status:** Accepted
- **Date:** 2026-06-06
- **Phase:** 0 (Foundation & Scaffolding)

## Context

The agentic core must plan and invoke specialist roles (Diagnostic, Root-Cause,
Predictive, Risk & Priority, Recommendation, Reporting) that share one framework
and differ only by system prompt, allowed tools, and output schema. The loops
must be bounded and dependable -- not autonomous agents chatting indefinitely.
Two cross-cutting requirements shape this decision: every output must be
explainable and traceable to its source, and the LLM layer must be
provider-agnostic and tiered.

We considered two approaches: a hand-rolled tool-calling loop, or a framework
such as LangGraph.

## Hand-rolled tool-calling loop

**Pros**
- Full control over the loop: max-iterations, timeouts, retries, and provenance
  capture are all our code, which makes the explainability/traceability
  requirement trivial to honor.
- Keeps the provider-agnostic LLM client clean -- no framework message types
  competing with ours, and tiered routing (small for routing, large for
  reasoning) is expressed directly.
- Lower dependency weight, faster cold install, smaller surface to reason about.
- Maps cleanly onto the OpenAI-style tool-call interface every provider exposes.

**Cons**
- We write the loop and the message-history primitive ourselves (modest).
- If a later phase needs graph features (parallel branches, human-in-the-loop
  interrupts, durable checkpoints), we build them. The current scope asks for
  none of these.

## LangGraph

**Pros**
- State machine, checkpointer, and interrupts come for free.
- Graphical flow visualization and a library of multi-agent examples.

**Cons**
- Pulls in the LangChain dependency tree; heavier and more version churn (still
  pre-1.0).
- Its opinions on message types can conflict with a provider-agnostic client and
  make tiered routing less direct.
- Most of its value (parallel/HITL/checkpoint) is outside the current scope, and
  threading provenance through it is less direct than owning the loop.

## Decision

Use a **hand-rolled bounded tool-calling loop**. Provider-agnostic, tiered,
provenance-first, and a hackathon timeline all point the same way.

To keep the door open, the orchestrator exposes a deliberately narrow interface:

```python
class ToolLoopOrchestrator:
    def run(self, messages, *, allow=None, max_iters=None) -> AgentResult: ...
```

Callers depend only on `.run(...) -> AgentResult`. Swapping in a LangGraph-backed
implementation later is a single-file replacement behind this interface if a
phase genuinely needs graph semantics.

## Consequences

- Phase 0 ships `backend/app/agents/loop.py` with `run_tool_loop(...)` and the
  `ToolLoopOrchestrator` wrapper.
- All specialists in later phases are the same loop with a different system
  prompt, a different tool allowlist, and a different output schema.
- Loops are bounded by `max_iters` and raise a typed `ToolLoopError` rather than
  looping unbounded.
