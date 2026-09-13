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

## Change log

- 2026-09-13: File created. Backfilled `aegis-ceo` (live, premium) and `aegis-infra` (proposed, free-pool, not yet applied) for context. Recorded `aegis-threat-intel`'s tier (proposed, free-pool via OmniRoute/gemini-3.7-flash, not yet applied — dependency on OmniRoute + an explicit auth-mode switch, neither confirmed done).
- 2026-09-13: Folded container "TI Approved" update into this file. Marked `aegis-threat-intel` approved by CEO/Hamid and live on OmniRoute free-pool after explicit auth flip. Marked `aegis-infra` live on the same free-pool path (subscription cleared; OmniRoute `.env` durable via `.credentials.enc`).
