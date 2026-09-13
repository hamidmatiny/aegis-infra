# AEGIS Infra Architecture (Current State)

**What this is:** the agent as it actually runs today. For where it's deliberately headed, see the companion **`TARGET-ARCHITECTURE.md`**. When a target ships, it moves *out* of that doc and *into* this one.

**Last updated:** 2026-09-13

## Overview

AEGIS Infra is a Trinity-compatible Claude Code agent with purpose-built skills covering the core mission (OmniRoute audit, tier proposal, skill/capability upgrade proposals, revenue-claim verification pilot, usage tracking, pricing review), plus the standard onboarding/dashboard/doc-reconciliation trio. It holds no live write access to OmniRoute or to other agents' configs by default — every skill that changes something outside its own memory files stops short and asks for approval. Skill upgrades use `/propose-skill-upgrade` → explicit approve → apply (`memory/skill-proposals.md`).

## Components

### Skills

- `/audit-omniroute` — read-only ground-truth check of OmniRoute's actual install/config state (includes Known failure modes for auth durability and mid-cost model-alias restart)
- `/propose-agent-tier` — decides and proposes (never applies) a tier + model for an agent (includes Known failure modes for Trinity #74 hire-time subscription auto-assign)
- `/propose-skill-upgrade` — reviews live agents' skills vs mission; proposes (never applies) skill additions, independent verification, memory-structure upgrades, or model reconsiderations; manual trigger only (no schedule yet)
- `/verify-revenue-claim` — independent PASS/FAIL for `aegis-analyst` revenue claims (claim + sources only); called from analyst `/check-revenue`
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
- `memory/MEMORY.md` — consult-first structured spine (verified facts / rules / open / last session)
- `memory/tier-assignments.md` — running record of proposed and approved tier/model assignments
- `memory/skill-proposals.md` — skill / verification / memory-structure proposals (approve gate)
- `memory/usage-log.md` — weekly usage rollups
- `memory/pricing-checks.md` — provider pricing check history

### Schedules

Declared in `template.yaml`, all shipped `enabled: false` pending explicit approval:

- Weekly usage rollup (`/track-usage`)
- Pricing & free-tier re-check, every 2 weeks (`/review-pricing`)
- Dashboard refresh, every 6 hours (`/update-dashboard`)
- Doc reconciliation, weekly (`/reconcile-docs`)

`/propose-skill-upgrade` has **no** schedule yet — manual only.

## Trinity Integration

Resources: 1 CPU / 2g memory (deliberately modest — this agent should be one of the cheapest in the fleet to run, per its own operating rule). Declared plugins: `agent-dev`, `trinity`, `utilities`. Declared credentials: `OMNIROUTE_API_URL` (required), `OMNIROUTE_API_KEY` (optional, only if the OmniRoute instance requires auth). No MCP servers of its own — `.mcp.json.template` is empty; it uses Trinity's own injected `trinity` MCP tools (`list_agents`, `list_recent_executions`, `get_agent_activity_summary`, `chat_with_agent`, `report`) once deployed.

This agent's own tier, per its policy, is **free-pool** — it should not be deployed on Hamid's Claude Pro subscription once OmniRoute's free tier is confirmed working.

## Applied skill upgrades (2026-09-13)

- **SU-2026-09-13-1** — Independent free-pool verification for `aegis-analyst` (`/check-revenue` → `/verify-revenue-claim`)
- **SU-2026-09-13-2** — Structured `memory/MEMORY.md` on `aegis-infra` (topic logs retained)
