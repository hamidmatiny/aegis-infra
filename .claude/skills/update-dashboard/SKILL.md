---
name: update-dashboard
description: Refresh dashboard.yaml with current tier/cost metrics from memory files and OmniRoute
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-09-13
  author: aegis-infra
  changelog:
    - "1.1: Dedup — skip if this agent already completed /update-dashboard successfully in the last 90 minutes (overlapping schedule/retry waste)"
---

# Update Dashboard

Refresh `dashboard.yaml` with current metrics gathered from this agent's memory files and, where reachable, OmniRoute directly.

## Dedup gate (mandatory)

If `dashboard.yaml` `updated` timestamp (or a successful schedule execution) is within the last **90 minutes**, skip a full refresh: exit with a one-line note that the dashboard is already fresh. Fleet-wide: **only `aegis-infra`** should own the recurring `/update-dashboard` schedule; overlapping scout/agent schedules are waste.

## Process

### Step 1: Gather Metrics

Read the agent's data sources to collect current values:
- `memory/tier-assignments.md` — current fleet roster, tier per agent, provider/model
- **Agents Tracked comes only from `memory/fleet-roster.json`.** That file is written on the host from Trinity `agent_ownership` (non-system, `deleted_at` null) by `scripts/capacity-watch.py`. It is the full fleet. `list_agents` on this agent's key returns outbound A2A peers plus self, which has published counts as low as 7. Do not use `list_agents`, `get_fleet_health`, or `usage-log.md` for this number. If `fleet-roster.json` is missing, leave the previous dashboard count in place and say the roster file was missing. Exclude `trinity-system`. The count changes every hire.
- `memory/usage-log.md` — most recent rollup: agents tracked, anomalies flagged this week
- `memory/pricing-checks.md` (or the pricing section of `usage-log.md`) — when each provider was last checked, to compute "checks overdue"
- OmniRoute's own health endpoint, if `OMNIROUTE_API_URL` is set and reachable (a quick `curl -m 5`, not a full audit — that's `/audit-omniroute`'s job)
- Recent git activity: `git log --oneline -10`

### Step 2: Update Dashboard

Read `dashboard.yaml`, update widget values with fresh data:
- Update the `updated` timestamp to now
- "OmniRoute" status widget: green if the last `/audit-omniroute` found it fully configured and reachable, yellow if partially, red if unreachable/misconfigured, gray if never audited
- "Own Tier" metric: reflect this agent's actual current tier — flag visually (e.g. red) if it's ever not free-pool, since that would be this agent violating its own policy
- "Agents Tracked": the live count from Step 1, plus a Roster row for every live agent. An agent with no approved tier is "Pending", not omitted. "Anomalies This Week" may still come from the latest `usage-log.md` entry.
- "Pricing Checks Overdue": providers not re-checked in the review cadence set by the `/review-pricing` schedule
- "Agents by Tier" table from `memory/tier-assignments.md`
- "Recent Rollups & Reviews" list from the last few entries across memory files

Write the updated `dashboard.yaml`.

### Step 3: Publish a KPI snapshot report (Trinity)

If the `mcp__trinity__report` tool is available (i.e. running on Trinity), also publish the same headline numbers as a report so they accumulate as history alongside the live snapshot:

- `report_type`: `aegis_infra.kpi_snapshot`
- `display_hint`: `kpi`
- `payload`: `{ "tiles": [ {"label": "Agents Tracked", "value": "..."}, {"label": "Anomalies This Week", "value": "..."}, {"label": "OmniRoute Status", "value": "..."} ] }`

Skip this step silently if the tool isn't available — the dashboard refresh above still succeeds.

### Step 4: Confirm

Report what was updated:
```
Dashboard refreshed:
- OmniRoute status: [old] → [new]
- Agents tracked: [old] → [new]
- Last updated: [timestamp]
```

Note: On Trinity remote, the dashboard path is `/home/developer/dashboard.yaml`.

## Outputs

- Updated `dashboard.yaml` with current metrics
