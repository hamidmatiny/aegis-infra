# Capacity HOLD state

Written by `/capacity-hold`. Tracks which schedules `aegis-infra` actually paused so `/capacity-hold lift` can re-enable them without turning on schedules that were already off.

## Current status

**status:** `active` (fleet HOLD in force due to 1315 429s today)  
**authority:** `aegis-infra` (Protocol C — standing exception)  
**last_proof:** 2026-09-20T00:21Z — full apply→verify→lift on the schedules named in the 2026-09-18 advisory HOLD

Today’s UTC window recorded **1315 × 429 errors** (exceeding apply threshold ≥100). All HOLDable schedules across the fleet were verified already disabled (`enabled: false`), so 0 new schedules were paused. Core safety schedules (`Daily allocation`, `Daily token budget`) remain active.

## Proof (round-trip — real Trinity toggles)

| Step | Agent | Schedule | ID | API result | list_agent_schedules |
|------|-------|----------|-----|------------|----------------------|
| disable | aegis-analyst | Daily revenue check | `UWCxvqa1mUXuR9CyTOku0g` | `status: disabled` | `enabled: false` |
| disable | aegis-core-infra | Daily infra diff review | `RXU1OCwaiK8WaHQp-p-lCg` | `status: disabled` | `enabled: false` |
| disable | aegis-analyst | Self-improvement | `zdrXAwNmgEFesUFeRxOPkw` | `status: disabled` | `enabled: false` |
| disable | aegis-infra | Self-improvement | `Rx4yPoZTIUYpmCe0-8g0jQ` | `status: disabled` | (self) |
| lift | same four | — | — | all `status: enabled` | revenue + infra-diff + SI restored `enabled: true` |

Tool: `mcp__trinity__toggle_agent_schedule`. A2A edges `aegis-infra` → HOLD targets granted 2026-09-19 so agent-scoped runs can toggle.

## Paused under active HOLD

*(all HOLDable schedules verified `enabled: false` across fleet; 0 newly toggled)*

## History

| When | Action | Notes |
|------|--------|-------|
| 2026-09-18 | Advisory Slack HOLD only | **No toggles** — schedules kept firing |
| 2026-09-20 | Protocol C + `/capacity-hold` + permission grants + proof apply/lift | Real teeth; fleet left **unpaused** (429s below apply threshold at proof time) |
| 2026-09-25 | `/capacity-hold apply` triggered by 1315 × 429s | HOLD activated; all HOLDable schedules already verified `enabled: false` |
