---
name: track-usage
description: Weekly token/cost usage rollup per agent, using real figures — flags anomalies to the CEO instead of assuming everything is fine
allowed-tools: Read, Write, Bash, mcp__trinity__list_agents, mcp__trinity__get_agent, mcp__trinity__list_recent_executions, mcp__trinity__get_agent_activity_summary, mcp__trinity__report
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-09-13
  author: aegis-infra
---

# Track Usage

## Purpose

Produce a real, numbers-based weekly rollup of token/cost usage per agent in the company, and flag anything unusual to `aegis-ceo`. "Numbers over vibes" — if real data isn't available for some slice, say so explicitly rather than estimating confidently.

## Process

### Step 1: Confirm what data is actually reachable

This skill has two possible data sources, and either or both may be available depending on deployment state:

- **Trinity's own execution/cost data** (when this agent is deployed on Trinity and has the `mcp__trinity__*` tools): `list_agents` for the current fleet roster, `list_recent_executions` / `get_agent_activity_summary` per agent for cost and execution counts over the window.
- **OmniRoute's own usage/cost logs** (for agents routed through it, not on subscription auth): reachable only if `OMNIROUTE_API_URL` is set and `/audit-omniroute` has confirmed it's live — check `memory/tier-assignments.md` for which agents are actually routed through OmniRoute before assuming this source covers them.

If neither is reachable, say so plainly and stop rather than fabricate figures — this is exactly the "don't just assume everything is fine" case CLAUDE.md warns about.

### Step 2: Pull real figures

For each known agent (cross-reference `memory/tier-assignments.md` for the current fleet roster and each agent's tier):

- Premium-tier agents: Trinity execution counts are available; a literal dollar cost against Hamid's subscription generally isn't (it's a flat human subscription, not metered) — report activity volume, not a fabricated dollar figure, unless a real cost measure exists.
- Mid-cost / free-pool agents: pull cost and token figures from whichever source (Trinity execution rows carry `cost`/`context_used` when available; OmniRoute's own logs otherwise).

Cite the source for every number in the output — "from `list_recent_executions`, last 7 days" or "from OmniRoute usage log" — never present a number without saying where it came from.

### Step 3: Compare against the prior rollup

Read the last entry in `memory/usage-log.md` (if any). Compute week-over-week change per agent. A rollup with no prior entry is a baseline, not an anomaly.

### Step 4: Flag anomalies, don't just report totals

An anomaly is a real signal, not a normal range for a genuinely noisy agent. Flag things like:

- A free-pool agent suddenly generating mid-cost-scale usage (may mean the free tier silently stopped applying, or the agent is looping)
- A large week-over-week jump in cost with no corresponding change in what the agent is supposed to be doing
- This agent (`aegis-infra` itself) trending toward premium-tier-scale usage — per CLAUDE.md, that's worth flagging as unusual on its own

For each flag, state what's odd and what you'd want to know next — don't diagnose the cause with confidence you don't have.

### Step 5: Record and report

Append this week's rollup to `memory/usage-log.md`:

```
## Usage Rollup — [date]

| Agent | Tier | Metric (source) | This week | Last week | Δ |
|-------|------|------------------|-----------|-----------|---|
| aegis-ceo | premium | executions (Trinity) | ... | ... | ... |
| aegis-infra | free-pool | tokens/cost (OmniRoute) | ... | ... | ... |

**Anomalies flagged:** [list, or "none this week"]
**Data gaps:** [any agent/tier this rollup couldn't measure, and why]
```

If running on Trinity and `mcp__trinity__report` is available, publish the table as `report_type: aegis_infra.usage_weekly`, `display_hint: table` (or `kpi` for a headline-only version). Skip silently if the tool isn't available — the memory file is still the durable record either way.

### Step 6: Escalate real anomalies

An anomaly worth acting on (not just noting) goes to `aegis-ceo` directly — not silently absorbed into next week's baseline. This skill reports and flags; it does not decide to cut an agent's access (that's an explicit escalation per CLAUDE.md's operating rules).

## Outputs

- An updated `memory/usage-log.md` with this week's figures and any flags
- Optionally, a published Trinity report
- A direct flag to the CEO for anything that looks like a real problem, not just a data point
