---
name: verify-revenue-claim
description: Independent structural check that an aegis-analyst revenue claim is supported by the cited corp payload — claim + sources only, no producer reasoning
allowed-tools: Read, Bash
user-invocable: true
metadata:
  version: "1.2"
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

If either is missing, the reply is `FAIL: missing claim or sources` — then still do the Final step.

**Do not call `list_agents` to "find" the analyst.** Agent-scoped `list_agents` only returns agents you have *outbound* A2A permission to chat with (today: `aegis-ceo` + self). `aegis-analyst` can message you (`analyst → infra`) but you cannot message them back, so they will **not** appear in your `list_agents` result. That is intentional Protocol A asymmetry — not a missing agent, not a broken verify path. This skill only needs the claim + sources in the inbound message.

## Process

The comparison is deterministic — do not do it by reading the JSON yourself. Put the claim and the cited excerpts into one JSON object and pipe it to the script:

```bash
python3 scripts/verify_revenue_claim.py <<'EOF'
{"claim":   {"mrr": 1234.5, "currency": "USD", "paying_subscribers": 7, "signups": 3,
             "not_returned": []},
 "sources": {"summary": <bev/summary excerpt as cited>, "trajectory": <bev/trajectory excerpt as cited>}}
EOF
```

- `mrr` is in major units (e.g. dollars). The script matches it against `mrr_usd`, else `mrr_cents / 100`, else `mrr_display`, and checks `currency` when both sides state one.
- `paying_subscribers` is matched in the summary excerpt; `signups` in the trajectory excerpt. Omit a field the claim doesn't make.
- List a field in `not_returned` when the claim says the API did not return it; the script FAILs if the excerpt contradicts that.
- The script prints exactly one line: the `PASS: ...` / `FAIL: ...` reply. Use it verbatim.

Do **not** invent missing numbers, fetch live endpoints yourself (unless the caller explicitly asked you to and provided `CORP_READONLY_TOKEN` — default is do not fetch), or grade prose quality.

### If you must fetch live BEV (optional path only)

Default remains: **do not fetch** — use the cited Sources in the message. When the caller explicitly asks you to re-query corp and a `CORP_READONLY_TOKEN` is available (message or `/home/developer/.env`), load the token and call **GET only**:

```bash
# Token is often in .env but not exported into the shell — load it first
set -a && . /home/developer/.env && set +a
test -n "$CORP_READONLY_TOKEN" || { echo "FAIL: CORP_READONLY_TOKEN missing"; exit 1; }

# Prefer curl. Cloudflare returns 403 / error code 1010 for bot-looking UAs
# (default Python urllib / bare curl). That is a WAF block, not a bad token.
curl -sS -H "Authorization: Bearer $CORP_READONLY_TOKEN" \
  -H "User-Agent: aegis-infra/1.0 (+https://defenseaegis.org)" \
  https://defenseaegis.org/api/corp/v1/bev/summary
curl -sS -H "Authorization: Bearer $CORP_READONLY_TOKEN" \
  -H "User-Agent: aegis-infra/1.0 (+https://defenseaegis.org)" \
  https://defenseaegis.org/api/corp/v1/bev/trajectory
```

If you must use Python, set the same `User-Agent` on `urllib.request.Request` / `requests` headers. Never treat a 1010 as an expired token until you have confirmed a proper UA was sent. Feed the fetched JSON to the script as `sources`.

## Reply format (exactly)

The reply **to the caller** is one of:

```
PASS: claim matches cited sources (MRR <value> <currency>, paying_subscribers <n>, ...)
```

```
FAIL: <field> claimed <X> but source shows <Y>
```

No preamble. No rewrite of the report. "No preamble" applies to the A2A reply text only — it does **not** exempt this run from the Slack close-out below.

## Final step — Slack completed-task close-out (mandatory)

After the reply line is decided — PASS **or** FAIL, including `missing claim or sources` — post to `#aegis-infra`: `mcp__trinity__list_channel_groups` (`channel_type: "slack"`) → `mcp__trinity__send_group_message`. Keep it short:

```
verify-revenue-claim for aegis-analyst (A2A): <PASS/FAIL line from the script>. Replied to aegis-analyst in the A2A chat.
```

No commit trailers (`Co-Authored-By`, `Generated with Claude Code`). This is the step inbound A2A runs kept skipping (Trinity had to post fallback close-outs, 2026-10-09). The run is not done until the post is confirmed or its error is stated. See CLAUDE.md § HARD GATE — Slack completed-task close-out.

## Known failure modes

### FM-1 — Self-grading contamination

**What went wrong:** Checking a claim while still holding the producer's reasoning trail systematically under-detects errors.

**Correct behavior:** If this chat already contains the analyst's full analysis trail, refuse and ask for a fresh invocation with claim + sources only — or ignore prior context and use only the explicit Claim/Sources blocks in the latest message.

### FM-2 — Cloudflare WAF 1010 on live BEV fetch

**What went wrong:** Optional live re-query (or ad-hoc BEV curl) used default Python/`curl` User-Agent → Cloudflare **403 / error code 1010**. Agents then misread that as a bad/expired `CORP_READONLY_TOKEN` and the analyst publish gate stalls.

**Correct behavior:** Always send `User-Agent: aegis-infra/1.0 (+https://defenseaegis.org)` (same pattern as `aegis-growth`'s BEV reads). Prefer `curl` over bare `urllib`. A 1010 with no UA is a WAF block, not credential failure.

### FM-3 — `list_agents` does not show `aegis-analyst`

**What went wrong (2026-09-17):** Infra answered a troubleshooting ask by calling `list_agents`, saw no `aegis-analyst`, and reported "cannot access aegis-analyst" — then ~2 minutes later successfully ran this skill on an inbound `analyst → infra` verify request.

**Correct behavior:** Treat missing analyst in `list_agents` as expected (outbound A2A only to `aegis-ceo`). Never refuse or delay `/verify-revenue-claim` because of that. Do not invent an access outage from a filtered roster.

### FM-4 — "No preamble" read as "no close-out"

**What went wrong (2026-10-09):** The strict reply format was taken as "send the one line and stop", so A2A-triggered runs ended without their own `#aegis-infra` close-out.

**Correct behavior:** Reply to the caller with the single line, then always do the Final step.

## Outputs

- Single-line `PASS` or `FAIL` (from `scripts/verify_revenue_claim.py`) as the A2A reply
- `#aegis-infra` close-out post
- No Trinity report publish from this skill (analyst owns publish after PASS)
