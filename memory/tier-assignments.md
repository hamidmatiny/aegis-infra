# Tier Assignments

Running record of proposed and approved tier/model assignments across the fleet. Appended to by `/propose-agent-tier`; read by `/track-usage` and `/review-pricing`.

## aegis-ceo

**Tier:** Premium (subscription) — Hamid's Claude Pro subscription auth.
**Why:** Final judgment calls, CEO-adjacent decisions. First hire, predates this agent's tier-assignment process.
**Status:** Live (confirmed running on subscription auth as of 2026-09-13).

## aegis-infra

**Tier:** Free-pool — this agent's own stated policy ("be the boring one").
**Why:** Bookkeeping and routing logic; should be one of the cheapest agents to run.
**Auth mode:** OmniRoute API-key routing (`ANTHROPIC_BASE_URL` → OmniRoute → Gemini), not subscription auth (mutually exclusive per agent in Trinity).
**Status:** Live on OmniRoute free-pool (verified 2026-09-13: chat traffic `Provider: gemini`, Trinity subscription cleared, `use_platform_api_key=false`).

## aegis-threat-intel

**Tier:** Free-pool — via OmniRoute, provider `gemini/gemini-3.7-flash` (runtime currently mapped via OmniRoute combos to `gemini/gemini-flash-lite-latest`).
**Why:** High-volume, low-stakes CVE/security-news polling and classification. Doesn't need Hamid's scarce Claude Pro subscription or paid mid-cost API budget — exactly the free-pool use case.
**Auth mode:** OmniRoute API-key routing, not subscription auth (mutually exclusive per agent in Trinity).
**Token-saving habits assigned:** filter feeds upstream before pulling full text into context; rely on OmniRoute's built-in compression; batch related CVE checks into one consolidated pass; reuse prior findings/baselines from its own memory instead of re-deriving history each time.
**Status:** Applied and live on OmniRoute free-pool (verified 2026-09-13: chat traffic `Provider: gemini`, platform API key disabled, OmniRoute `.env` + `.credentials.enc` in place).

## aegis-analyst (P&L / MRR Analyst)

**Tier:** Free-pool
**Provider/model:** `gemini/gemini-3.7-flash` via OmniRoute free pool
**Why:** Reading structured JSON endpoints (`/bev/trajectory`, `/bev/summary`), formatting numeric reports, and checking for explicit arithmetic anomalies is high-volume structured reporting — not Claude Pro or mid-cost. (Recorded in stash as `aegis-mrr-analyst`; live Trinity name is `aegis-analyst`.)
**Auth mode:** OmniRoute API-key routing, not subscription auth (mutually exclusive per agent in Trinity).
**Token-saving habits assigned:** query specific JSON fields; OmniRoute compression; batch scheduled reporting; reuse memory baselines.
**Status:** Live on Trinity as `aegis-analyst` (free-pool intended; confirm OmniRoute auth still applied after any subscription auto-assign).

## the-brain (VP)

**Tier:** Mid-cost — OmniRoute combo `sonnet` / `aegis-mid` (priority: CFP DeepSeek Pro → GPT-OSS → Gemini 3.1 Pro preview). No flash in mid chain.
**Why:** Synthesis / VP judgment needs stronger reasoning than free-pool; not founder-facing premium subscription.
**Auth mode:** OmniRoute API-key routing, not subscription auth.
**Status:** Live; in-memory `sonnet` alias must be re-PUT after restart until durable.

## aegis-core-infra

**Tier:** Mid-cost — OmniRoute combo `sonnet` / `aegis-mid` (priority: CFP DeepSeek Pro → GPT-OSS → Gemini 3.1 Pro preview). No flash in mid chain.
**Why:** Real Docker/CI/migration reasoning needs more than free-pool reliably provides; no write/deploy/block authority so Claude Pro subscription is not warranted.
**Auth mode:** OmniRoute API-key routing, not subscription auth (mutually exclusive per agent). `use_platform_api_key=false`; subscription cleared after create-time auto-assign to Hamid's Pro.
**Token-saving habits assigned:** query specific diffs/targeted files; OmniRoute compression; batch review passes; reuse `memory/` baselines.
**Status:** Applied and live on Trinity (`github:hamidmatiny/aegis-core-infra@main`): auth `not_configured`, model `sonnet`, OmniRoute `.env` + `.credentials.enc` in place. Note: in-memory `sonnet` alias does not survive restart (same class as `the-brain`) — re-PUT model after restart until durable. Verified 2026-09-14: chat served `deepseek-ai/deepseek-v4-pro-0813` via combo `sonnet` (not flash).

