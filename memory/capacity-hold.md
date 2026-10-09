# Capacity HOLD state

Written by `/capacity-hold`. Tracks which schedules `aegis-infra` actually paused so `/capacity-hold lift` can re-enable them without turning on schedules that were already off.

## Current status

**status:** `lifted` (host watcher lifted 2026-10-09T00:00:41Z under the normal lift rule: daily_429=0, errors_2h=0)  
**authority:** host `scripts/capacity-watch.py` (Protocol C), every 60 s. Not the 07:00 LLM check. State file: `~/Library/Application Support/aegis-capacity-watch/state.json` on the Mac.  
**last lift:** 19 HOLDable schedules re-enabled, each HTTP 200. Trip rule is 429 only (daily 429 >= 100, or 40 x 429 in 10 min); 503/504 count only toward the 2-hour lift guard.

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
| 2026-09-23T16:34Z | Host watcher apply | 19 schedules disabled. Replay trip 14:07:21Z. Redteam attack batch and the two infra recovery schedules left on. |
