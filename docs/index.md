# ElectriPy AI

**The Open Source AI Application Runtime.**

Everything required between prototype and production.

## Overview

ElectriPy AI is the open source AI Application Runtime for operating reliable, observable, governable, and evaluable production AI systems. It provides composable runtime infrastructure for reliability, observability, governance, evaluation, orchestration, and model runtime execution — all without adopting a framework.

> Import the pieces you need; leave the rest.

## Status

- **Maturity**: Early alpha — APIs may still evolve. Core runtime domains are implemented and tested.
- **Test suite**: 1,000+ offline, deterministic tests.
- **Versioning**: SemVer at `v0.x` — expect breaking changes until `v1.0`.

See the [LSAS Architecture](lsas.md) for the layered systems model behind ElectriPy AI.

## Runtime Domains

### Reliability

| Component | Purpose |
|-----------|---------|
| Circuit breaker | Stop cascading failures before they propagate |
| Retry (sync/async) | Configurable backoff with exception scoping |
| Fallback chain | Ranked provider failover with metadata tracking |
| Rate limiter | Token bucket algorithm, async-native |

### Observability

| Package | Purpose |
|---------|---------|
| `observe` | OpenTelemetry-aligned tracing with AI-specific span kinds (LLM, agent, tool, retrieval, policy, MCP) |
| `telemetry` | Provider-agnostic telemetry adapters (JSONL, OpenTelemetry) |
| `sensitive_data_scanner` | PII and secret detection with 9+ built-in patterns |

### Governance

| Package | Purpose |
|---------|---------|
| `policy` | Enterprise policy engine — rules, approval workflows, escalation chains |
| `policy_gateway` | Request/response guardrails with regex-based detection and multi-stage enforcement |

### Evaluation

| Package | Purpose |
|---------|---------|
| `evals` | Dataset-driven evaluation with scoring and baseline comparison |
| `eval_assertions` | Pytest-native assertion helpers for LLM output validation |
| `rag_eval_runner` | Retrieval benchmarking with precision/recall/MRR metrics |

### Orchestration

| Package | Purpose |
|---------|---------|
| `workload_router` | Cost/latency/capability-aware model routing |
| `realtime` | Session lifecycle — event sequencing, tool calls, interruption, backpressure |
| `mcp` | Strongly typed Model Context Protocol |
| `skills` | Versioned skill packages with manifest-driven composition |
| `agent_collaboration` | Bounded multi-agent handoff with hop limits and policy integration |

### Model Runtime

| Package | Purpose |
|---------|---------|
| `llm_gateway` | Provider-agnostic sync/async LLM clients with request/response hooks |
| `provider_adapters` | OpenAI, Anthropic, Ollama, and generic HTTP-JSON adapters |
| `fallback_chain` | Ranked provider failover with metadata tracking |
| `structured_output` | Pydantic extraction from LLM text with auto-retry |
| `llm_cache` | Response caching (in-memory LRU, SQLite WAL) |
| `replay_tape` | Record, replay, and diff LLM interactions |

### Core Infrastructure

| Package | Purpose |
|---------|---------|
| `core` | Configuration, structured logging, error hierarchy |
| `concurrency` | Retry, rate limiting, circuit breaker |
| `io` | JSONL read/write utilities |
| `cli` | CLI commands, health checks, and demo showcase |

## Quick Links

### Getting started

- [Installation](getting-started/installation.md)
- [Quickstart Guide](getting-started/quickstart.md)
- [LSAS Architecture](lsas.md)
- [Manifesto](manifesto.md)

### Observability & governance

- [Observe — Structured Tracing](user-guide/ai-observe.md)
- [AI Telemetry](user-guide/ai-telemetry.md)
- [Policy Engine](user-guide/ai-policy.md)
- [Policy Gateway](user-guide/ai-policy-gateway.md)
- [Sensitive Data Scanner](user-guide/ai-sensitive-data-scanner.md)

### Evaluation & quality

- [Evaluation Pipeline](user-guide/ai-evals.md)
- [Eval Assertions](user-guide/ai-eval-assertions.md)
- [RAG Evaluation Runner](user-guide/ai-rag-eval-runner.md)

### Model Runtime

- [LLM Gateway](user-guide/ai-llm-gateway.md)
- [Provider Adapters](user-guide/ai-provider-adapters.md)
- [Workload Router](user-guide/ai-workload-router.md)
- [Fallback Chain](user-guide/ai-fallback-chain.md)
- [Structured Output](user-guide/ai-structured-output.md)
- [LLM Cache](user-guide/ai-llm-cache.md)
- [Replay Tape](user-guide/ai-replay-tape.md)

### Orchestration

- [Realtime Sessions](user-guide/ai-realtime.md)
- [Agent Collaboration](user-guide/ai-agent-collaboration.md)
- [MCP](user-guide/ai-mcp.md)
- [Skills](user-guide/ai-skills.md)
- [Cost Ledger](user-guide/ai-cost-ledger.md)

### Foundation

- [Core Concepts](user-guide/core.md)
- [Concurrency & Resilience](user-guide/concurrency.md)
- [Circuit Breaker](user-guide/circuit-breaker.md)
- [I/O Utilities](user-guide/io.md)
- [CLI Guide](user-guide/cli.md)

### Reference

- [API Reference](api.md)
- [Component Maturity Model](user-guide/component-maturity.md)

## Requirements

- Python 3.11 or higher
- Dependencies managed via `pyproject.toml`

## License

MIT License.

MIT License — see [LICENSE](https://github.com/inference-stack-llc/electripy-ai/blob/main/LICENSE) for details.
