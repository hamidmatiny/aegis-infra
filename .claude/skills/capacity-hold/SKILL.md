---
name: capacity-hold
description: Apply or lift a capacity HOLD by actually toggling Trinity schedules (not advisory Slack). Use when /token-budget or /daily-allocation finds sustained free-pool exhaustion, or when capacity recovers.
allowed-tools: Bash, Read, Write, mcp__trinity__list_agent_schedules, mcp__trinity__toggle_agent_schedule, mcp__trinity__list_channel_groups, mcp__trinity__send_group_message, mcp__trinity__chat_with_agent, mcp__trinity__report
user-invocable: true
disable-model-invocation: false
metadata:
  version: "1.0"
  created: 2026-09-19
  author: aegis-infra
  changelog:
    - "1.0: Real toggle teeth for capacity HOLD/lift; infra-owned standing exception"
---

# Capacity HOLD

## Purpose

When free-pool capacity is genuinely exhausted, **pause** named autonomous schedules via `mcp__trinity__toggle_agent_schedule` — do not stop at Slack advice. When capacity recovers, **re-enable** only the schedules this skill previously paused (tracked in `memory/capacity-hold.md`).

## Authority (standing exception)

**`aegis-infra` acts directly** — judges capacity (already owns `/token-budget` / `/daily-allocation`) and calls `toggle_agent_schedule` on the named targets. CEO is **notified after**, not a gate before. Rationale: requiring manager approval for the pause recreated the 2026-09-18 failure mode (advisory HOLD, schedules kept firing).

Documented in `docs/a2a-routing.md` § Protocol C. Narrow A2A edges `aegis-infra` → HOLD-target specialists exist solely so agent-scoped keys can toggle those agents' schedules (same permission surface as list/toggle read access).

## Modes

| Arg / ask | Action |
|-----------|--------|
| `apply` / HOLD | Disable HOLDable schedules that are currently enabled; record them |
| `lift` / recover | Re-enable only schedules listed under the active HOLD |
| `status` | Report `memory/capacity-hold.md` + live enabled flags for tracked IDs |

## HOLD threshold (reuse existing judgment — do not invent a second detector)

Apply HOLD when **any** of these is true from a fresh `/token-budget` (or same-run query of live OmniRoute `call_logs`):

1. Today's Gemini-family **429 count ≥ 100**, **or**
2. Sustained exhaustion language already in today's token-budget verdict (e.g. "exhausted / rate-limited today", "HOLD autonomous tasks"), **or**
3. Operator/`aegis-ceo`/Hamid explicitly orders a capacity HOLD

Lift HOLD when **all** are true:

1. An active HOLD exists in `memory/capacity-hold.md`
2. Today's 429 count is **&lt; 40** (cool-down band — not zero; free pool is noisy)
3. Last 2 hours are not dominated by 429/503 on shared free keys (spot-check `call_logs`)

If threshold is ambiguous → do **not** apply or lift; Slack the ambiguity and stop (Protocol B to CEO only if you cannot decide).

## HOLDable schedule set (names — resolve live IDs each run)

Pause these when **enabled**. Skip if already disabled (do not claim credit).

| Agent | Schedule name (exact or contains) |
|-------|-----------------------------------|
| `aegis-analyst` | Daily revenue check; Self-improvement |
| `aegis-core-infra` | Daily infra diff review |
| `aegis-threat-intel` | Threat scan; Self-improvement |
| `aegis-redteam` | Live gateway attack batch; Self-improvement |
| `aegis-data-quality` | Fleet output review; Self-improvement |
| `aegis-growth` | Daily growth check; Self-improvement; Weekly SEO draft; Weekly directory pass |
| `aegis-scout` | Fleet capability scout; Founder learning; Self-improvement |
| `aegis-product-eng` | Self-improvement; Dashboard refresh |
| `aegis-gateway` | Self-improvement |
| `aegis-policy-engine` | Self-improvement |
| `aegis-model-router` | Self-improvement |
| `aegis-agent-gate` | Self-improvement |
| `aegis-audit` | Self-improvement |
| `aegis-infra` | Self-improvement (staggered); Dashboard refresh |

Resolve the **live** schedule list each run via `list_agent_schedules` for **every** agent returned by `list_agents` (minus `trinity-system`). The table above is a hint — if a free-pool/mid-cost agent has an autonomous schedule not listed, include it.

**Never pause** (capacity sensing + recovery path):

- `aegis-infra` Daily token budget
- `aegis-infra` Daily allocation
- Premium CEO schedules (not free-pool burners)

Refresh IDs with `list_agent_schedules` every run — do not hardcode IDs in the skill body beyond `memory/capacity-hold.md` for the active HOLD.

## Process — apply

1. Confirm threshold (cite real 429 count / token-budget line).
2. If `memory/capacity-hold.md` already has `status: active`, skip re-apply unless new enabled HOLDable schedules appeared — then pause only the new ones and append.
3. For each HOLDable row: `list_agent_schedules` → if `enabled: true` and name matches → `toggle_agent_schedule(enabled=false)`.
4. Record each successful toggle: agent, schedule_id, schedule_name, `was_enabled: true`, `disabled_at` UTC.
5. Write `memory/capacity-hold.md` with `status: active`, evidence, and the paused list.
6. Notify `aegis-ceo` via `chat_with_agent` (one short message: HOLD active + count paused + evidence). Slack `#aegis-infra`. Optional Trinity report `aegis_infra.capacity_hold`.
7. Fail closed: if a toggle returns Access denied, record it, continue others, escalate the miss to CEO/Hamid.

## Process — lift

1. Confirm lift threshold with fresh numbers.
2. Read active HOLD list from `memory/capacity-hold.md`.
3. For each recorded schedule: `toggle_agent_schedule(enabled=true)` only if we paused it (do not enable schedules that were already off before the HOLD).
4. Verify with `list_agent_schedules` that each re-enabled row shows `enabled: true`.
5. Set `status: lifted`, `lifted_at`, evidence; keep history (append, do not delete).
6. Notify CEO + Slack.

## Test / proof (required when changing this skill)

Round-trip on one real schedule: disable → confirm `enabled: false` → enable → confirm `enabled: true`. Log the schedule_id and timestamps in `memory/capacity-hold.md` under `## Proof`.

## Final step — Slack close-out

Mandatory `#aegis-infra` close-out. No commit trailers.
