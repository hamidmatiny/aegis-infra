# Capacity HOLD state

Written by `/capacity-hold`. Tracks which schedules `aegis-infra` actually paused so `/capacity-hold lift` can re-enable them without turning on schedules that were already off.

## Current status

**status:** `active` (host watcher applied 2026-09-23T16:34:41Z)  
**authority:** host `scripts/capacity-watch.py` (Protocol C). Not the 07:00 LLM check.  
**last_proof:** 2026-09-23T16:34Z — replay of today's `call_logs` trips at 14:07:21Z (`burst_40_in_10m`); live `--apply` disabled 19 HOLDable schedules (`still_enabled_after` empty). `aegis-redteam` Live gateway attack batch left enabled. Daily token budget and Daily allocation left enabled.

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

*(empty — last proof lifted)*

## History

| When | Action | Notes |
|------|--------|-------|
| 2026-09-18 | Advisory Slack HOLD only | **No toggles** — schedules kept firing |
| 2026-09-20 | Protocol C + `/capacity-hold` + permission grants + proof apply/lift | Real teeth; fleet left **unpaused** (429s below apply threshold at proof time) |
| 2026-09-23T16:34Z | Host watcher apply | 19 schedules disabled. Replay trip 14:07:21Z. Redteam attack batch and the two infra recovery schedules left on. |
