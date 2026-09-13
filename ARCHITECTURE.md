# AEGIS Infra Architecture (Current State)

**What this is:** the agent as it actually runs today. For where it's deliberately headed, see the companion **`TARGET-ARCHITECTURE.md`**. When a target ships, it moves *out* of that doc and *into* this one.

**Last updated:** 2026-09-13

## Overview

AEGIS Infra is a Trinity-compatible Claude Code agent with four purpose-built skills covering the full core mission (OmniRoute audit, tier proposal, usage tracking, pricing review), plus the standard onboarding/dashboard/doc-reconciliation trio every agent in this fleet ships with. It holds no live write access to OmniRoute or to other agents' configs by default — every skill that changes something outside its own memory files stops short and asks for approval.

## Components

### Skills

- `/audit-omniroute` — read-only ground-truth check of OmniRoute's actual install/config state
- `/propose-agent-tier` — decides and proposes (never applies) a tier + model for an agent
- `/track-usage` — weekly cost/usage rollup, pulling from Trinity execution data and/or OmniRoute logs
- `/review-pricing` — periodic external check of provider pricing/free-tier pages
- `/onboarding` — setup progress tracker
- `/update-dashboard` — refreshes `dashboard.yaml` from memory files
- `/reconcile-docs` — checks CLAUDE.md, README, ARCHITECTURE docs, and skills stay mutually consistent

### Subagents

None yet.

### Data & State

- `onboarding.json` — setup progress
- `dashboard.yaml` — live fleet cost/tier snapshot
- `memory/tier-assignments.md` — running record of proposed and approved tier/model assignments (created by first `/propose-agent-tier` run)
- `memory/usage-log.md` — weekly usage rollups (created by first `/track-usage` run)
- `memory/pricing-checks.md` — provider pricing check history (created by first `/review-pricing` run, or folded into `usage-log.md`)

### Schedules

Declared in `template.yaml`, all shipped `enabled: false` pending explicit approval:

- Weekly usage rollup (`/track-usage`)
- Pricing & free-tier re-check, every 2 weeks (`/review-pricing`)
- Dashboard refresh, every 6 hours (`/update-dashboard`)
- Doc reconciliation, weekly (`/reconcile-docs`)

## Trinity Integration

Resources: 1 CPU / 2g memory (deliberately modest — this agent should be one of the cheapest in the fleet to run, per its own operating rule). Declared plugins: `agent-dev`, `trinity`, `utilities`. Declared credentials: `OMNIROUTE_API_URL` (required), `OMNIROUTE_API_KEY` (optional, only if the OmniRoute instance requires auth). No MCP servers of its own — `.mcp.json.template` is empty; it uses Trinity's own injected `trinity` MCP tools (`list_agents`, `list_recent_executions`, `get_agent_activity_summary`, `report`) once deployed.

This agent's own tier, per its policy, is **free-pool** — it should not be deployed on Hamid's Claude Pro subscription once OmniRoute's free tier is confirmed working.
