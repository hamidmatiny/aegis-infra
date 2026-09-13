# Skill Upgrade Proposals

Running record of proposed / approved / declined skill, verification, and memory-structure upgrades. Appended by `/propose-skill-upgrade`. Same explicit **approved** / **approve** gate as `memory/tier-assignments.md` — silence is not approval.

---

## Proposal SU-2026-09-13-1 — Independent verification for `aegis-analyst` revenue reports (pilot)

**Status:** approved (2026-09-13) by Hamid — **applied** (2026-09-13)  
**Agent:** `aegis-analyst` (fleet-first pilot; not fleet-wide)

**Gap:** Revenue/MRR figures leave the fleet and reach Hamid / `aegis-ceo` with no second check that the claimed numbers are supported by the cited corp-orchestrator payload. A producer that grades its own report in the same context is biased toward agreeing with itself.

**Why now:** Analyst is the only agent whose primary product is a money number ($29.00 CAD / 1 subscriber was the verified baseline in its CLAUDE.md). Wrong MRR is high-cost for decision-making; a cheap structural check is proportionate. Other outbound reports (threat-intel escalations, VP synthesis) can follow once this pilot works.

**Applied as:**

1. `aegis-analyst` `/check-revenue` — draft claim → Step 5 independent verify via `chat_with_agent` → `aegis-infra` `/verify-revenue-claim` (claim + sources only) → publish only on `PASS`.
2. New skill `aegis-infra` `/verify-revenue-claim` — structural PASS/FAIL only.
3. Local runs without Trinity chat skip verify and must say so — no fake PASS.

**Tier/cost:** free-pool verifier call.  
**Pilot scope:** `aegis-analyst` only until a real PASS/FAIL cycle is proven.

---

## Proposal SU-2026-09-13-2 — Structured memory standard (pilot: `aegis-infra`)

**Status:** approved (2026-09-13) by Hamid — **applied** (2026-09-13)  
**Agent:** `aegis-infra` first; other agents only after further approval

**Gap:** Loose topic logs without a consult-first spine.

**Applied as:** created `memory/MEMORY.md` (Verified facts / Rules / Open / Last session summary). Topic logs (`tier-assignments.md`, `usage-log.md`, `pricing-checks.md`, `skill-proposals.md`) kept as append-only satellites.

---

## Change log

- 2026-09-13: File created. Logged SU-2026-09-13-1 and SU-2026-09-13-2 as proposed.
- 2026-09-13: Both approved by Hamid; both applied (analyst verify step + infra `/verify-revenue-claim`; `memory/MEMORY.md` retrofit).
