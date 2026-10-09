---
name: reserve-utilization
description: Reserve utilization logs
metadata:
  type: project
---

# Reserve utilization

Weekly: how often the emergency reserve was actually touched, and by how much. Feeds autonomous `reserve_pct` adjustments in `/daily-allocation`.

## Week of 2026-09-21

| Agent | Days reserve touched | Peak touch (% of reserve) | Notes |
|-------|----------------------|---------------------------|-------|
| aegis-infra | 0 | 0% | Task budgets adequate; rate-limit precautions handled via SI deferral rather than reserve exhaustion. |
| aegis-threat-intel | 0 | 0% | |
| aegis-analyst | 0 | 0% | |
| aegis-core-infra | 0 | 0% | |
| aegis-data-quality | 0 | 0% | |
| aegis-growth | 0 | 0% | |

**Decision:** keep `reserve_pct` at 20% for another week given active free-pool 429/503 rates.
