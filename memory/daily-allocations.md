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

## STALENESS NOTE (2026-09-20)

The 2026-09-16 table above covers **7 agents only**. Live fleet is **15+** (`list_agents`: includes scout, product-eng, 5 PE ICs, redteam). Skills that assign SI/HOLD **must** regenerate from live `list_agents` each run — do not copy this table forward. Next `/daily-allocation` must list every non-system agent or mark N/A with reason.

