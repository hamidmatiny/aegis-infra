# Daily allocations

Schedule-derived task / reserve / SI budgets. Written by `/daily-allocation`.

## 2026-09-16 (active allocation — free pool nominal)

**reserve_pct:** 20%  
**Provider ceiling note:** Token-budget reported no sustained OmniRoute 503/429 errors today. Free-pool RPD ceiling is stable; genuine surplus exists after task needs + 20% reserve. Self-improvement (SI) is **ACTIVE** (staggered, max 1 in flight fleet-wide).

| Agent | Tier | Enabled core schedules (UTC) | Task budget basis | Reserve (20%) | SI budget | SI window (UTC) | Notes |
|-------|------|------------------------------|-------------------|---------------|-----------|-----------------|-------|
| aegis-ceo | premium | Daily trajectory `0 8 * * *` | 1 daily review slot | n/a (sub) | when calendar free | after 09:00 review | Judged by Hamid |
| aegis-infra | free | usage Mon 08:00; token-budget + allocation | core infra jobs | 20% | active | 15:00 | Staggered SI active |
| aegis-threat-intel | free | Threat scan (enable) | 1× `/scan-threats` | 20% | active | 16:00 | Staggered SI active |
| aegis-analyst | free | Daily revenue `0 13 * * *` | 1× `/check-revenue` | 20% | active | 17:00 | Staggered SI active |
| aegis-core-infra | mid | Daily infra diff `0 7 * * *` | 1× `/review-infra-diff` | 20% | on CFP path if healthy | 07:30 after review | Mid-cost path |
| aegis-data-quality | free | Fleet output review (enable) | 1× `/review-fleet-outputs` | 20% | active | 18:00 | Staggered SI active |
| aegis-growth | free | Daily growth `0 14 * * *` + execution skills | check-growth + SEO/dir | 20% | active | 19:00 | Staggered SI active |

**Stampede rule today:** max 1 free-pool SI in flight fleet-wide; windows strictly staggered from 15:00 UTC to 19:00 UTC.

## 2026-10-08 (cool-pool floor — one SI slot)

OmniRoute `call_logs` for this UTC day, read before re-enabling schedules: 196×200, 0×429, 1×504. That is under the 40-error floor. No capacity hold is active. Arithmetic surplus is still 0 after task needs and the 20% reserve, so the cool-pool floor applies: **one** free-pool SI slot, not a fleet-wide surplus.

| Agent | si_budget today | Why |
|-------|-----------------|-----|
| aegis-analyst | 1 | Next unfired SI window is 17:00 UTC. This is the one slot. |
| aegis-infra, aegis-threat-intel | 0 | 15:00 and 16:00 windows already passed today. |
| aegis-data-quality, aegis-growth | 0 | Later windows stay off so only one SI runs. |
| aegis-ceo, aegis-redteam | 0 | Subscription agents. Not on the free-pool SI key. |
| aegis-core-infra, aegis-scout, aegis-product-eng, aegis-gateway, aegis-policy-engine, aegis-model-router, aegis-agent-gate, aegis-audit, the-brain | 0 | No SI schedule row exists. Not assigned a slot today. |

## STALENESS NOTE (2026-09-20)

The 2026-09-16 table above covers **7 agents only**. Live fleet is **15+** (`list_agents`: includes scout, product-eng, 5 PE ICs, redteam). Skills that assign SI/HOLD **must** regenerate from live `list_agents` each run — do not copy this table forward. Next `/daily-allocation` must list every non-system agent or mark N/A with reason.

