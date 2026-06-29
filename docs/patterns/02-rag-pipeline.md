# Pattern 02 — Simple RAG vs. Production Retrieval

Basic RAG retrieves documents and calls a model. Production RAG adds
quality gates, evaluation, and fallback so regressions are caught
before users see them.

---

## ❌ Before — The Prototype RAG Pattern

```mermaid
flowchart LR
    Q["User Query"]
    VDB["Vector DB\n(embedding search)"]
    LLM["LLM\n(context injection)"]
    Resp["Response\n(unchecked)"]

    Q -->|"embed + search"| VDB
    VDB -->|"top-k docs\n(no quality score)"| LLM
    LLM -->|"generated answer\n(no evaluation)"| Resp

    style Q fill:#1e1e2e,stroke:#585b70,color:#cdd6f4
    style VDB fill:#313244,stroke:#585b70,color:#cdd6f4
    style LLM fill:#313244,stroke:#585b70,color:#cdd6f4
    style Resp fill:#313244,stroke:#585b70,color:#cdd6f4
```

**What breaks:**

- Retrieval quality degrades silently as the corpus changes
- No precision/recall tracking — you don't know when retrieval drifts
- No evaluation harness — hallucinations discovered in production
- No CI gate — bad outputs ship automatically

---

## ✅ After — The Production RAG Pattern

```mermaid
flowchart TD
    Q["User Query"]

    subgraph Governance["🟣 L01 Governance"]
        PG["PolicyGateway\npreflight — mask PII in query"]
    end

    subgraph Knowledge["🔵 L06 Knowledge"]
        VDB["Vector DB\n(retrieval)"]
        RQ["rag_quality\nprecision · recall · MRR"]
    end

    subgraph ModelRuntime["🟠 L04 Model Runtime"]
        GW["LLM Gateway\ncontext-injected prompt"]
    end

    subgraph Evaluation["🟢 Evaluation"]
        EA["eval_assertions\nCI quality gates"]
        RER["RAGEvalRunner\ndrift detection vs baseline"]
    end

    subgraph Observability["🔵 L02 Observability"]
        OBS["ObservabilityService\nretrieval span + LLM span"]
    end

    Q --> PG
    PG --> VDB
    VDB -->|"top-k docs"| RQ
    RQ -->|"quality score\nprecision / recall"| GW
    GW -->|"grounded answer"| EA
    EA -->|"PASS: deliver response\nFAIL: trigger fallback"| RER
    RER -->|"compare vs baseline\nalert on drift"| OBS
    OBS --> Q

    style Governance fill:#1a0d2e,stroke:#cba6f7,color:#cdd6f4
    style Knowledge fill:#0d1a2e,stroke:#89dceb,color:#cdd6f4
    style ModelRuntime fill:#2e1a0d,stroke:#fab387,color:#cdd6f4
    style Evaluation fill:#0d2e0d,stroke:#a6e3a1,color:#cdd6f4
    style Observability fill:#0d1a2e,stroke:#89dceb,color:#cdd6f4
```

**Key additions:**

| Component | What it prevents |
|-----------|-----------------|
| `rag_quality` | Silent retrieval degradation — you see precision/recall drift |
| `eval_assertions` | Hallucinations shipping to users |
| `RAGEvalRunner` | Regression against a golden dataset baseline |
| `ObservabilityService` | Invisible retrieval — every doc fetch is a traced span |
| `PolicyGateway` | PII in queries reaching the vector DB or LLM logs |

```python
# Production RAG quality gate
from electripy.ai.rag_eval_runner import RAGEvalRunner
from electripy.ai.eval_assertions import assert_llm_output, contains_keywords, satisfies_length
from electripy.ai.rag_quality import compute_retrieval_metrics

# Evaluate retrieval quality against a golden query set
runner = RAGEvalRunner(queries=golden_queries, corpus=corpus)
report = runner.run()
assert report.mean_reciprocal_rank >= 0.70, f"Retrieval MRR regressed: {report.mean_reciprocal_rank}"

# Gate the generated answer before delivery
assert_llm_output(
    answer,
    checks=[
        contains_keywords(expected_keywords),
        satisfies_length(min_length=50),
    ],
)
```
