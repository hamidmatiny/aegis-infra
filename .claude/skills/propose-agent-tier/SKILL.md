---
name: propose-agent-tier
description: Propose a tier (premium/mid-cost/free-pool) and specific provider/model for a newly hired or reassessed agent, with reasoning — never applies the change itself
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-09-13
  author: aegis-infra
---

# Propose Agent Tier

## Purpose

Decide which of the three tiers a given agent role should run on, and which specific provider/model within that tier — then present it as a proposal for Hamid or `aegis-ceo` to approve. This skill never applies a live config change; it produces a recommendation and appends it to this agent's memory once decided.

## The three tiers (from CLAUDE.md — do not redefine these)

- **Premium (subscription)** — Hamid's Claude Pro subscription auth. Reserved for the CEO and any future role doing final judgment calls, customer-facing work, or CEO-adjacent decisions. Scarce, shared, finite.
- **Mid-cost (paid API via OmniRoute)** — for real analysis/coding work frequent enough that subscription-only doesn't scale, but that still needs a genuinely strong model. Routed through OmniRoute's cost-optimized strategy, not a hardcoded single provider.
- **Free-pool (OmniRoute free tier)** — high-volume, low-stakes work: polling, status checks, formatting, first-pass drafts. Default starting point for a new agent until proven to need more.

## Process

### Step 1: Gather the role's actual requirements

Ask (via `AskUserQuestion` if not already given):

- What will this agent actually do day to day? (Be specific — "customer-facing negotiation" and "polling a status page" have very different tier needs.)
- Expected frequency/volume of calls (occasional, several times a day, continuous polling)?
- Does it need long-context reasoning, coding ability, or just formatting/classification?
- Is it customer-facing, or does it make judgment calls that are hard to walk back?

### Step 2: Apply the tier decision

Match the role against the three tiers above. Default to the **cheapest tier that plausibly covers the role** — the burden of proof is on moving up a tier, not down. A role should start free-pool unless there's a concrete reason (frequency + real reasoning need) to place it mid-cost, or a concrete reason (final judgment, customer-facing, CEO-adjacent) to place it premium.

**State the either/or explicitly.** Claude subscription auth and OmniRoute/API-key routing are mutually exclusive per agent in Trinity — subscription mode strips injected API keys. So the recommendation is never "subscription, but also route some calls through OmniRoute" — pick one.

### Step 3: Pick the specific model, if mid-cost or free-pool

Within OmniRoute's routing:

- **Mid-cost:** name a specific model tier appropriate to the work (a genuinely strong general model, not the cheapest thing that technically runs) and note it should go through OmniRoute's cost-optimized strategy rather than being hardcoded to one provider forever — see `/review-pricing` for why.
- **Free-pool:** name which free-tier pool/model is actually confirmed live (check `/audit-omniroute`'s last findings in `memory/tier-assignments.md` or run it fresh if stale). Don't propose a specific free-tier model you haven't confirmed still exists — free-tier terms change (e.g. Gemini Pro moving off free tier while Flash stayed free).

If you don't have a recent OmniRoute audit to draw on, run `/audit-omniroute` first rather than guessing at what's currently free.

### Step 4: Hand the new agent token-saving discipline

Every proposal includes concrete habits for the agent being assigned, not just the tier/model:

- Use documentation lookup tools instead of pasting whole files into context
- Rely on OmniRoute's built-in compression where available
- Batch small related subtasks into one call instead of many round-trips
- Reuse prior notes/memory instead of re-deriving the same answer

### Step 5: Present the proposal — do not apply it

Format:

```
## Tier Proposal — [agent name / role]

**Tier:** premium / mid-cost / free-pool
**Provider/model:** [specific]
**Why this tier, not one cheaper or more expensive:** [reasoning tied to Step 1's answers]
**Auth mode note:** subscription and OmniRoute/API-key are mutually exclusive here — this is a [subscription | OmniRoute] choice, not a blend
**Token-saving habits to hand this agent:** [from Step 4]
**Dependencies:** [e.g. "requires OmniRoute's X pool confirmed live — see latest /audit-omniroute"]
```

Ask explicitly whether to proceed. End every proposal with: reply **approved** / **approve** to accept, or decline with a reason. Silence is not approval. This skill stops here — actually wiring the agent's auth/credentials on Trinity is a separate action that needs Hamid's or the CEO's go-ahead, per this agent's operating rules (no live config changes without approval).

### Step 6: Record the decision

Once approved (not before), append the proposal and its outcome to `memory/tier-assignments.md` (create if absent) — this is the running record `/track-usage` and `/review-pricing` check against. Record proposals that were *not* approved too, with why, so the same ground isn't re-covered from scratch later.

If running on Trinity and `mcp__trinity__report` is available, publish the approved proposal as `report_type: aegis_infra.tier_proposal`, `display_hint: markdown`. Skip silently if the tool isn't available.

## Known failure modes

### FM-1 — Treating hire-time create as free-pool (Trinity #74)

**What went wrong:** Creating a Claude Code agent via `/create-agent:custom` + `/trinity:onboard` always triggers Trinity backend `#74` auto-assign: `_apply_subscription_env` round-robins the least-used Claude subscription onto every new Claude-runtime agent. There is no create-time opt-out for OmniRoute free-pool. A tier proposal of "free-pool" does **not** take effect at hire time.

**Correct behavior:** After every free-pool (or mid-cost OmniRoute) hire, record that the proposal is **approved but not yet applied** until the manual flip completes: clear subscription → `use_platform_api_key: false` → inject OmniRoute `.env` → restart → export `.credentials.enc` → verify OmniRoute traffic. Never tell Hamid the agent is "on free-pool" until that verification. Full steps live in README ("Known gotcha: new agents auto-land on Claude subscription").

### FM-2 — Confusing "approved proposal" with "live durable config"

**What went wrong:** Approval updates `memory/tier-assignments.md` but does not by itself persist OmniRoute credentials or mid-cost model aliases across restarts.

**Correct behavior:** After apply, confirm (1) `.credentials.enc` exists for free/mid OmniRoute agents, and (2) for mid-cost agents that need a Trinity chat model alias (e.g. `sonnet`), note the restart gotcha until durable `AGENT_RUNTIME_MODEL` exists — see `/audit-omniroute` FM-2.

### FM-3 — Skills compound: write failures back into this file

When a real hire/flip failure is diagnosed, add another Known failure modes entry here (and a short README pointer if humans need the flip checklist). Do not leave the lesson only in chat or an external log.

## Outputs

- A tier + model proposal, clearly marked as a proposal, not an action
- An updated `memory/tier-assignments.md` once a decision is made (approved or declined)
- Optionally, a published Trinity report of the outcome
