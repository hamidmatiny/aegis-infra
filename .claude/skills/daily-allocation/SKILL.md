---
name: daily-allocation
description: Compute each agent's real daily token allocation from Trinity schedules/workload, apply the emergency reserve, assign surplus to manager-judged self-improvement, and enforce stampede-aware staggering. Use for daily budget planning or reserve adjustments.
allowed-tools: Bash, Read, Write, mcp__trinity__list_agents, mcp__trinity__list_recent_executions, mcp__trinity__list_channel_groups, mcp__trinity__send_group_message, mcp__trinity__report, mcp__trinity__chat_with_agent
user-invocable: true
disable-model-invocation: false
metadata:
  version: "1.0"
  created: 2026-09-15
  author: aegis-infra
  changelog:
    - "1.1: Pull free-pool ceiling from live OmniRoute SQLite mount (same path resolution as /token-budget Step 0)"
    - "1.0: Initial — schedule-derived allocation, 20% reserve (infra-owned), surplus→SI, stampede stagger"
---

# Daily Allocation

## Purpose

Turn real Trinity schedule/workload data into a per-agent daily token/request allocation with:

1. **Task budget** — enough for today's scheduled core jobs
2. **Emergency reserve** — percentage held back (starts at 20%; this agent owns adjustments)
3. **Self-improvement surplus** — anything left after task+reserve must fund a real before/after skill experiment (manager-judged, never self-graded)
4. **Rate-limit awareness** — stagger SI so shared free-tier keys do not stampede (429 under concurrent load)

## Reserve policy (infra-owned)

- **Current default:** 20% of each agent's daily allocation held as emergency buffer (conservative; no long history yet; 2026-09-15 shared Gemini key hit concurrent 429s).
- **Owner:** `aegis-infra` adjusts this percentage autonomously from weekly reserve-utilization evidence.
- **Adjustment rule:** weekly, read `memory/reserve-utilization.md`. If reserve is consistently unused → lower a few points. If agents keep exhausting reserve → raise. Each change: post to Slack `#aegis-infra` with old %, new %, and the trend that justified it. **No separate Hamid approval** (low-risk, reversible).
- Record every change in `memory/reserve-policy.md`.

## Process

### Step 0: Live OmniRoute SQLite (shared with /token-budget)

Before budgeting against free-pool RPD ceilings, resolve the **live** OmniRoute DB the same way `/token-budget` does — prefer `$HOME/.omniroute/storage.sqlite` (host bind mount via `scripts/mount-omniroute-sqlite.sh`), never a one-time `memory/` copy. If only `memory/omniroute-storage.sqlite` exists, label the allocation **STALE RISK** and say to re-run the mount script. Cite the path used.

### Step 1: Pull real workload (not a guess)

For each fleet agent (from `list_agents` + `memory/tier-assignments.md`):

1. List enabled schedules (Trinity API or MCP) — cron + message/skill.
2. Estimate today's expected runs from cron (UTC).
3. If prior execution history exists (`list_recent_executions`), use median tokens/context from recent successful runs of that skill as the unit cost. If no history: use a documented placeholder unit cost labeled **estimate pending history**, and prefer request-count budgeting on free pool (RPD) over fake token precision.

Premium (`aegis-ceo`): allocation is activity slots against subscription capacity, not OmniRoute tokens — still reserve calendar time for SI when surplus capacity exists.

### Step 2: Compute allocation

```
daily_pool_unit = sum(expected_runs × unit_cost)   # from Step 1
reserve_pct     = current value from memory/reserve-policy.md  # default 0.20
reserve         = daily_pool_unit × reserve_pct
task_budget     = daily_pool_unit                  # scheduled work
# If the shared free-pool RPD ceiling (from /token-budget) is smaller than
# sum(task+reserve) across agents, scale all agents down proportionally and
# say so — do not pretend the ceiling is larger than it is.
allocatable    = min(fair_share_of_provider_ceiling, task_budget / (1 - reserve_pct))
task_spend_cap = allocatable × (1 - reserve_pct)
reserve_hold   = allocatable × reserve_pct
si_budget      = max(0, fair_share_of_provider_ceiling - allocatable)
```

Interpret `si_budget`: surplus beyond task needs + reserve **must** go to self-improvement when > 0. If ceiling is tight and si_budget is 0, say so — no fake SI mandate that would burn the reserve.

### Step 3: Assign self-improvement (when surplus exists)

- Pick one skill improvement candidate (prefer open gaps from `memory/skill-proposals.md`).
- Require a real before/after comparison plan (same discipline as the skill-adoption experiment).
- **Judgment:** the agent's manager grades with evidence — never self-graded. Specialists → `aegis-ceo`; `aegis-ceo` → Hamid.
- Write the day's SI assignment into `memory/daily-allocations.md`.

### Step 4: Stampede controls (mandatory)

Shared free Gemini key failure mode: concurrent agents → 429 stampede.

Rules:

1. At most **one** free-pool self-improvement run in flight fleet-wide.
2. Stagger SI windows by agent (UTC), e.g.:
   - `aegis-infra` 15:00 · `aegis-threat-intel` 16:00 · `aegis-analyst` 17:00 · `aegis-data-quality` 18:00 · `aegis-growth` 19:00 · mid-cost SI on separate CFP path when available
3. Core scheduled jobs also stagger where crons would collide on the minute — prefer existing template crons; if two fire same minute, offset one by +5–10 minutes via schedule update and log it.
4. Before starting SI, run `/token-budget` (or read today's log): if Gemini family already showing sustained 429s, **defer SI** and spend only task+reserve.

### Step 5: Persist, report, Slack

Update:

- `memory/daily-allocations.md` — today's table
- `memory/reserve-utilization.md` — whether reserve was touched (and by how much) when known

Slack `#aegis-infra` with the allocation table + any reserve-policy change. Optional Trinity report `aegis_infra.daily_allocation`.

When the SI assignment message (or any Slack close-out) is posted — by this agent or by the specialist running the SI slot — obey **CLAUDE.md HARD GATE — Slack / chat text hygiene**: no `Co-Authored-By` / `Generated with Claude Code` / commit trailers. SI is an explicit covered path.

## Outputs

- Per-agent task / reserve / SI budgets for today
- Stagger plan
- Updated memory files + Slack close-out
---

## Final step — Slack completed-task close-out (mandatory)

Post a real close-out to `#aegis-infra`.
