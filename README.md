# AEGIS Infra

**Role:** Head of Infrastructure & Compute for Hamid's personal agent company (built on Trinity) — reports to `aegis-ceo`.

Every other agent in the company runs on a model, provider, and budget that AEGIS Infra decided on, not one it picked for itself. AEGIS Infra doesn't do the company's analysis work; it makes that work possible and affordable — configuring the fleet's shared OmniRoute gateway, tracking what things actually cost, and catching provider pricing changes before they silently break a free assignment.

## Capabilities

- **Model/Provider Assignment** — proposes (never silently applies) a tier + specific model for a newly hired agent, with reasoning (`/propose-agent-tier`)
- **Skill / Capability Upgrades** — reviews live agents' skills vs mission; proposes (never applies) new skills, independent verification, or memory-structure upgrades (`/propose-skill-upgrade`)
- **OmniRoute Configuration & Audit** — checks what's actually installed and configured right now, rather than assuming it's live (`/audit-omniroute`)
- **Usage & Cost Tracking** — a real, numbers-based weekly rollup per agent, with anomalies flagged instead of assumed away (`/track-usage`)
- **Pricing & Free-Tier Rebalancing** — periodic re-check of provider pricing/free-tier terms, with rebalance proposals only when something changed materially (`/review-pricing`)

## Getting Started

```
cd aegis-infra && claude
/onboarding
```

See **[ARCHITECTURE.md](ARCHITECTURE.md)** for how the agent is built today and **[TARGET-ARCHITECTURE.md](TARGET-ARCHITECTURE.md)** for where it's headed.

## Skills

| Skill | Purpose |
|-------|---------|
| `/audit-omniroute` | Audit OmniRoute's actual current install/config |
| `/propose-agent-tier` | Propose a tier + model for a new or existing agent |
| `/propose-skill-upgrade` | Propose skill / verification / memory upgrades (manual; approve before apply) |
| `/verify-revenue-claim` | Independent PASS/FAIL for analyst revenue claims (pilot) |
| `/track-usage` | Weekly token/cost usage rollup per agent |
| `/review-pricing` | Re-check provider pricing/free-tier terms, propose rebalancing |
| `/fleet-directory` | Answer which agent ↔ which Slack channel (real docs/bindings only) |
| `/reconcile-docs` | Keep docs, skills, and architecture consistent |

## Ground Rules

- Never picks a model for itself — every assignment is proposed and approved, not applied silently.
- Never expands an agent's capabilities unattended — skill upgrades use the same propose → **approved** / **approve** → apply gate (`memory/skill-proposals.md`).
- Runs itself in the cheapest viable tier (free-pool); if it ever needs premium-tier reasoning to do its own job, that's a flag, not a shrug.
- Escalates before spending: no new paid plan, no cutting an agent's access, no spend beyond budget, without Hamid's or `aegis-ceo`'s go-ahead.
- Slack: Hamid can instruct this agent in `#aegis-infra` / `#fleet-directory` with the same authority as Trinity Chat (see [docs/slack-channel-pattern.md](docs/slack-channel-pattern.md)). Propose→approve gates still apply. Posts skill results outbound to `#aegis-infra`.
- Real failures get written into the skill that caused or exposed them (**Known failure modes** in `SKILL.md`), not only into this README.

## Known gotcha: free-pool auth durability

Trinity DB settings (`no subscription` + `use_platform_api_key=false`) and the agent's OmniRoute `.env` (usually re-injected from `.credentials.enc` on start) survive normal recreates. Free-pool auth **breaks** and needs **manual reinjection** of the OmniRoute `.env` (and a restart) if:

- a Claude Pro **subscription is reassigned** to the agent, or
- the **platform Anthropic API key is re-enabled**, or
- the agent **volume is wiped** without a `.credentials.enc` file to restore credentials from.

## Known gotcha: the-brain (VP) mid-cost model alias does not survive restart

`the-brain` (VP)'s mid-cost model alias (`sonnet` → Gemini Pro/mid-cost combo) is in-memory on the Trinity agent-server and does not survive an agent restart — must be re-applied via `PUT /api/agents/the-brain/model` with `{"model":"sonnet"}` after every restart until a durable `AGENT_RUNTIME_MODEL` mechanism exists. (Env may already list `AGENT_RUNTIME_MODEL` / `CLAUDE_MODEL` for OmniRoute; the Trinity chat alias is still a separate in-memory field.)

## Known gotcha: the-brain (VP) skill durability — FIXED for pull-gate (2026-09-13)

**Was:** VP was deployed from read-only upstream `github:Abilityai/cornelius` (`source_mode`, push URL stubbed). The `/synthesize` pull-gate fix lived only on the container volume and would vanish on workspace wipe / recreate from template.

**Now:** Bound to own writable repo via Trinity `POST /api/agents/the-brain/git/bind-to-own-repo` → [`hamidmatiny/the-brain`](https://github.com/hamidmatiny/the-brain) (private). Pull-gate skill is committed on `main` (`f904c86`). Verified after **workspace volume wipe + agent restart**: fresh clone from `origin` still contains `Pull gate` / `pull-failed` abort logic.

**Still manual after volume wipe:** OmniRoute `.env` / `.credentials.enc` (re-inject + export), sibling `knowledge/` deploy keys, and the mid-cost `sonnet` chat alias (see above). Skill text itself no longer needs re-application after recreate when the agent stays bound to `hamidmatiny/the-brain`.

## Known gotcha: new agents auto-land on Claude subscription (#74)

**This is not solved in the current Trinity version.** Creating an agent via `/create-agent:custom` + `/trinity:onboard` (Claude Code runtime) always triggers Trinity backend `#74` auto-assign: on create, `_apply_subscription_env` in `trinity/src/backend/services/agent_service/crud.py` round-robins the least-used Claude subscription (`get_least_used_subscription`) onto every new Claude-runtime agent and persists it. There is **no** `AgentConfig` field, Settings toggle, or onboard skill flag to opt out or to request OmniRoute free-pool at creation time. Non-Claude runtimes (`gemini-cli`, etc.) skip auto-assign, but that is not how this fleet's agents are built.

So `aegis-infra`'s tier proposal does **not** take effect at hire time. After every free-pool hire, run the same manual flip used for `aegis-infra` / `aegis-threat-intel` / `aegis-analyst`:

1. `DELETE /api/subscriptions/agents/<name>` (clear the auto-assigned Pro subscription)
2. `PUT /api/agents/<name>/api-key-setting` with `{"use_platform_api_key": false}`
3. `POST /api/agents/<name>/credentials/inject` with the shared OmniRoute `.env` (`ANTHROPIC_BASE_URL` → OmniRoute, Gemini model aliases)
4. Restart the agent; `POST .../credentials/export` so `.credentials.enc` exists for recreates
5. Verify: Trinity `auth_mode: not_configured`, chat `model_name` is Gemini, OmniRoute log shows `Provider: gemini`

Related: fixing a subscription token **only inside one agent's container** does not update Trinity's central "Hamid Matiny" record. New agents inherit the **central** encrypted token. After a revoke, upsert a fresh `sk-ant-oat01-…` via `POST /api/subscriptions` (`name: "Hamid Matiny"`) and restart subscription-mode agents (hot-reload is best-effort and may not apply).