## aegis-data-quality (Data/Quality Analyst)

**Tier:** Free-pool
**Provider/model:** `gemini/gemini-3.7-flash` via OmniRoute free pool
**Why:** Structured validation and anomaly-flagging against known schemas/baselines; strictly advisory; periodic rather than continuous — same free-pool fit as `aegis-analyst`. Does not need Claude Pro or mid-cost.
**Auth mode:** OmniRoute API-key routing, not subscription auth (mutually exclusive per agent in Trinity).
**Token-saving habits assigned:**
- Query specific target report outputs and data endpoints directly rather than ingesting full logs or historical archives.
- Rely on OmniRoute's built-in compression.
- Batch periodic data-quality sweeps into scheduled verification runs rather than continuous polling.
- Reuse prior schema rules and validation baselines stored in memory rather than re-deriving validation checks on every run.
**Status:** Applied and live on Trinity (`github:hamidmatiny/aegis-data-quality@main`): auth `not_configured`, `use_platform_api_key=false`, OmniRoute `.env` + `.credentials.enc` in place, model `claude-sonnet-4-6` (free-pool combo). A2A hub `aegis-data-quality`↔`aegis-ceo` granted. *(Recovered from stash@{0} then onboarded 2026-09-14.)*

## aegis-growth (Growth/Marketing Analyst)

**Tier:** Free-pool
**Provider/model:** `gemini/gemini-3.7-flash` via OmniRoute free pool (combo lane `aegis-free-37` per fallback-pools)
**Why:** Signup/conversion reads and organic growth checks are structured reporting — same free-pool fit as `aegis-analyst`. Paid ads / cold outreach excluded from scope.
**Auth mode:** OmniRoute API-key routing, not subscription auth (mutually exclusive per agent in Trinity).
**Token-saving habits assigned:** query specific signup/conversion fields; OmniRoute compression; batch into scheduled runs; reuse baselines in `memory/`.
**Status:** Live on Trinity (`github:hamidmatiny/aegis-growth`). **2026-09-21 formalization:** originally backfilled 2026-09-16 without a full `/propose-agent-tier` → approve trail. Re-proposed below for explicit `aegis-ceo` / Hamid confirmation so the roster matches process ("nobody else picks their own model").

### 2026-09-21 — formal `/propose-agent-tier` (awaiting approval)

| Field | Proposal |
|-------|----------|
| Agent | `aegis-growth` |
| Tier | **Free-pool** |
| Model/combo | OmniRoute free — `aegis-free-37` / `gemini/gemini-3.7-flash` class |
| Auth | OmniRoute API-key routing (`use_platform_api_key=false`; no Claude Pro) |
| Rationale | High-volume structured BEV reads + directory/SEO drafts; not final judgment or customer-facing negotiation |
| Apply? | **No until approved** — already live on this path; approval confirms the record, does not change runtime unless CEO requests a different tier |

**Decision needed from `aegis-ceo` (or Hamid):** Approve free-pool for `aegis-growth` as standing assignment, or request mid-cost reassessment.

## aegis-scout (Capability & Learning Scout)

