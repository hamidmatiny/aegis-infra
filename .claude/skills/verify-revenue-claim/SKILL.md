---
name: verify-revenue-claim
description: Independent structural check that an aegis-analyst revenue claim is supported by the cited corp payload — claim + sources only, no producer reasoning
allowed-tools: Read, Bash
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-09-13
  author: aegis-infra
---

# Verify Revenue Claim

## Purpose

Cheap, independent sanity check for `aegis-analyst` revenue outputs (SU-2026-09-13-1). You receive **only** a claim artifact and the cited source excerpts. You do **not** re-run corp-orchestrator, rewrite the report, or see the analyst's reasoning trail.

This is a structural PASS/FAIL — not a second full analysis.

## When invoked

Typically via Trinity `chat_with_agent` from `aegis-analyst`'s `/check-revenue` Step 5 (verify-before-publish). The inbound message should contain:

1. **Claim** — MRR (value + currency), paying subscribers / signups, checked_at timestamp (as the analyst intends to publish)
2. **Sources** — JSON excerpts from `GET .../bev/summary` and/or `GET .../bev/trajectory` that the claim cites

If either is missing, reply `FAIL: missing claim or sources` and stop.

## Process

1. Parse the claim's numeric fields (MRR display/value, currency, subscriber/signup counts).
2. Locate the matching fields in the provided source excerpts (`mrr_snapshot.mrr_display` / `mrr_usd` / `mrr_cents` + `currency`, `paying_subscribers`, trajectory signup entry, etc.).
3. Check support only:
   - Claimed MRR equals the cited summary field (same currency).
   - Claimed subscriber/signup count equals the cited field.
   - If the claim says a field was "not returned by the API", the excerpt must not contain a contradictory value for that field.
4. Do **not** invent missing numbers, fetch live endpoints yourself (unless the caller explicitly asked you to and provided `CORP_READONLY_TOKEN` — default is do not fetch), or grade prose quality.

## Reply format (exactly)

One of:

```
PASS: claim matches cited sources (MRR <value> <currency>, subscribers/signups <n>)
```

```
FAIL: <field> claimed <X> but source shows <Y>
```

No preamble. No rewrite of the report.

## Known failure modes

### FM-1 — Self-grading contamination

**What went wrong:** Checking a claim while still holding the producer's reasoning trail systematically under-detects errors.

**Correct behavior:** If this chat already contains the analyst's full analysis trail, refuse and ask for a fresh invocation with claim + sources only — or ignore prior context and use only the explicit Claim/Sources blocks in the latest message.

## Outputs

- Single-line `PASS` or `FAIL` as above
- No Trinity report publish from this skill (analyst owns publish after PASS)
