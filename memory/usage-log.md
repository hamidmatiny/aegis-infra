---
name: usage-log
description: Weekly token and cost usage rollup per agent
metadata:
  type: project
---

## Usage Rollup — 2026-09-13

| Agent | Tier | Metric (source) | This week | Last week | Δ |
|-------|------|------------------|-----------|-----------|---|
| aegis-ceo | premium | activity volume / subscription (Slack `#aegis-ceo`) | active (subscription) | N/A (baseline) | N/A |
| aegis-infra | free-pool | executions & estimated cost (Trinity executions / OmniRoute gateway) | 30 total executions logged (est. runtime cost ~$12.50; note: Trinity cost metadata estimates Claude pricing even when running on Gemini via OmniRoute) | Baseline | 0% |
| Threat Intel Analyst | free-pool | planned polling capacity (OmniRoute free pool) | provisioned / approved (0 runs yet) | N/A | N/A |

**Anomalies flagged:** None this week.
**Data gaps:** Precise token counts from OmniRoute require administrative dashboard metrics access; Trinity execution cost metadata uses Claude pricing estimates rather than actual Gemini free-tier pricing.
