# MEMORY

Consult-first spine for `aegis-infra`. Topic logs under `memory/*.md` remain the append-only audit trail — do not delete them. Update this file when facts change; overwrite **Last session summary** each meaningful run.

## Verified facts

- **2026-09-13** — `aegis-ceo`: premium (Claude Pro subscription). Source: `memory/tier-assignments.md`.
- **2026-09-13** — `aegis-infra`, `aegis-threat-intel`, `aegis-analyst`: free-pool via OmniRoute (Gemini); Trinity subscription cleared, `use_platform_api_key=false`, `.credentials.enc` for durability. Source: `memory/tier-assignments.md` + live chat `Provider: gemini` checks.
- **2026-09-13** — OmniRoute is the live free/mid router for this fleet (local gateway; health/routing confirmed in ops). Source: `/audit-omniroute` runs + README gotchas.
- **2026-09-13** — Gemini Flash remains on free-tier path used by free-pool; Pro models are paid. Source: `memory/pricing-checks.md`.
- **2026-09-13** — SU-2026-09-13-1 and SU-2026-09-13-2 approved by Hamid. Source: `memory/skill-proposals.md`.

## Rules / lessons

- Tier and skill changes: propose → explicit **approved**/**approve** → apply. Silence is not approval. (`/propose-agent-tier`, `/propose-skill-upgrade`)
- Claude subscription auth and OmniRoute/API-key are mutually exclusive per agent in Trinity.
- New Claude-runtime agents auto-get Pro subscription (Trinity #74) — free-pool requires post-hire manual flip. See `/propose-agent-tier` FM-1 + README.
- Free-pool durability needs `.credentials.enc` / re-inject after subscription or platform-key regressions. See `/audit-omniroute` FM-1.
- Mid-cost Trinity model alias (e.g. `the-brain` `sonnet`) does not survive restart until durable `AGENT_RUNTIME_MODEL`. See `/audit-omniroute` FM-2.
- Independent verification must be a separate free-pool call with claim + sources only — never self-grade in the producer context. (`/verify-revenue-claim`, `/propose-skill-upgrade` FM-3)
- Number-reporting agents: spot-check live API shape before trusting CLAUDE.md. (`/propose-skill-upgrade` FM-2)
- **Fail-closed gate:** no explicit positive result (`PASS` / `approved` / `pull-ok` / `delivered`) → do not claim success. Every `/propose-skill-upgrade` run must check this (Step 2b / FM-4).

## Open / unresolved

- Durable `AGENT_RUNTIME_MODEL` (or equivalent) for mid-cost aliases across restart — still a platform gap; manual re-apply for `the-brain`.
- `/propose-skill-upgrade` schedule — not enabled yet (manual only).
- Fleet-wide structured memory beyond `aegis-infra` — not approved yet.
- Independent verification expansion beyond `aegis-analyst` — wait for a proven PASS/FAIL cycle. **(2026-09-13: first live PASS cycle completed — expand still needs explicit approval.)**
- OmniRoute precise token counts for `/track-usage` — still limited; Trinity cost metadata may price as Claude even when Gemini is used (`memory/usage-log.md`).
- Durable A2A edge `aegis-analyst` → `aegis-infra` is now permitted on this Trinity instance (required for verify loop).

## Last session summary

**2026-09-13** — Applied SU-2026-09-13-3 (a)(b); DN-1A; DN-2B+mandatory queue. A2A: analyst→ceo, TI→ceo. E2E: analyst anomaly → ceo exec `CuCc-tX8Kvft008v1bJqzA`; TI finding → ceo exec `MfNaGAz4AtJWOiheDUmDwA` (both `source_agent` set, delivery confirmed). VP synthesize pull-gate live on container (Cornelius read-only upstream — volume-local).
