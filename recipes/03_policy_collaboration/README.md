# Recipe: Policy Gateway + Agent Collaboration Runtime

This offline recipe demonstrates a full flow using **ElectriPy AI** governance and orchestration layers:

- policy preflight/postflight checks
- LLM gateway request/response hooks
- bounded agent collaboration runtime
- in-memory telemetry capture

This exercises Governance (Layer 01), Observability (Layer 02), and Orchestration (Layer 08) of the LSAS Architecture.

## Run

```bash
python recipes/03_policy_collaboration/run_demo.py
```

## What to look for

- prompt sanitization is applied before the fake LLM call
- postflight policy checks run before the result is used downstream
- collaboration completes deterministically with bounded hops
- telemetry events are emitted for policy decisions