**Tier:** Mid-cost
**Provider/model:** OmniRoute combo `sonnet` / `aegis-mid` (priority: Gemini 3.1 Pro preview → CFP GPT-OSS → CFP DeepSeek Pro). No flash in mid chain.
**Why:** High-synthesis research across papers/repos/courses; must discriminate actionable department learning vs generic AI noise; Executive-adjacent awareness like `the-brain` but service role (not a manager). Free-pool flash is too weak for that filter; Premium Claude Pro not warranted (not founder judgment / not customer-facing).
**Auth mode:** OmniRoute API-key routing, not subscription auth (mutually exclusive per agent in Trinity).
**Token-saving habits assigned:** targeted search/lookup vs multi-page dumps; OmniRoute compression; batch findings into structured digests; reuse scouting baselines in memory.
**Dependencies:** OmniRoute mid-cost `sonnet` / `aegis-mid` confirmed live; post-hire manual auth flip required (Trinity #74 / FM-1).
**Status:** Live on Trinity (`github:hamidmatiny/aegis-scout@main`): Slack `#aegis-scout` `C0C297RQ7PY`; A2A scout↔ceo. `/trial-scout` verified 2026-09-16 (`v-ymLhktVJQNjHDA_ZZ6aQ` success; GrowthBook for Growth; Slack delivery `success: true` on `C0C297RQ7PY`; schedules enabled). **Runtime exception:** Gemini Pro quota exhausted and CFP mid hops reject Trinity-sized prompts (max 6000 chars) — agent temporarily on free OmniRoute alias `claude-sonnet-4-6` (routes to Gemini flash-lite chain via `ANTHROPIC_BASE_URL=OmniRoute`; Trinity `auth_mode=not_configured`, no Claude Pro subscription). **Not** subscription auth. **Restore mechanism:** Trinity reminder on `aegis-infra` `rem_fcab848e2aa940f8b21c1e6f7da17bae` fires `2026-09-17T00:25:34Z` (re-arms every 6h until Pro long-prompt works); `/audit-omniroute` Step 4b also checks and flips.

## Fallback-pool diversification (2026-09-17)

Fleet no longer shares one mid/free ordered chain. Structured lanes live in `memory/fallback-pools.md`.

| Agent | Combo |
|-------|-------|
| `the-brain` | `aegis-mid-ds` (free Flash-Lite chain as of 2026-09-22; see fallback-pools) |
| `aegis-core-infra` | `aegis-mid-oss` (free Flash-Lite chain as of 2026-09-22) |
| `aegis-product-eng` | `aegis-mid` (moved off `aegis-mid-oss` 2026-09-22) |
| `aegis-scout` | `aegis-free-latest` (temp free while mid long-prompt fragile) |
| `aegis-infra` | `aegis-free-lite` |
| `aegis-threat-intel` | `aegis-free-20` |
| `aegis-analyst` | `aegis-free-36` |
| `aegis-data-quality` | `aegis-free-latest` |
| `aegis-growth` | `aegis-free-37` |

## Change log

- 2026-09-22: No tier move applied. Recurring OmniRoute "unreachable" plus the 08:19 local four-agent cancel wave were the Mac idle-sleeping (display off 02:02, idle sleep 02:13, user wake 08:18:19 -0300), not an OmniRoute crash. Gemini 429/503 on the shared `claude-sonnet-4-6` combo is a separate awake-hours capacity problem. Rebalancing agents off that combo still needs an `aegis-ceo` approval; not done this pass.
- 2026-09-22: Drafted the Gemini quota rebalance below. Not applied. One active Gemini API-key connection serves every combo, so renaming combos does not add free quota.

### 2026-09-22 — Gemini quota tier-rebalance (awaiting `aegis-ceo` approval)

Proposal only. No combo, key, or agent auth was changed.

**Evidence (OmniRoute `call_logs`, queried 2026-09-22, window from 2026-09-16):**

| Combo | Calls | HTTP 429 | HTTP 200 | Successful input tokens |
| --- | ---: | ---: | ---: | ---: |
| `claude-sonnet-4-6` | 4,749 | 1,054 | 1,804 | 174,672,632 |
| `sonnet` | 619 | 193 | 19 | 249,806 |
| `aegis-mid-oss` | 49 | 28 | 2 | 133 |
| `aegis-mid-ds` | 7 | 4 | 1 | 65 |

The runtime API key `aegis-infra-runtime` accounts for 6,514 of those calls and 1,471 of the 429s. On 2026-09-22 UTC the shared combo alone had 25 more 429s (171 calls). `provider_connections` has one active Gemini connection (`auth_type=apikey`). Every combo shares it.

`claude-sonnet-4-6` is a priority chain of `gemini/gemini-flash-lite-latest`, `gemini/gemini-2.0-flash-lite`, and `gemini/gemini-3.7-flash`. Successful calls on it were those flash models (1,079 / 664 / 61). Calls whose requested model string was `claude-sonnet-4-6` itself: 1,539 attempts, 255×429, 0×200.

**Who is assigned where (live container `.env`, 2026-09-22), which is not the same as who generated the 4,749 calls:**

| Combo in `.env` | Agents |
| --- | --- |
| `aegis-mid-oss` | `aegis-core-infra`, `aegis-product-eng` |
| `aegis-mid-ds` | `the-brain` |
| `aegis-free-lite` | `aegis-infra` |
| `aegis-free-20` | `aegis-threat-intel` |
| `aegis-free-36` | `aegis-analyst` |
| `aegis-free-37` | `aegis-growth`, `aegis-gateway`, `aegis-policy-engine`, `aegis-model-router`, `aegis-agent-gate`, `aegis-audit` |
| `aegis-free-latest` | `aegis-data-quality`, `aegis-scout` |
| no OmniRoute `.env` | `aegis-ceo` (subscription), `aegis-redteam` (creation auth, no `.env`) |

Headless still passes the platform model id `claude-sonnet-4-6` when the caller supplies it. That id is also the shared flash combo, so it overrides the per-agent `.env` combo. Three enabled schedules still store `model=sonnet` (`aegis-analyst` daily revenue, `aegis-data-quality` fleet review, `aegis-growth` daily growth). A Trinity source change maps those aliases and the platform default onto `ANTHROPIC_MODEL` for a custom gateway. It is not in the running agent image, and it does not add quota while every combo uses the same Gemini key.

**Published rates (https://ai.google.dev/gemini-api/docs/pricing, fetched 2026-09-22):**

- `gemini-3.1-pro-preview`: free tier not available. Paid standard $2.00 input / $12.00 output per 1M tokens for prompts ≤200k ($4 / $18 above 200k). Output includes thinking tokens.
- `gemini-2.5-flash-lite`: free tier still listed. Paid standard $0.10 input / $0.40 output per 1M tokens.
- That page does not price `gemini-flash-lite-latest`, `gemini-2.0-flash-lite`, or `gemini-3.7-flash` as their own rows. Those ids are not given a dollar figure here.

**Cost if the Pro agents were on the paid Pro rate.** Successful tokens on `aegis-mid-oss` + `aegis-mid-ds` since Sep 16 are 198 input tokens. At $2 / 1M that is under one cent. The 429s are because Pro has no free tier, not because those agents have already spent a large bill. Illustration, not a forecast: one review of 100k input + 8k output at the ≤200k rate is about $0.30. Three such reviews a day for a month is about $27. Actual spend follows tokens served after calls start succeeding.

**Illustration only, not a recommendation to bill the flash pile as 2.5 Flash-Lite:** the 111.4M successful `gemini-flash-lite-latest` input tokens since Sep 16 would be about $11.14 at the published 2.5 Flash-Lite input rate, plus about $0.16 of output. The 2.0-flash-lite and 3.7-flash slices are not priced here.

**Recommended split (do not apply until `aegis-ceo` approves):**

1. Add a paid Gemini key and point only the Pro targets in `aegis-mid-oss` and `aegis-mid-ds` at it. That covers `aegis-core-infra`, `aegis-product-eng`, and `the-brain`.
2. Leave every `aegis-free-*` agent, including `aegis-infra`, on the existing free key.
3. Do not move the shared flash combo onto Pro pricing. That is where the tokens are.
4. Either/or stays: this is OmniRoute API-key routing, not Claude Pro subscription auth.

**Status:** Hamid declined a paid Gemini key on 2026-09-22. This proposal was not applied. The free-tier routing change that was applied is in `memory/fallback-pools.md` (2026-09-22 changelog). Do not add a paid key.
- 2026-09-21: Formalized `/propose-agent-tier` for **aegis-growth** (free-pool / `aegis-free-37`) after process-gap flag — awaiting `aegis-ceo` explicit approve (was backfilled 2026-09-16 without full propose→approve trail).
- 2026-09-17: Diversified OmniRoute fallback pools (per-agent combo lanes). See `memory/fallback-pools.md`. Fixed free agents that had been pointing at mid combo `sonnet`.
- 2026-09-13: File created. Backfilled `aegis-ceo` (live, premium) and `aegis-infra` (proposed, free-pool, not yet applied) for context. Recorded `aegis-threat-intel`'s tier (proposed, free-pool via OmniRoute/gemini-3.7-flash, not yet applied — dependency on OmniRoute + an explicit auth-mode switch, neither confirmed done).
- 2026-09-13: Folded the container's threat-intel status update into this file. Marked `aegis-threat-intel` live on OmniRoute free-pool after explicit auth flip. Marked `aegis-infra` live on the same free-pool path (subscription cleared; OmniRoute `.env` durable via `.credentials.enc`).
- 2026-09-13: Proposed free-pool tier (`gemini/gemini-3.7-flash` via OmniRoute free pool) for new hire **P&L / MRR Analyst** — live name `aegis-analyst`.
- 2026-09-13: Proposed mid-cost tier (paid API via OmniRoute cost-optimized routing) for new hire **the-brain (VP)**.
- 2026-09-14: Recorded `aegis-core-infra` mid-cost OmniRoute applied (subscription auto-assign cleared; platform API key off; Slack `#aegis-core-infra` `C0C1H5WD5NJ`; A2A core-infra↔ceo).
- 2026-09-14: Mid-cost fallback chain fixed fleet-wide (`sonnet`/`aegis-mid` → DeepSeek Pro / GPT-OSS / Gemini Pro; no flash). Confirmed on `the-brain` + `aegis-core-infra` with real OmniRoute logs.
- 2026-09-14: Proposed free-pool tier (`gemini/gemini-3.7-flash`) for **Data/Quality Analyst** (`aegis-data-quality`). Merged into committed file after stash recovery (A2A closeout pull).
- 2026-09-14: `aegis-data-quality` deployed from GitHub, free-pool OmniRoute applied, A2A hub edges granted, routing table updated.
- 2026-09-16: Backfilled `aegis-growth` (free-pool) — was live on Trinity but missing from this file; fixed infra dashboard "Agents Tracked" 7→8.
- 2026-09-16: Proposed mid-cost tier (`sonnet` / `aegis-mid`) for new hire **Capability & Learning Scout** (`aegis-scout`) — Slack `#aegis-infra` close-out confirmed.
- 2026-09-16: `aegis-scout` mid-cost tier recorded; position spec + deploy underway.
- 2026-09-16: `aegis-scout` deployed from GitHub; mid-cost OmniRoute applied; Slack + A2A hub edges granted; mid-cost probe OK.
- 2026-09-16: `/trial-scout` success (GrowthBook → Growth; Slack `#aegis-scout` delivery confirmed); all four schedules enabled. Temporary free alias `claude-sonnet-4-6` while Gemini Pro mid path is quota-blocked / CFP 6k-capped.
- 2026-09-16: Confirmed `claude-sonnet-4-6` = OmniRoute free flash chain (not Claude Pro). Confirmed fleet-wide mid 6k-cap exposure (`sonnet` long-prompt → CFP 502). Created restore reminder `rem_fcab848e2aa940f8b21c1e6f7da17bae` + audit Step 4b.

## Phase 1 component owners (enforcer) — 2026-09-17

Phase 1 hires: `aegis-gateway`, `aegis-policy-engine`, `aegis-model-router`, `aegis-agent-gate`, `aegis-audit`. Deferred: dashboard, sdk, redteam, deploy, input-defense, output-defense, shared, examples.

| Agent | Tier | Model | Level | Why |
|-------|------|-------|-------|-----|
| aegis-gateway | Free-pool | OmniRoute `gemini/gemini-3.7-flash` (flash-lite fallback chain) | SE I | Component ownership + PR drafts; capacity too thin for mid-cost×5 |
| aegis-policy-engine | Free-pool | same | SE I | same |
| aegis-model-router | Free-pool | same | SE I | same |
| aegis-agent-gate | Free-pool | same | SE I | same — inherits adapt_defense backlog |
| aegis-audit | Free-pool | same | SE I | same |

**Auth mode:** OmniRoute API-key routing; `use_platform_api_key=false`; no Claude Pro subscription (mutually exclusive).
**Capacity gate:** 469×429 on 2026-09-17 → stagger deploys; schedules off until first audit.
**Access:** scoped `AEGIS_PR_TOKEN` per agent (Contents R/W + PRs R/W on `hamidmatiny/aegis` only). Not the operator's broad `repo` OAuth token.
**Status:** Proposed by hire pipeline / aegis-infra role. Applying staggered free-pool deploy.
**Token habits:** component-subdir reads only; OmniRoute compression; batch audits; memory reuse; spare tokens → SI per daily-allocation.


### GitHub access boundary — Phase 1 component owners (2026-09-17)

**Required credential:** one fine-grained PAT **per agent** (or one shared machine-user PAT used only by these five), named e.g. `aegis-component-pr-only`, scoped to:

- Resource owner: `hamidmatiny`
- Repository access: **Only** `hamidmatiny/aegis` (not all repos, not aegis-ceo / Trinity / other agent repos)
- Permissions: Contents **Read and write**; Pull requests **Read and write**; Metadata Read
- **Not granted:** Administration, Actions, Secrets, Environments, Merge queues bypass, other repos

Inject as `AEGIS_PR_TOKEN` via Trinity credentials inject. Agents' `/audit-repo-access` must fail-closed if the token can read `hamidmatiny/aegis-ceo` (too broad).

**Explicitly NOT used:** operator Cursor/`gh` OAuth token (`repo`+`workflow` scopes) — that remains Hamid's interactive credential, never injected into agents.

**Merge control:** `main` branch protection on `hamidmatiny/aegis` enabled 2026-09-17 — required approving review = 1, enforce_admins, no force pushes. Agents open PRs only.

**Current state:** `AEGIS_PR_TOKEN` intentionally empty on all five until Hamid mints the scoped PAT(s). Public clone via `AEGIS_REPO_URL` works without a token.

## aegis-product-eng (Product Engineering Manager)

**Tier:** Mid-cost — OmniRoute `sonnet` / `aegis-mid` chain (same class as `the-brain` / `aegis-core-infra`).
**Level:** Manager (L5) — **structural hire exception** 2026-09-17 (not organic SE-track promotion). Fresh start; no fabricated prior history.
**Why mid-cost:** Real coaching / Protocol B judgment across five enforcer component owners; free-pool flash insufficient for manager bar.
**Auth mode:** OmniRoute API-key routing; `use_platform_api_key=false`; not Claude Pro.
**Reports:** → `aegis-ceo`. Direct reports: gateway, policy-engine, model-router, agent-gate, audit (tags `reports-to-aegis-product-eng`).
**Status:** Live on Trinity (`github:hamidmatiny/aegis-product-eng@main`). Slack `#aegis-product-eng` C0C2S6U2XN0; Hamid invited.
**Capacity note:** Fleet still thin on free-pool (478×429 on 2026-09-17) — one mid-cost manager only; schedules off until first `/review-team`.


## 2026-09-20 — aegis-redteam (proposed)

- **Agent:** `aegis-redteam`
- **Proposed tier:** Mid-cost (OmniRoute cost-optimized) — adversarial judgment + bypass packaging
- **Auth:** OmniRoute API-key (not subscription)
- **Status:** **Pending aegis-infra `/propose-agent-tier` apply** — agent is live on default creation auth until flipped
- **Schedules:** Live gateway attack batch every 4h; autonomy **enabled**
