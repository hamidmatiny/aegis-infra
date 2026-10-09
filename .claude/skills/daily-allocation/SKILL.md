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

First run `python3 scripts/allocation_inputs.py`. It prints the full roster (`roster`, `roster_count`, from `memory/fleet-roster.json`, which the host writes from Trinity `agent_ownership` every minute) and today's SI gate (`si`: `open` / `deferred`, from the capacity watcher's own 429 rule). Use those values; do not recompute them. If it exits 1, the `problems` list says which input is missing or stale. Report that and stop; do not fall back to `list_agents`, which on this agent's key returns only outbound A2A peers (it returned 7 on 2026-10-09 when the fleet had 16).

For each agent in `roster` (plus `memory/tier-assignments.md` for tier):

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

**Cool-pool floor (2026-10-08; gate fixed 2026-10-09).** If `allocation_inputs.py` reports `si: open`, set `si_budget` to at least 1 for **one** free-pool agent (from `free_pool_si_candidates`): the next unfired SI window. Every other agent's `si_budget` stays 0 that day. This is one bounded run, not a surplus for the whole fleet. If it reports `si: deferred`, the floor is 0 and SI stays deferred; quote `si_reason`.

The SI gate is the capacity watcher's rule: **429 only** (daily 429 >= 100, or 40 x 429 inside 10 minutes) or an active hold. **503 and 504 never defer SI.** They are upstream noise (provider "high demand", local queue expiry). Report `status_counts_today` for 503/504 as information only. On 2026-10-09 this skill counted 530 errors across 429/503/504 and zeroed SI for the whole fleet; that was wrong.

**Who owns whether improvement runs (Hamid, 2026-10-08).** `aegis-infra` is accountable for whether a self-improvement slot runs. The duties are:

1. Set the one-slot cool-pool SI budget (the floor above). While a capacity hold is active, the floor is 0 and SI schedules stay disarmed. Paid headroom is separate: one nightly batch on the Claude subscription, sized to the measured idle window, covering several agents. That batch does not run during Hamid's working hours, stops on a session-limit signal, and yields to aegis-ceo and aegis-redteam.
2. Keep the existing SI schedules armed when the hold is lifted by the normal lift rule. Do not force-lift to make a slot run.
3. Report each week which agent got the slot and which agents still have no SI schedule.

`aegis-scout` still chooses what to learn from the live roster. `aegis-ceo` still approves or rejects the skill change. `the-brain` still records levels. This duty is not a hire and not a new authority over credentials, tiers, or Track A.

### Step 3: Assign self-improvement (when surplus exists)

- Pick one skill improvement candidate (prefer open gaps from `memory/skill-proposals.md`).
- Require a real before/after comparison plan (same discipline as the skill-adoption experiment).
- **Judgment:** the agent's manager grades with evidence — never self-graded. Specialists → `aegis-ceo`; `aegis-ceo` → Hamid.
- Write the day's SI assignment into `memory/daily-allocations.md`.

### Step 4: Stampede controls (mandatory)

Shared free Gemini key failure mode: concurrent agents → 429 stampede.

Rules:

1. At most **one** free-pool self-improvement run in flight fleet-wide.
2. Stagger SI windows by agent (UTC). **Build the stagger list every run from `free_pool_si_candidates`** in `allocation_inputs.py` (full roster minus subscription agents). Do not freeze an example list and never write a fixed agent count. Example spacing (+60 min): assign free-pool agents in name-sort order starting 15:00 UTC; mid-cost OmniRoute agents on a separate CFP path when available. Example (illustrative only — regenerate from live roster):
   - free-pool: infra 15:00 · threat-intel 16:00 · analyst 17:00 · data-quality 18:00 · growth 19:00 · scout / redteam / others continue +1h
3. Core scheduled jobs also stagger where crons would collide on the minute — prefer existing template crons; if two fire same minute, offset one by +5–10 minutes via schedule update and log it.
4. Before starting SI, run `python3 scripts/allocation_inputs.py`: if `si` is `deferred`, **defer SI** and spend only task+reserve. 503/504 alone never defer SI.
5. **Live SI schedule gate (enforced in schedule message + here):** SI slots must check spare capacity **before** any skill edit. If `si_budget` for today is 0, SI was deferred in `memory/daily-allocations.md`, or the capacity watcher reports a 429 trip (`si: deferred` in `memory/capacity-state.json`), the agent replies `NONE (no surplus capacity)` and exits — schedules still fire, but must not burn capacity. Stagger alone is not a capacity check.
6. **Coverage check:** after writing `memory/daily-allocations.md`, assert every agent in `roster` from `allocation_inputs.py` appears in the table (`roster_count` rows) (or is explicitly marked N/A with reason, e.g. premium CEO). If any hire is missing, that is a bug — fix before Slack close-out.

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
