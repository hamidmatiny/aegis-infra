---
name: usage-log
description: Weekly token and cost usage rollup per agent
metadata:
  type: project
---

## Usage Rollup — 2026-09-21

| Agent | Tier | Metric (source) | This week | Last week | Δ |
|-------|------|------------------|-----------|-----------|---|
| aegis-ceo | premium | activity volume / subscription (Slack `#aegis-ceo`) | active (subscription) | active | 0% |
| aegis-infra | free-pool | executions & estimated cost (Trinity executions / OmniRoute gateway) | 45 executions logged (est. cost ~$8.20) | 30 executions | +50% |
| aegis-threat-intel | free-pool | planned polling capacity (OmniRoute free pool) | active polling / low usage | provisioned | N/A |
| aegis-analyst | free-pool | structured reports / JSON endpoint queries | active | N/A | N/A |
| aegis-data-quality | free-pool | data-quality sweeps | active | N/A | N/A |
| aegis-core-infra | mid-cost | container & migration reasoning | active | N/A | N/A |
| aegis-growth | **Unregistered / Unknown** | fleet presence without tier assignment | running (port 2239, container created 2026-09-15) | N/A | **NEW** |

**Anomalies flagged:** `aegis-growth` is present in the Trinity fleet (`port 2239`, container `ee506e4da610`) but lacks an approved tier assignment in `memory/tier-assignments.md`. Per CLAUDE.md rule ("Nobody else picks their own model"), this requires review and a tier proposal.
**Data gaps:** Precise token counts from OmniRoute require administrative dashboard metrics access; Trinity execution cost metadata uses Claude pricing estimates rather than actual Gemini free-tier pricing.
