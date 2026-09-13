# Tier Assignments

Running record of proposed and approved tier/model assignments across the fleet. Appended to by `/propose-agent-tier`; read by `/track-usage` and `/review-pricing`.

## aegis-ceo

**Tier:** Premium (subscription) — Hamid's Claude Pro subscription auth.
**Why:** Final judgment calls, CEO-adjacent decisions. First hire, predates this agent's tier-assignment process.
**Status:** Live (confirmed running on subscription auth as of 2026-09-13).

## aegis-infra

**Tier:** Free-pool — this agent's own stated policy ("be the boring one").
**Why:** Bookkeeping and routing logic; should be one of the cheapest agents to run.
**Status:** Proposed, not yet applied — still deployed on default auth (same as `aegis-ceo`'s tier) as of 2026-09-13. Moving it to OmniRoute free-pool is blocked on OmniRoute's free tier being confirmed live end-to-end (see `/audit-omniroute`).

## aegis-threat-intel

**Tier:** Free-pool — via OmniRoute, provider `gemini/gemini-3.7-flash`.
**Why:** High-volume, low-stakes CVE/security-news polling and classification. Doesn't need Hamid's scarce Claude Pro subscription or paid mid-cost API budget — exactly the free-pool use case.
**Auth mode:** OmniRoute API-key routing, not subscription auth (mutually exclusive per agent in Trinity).
**Dependency:** Requires OmniRoute free-pool routing confirmed live before this assignment can actually take effect — not yet verified as of 2026-09-13.
**Token-saving habits assigned:** filter feeds upstream before pulling full text into context; rely on OmniRoute's built-in compression; batch related CVE checks into one consolidated pass; reuse prior findings/baselines from its own memory instead of re-deriving history each time.
**Status:** Proposed and recorded (2026-09-13). Not yet applied — deployed agent is still on whatever auth mode this Trinity instance defaults new agents to, per `aegis-threat-intel`'s own onboarding checklist (`auth_mode_confirmed` step, currently unchecked). Requires an explicit `aegis-infra`/admin action to actually switch the agent's Trinity auth mode to OmniRoute-routed.

## Change log

- 2026-09-13: File created. Backfilled `aegis-ceo` (live, premium) and `aegis-infra` (proposed, free-pool, not yet applied) for context. Recorded `aegis-threat-intel`'s tier (proposed, free-pool via OmniRoute/gemini-3.7-flash, not yet applied — dependency on OmniRoute + an explicit auth-mode switch, neither confirmed done).
