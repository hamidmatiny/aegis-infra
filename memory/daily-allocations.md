# Daily allocations

Schedule-derived task / reserve / SI budgets. Written by `/daily-allocation`.

## 2026-09-15 (first allocation — post policy create)

**reserve_pct:** 20%  
**Provider ceiling note:** Gemini free tier is rate-limit-only; shared key already 429-heavy today → SI deferred fleet-wide for remainder of UTC day; task jobs only, staggered.

| Agent | Tier | Enabled core schedules (UTC) | Task budget basis | Reserve (20%) | SI budget | SI window (UTC) | Notes |
|-------|------|------------------------------|-------------------|---------------|-----------|-----------------|-------|
| aegis-ceo | premium | Daily trajectory `0 8 * * *` | 1 daily review slot | n/a (sub) | when calendar free | after 09:00 review | Judged by Hamid |
| aegis-infra | free | usage Mon 08:00; token-budget + allocation (new) | core infra jobs | 20% | deferred today | 15:00 | Stampede day |
| aegis-threat-intel | free | Threat scan (enable) | 1× `/scan-threats` | 20% | deferred | 16:00 | |
| aegis-analyst | free | Daily revenue `0 13 * * *` | 1× `/check-revenue` | 20% | deferred | 17:00 | |
| aegis-core-infra | mid | Daily infra diff `0 7 * * *` | 1× `/review-infra-diff` | 20% | on CFP path if healthy | 07:30 after review | Prefer CFP not Gemini flash |
| aegis-data-quality | free | Fleet output review (enable) | 1× `/review-fleet-outputs` | 20% | deferred | 18:00 | |
| aegis-growth | free | Daily growth `0 14 * * *` + execution skills | check-growth + SEO/dir when scheduled | 20% | deferred | 19:00 | |

**Stampede rule today:** max 1 free-pool SI in flight; **SI = 0 until `/token-budget` shows Gemini without sustained 429s.**
