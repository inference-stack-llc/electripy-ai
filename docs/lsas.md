# LSAS Architecture

**LSAS** — Layered Systems Architecture for AI Systems.

LSAS is the architectural model behind ElectriPy AI. It defines nine layers of concern for production AI systems, from governance at the foundation to application logic at the top.

LSAS does not prescribe application architecture. It defines **where production AI concerns belong**, so teams can reason clearly about what is missing and build it incrementally.

---

## The Layer Stack

| Layer | Name | One-line summary |
|-------|------|-----------------|
| 09 | Application | Product surface, business logic, user experience |
| 08 | Orchestration | Agent routing, session flow, multi-agent coordination |
| 07 | Memory | Conversation history, context window management |
| 06 | Knowledge | Retrieval, RAG, document indexing |
| 05 | Tool Integration | MCP, function calls, tool registry |
| 04 | Model Runtime | LLM gateway, provider adapters, structured output, caching |
| 03 | Reliability | Circuit breakers, retries, fallbacks, rate limiting |
| 02 | Observability | Tracing, spans, telemetry, redaction, cost metadata |
| 01 | Governance | Policy engine, policy gateway, approvals, audit trails |

Layers 01–04 are the **runtime foundation**. Every production AI system needs them.  
Layers 05–08 are **orchestration and knowledge infrastructure**. Their complexity scales with the sophistication of the system.  
Layer 09 is the **application** — the product-specific logic that sits on top of the runtime.

---

## Layer Reference

### Layer 01 — Governance

**Purpose:** Enforce policy decisions deterministically across the AI request lifecycle.

**Production problem solved:** AI systems make autonomous decisions. Without governance, there is no control plane — no way to enforce rules, require approvals, redact sensitive data, or maintain audit trails.

**ElectriPy AI components:**
- `ai.policy` — enterprise policy engine with subject/resource/action rules, approval workflows, evidence requirements, escalation chains
- `ai.policy_gateway` — request/response guardrails with regex-based detection, sanitization, and multi-stage enforcement (preflight, postflight, tool call, stream)
- `ai.sensitive_data_scanner` — PII and secret detection with 9+ built-in patterns and extensible custom rules

**Example use case:**  
Mask all email addresses in inbound prompts before they reach the model. Require human approval for tool calls that include `drop` or `delete` operations. Block LLM responses that contain secret markers.

---

### Layer 02 — Observability

**Purpose:** Make AI system behaviour visible, traceable, and auditable without relying on log scraping.

**Production problem solved:** AI systems are black boxes without deliberate instrumentation. When something goes wrong — cost spikes, policy violations, model drift, latency regressions — you need structured evidence, not grep.

**ElectriPy AI components:**
- `ai.observe` — OpenTelemetry-aligned structured tracing with AI-specific span kinds: `LLM`, `agent`, `tool`, `retrieval`, `policy`, `MCP`
- `ai.telemetry` — provider-agnostic telemetry adapters (JSONL sink, OpenTelemetry export) for HTTP, LLM, policy, and RAG events
- `ai.cost_ledger` — thread-safe token cost accumulation with multi-label slicing
- `ai.prompt_fingerprint` — deterministic SHA-256 request hashing for caching, dedup, and drift detection

**Example use case:**  
Emit a structured span for every LLM call including model, latency, input/output tokens, and finish reason. Export to an OpenTelemetry collector. Alert when cost per session crosses a threshold.

---

### Layer 03 — Reliability

**Purpose:** Protect AI systems from cascading failures, transient errors, and provider instability.

**Production problem solved:** LLM providers are remote HTTP services. They time out, return 503s, rate-limit aggressively, and fail under load. Without reliability primitives, a provider blip becomes a user-facing outage.

**ElectriPy AI components:**
- `concurrency.CircuitBreaker` — closed→open→half-open FSM with configurable thresholds and thread-safe state transitions
- `concurrency.retry` / `concurrency.async_retry` — configurable exponential backoff with exception scoping
- `ai.fallback_chain` — ranked provider failover with metadata tracking
- `concurrency.AsyncTokenBucketRateLimiter` — token bucket rate limiting, async-native

**Example use case:**  
Wrap the primary model provider in a circuit breaker. After 5 failures, trip open and route to a fallback provider via `fallback_chain`. Retry with exponential backoff before counting a failure.

---

### Layer 04 — Model Runtime

**Purpose:** Execute model calls in a provider-neutral, observable, and governed way.

**Production problem solved:** Switching LLM providers should not require rewriting business logic. Structured output extraction should not require ad-hoc parsing. Response caching should not require a separate cache service.

**ElectriPy AI components:**
- `ai.llm_gateway` — provider-agnostic sync/async LLM clients with request/response hook points
- `ai.provider_adapters` — OpenAI, Anthropic, Ollama, and generic HTTP-JSON adapters
- `ai.structured_output` — Pydantic model extraction from LLM text with auto-retry and temperature decay
- `ai.llm_cache` — pluggable response caching (in-memory LRU, SQLite WAL) with hit-rate tracking
- `ai.replay_tape` — record, replay, and diff LLM interactions for deterministic offline testing
- `ai.workload_router` — policy-driven, cost/latency/capability-aware model selection
- `ai.batch_complete` — concurrent LLM fan-out with bounded concurrency and per-request error isolation
- `ai.streaming_chat` — sync/async stream chunk primitives

