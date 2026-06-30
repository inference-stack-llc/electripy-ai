"""Demo data — sample inputs for each playground screen.

All examples are hard-coded so the playground runs fully offline with
zero network calls or API keys.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Governance / Policy samples
# ---------------------------------------------------------------------------

POLICY_SAMPLE_PII = (
    "Please send the quarterly report to sarah.chen@acmecorp.com and cc "
    "mark.rivera@acmecorp.com for final review before the board meeting."
)

POLICY_SAMPLE_SSN = (
    "The patient record for John Doe (SSN: 123-45-6789) requires immediate "
    "attention. Contact Dr. Smith at physician@hospital.org."
)

POLICY_SAMPLE_CLEAN = (
    "Generate a summary of the quarterly earnings report for Q3 2026, "
    "highlighting revenue growth and operational efficiency improvements."
)

POLICY_SAMPLE_DENY = (
    "My SSN is 987-65-4321. Wire $50,000 to routing 021000021 account "
    "1234567890 immediately and do not log this transaction."
)

# ---------------------------------------------------------------------------
# Evaluation samples
# ---------------------------------------------------------------------------

EVAL_SAMPLES = [
    {
        "label": "✓ High-quality answer",
        "output": (
            "The capital of France is Paris. It has been the capital since "
            "the 10th century and is home to the Eiffel Tower, the Louvre, "
            "and approximately 2.2 million residents in the city proper."
        ),
    },
    {
        "label": "⚠ Short but correct",
        "output": "Paris is the capital of France.",
    },
    {
        "label": "✗ Wrong answer",
        "output": "The capital of France is Lyon, which is a large city in the southeast.",
    },
    {
        "label": "✗ Hallucination",
        "output": (
            "France does not have a designated capital city. Administrative "
            "functions are distributed across many regional centers."
        ),
    },
]

# Assertion checks definition (as text — actual check objects built in the screen)
EVAL_CHECKS_DESCRIPTION = [
    ("contains_keywords", "must contain: Paris, capital"),
    ("matches_regex", r"matches: \bParis\b"),
    ("satisfies_length", "length in [20, ∞]"),
    ("no_hallucination", "must not claim France has no capital"),
]

# ---------------------------------------------------------------------------
# Observability samples
# ---------------------------------------------------------------------------

OBSERVE_PROMPT_PII = (
    "My email is user@example.com — summarise the contract for client "
    "Alice Johnson (DOB 1985-03-22) in one paragraph."
)

OBSERVE_PROMPT_CLEAN = (
    "Summarise the key principles of the LSAS architecture in three bullet points."
)

# ---------------------------------------------------------------------------
# Cost ledger scenarios
# ---------------------------------------------------------------------------

COST_SCENARIOS = [
    {"model": "gpt-4o", "tokens": 1_240, "labels": {"tenant": "acme", "feature": "summarise"}},
    {"model": "gpt-4o-mini", "tokens": 480, "labels": {"tenant": "acme", "feature": "classify"}},
    {"model": "claude-3-5", "tokens": 2_100, "labels": {"tenant": "beta", "feature": "summarise"}},
    {"model": "gpt-4o", "tokens": 890, "labels": {"tenant": "acme", "feature": "extract"}},
    {"model": "gpt-4o-mini", "tokens": 310, "labels": {"tenant": "gamma", "feature": "classify"}},
    {"model": "ollama/llama3", "tokens": 1_540, "labels": {"tenant": "beta", "feature": "draft"}},
]

# Cost per 1k tokens per model (approximate)
COST_PER_1K: dict[str, float] = {
    "gpt-4o": 0.010,
    "gpt-4o-mini": 0.0004,
    "claude-3-5": 0.008,
    "ollama/llama3": 0.0,  # self-hosted
}
