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
**Status:** Approved by CEO / Hamid (2026-09-13). Applied and live on OmniRoute free-pool (verified 2026-09-13: chat traffic `Provider: gemini`, platform API key disabled, OmniRoute `.env` + `.credentials.enc` in place).

## aegis-analyst (P&L / MRR Analyst)

**Tier:** Free-pool
**Provider/model:** `gemini/gemini-3.7-flash` via OmniRoute free pool
**Why:** Reading structured JSON endpoints (`/bev/trajectory`, `/bev/summary`), formatting numeric reports, and checking for explicit arithmetic anomalies is high-volume structured reporting — not Claude Pro or mid-cost. (Recorded in stash as `aegis-mrr-analyst`; live Trinity name is `aegis-analyst`.)
**Auth mode:** OmniRoute API-key routing, not subscription auth (mutually exclusive per agent in Trinity).
**Token-saving habits assigned:** query specific JSON fields; OmniRoute compression; batch scheduled reporting; reuse memory baselines.
**Status:** Approved by CEO / Hamid (2026-09-13). Live on Trinity as `aegis-analyst` (free-pool intended; confirm OmniRoute auth still applied after any subscription auto-assign).

## the-brain (VP)

**Tier:** Mid-cost — OmniRoute combo `sonnet` / `aegis-mid` (priority: CFP DeepSeek Pro → GPT-OSS → Gemini 3.1 Pro preview). No flash in mid chain.
**Why:** Synthesis / VP judgment needs stronger reasoning than free-pool; not founder-facing premium subscription.
**Auth mode:** OmniRoute API-key routing, not subscription auth.
**Status:** Approved by CEO / Hamid (2026-09-13). Live; in-memory `sonnet` alias must be re-PUT after restart until durable.

## aegis-core-infra

**Tier:** Mid-cost — OmniRoute combo `sonnet` / `aegis-mid` (priority: CFP DeepSeek Pro → GPT-OSS → Gemini 3.1 Pro preview). No flash in mid chain.
**Why:** Real Docker/CI/migration reasoning needs more than free-pool reliably provides; no write/deploy/block authority so Claude Pro subscription is not warranted.
**Auth mode:** OmniRoute API-key routing, not subscription auth (mutually exclusive per agent). `use_platform_api_key=false`; subscription cleared after create-time auto-assign to Hamid's Pro.
**Token-saving habits assigned:** query specific diffs/targeted files; OmniRoute compression; batch review passes; reuse `memory/` baselines.
**Status:** Approved by Hamid (2026-09-14 hire brief). Applied and live on Trinity (`github:hamidmatiny/aegis-core-infra@main`): auth `not_configured`, model `sonnet`, OmniRoute `.env` + `.credentials.enc` in place. Note: in-memory `sonnet` alias does not survive restart (same class as `the-brain`) — re-PUT model after restart until durable. Verified 2026-09-14: chat served `deepseek-ai/deepseek-v4-pro-0813` via combo `sonnet` (not flash).

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
**Status:** Approved by Hamid (2026-09-14, Slack). Applied and live on Trinity (`github:hamidmatiny/aegis-data-quality@main`): auth `not_configured`, `use_platform_api_key=false`, OmniRoute `.env` + `.credentials.enc` in place, model `claude-sonnet-4-6` (free-pool combo). A2A hub `aegis-data-quality`↔`aegis-ceo` granted. *(Recovered from stash@{0} then onboarded 2026-09-14.)*

## Change log

- 2026-09-13: File created. Backfilled `aegis-ceo` (live, premium) and `aegis-infra` (proposed, free-pool, not yet applied) for context. Recorded `aegis-threat-intel`'s tier (proposed, free-pool via OmniRoute/gemini-3.7-flash, not yet applied — dependency on OmniRoute + an explicit auth-mode switch, neither confirmed done).
- 2026-09-13: Folded container "TI Approved" update into this file. Marked `aegis-threat-intel` approved by CEO/Hamid and live on OmniRoute free-pool after explicit auth flip. Marked `aegis-infra` live on the same free-pool path (subscription cleared; OmniRoute `.env` durable via `.credentials.enc`).
- 2026-09-13: Proposed free-pool tier (`gemini/gemini-3.7-flash` via OmniRoute free pool) for new hire **P&L / MRR Analyst** (Approved) — live name `aegis-analyst`.
- 2026-09-13: Proposed mid-cost tier (paid API via OmniRoute cost-optimized routing) for new hire **the-brain (VP)** (Approved).
- 2026-09-14: Recorded `aegis-core-infra` mid-cost OmniRoute applied (subscription auto-assign cleared; platform API key off; Slack `#aegis-core-infra` `C0C1H5WD5NJ`; A2A core-infra↔ceo).
- 2026-09-14: Mid-cost fallback chain fixed fleet-wide (`sonnet`/`aegis-mid` → DeepSeek Pro / GPT-OSS / Gemini Pro; no flash). Confirmed on `the-brain` + `aegis-core-infra` with real OmniRoute logs.
- 2026-09-14: Proposed and approved free-pool tier (`gemini/gemini-3.7-flash`) for **Data/Quality Analyst** (`aegis-data-quality`) — Hamid Slack approval. Merged into committed file after stash recovery (A2A closeout pull).
- 2026-09-14: `aegis-data-quality` deployed from GitHub, free-pool OmniRoute applied, A2A hub edges granted, routing table updated.