**Example use case:**  
Attach a policy gateway hook to the LLM gateway so every request is inspected before it reaches the provider and every response is checked before it reaches the application. Swap OpenAI for Anthropic without changing any downstream code.

---

### Layer 05 — Tool Integration

**Purpose:** Connect AI systems to external capabilities through typed, governed, and observable interfaces.

**Production problem solved:** Tool calls are where AI systems interact with real infrastructure. A tool call that writes to a database, sends an email, or deletes a resource needs the same governance and observability as a model call.

**ElectriPy AI components:**
- `ai.mcp` — strongly typed Model Context Protocol clients, servers, and tool adapters
- `ai.tool_registry` — declarative tool definitions with JSON schema generation and OpenAI function-calling format
- `ai.agent_runtime` — deterministic tool-plan execution with step-by-step control

**Example use case:**  
Register tools with the tool registry. Route tool calls through the policy gateway to enforce approval requirements on destructive operations. Emit tool-call spans via `ai.observe`.

---

### Layer 06 — Knowledge

**Purpose:** Provide AI systems with relevant, retrieved context from structured and unstructured sources.

**Production problem solved:** Models have knowledge cutoffs and context window limits. Production systems need retrieval pipelines that are measurable, tunable, and regression-testable.

**ElectriPy AI components:**
- `ai.rag_eval_runner` — retrieval benchmarking with precision/recall/MRR metrics and drift detection
- `ai.rag_quality` — retrieval quality metrics and drift comparison helpers
- `ai.context_assembly` — priority-based context window packing and truncation
- `ai.token_budget` — pluggable token counting and budget-aware truncation

**Example use case:**  
Evaluate retrieval quality across chunking configurations using `rag_eval_runner`. Gate CI on hit-rate@5 ≥ 0.85. Detect drift when switching embedding models.

---

### Layer 07 — Memory

**Purpose:** Maintain coherent conversation state across turns without exceeding context window limits.

**Production problem solved:** Stateful AI conversations require context management. Naïvely passing all history exceeds token limits and degrades quality. Smart truncation preserves the most relevant context.

**ElectriPy AI components:**
- `ai.conversation_memory` — sliding-window and token-aware chat history management
- `ai.context_assembly` — priority-based context window packing and truncation
- `ai.token_budget` — pluggable token counting and budget-aware truncation

**Example use case:**  
Maintain a conversation with 50-turn history but limit context to 4,000 tokens. Use priority-based packing to keep system instructions and recent turns; drop older turns when the budget is exceeded.

---

### Layer 08 — Orchestration

**Purpose:** Coordinate work across agents, sessions, and tools with deterministic, bounded, and observable execution.

**Production problem solved:** Multi-step AI workflows that involve multiple agents or sessions are hard to debug, hard to bound, and hard to govern without explicit orchestration infrastructure.

**ElectriPy AI components:**
- `ai.realtime` — session lifecycle orchestration with event sequencing, tool-call dispatch, interruption handling, backpressure directives, and transport abstraction
- `ai.agent_collaboration` — bounded multi-agent handoff orchestration with hop limits and policy integration
- `ai.workload_router` — policy-driven, cost/latency/capability-aware model selection and routing
- `ai.skills` — versioned, validated skill packages with manifest-driven composition and `{{variable}}` template rendering
- `ai.prompt_engine` — template composition, variable substitution, and few-shot example management

**Example use case:**  
Run a planner → retriever → verifier agent pipeline using `agent_collaboration`. Bound execution to 10 hops. Attach a policy gateway to intercept tool calls. Capture telemetry for every agent turn.

---

### Layer 09 — Application

**Purpose:** Deliver product value to users.

**Production problem solved:** The application layer is where business logic lives. It depends on all the layers below it being reliable, observable, and governed.

**ElectriPy AI role at this layer:**  
ElectriPy AI does not own application logic. It provides the runtime that application code runs on top of. The CLI (`cli`) provides a thin interface for common application patterns.

---

## Implementing LSAS Incrementally

You do not need to implement all nine layers on day one.

A practical starting sequence for a production AI system:

1. **Layer 04** — Start with the LLM gateway and provider adapters. Get model calls working.
2. **Layer 03** — Add retry, circuit breaker, and fallback. Make calls resilient.
3. **Layer 02** — Add structured tracing. Make behaviour visible.
4. **Layer 01** — Add policy gateway. Enforce governance around sensitive data and tool calls.
5. **Layer 05** — Register tools. Add MCP integration when needed.
6. **Layer 06** — Add retrieval and evaluation when RAG is required.
7. **Layers 07/08** — Add memory and orchestration when multi-turn or multi-agent patterns emerge.

---

## LSAS and ElectriPy AI

ElectriPy AI implements runtime primitives for LSAS layers 01 through 08.

It does not impose a framework. It does not own your application. It does not require a platform.

Import the layers you need. The rest stays out of the way.

---

*See also: [MANIFESTO.md](../MANIFESTO.md) — AI Needs Infrastructure*  
*See also: [Architecture overview](architecture.md)*
