# Fleet org chart (Track B — personal Trinity agents)

**Canonical location:** this file in `aegis-infra` (`docs/org-chart.md`).  
**Also linked from:** each agent's `CLAUDE.md` (pointer only) and `aegis-infra/docs/a2a-routing.md`.  
**Public verification:** [docs/public-verification.md](./public-verification.md) (unauthenticated GitHub URLs).

**How to refresh:** call Trinity `list_agents` (exclude `trinity-system`). Do **not** treat this table as forever-true — tags + live list win when they disagree.

**Standing rule — Cursor workspace:** every new hire’s repo/folder is added to `/Users/hamidrezamatiny/Cursor/aegis-fleet.code-workspace` during onboarding (same pass as Trinity deploy / `/propose-agent-tier`), not later. See `/propose-agent-tier` Step 0.

*Snapshot: 2026-09-22 from live `list_agents` — **16** fleet agents. Schedule-trigger section below is from live `agent_schedules` + `schedule_executions` the same day.*

```
Hamid (founder)
└── aegis-ceo                          [Executive · L5]
    ├── the-brain                      [Executive · VP]
    ├── aegis-infra                    [Infrastructure & Compute]
    ├── aegis-scout                    [Capability / Learning]
    ├── aegis-threat-intel             [Cybersecurity]
    ├── aegis-redteam                  [Cybersecurity · Red Team]  ← new
    ├── aegis-analyst                  [Finance]
    ├── aegis-core-infra               [Engineering]
    ├── aegis-data-quality             [Data / Quality]
    ├── aegis-growth                   [Growth / Marketing]
    └── aegis-product-eng              [Product Engineering · Manager · L5]
        ├── aegis-gateway
        ├── aegis-policy-engine
        ├── aegis-model-router
        ├── aegis-agent-gate
        └── aegis-audit
```

| Agent | Department | Reports to | Notes |
|-------|------------|------------|-------|
| aegis-ceo | Executive | Hamid | Founder-facing CEO agent |
| the-brain | Executive | aegis-ceo (peer VP) | Same-branch with CEO |
| aegis-infra | Infrastructure & Compute | aegis-ceo | OmniRoute, capacity HOLD |
| aegis-scout | Capability / Learning | aegis-ceo | Learning finds; does not install skills unilaterally |
| aegis-threat-intel | Cybersecurity | aegis-ceo | CVE / news watch |
| aegis-redteam | Cybersecurity | aegis-ceo | Live gateway attacks; Protocol D sink |
| aegis-analyst | Finance | aegis-ceo | MRR read-only |
| aegis-core-infra | Engineering | aegis-ceo | Product-repo infra diff review |
| aegis-data-quality | Data / Quality | aegis-ceo | Fleet output drift |
| aegis-growth | Growth / Marketing | aegis-ceo | Signups / SEO / directories |
| aegis-product-eng | Product Engineering | aegis-ceo | Manager of PE ICs |
| aegis-gateway | Product Engineering | aegis-product-eng | IC |
| aegis-policy-engine | Product Engineering | aegis-product-eng | IC |
| aegis-model-router | Product Engineering | aegis-product-eng | IC |
| aegis-agent-gate | Product Engineering | aegis-product-eng | IC |
| aegis-audit | Product Engineering | aegis-product-eng | IC |

`trinity-system` is platform infrastructure — **not** on this chart.

Peers with no reporting line (e.g. `aegis-infra` ↔ `aegis-scout`) still use this chart for orientation. Cross-branch **tasks** still follow Protocol A (manager-routed) unless an approved exception (verify-revenue, Protocol C HOLD, Protocol D technique handoff) applies.

## Schedule trigger ownership (verified 2026-09-22)

Reporting line (table above) and **who fires a scheduled run** are different facts. Checked live, not inferred from this chart.

**Mechanism:** `trinity-scheduler` fires each agent's own `agent_schedules` row when `enabled=1` (`triggered_by=schedule` in `src/scheduler/service.py`). There are **0** `process_schedules`. `aegis-ceo` has five schedules; none of their messages name another agent. CEO-sourced executions in `schedule_executions` are two ad-hoc A2A chats to `aegis-infra` only — not a cron fan-out.

