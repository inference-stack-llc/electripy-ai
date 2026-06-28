# Roadmap

ElectriPy AI is alpha software under active development.

## Current state (v0.4.x)

The following runtime domains are implemented and tested:

- ✅ Reliability — circuit breaker, retry, rate limiting, fallback chain
- ✅ Observability — structured tracing (observe), telemetry adapters, cost ledger, prompt fingerprint, sensitive data scanner
- ✅ Governance — policy engine, policy gateway
- ✅ Evaluation — evals framework, eval assertions, RAG eval runner
- ✅ Orchestration — workload router, realtime sessions, agent collaboration, skills, MCP
- ✅ Model Runtime — LLM gateway, provider adapters, structured output, LLM cache, replay tape

## Planned for upcoming releases

- Improved LSAS tooling and layer diagnostics
- Additional provider adapters
- Streaming evaluation support
- Cost analytics integration
- Expanded MCP tooling
- Improved context assembly and token budget strategies

## ElectriPy Cloud

ElectriPy Cloud is planned as the hosted operational layer for teams using ElectriPy AI in production.

Planned capabilities:
- hosted traces and spans
- agent and session replay
- reliability scoring
- policy analytics
- cost analytics
- operational dashboards
- team workspaces

*ElectriPy Cloud does not exist yet. No timeline is implied.*

## Contributing

See [CONTRIBUTING.md](https://github.com/inference-stack-llc/electripy-ai/blob/main/CONTRIBUTING.md) if you want to contribute to any of the planned capabilities.
