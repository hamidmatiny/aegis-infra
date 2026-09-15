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

## Fleet A2A routing (hybrid protocol)

Same-branch peers may message directly; cross-branch traffic goes through the branch manager (today: always `aegis-ceo`). Source of truth and exception list: **[docs/a2a-routing.md](docs/a2a-routing.md)**. Before proposing any new A2A permission, check that table and refuse direct cross-branch grants.

**Approved exception (only one):** `aegis-analyst` → `aegis-infra` for `/verify-revenue-claim` only — see the routing doc. Do not copy.

## Known gotcha: A2A matrix not enforced on raw REST chat (2026-09-14)

**What:** Trinity’s agent-permission matrix is checked on MCP `chat_with_agent` (`checkAgentAccess`). `POST /api/agents/{name}/chat` with an agent-scoped MCP/API key does **not** apply that same matrix (proven during A2A protocol verify: analyst→core-infra succeeded over REST, denied over MCP).

**Fleet callers today:** inert for Track B. Live agent workspaces (`aegis-ceo`, `aegis-infra`, `aegis-analyst`, `aegis-threat-intel`, `aegis-core-infra`, `the-brain`) and their repo skills use `mcp__trinity__chat_with_agent` for A2A — no skill/schedule script posts to `/api/agents/*/chat` for peer messaging. (Slack bind curls hit `/slack/...`, not chat. Infra `propose-skill-upgrade` mentions “or HTTP chat” as a design option only; `/verify-revenue-claim` / `/check-revenue` call MCP.)

**If this becomes live:** any agent (or script) that A2A-chats via raw REST with an agent key bypasses the hybrid protocol. Close by enforcing the matrix on REST when the caller is an agent-scoped key, or by forbidding that path and requiring MCP.

## Known gotcha: schedule `next_run` stuck in the past

**What broke:** `aegis-ceo` `Daily trajectory review` showed Active / overdue in the UI with 0 runs. Live `GET /api/agents/scheduler/status` had the job registered, but `next_run` was stuck in the past — cron never woke. Agent redeploys did **not** delete the DB row; this is an APScheduler wake / overdue-stuck failure mode, not the OmniRoute `.env` wipe class.

**Verify:** `jobs[].next_run` on `/api/agents/scheduler/status` must be **in the future**. Past + `last_run_at=null` = stuck. Fix: disable→enable the schedule (wait ~60s for sync) or restart `trinity-scheduler`. Affects every agent's cron on this instance.

**Related (2026-09-15):** host/Docker sleep can also miss a fire window even when `next_run` looked healthy beforehand — see the next gotcha. Prefer the runtime sync catch-up over relying on disable→enable alone.

## Known gotcha: host/Docker sleep can miss schedule fires (fleet-wide, 2026-09-15)

**What broke:** `trinity-scheduler` is a **shared** process for every agent's crons. On a laptop / Docker Desktop, host sleep freezes that process **without** restarting the container. Health checks showed multi-minute gaps (e.g. ~83 min straddling `2026-09-15T08:00Z`). APScheduler often does **not** misfire-recover those windows after wake. Boot-only catch-up (#145) never runs (container stayed up). Symptom for `aegis-ceo` `Daily trajectory review` (`0 8 * * *`): UI Active / Overdue / "0 runs", job still registered, **no** `Executing schedule … triggered_by=schedule` at 08:00 — not an agent-redeploy wipe.

**Fleet scope (checked live 2026-09-15):** Only **one** schedule was enabled on this instance — `aegis-ceo` / Daily trajectory review. All other hire schedules (`aegis-infra`, `aegis-threat-intel`, `aegis-analyst`, `aegis-core-infra`, `aegis-data-quality`, `the-brain`) were `enabled: false` (or had no schedules). So no second agent was found already stuck in the same enabled+overdue state. The failure mode is still **fleet-wide**: any future enabled cron on any agent shares `trinity-scheduler` and the same sleep gap.

**Mitigation (local Trinity checkout):** runtime `_recover_overdue_schedules` on every schedule sync tick (~60s) in `src/scheduler/service.py` — within `MISFIRE_GRACE_TIME` catch-up fire; past grace advance `next_run_at` only. Verified: rebuilt `trinity-scheduler` image; overdue `next_run_at` within grace → `Runtime catch-up: firing …` + new `triggered_by=schedule` execution. Survives scheduler container recreate when the image includes the fix; does **not** require disable→enable after agent redeploys.

**Ops check:** after a long host sleep, confirm `GET /api/agents/scheduler/status` `jobs[].next_run` is future, and look for `Runtime catch-up` in `trinity-scheduler` logs if a window was straddled.

## Known gotcha: free-pool auth durability

Trinity DB settings (`no subscription` + `use_platform_api_key=false`) and the agent's OmniRoute `.env` (usually re-injected from `.credentials.enc` on start) survive normal recreates. Free-pool auth **breaks** and needs **manual reinjection** of the OmniRoute `.env` (and a restart) if:

- a Claude Pro **subscription is reassigned** to the agent, or
- the **platform Anthropic API key is re-enabled**, or
- the agent **volume is wiped** without a `.credentials.enc` file to restore credentials from.

## Known gotcha: the-brain (VP) mid-cost model alias does not survive restart

