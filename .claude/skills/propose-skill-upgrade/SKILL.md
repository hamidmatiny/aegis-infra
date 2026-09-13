---
name: propose-skill-upgrade
description: Review live agents' skills/missions and propose (never apply) skill additions, model changes, verification checks, or memory-structure improvements — same approve-before-apply gate as tier proposals
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, mcp__trinity__list_agents, mcp__trinity__get_agent, mcp__trinity__report
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-09-13
  author: aegis-infra
---

# Propose Skill Upgrade

## Purpose

Periodically (manual trigger first — **no schedule until Hamid enables one**) review each live agent's skillset against its stated mission and propose — never apply — upgrades: a new skill worth building, a model/tier change worth considering (hand off to `/propose-agent-tier` when the change is primarily tier/auth), or a structural improvement (independent output verification, structured memory retrofit).

**Hard rule:** this skill never grants any agent new capabilities, never edits another agent's live tools/config, and never schedules itself. Same gate as `/propose-agent-tier`: propose → explicit Hamid/`aegis-ceo` approve → separate apply step.

## What Trinity actually supports (do not invent mechanisms)

Verified against this fleet's Trinity instance / docs — prefer these over patterns from other platforms:

| Pattern | Trinity reality |
|---------|-----------------|
| Separate cheap verification call | **Yes** — `mcp__trinity__chat_with_agent` (or HTTP chat) to a free-pool agent with a prompt that includes *only* the claim artifact + cited source excerpts. Same-agent second turn that still sees the prior reasoning trail is **not** independent enough. |
| Scheduled review | **Yes** — agent schedules in `template.yaml` / Trinity UI; ship `enabled: false` until approved. |
| Webhook-triggered runs | **Yes** — webhook triggers exist; usable later for "on report publish" if we wire them. Not required for v1. |
| Automatic pre-finalize hook inside another agent's skill | **No first-class Trinity hook** — implement as an explicit step *inside* that agent's skill (e.g. `/check-revenue` calls infra/verifier) or as a follow-up chat after the report draft. Do not claim an invisible platform interceptor. |
| Vision / screenshot self-check | **Not assumed** — do not propose vision-based verification unless Trinity + this fleet's runtime are confirmed to support it for that agent. |

## Process

### Step 1: Roster + sources

1. Call `mcp__trinity__list_agents` (if available) for the live roster — do not invent hires from memory.
2. For each agent under review, read what you can: that agent's `CLAUDE.md` / skills / `memory/` from its GitHub repo or a known local checkout. Prefer committed repo state.
3. Read `memory/skill-proposals.md` and `memory/tier-assignments.md` so you don't re-propose declined or already-approved items.

### Step 2: Gap analysis (per agent)

For each agent, ask:

- Does every Core Capability in its CLAUDE.md have a real skill/playbook?
- Are there recurring request types still hitting "playbook gap"?
- Did a real failure this period expose a missing skill step, a missing "known failure modes" section, or a missing verification check?
- Would structured memory (`memory/MEMORY.md` standard — see proposal template below) reduce re-derivation?
- Is the current tier/model still appropriate? If the main ask is tier/auth, **invoke `/propose-agent-tier`** instead of burying it here — cross-link both memory files.

### Step 3: Draft proposals (cite everything)

Every proposal **must** include:

- **Gap:** what is missing or broken (concrete)
- **Why now:** evidence (incident, missing playbook, stale model, empty memory, etc.)
- **Proposed change:** skill / verification step / memory retrofit / model change
- **Tier/cost if approved:** free-pool / mid-cost / premium — and whose tokens pay for it
- **Trinity mapping:** which real mechanism (chat_with_agent, skill step, schedule) — not a fantasy hook
- **Pilot scope:** start with one agent unless Hamid asks for broader

### Step 4: Present — do not apply

Format:

```
## Skill Upgrade Proposal — [id] — [agent or fleet]

**Gap:** …
**Why now:** …
**Proposed change:** …
**Tier/cost if approved:** …
**Trinity mapping:** …
**Pilot scope:** …
**Depends on:** …

Reply **approved** / **approve** to accept, or decline with a reason. Nothing is applied until then.
```

### Step 5: Record

Append to `memory/skill-proposals.md` (create if absent) with status `proposed`. On explicit approve/decline, update that entry's status and date. Never mark approved from silence.

If Trinity `mcp__trinity__report` is available, publish as `report_type: aegis_infra.skill_proposal`, `display_hint: markdown`. Skip silently if unavailable.

## Standing practice: skills that compound

When a real failure is diagnosed (auth default, OmniRoute durability, data-contract mismatch, etc.):

1. Write a **Known failure modes** section into the **skill that caused or exposed it** (this file or the sibling skill) — not only into README.
2. Optionally also note it in README for humans.
3. Future invocations of that skill must read those modes before acting.

## Known failure modes

### FM-1 — Proposing platform magic Trinity does not have

**What went wrong:** Cross-platform docs describe event hooks / vision self-checks that Trinity may not expose as agent-callable primitives.

**Correct behavior:** Always map proposals to `chat_with_agent`, explicit skill steps, schedules, or webhooks that exist. If nothing maps cleanly, say so and propose the closest real equivalent — never claim an invisible pre-finalize interceptor.

### FM-2 — Reviewing number-reporting agents without checking the live data contract

**What went wrong:** An agent's CLAUDE.md / skill prose can drift from the live API shape (e.g. MRR fields present in docs but null/missing in the HTTP response until the product endpoint was fixed). A skill-upgrade review that only reads CLAUDE.md will "confirm" a capability that fails at runtime.

**Correct behavior:** For any agent whose mission is numeric reporting, spot-check the live read path (or the last successful execution log / cited payload) before proposing "add verification" or "all good." Cite the endpoint or execution, not just the markdown.

### FM-3 — Self-grading instead of independent verification

**What went wrong:** Asking the same model, in the same context that produced a report, to "check if this looks right" inherits the reasoning trail and systematically under-detects errors.

**Correct behavior:** Verification proposals must specify a **separate** free-pool call whose prompt contains only the claim artifact + source excerpts — no chain-of-thought from the producer.

## Outputs

- One or more skill-upgrade proposals, clearly marked as proposals
- Updated `memory/skill-proposals.md`
- Optional Trinity report