**Product Engineering ICs:** all 15 IC schedule rows (3 × gateway, policy-engine, model-router, agent-gate, audit) are `enabled=0` and have `last_run_at` null. `aegis-product-eng`'s two schedules (`Weekly team review`, `Update dashboard`) are also `enabled=0` and have never run. IC execution history is Hamid chat/MCP plus one peer A2A (`aegis-policy-engine` → `aegis-agent-gate`). **No schedule execution, and no `source_agent_name=aegis-ceo`.** Nothing to re-route: CEO is not triggering these ICs. If an IC cron is later turned on, the platform fires that row on the IC itself — it does not pass through `aegis-product-eng` or `aegis-ceo`. Leave them off until the manager explicitly owns the enable.

**Single-person departments:** no manager layer underneath, so a platform cron on the agent (not a CEO chat, and not an invented middle manager) is the correct trigger. Same for `the-brain` and `aegis-ceo`'s own jobs.

| Agent | Reports to | Who fires enabled schedules | Live enabled work (2026-09-22) |
|-------|------------|-----------------------------|-------------------------------|
| aegis-ceo | Hamid | Own Trinity cron | Trajectory review, GitHub pulse, weekly strategy brief, weekly project manage. CVE watch off |
| the-brain | aegis-ceo | Own Trinity cron | Fleet KG ingest |
| aegis-infra | aegis-ceo | Own Trinity cron | Token budget, daily allocation, usage rollup, dashboard, pricing re-check, SI |
| aegis-scout | aegis-ceo | Own Trinity cron | Fleet capability scout, founder learning curation, weekly doc reconciliation. Dashboard refresh off |
| aegis-threat-intel | aegis-ceo | Own Trinity cron | Threat scan, SI |
| aegis-redteam | aegis-ceo | Own Trinity cron | Live gateway attack batch, dashboard refresh |
| aegis-analyst | aegis-ceo | Own Trinity cron | Daily revenue check, SI |
| aegis-core-infra | aegis-ceo | Own Trinity cron | Daily infra diff review |
| aegis-data-quality | aegis-ceo | Own Trinity cron | Fleet output review, SI |
| aegis-growth | aegis-ceo | Own Trinity cron | Daily growth check, weekly SEO draft, weekly directory pass, SI |
| aegis-product-eng | aegis-ceo | Own Trinity cron (none enabled) | Weekly team review off; dashboard off. Has never schedule-fired |
| aegis-gateway | aegis-product-eng | None (rows exist, all off) | Daily component audit / dashboard / reconcile-docs all off; never run |
| aegis-policy-engine | aegis-product-eng | None (rows exist, all off) | Same three, all off; never run |
| aegis-model-router | aegis-product-eng | None (rows exist, all off) | Same three, all off; never run |
| aegis-agent-gate | aegis-product-eng | None (rows exist, all off) | Same three, all off; never run |
| aegis-audit | aegis-product-eng | None (rows exist, all off) | Same three, all off; never run |

## A2A permission map (live `agent_permissions`, 2026-10-08)

60 Track B edges. Demo `acme-*` rows are not included. This is who can message whom. It is not the reporting tree above.

**Protocol A — task routing.** Same-branch peers message directly. Cross-branch work goes to the manager, then the manager forwards. Live edges that carry that:

- Executive: `aegis-ceo` ↔ `the-brain`.
- CEO to branch leads: `aegis-ceo` → `aegis-infra`, `aegis-scout`, `aegis-threat-intel`, `aegis-redteam`, `aegis-analyst`, `aegis-core-infra`, `aegis-data-quality`, `aegis-growth`, `aegis-product-eng`. Each of those leads has the reverse edge to `aegis-ceo`, except the return path is one-way where noted below.
- Product Engineering mesh: `aegis-product-eng` ↔ each of `aegis-gateway`, `aegis-policy-engine`, `aegis-model-router`, `aegis-agent-gate`, `aegis-audit`. The five ICs can also message each other. CEO has no direct edge to an IC.

