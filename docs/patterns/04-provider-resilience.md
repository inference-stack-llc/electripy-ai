# Pattern 04 — Single Provider vs. Resilient Provider Chain

Hard-coding a single LLM provider is a single point of failure.
This pattern shows how to add multi-provider resilience with circuit
breaking, automatic failover, and cost-aware routing.

---

## ❌ Before — The Single-Provider Prototype

```mermaid
flowchart LR
    App["Application"]
    API["OpenAI API\n(only option)"]
    Err["Exception\nHTTP 429 / 500 / 503\n→ crashes caller"]

    App -->|"direct SDK call"| API
    API -.->|"rate limit\noutage\nlatency spike"| Err
    Err -->|"unhandled"| App

    style App fill:#1e1e2e,stroke:#585b70,color:#cdd6f4
    style API fill:#313244,stroke:#585b70,color:#cdd6f4
    style Err fill:#3b1219,stroke:#f38ba8,color:#f38ba8
```

**What breaks:**

- Any provider outage or rate-limit kills your application
- No retry → transient errors become hard failures
- No fallback → 100% blast radius on provider degradation
- No circuit breaking → the application hammers a failing provider
- No routing → you're always paying premium pricing even for cheap tasks

---

## ✅ After — The Resilient Provider Chain

```mermaid
flowchart TD
    App["Application"]

    subgraph Routing["🟠 L04 Model Runtime — Routing"]
        WR["WorkloadRouter\ncost · latency · capability scoring"]
    end

    subgraph Reliability["🔴 L03 Reliability"]
        CB_A["CircuitBreaker A\nfailure_threshold=5"]
        CB_B["CircuitBreaker B\nfailure_threshold=5"]
        CB_C["CircuitBreaker C\nfailure_threshold=5"]
        FC["FallbackChainPort\n[A → B → C]"]
        RT["retry(max_attempts=3\nbackoff=2.0)"]
    end

    subgraph Providers["Providers"]
        PA["Provider A\nOpenAI gpt-4o\n(primary, capable)"]
        PB["Provider B\nAnthropic claude-3-5\n(fallback, capable)"]
        PC["Provider C\nOllama llama3\n(offline, free)"]
    end

    subgraph Observability["🔵 L02 Observability"]
        CL["CostLedger\nper-provider cost tracking"]
        OBS["ObservabilityService\nfallback_provider_index attribute"]
    end

    App --> WR
    WR -->|"route by score"| FC
    FC --> RT
    RT -->|"try 1"| CB_A
    RT -.->|"on failure"| CB_B
    RT -.->|"on failure"| CB_C
    CB_A --> PA
    CB_B --> PB
    CB_C --> PC
    PA & PB & PC -->|"response"| CL
    CL --> OBS
    OBS --> App

    style Routing fill:#2e1a0d,stroke:#fab387,color:#cdd6f4
    style Reliability fill:#2e0d0d,stroke:#f38ba8,color:#cdd6f4
    style Providers fill:#181825,stroke:#585b70,color:#cdd6f4
    style Observability fill:#0d1a2e,stroke:#89dceb,color:#cdd6f4
```

**What each layer provides:**

| Component | Failure mode addressed |
|-----------|----------------------|
| `CircuitBreaker` per provider | Stops hammering a degraded provider |
| `FallbackChainPort` | Automatic promotion to next provider on failure |
| `retry` | Transient errors (timeouts, 429s) resolved without caller awareness |
| `WorkloadRouter` | Cost-optimised routing — cheap tasks go to cheap models |
| `CostLedger` | Per-provider cost tracking to understand failover spend |
| `ObservabilityService` | `_fallback_provider_index` attribute shows which provider won |

```python
from electripy.ai.fallback_chain import FallbackChainPort
from electripy.concurrency.circuit_breaker import CircuitBreaker
from electripy.ai.cost_ledger import CostLedger

# Wrap each provider with its own circuit breaker
cb_a = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)
cb_b = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)

class ProtectedProvider:
    def __init__(self, provider, breaker):
        self._p, self._cb = provider, breaker
    def complete(self, request, *, timeout=None):
        return self._cb.call(lambda: self._p.complete(request, timeout=timeout))

chain = FallbackChainPort(providers=[
    ProtectedProvider(openai_adapter, cb_a),
    ProtectedProvider(anthropic_adapter, cb_b),
    ollama_adapter,  # no breaker — free, always available
])

response = chain.complete(request)
# response.metadata["_fallback_provider_index"] → 0 (OpenAI), 1 (Anthropic), 2 (Ollama)
```
