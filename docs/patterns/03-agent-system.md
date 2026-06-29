# Pattern 03 — Basic Agent vs. Governed Agent

Uncontrolled agents are the prototype trap at its worst: they work in
demos and cause incidents in production. This pattern shows how to add
governance, observability, and hop limits without changing the agent logic.

---

## ❌ Before — The Ungoverned Agent

```mermaid
flowchart TD
    User["User Request"]
    LLM["LLM\n(planning + reasoning)"]
    T1["Tool: send_email()"]
    T2["Tool: query_database()"]
    T3["Tool: call_external_api()"]
    Resp["Response\n(unaudited)"]

    User --> LLM
    LLM -->|"unbounded tool calls\nno hop limit\nno policy check"| T1
    LLM --> T2
    LLM --> T3
    T1 --> LLM
    T2 --> LLM
    T3 --> LLM
    LLM --> Resp

    style User fill:#1e1e2e,stroke:#585b70,color:#cdd6f4
    style LLM fill:#313244,stroke:#585b70,color:#cdd6f4
    style T1 fill:#3b1219,stroke:#f38ba8,color:#cdd6f4
    style T2 fill:#3b1219,stroke:#f38ba8,color:#cdd6f4
    style T3 fill:#3b1219,stroke:#f38ba8,color:#cdd6f4
    style Resp fill:#313244,stroke:#585b70,color:#cdd6f4
```

**What fails:**

- Infinite loops — no hop limit stops recursive tool calls
- No policy on tool calls — `send_email()` fires without approval
- No audit trail — you can't explain what the agent did
- No observability — failures are opaque
- State leaks across sessions with no boundary

---

## ✅ After — The Governed Agent

```mermaid
flowchart TD
    User["User Request"]

    subgraph Governance["🟣 L01 Governance"]
        POL["PolicyEngine\nsubject · resource · action rules"]
        PG["PolicyGateway\ntool_call stage"]
        AUDIT["Audit Trail\ndecision logging"]
    end

    subgraph Orchestration["🔵 L08 Orchestration"]
        AC["AgentCollaboration\nhop_limit=5\npolicy integration"]
        RT["Realtime\nsession lifecycle"]
    end

    subgraph Tools["🔵 L05 Tool Integration"]
        TR["ToolRegistry\ndeclarative definitions"]
        T1["send_email()\n→ REQUIRE_APPROVAL"]
        T2["query_database()\n→ ALLOW"]
        T3["call_external_api()\n→ SANITIZE params"]
    end

    subgraph Observability["🔵 L02 Observability"]
        OBS["ObservabilityService\nagent_span · tool_span\nper-hop tracing"]
    end

    User --> AC
    AC -->|"hop 1"| PG
    PG -->|"check: authorize_tool_call()"| POL
    POL --> AUDIT
    POL -->|"ALLOW"| T2
    POL -->|"REQUIRE_APPROVAL"| T1
    POL -->|"SANITIZE"| T3
    T1 & T2 & T3 -->|"results"| OBS
    OBS -->|"traces + audit"| AC
    AC -->|"hop limit enforced\nmax 5 iterations"| User

    style Governance fill:#1a0d2e,stroke:#cba6f7,color:#cdd6f4
    style Orchestration fill:#0d152e,stroke:#89b4fa,color:#cdd6f4
    style Tools fill:#0d152e,stroke:#89b4fa,color:#cdd6f4
    style Observability fill:#0d1a2e,stroke:#89dceb,color:#cdd6f4
```

**Key additions:**

| Component | What it prevents |
|-----------|-----------------|
| `AgentCollaboration` hop limit | Infinite recursion and runaway cost |
| `PolicyGateway` tool stage | Unauthorized tool invocations |
| `PolicyEngine` approval workflow | `send_email` firing without human confirmation |
| `Audit Trail` | Inability to explain agent decisions post-incident |
| `ObservabilityService` | Invisible tool calls — every hop is a traced span |
| `ToolRegistry` | Undocumented tool surfaces with no schema validation |

```python
from electripy.ai.agent_collaboration import AgentCollaborationService, CollaborationConfig
from electripy.ai.policy_gateway import PolicyGateway, PolicyStage

gateway = PolicyGateway(rules=tool_policy_rules)
svc = AgentCollaborationService(
    config=CollaborationConfig(max_hops=5, policy_gateway=gateway),
)

# Every tool call goes through the policy gateway.
# Every hop is a traced span. Hop limit enforced automatically.
result = svc.run(task=user_request, agents=[planner, executor, reviewer])
```
