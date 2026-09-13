---
name: review-pricing
description: Periodically re-check provider pricing and free-tier terms against current tier assignments, and propose rebalancing when something changed materially
allowed-tools: Read, Write, WebFetch, WebSearch, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-09-13
  author: aegis-infra
---

# Review Pricing

## Purpose

Model leaderboards and provider free-tier terms change monthly — this skill exists so a stale assumption ("Gemini Pro is free") doesn't sit unexamined for months. Re-check the pricing/free-tier pages for providers actually in use, compare against what `memory/tier-assignments.md` currently assumes, and propose rebalancing only where something changed materially.

## Process

### Step 1: List providers actually in use

Read `memory/tier-assignments.md` for the current set of provider/model assignments across the fleet (mid-cost and free-pool tiers only — premium is a fixed subscription, not a pricing question). If the file doesn't exist yet, there's nothing to re-check — say so and stop.

### Step 2: Check each provider's current terms

For each distinct provider named in an active assignment, use `WebSearch`/`WebFetch` to check its **current** pricing and free-tier page — not a leaderboard's summary of it, the provider's own page. Note the check date; these pages change without an announcement reaching this agent otherwise.

Look specifically for:

- A model that was free and no longer is (or vice versa)
- A free-tier rate limit that changed significantly
- A model that was recommended and has since been deprecated or superseded by something meaningfully better/cheaper for the same job

### Step 3: Compare against current assignments

For each change found, check whether it actually affects a live assignment. A pricing change to a model nobody here uses isn't material to this fleet. Only flag:

- An assignment that now costs meaningfully more than assumed
- A free-pool assignment whose free tier changed or disappeared (this is the urgent case — it can silently turn a "free" agent into a billed one)
- A clearly better option now available for a role already assigned elsewhere

### Step 4: Propose, don't apply

For each material change, propose a specific rebalance using the same reasoning shape as `/propose-agent-tier` — don't silently update `memory/tier-assignments.md` with a new assignment. Present:

```
## Pricing Review — [date]

**Checked:** [providers, with source URLs and check date]
**Material changes found:** [list, or "none — no rebalancing proposed"]

### Proposed rebalance: [agent name]
**Current:** [tier/provider/model]
**Why it needs to change:** [the specific pricing/free-tier fact, with source]
**Proposed:** [new tier/provider/model]
```

If nothing material changed, say so plainly — a review that finds nothing is still real information, not a failure to find something.

### Step 5: Record and report

Whether or not anything changed, append the check to `memory/usage-log.md` or a dedicated `memory/pricing-checks.md` (create if useful) so there's a record of when providers were last verified — this is what lets a future run know if a check is overdue.

If running on Trinity and `mcp__trinity__report` is available, publish as `report_type: aegis_infra.pricing_review`, `display_hint: markdown`. Skip silently if the tool isn't available.

### Step 6: Escalate approved rebalances

A rebalance that's approved by Hamid or `aegis-ceo` gets applied the same way a fresh `/propose-agent-tier` decision would — recorded in `memory/tier-assignments.md`, with the live Trinity config change (if any) made only after that approval, never before.

## Outputs

- A pricing review with real sources and dates
- Rebalance proposals for material changes only — never a silent update
- A record of when each provider was last checked, so drift is visible over time
