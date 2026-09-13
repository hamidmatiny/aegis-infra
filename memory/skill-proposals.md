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

## Proposal SU-2026-09-13-3 — P0 fail-closed wording (check-revenue + VP synthesize)

**Status:** approved (2026-09-13) by Hamid — **applied** (2026-09-13)  
**Agents:** `aegis-analyst`, `the-brain`  
**Type:** narrow logic / wording fix — **no new capability**

### (a) `aegis-analyst` `/check-revenue` — applied

Publish only after explicit `PASS:`. Skip/deny/timeout are never publish-worthy. Step 6/7 wording updated; residual "or explicit skip" removed.

### (b) `the-brain` `/synthesize` — applied

Pull gate: exit 0 + four SHAs required; else abort with `status: pull-failed`. Skill written into live `agent-the-brain` container (upstream is read-only Cornelius — **volume-local until own-repo bind**; survives normal restarts, at risk on recreate from template).

---

## DN-2026-09-13-1 — `aegis-analyst` `/escalate-anomaly` delivery

**Decision:** Option A (2026-09-13) — **applied**  
- Granted `aegis-analyst` → `aegis-ceo` A2A permission  
- Skill uses `mcp__trinity__chat_with_agent`; claim escalated only after confirmed delivery; on failure: "flagged, delivery failed"

## DN-2026-09-13-2 — `aegis-threat-intel` `/scan-threats` delivery

**Decision:** Option B + mandatory queue on chat failure (2026-09-13) — **applied**  
- Granted `aegis-threat-intel` → `aegis-ceo` A2A permission  
- Claim CEO notified only after confirmed delivery  
- Operator-queue alert **mandatory** when ceo-chat fails (not only "if urgent")  
- `CLAUDE.md` escalation channels + `/scan-threats` Step 7 updated

---

## Change log

- 2026-09-13: File created. Logged SU-2026-09-13-1 and SU-2026-09-13-2 as proposed.
- 2026-09-13: Both approved by Hamid; both applied (analyst verify step + infra `/verify-revenue-claim`; `memory/MEMORY.md` retrofit).
- 2026-09-13: Proposed SU-2026-09-13-3; logged DN-2026-09-13-1/2; standing fail-closed check in `/propose-skill-upgrade` Step 2b.
- 2026-09-13: SU-2026-09-13-3 approved+applied; DN-1 Option A and DN-2 Option B+mandatory queue approved+applied; A2A edges analyst→ceo and TI→ceo granted.