**Protocol B — judgment.** The same manager edges are the escalation path: specialist → own manager → `aegis-ceo` → Hamid. Hamid is not an A2A node. The last hop is the operator queue.

**Protocol C — capacity hold.** Live, and they match the granted list in `docs/a2a-routing.md`: `aegis-infra` → `aegis-analyst`, `aegis-core-infra`, `aegis-threat-intel`, `aegis-data-quality`, `aegis-growth`, `aegis-ceo`. The hold itself is `scripts/capacity-watch.py`, not a chat.

**Protocol D — technique handoff and bypass escalation.** Live, and they match the granted list: `aegis-threat-intel` → `aegis-redteam`, `aegis-scout` → `aegis-redteam`, `aegis-ceo` → `aegis-redteam`, `aegis-redteam` → `aegis-ceo`. Also live: `aegis-redteam` → `aegis-threat-intel` (same-branch Cyber peer).

**Other standing edge.** `aegis-analyst` → `aegis-infra` (verify-before-publish). Also live and not in that one-row exception: `aegis-data-quality` → `aegis-infra`.

**Not A2A edges.**

- Operator queue: any agent appends an item Hamid sees in Trinity's Operating Room. That is the path to Hamid after `aegis-ceo`.
- `the-brain` fleet-kg (`memory/fleet-kg.sqlite`): shared memory. Only `the-brain` writes it. Other agents do not have an A2A edge to it.

**In the routing doc, not in Trinity.**

- The onboarding rule says each new hire gets `<hire> → aegis-infra` for `/audit-omniroute`. As of the 2026-10-08 map those rows existed only for `aegis-analyst` and `aegis-data-quality`. The same edge is now granted for the other twelve: `aegis-core-infra`, `aegis-growth`, `aegis-scout`, `aegis-threat-intel`, `aegis-redteam`, `aegis-product-eng`, `the-brain`, and the five Product Engineering ICs. Confirm with `agent_permissions` after any later hire.

**In Trinity, not called out as a granted edge in the routing doc.**

- The Product Engineering mesh (IC ↔ IC and IC ↔ `aegis-product-eng`).
- `aegis-data-quality` → `aegis-infra`.
- `aegis-redteam` → `aegis-threat-intel` is allowed by the same-branch sentence, but it is not in the Protocol D table.
- CEO has no edge to the five ICs. That matches Protocol A (manager hop). It is recorded here so it is not mistaken for a missing grant.

## Notes — standing decisions

### Cybersecurity reporting (2026-09-20, Hamid)

**Decision:** `aegis-redteam` stays a **peer** to `aegis-threat-intel`. Both report **directly to `aegis-ceo`**. No dedicated cybersecurity manager for now.

**Reasoning:** Product Engineering needed a manager because it has 5 ICs (span-of-control problem). Cybersecurity only has 2 agents right now, and they already have a working peer path via Protocol D — so a manager would be structure without a real bottleneck to solve.

**Revisit threshold:** If cybersecurity grows to **3+ agents**, re-evaluate whether it needs its own manager — same span-of-control threshold that justified `aegis-product-eng`.

Fleet-kg record: `decision:cybersecurity-no-manager-2026-09-20`.

### Who owns whether improvement runs (2026-10-08, Hamid)

**Decision:** `aegis-infra` is accountable for whether a self-improvement slot runs.

**Duties, and only these:**

1. Set the one-slot cool-pool SI budget.
2. Keep existing SI schedules armed when the capacity hold lifts under the normal lift rule. Do not force-lift.
3. Report each week which agent got the slot and which agents still have no SI schedule.

`aegis-scout` still picks what to learn from the live roster. `aegis-ceo` still approves skill upgrades. `the-brain` still records levels. No hire. No change to who approves credentials, tiers, or Track A code.

### Production is ahead of main (2026-10-08)

The Oracle VM is deployed from PR #96's branch, not from `main`. See [production-checkout.md](./production-checkout.md). Do not redeploy from `main` until that PR merges.