`the-brain` (VP)'s mid-cost model alias (`sonnet` → mid-cost OmniRoute combo) is in-memory on the Trinity agent-server and does not survive an agent restart — must be re-applied via `PUT /api/agents/the-brain/model` with `{"model":"sonnet"}` after every restart until a durable `AGENT_RUNTIME_MODEL` mechanism exists. (Env may already list `ANTHROPIC_MODEL` / `CLAUDE_MODEL` / `AGENT_RUNTIME_MODEL=sonnet` for OmniRoute; the Trinity chat alias is still a separate in-memory field.) Same applies to `aegis-core-infra`.

## Known gotcha: mid-cost must not fall back to flash (2026-09-14)

**What broke:** Mid-cost agents (`the-brain`, `aegis-core-infra`) silently billed as flash-class (`gemini-3.7-flash` / `gemini-flash-lite-latest`) when Gemini Pro quota was exhausted. Root causes stacked: (1) OmniRoute combos `sonnet` / `aegis-mid` were single-step flash (or Pro-only with free-pool Claude aliases → flash-lite); (2) agent `.env` sometimes set `ANTHROPIC_DEFAULT_SONNET_MODEL=gemini/gemini-flash-lite-latest`, so Trinity `model=sonnet` remapped straight to free-pool; (3) only a Gemini API-key provider is connected in OmniRoute — no Anthropic/OpenAI paid key for a native Claude/GPT mid fallback.

**Fixed behavior (combo, not per-agent):** OmniRoute combos `sonnet` and `aegis-mid` use priority:

1. `cfp/deepseek-ai/deepseek-v4-pro-0813` (Cloudflare Playground — strong mid when Pro is cooling)
2. `cfp/openai/gpt-oss-120b`
3. `gemini/gemini-3.1-pro-preview`

No flash in the mid chain. Free-pool stays on `aegis-free` / `claude-sonnet-4-6` → flash-lite. Small/title traffic for mid agents uses combo `haiku` → flash-lite only (not the reasoning path).

**Verified (2026-09-14):** Trinity chat on both agents with `model=sonnet` returned `MID_COST_PROBE_OK`; OmniRoute call logs showed `combo=sonnet` → `deepseek-ai/deepseek-v4-pro-0813` (provider `cloudflare-playground`, status 200) — not flash.

**Remaining gap / variability:** There is still **no Anthropic or OpenAI API-key provider** in OmniRoute. Mid fallback is CFP DeepSeek Pro / GPT-OSS, then Gemini Pro when quota allows. When CFP is circuit-open **and** Gemini Pro is cooling, the mid combo **fail-closes** (429/502/503) instead of degrading to flash — correct vs free-pool collapse, but agents will error until a target recovers. To add a paid mid rail: connect Anthropic (`ANTHROPIC_API_KEY`) or OpenAI (`OPENAI_API_KEY`) in OmniRoute and insert e.g. `anthropic/claude-sonnet-4-5` (or GPT-class) into the `sonnet`/`aegis-mid` priority list ahead of flash forever.

**Ops checklist for mid agents:** `.env` must keep `ANTHROPIC_*_MODEL=sonnet` (not a `gemini/...` flash ID); haiku/small → `haiku`; after inject, `POST .../credentials/export`; after restart, re-`PUT .../model` `sonnet` until Trinity persists the alias.

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

## Known gotcha: Claude Pro `setup-token` is additive — revoke is what kills the fleet (2026-09-14)

**Hypothesis checked:** Does running `claude setup-token` in Hamid's own terminal (or another session) invalidate the fleet token because Anthropic OAuth is single-active-session?

**Answer: No.** `claude setup-token` **mints another** long-lived `sk-ant-oat01-…` token (~1 year, model-requests only). It does **not** rotate or revoke prior tokens. Multiple setup-tokens can be valid at once. Trinity docs / Anthropic CLI behavior agree: mint is additive; there is no CLI revoke. Server-side revoke is via [claude.ai → Settings → Claude Code](https://claude.ai/settings/claude-code) ("Revoke" on a specific token / instance).

**What actually broke `aegis-ceo` (evidence):** Anthropic returned `401 OAuth access token has been revoked` (not merely "invalid") for the token last upserted into Trinity subscription `Hamid Matiny` at `2026-09-13T20:02:18Z` (agent restarted ~30s later). Failures today: scheduled probe `11:42Z` and Slack `11:53Z`. So something **revoked that specific token server-side** — typical causes are an explicit Revoke in the Claude Code settings UI (e.g. cleaning up "old" connections after minting a new personal token), not the act of minting alone.

**Standing rules so this doesn't recur:**

1. Treat the Trinity-registered token as a **fleet secret**. Never click Revoke on it in claude.ai unless you are intentionally rotating.
2. Personal `claude setup-token` / `/login` on a laptop is fine and does **not** by itself kill the fleet — but if you then revoke "extra" Claude Code entries in the UI, you may revoke the fleet one by mistake (tokens look alike).
3. **Rotate safely:** mint new token → `POST /api/subscriptions` upsert `name: "Hamid Matiny"` with the new token → restart `aegis-ceo` → **verify chat + a real schedule trigger succeed** → only then revoke the old token in the UI (optional hygiene).
4. Do not patch `CLAUDE_CODE_OAUTH_TOKEN` only inside the container — central subscription record is what new assigns/recreates use.

**Verify health:** subscription auth probe (chat) succeeds; `POST .../schedules/<daily-trajectory-id>/trigger` succeeds (same path as 08:00 cron). UI "token present" is not enough.