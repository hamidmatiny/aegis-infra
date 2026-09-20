---
name: token-budget
description: Report the best real token/quota horizon available for fleet OmniRoute providers — remaining today/week/month when queryable, honest rate-limit proxies otherwise. Use when asked for token budget, quota remaining, or free-tier headroom.
allowed-tools: Bash, Read, Write, mcp__trinity__list_channel_groups, mcp__trinity__send_group_message, mcp__trinity__report, mcp__trinity__list_agent_schedules, mcp__trinity__toggle_agent_schedule, mcp__trinity__chat_with_agent
user-invocable: true
disable-model-invocation: false
metadata:
  version: "1.3"
  created: 2026-09-15
  author: aegis-infra
  changelog:
    - "1.3: On sustained exhaustion, run /capacity-hold apply (real schedule toggles); on recovery, /capacity-hold lift — see docs/a2a-routing.md Protocol C"
    - "1.2: Skip full recompute when a successful run already completed in the last 6 hours (dedupe overlapping schedule/retry/manual)"
    - "1.1: Prefer live host bind mount ~/.omniroute (no snapshot staleness); auto-fail if only a stale snapshot remains"
    - "1.0: Initial — SQLite call_logs + documented rate-limit ceilings; no fabricated monthly balances"
---

# Token Budget

## Purpose

Report the most honest real remaining-capacity numbers for every provider currently in the fleet's OmniRoute routing. Prefer a true running balance when one exists. When a provider only exposes rate limits (RPM/TPM/RPD) with no monthly balance API, say so and use an explicit proxy — never present a proxy as a precise balance.

## Dedup gate (mandatory)

Before Step 0: if `memory/token-budget-log.md` (or Slack `#aegis-infra`) already has a **successful** `/token-budget` entry from the last **6 hours UTC**, do **not** re-query OmniRoute and re-post a near-identical report. Post a one-line close-out (`unchanged since <timestamp>`) and exit. Operator/`--force` / explicit "recompute now" overrides. Never start a second parallel `/token-budget` while one is in flight.

## Ground truth (verify each run; do not invent)

As of the 2026-09-15 investigation (re-check if OmniRoute schema or providers change):

| Provider / path | Running monthly balance? | What is actually queryable |
|-----------------|--------------------------|----------------------------|
| Gemini free tier (API key via OmniRoute) | **No** | Rate limits only (RPM / TPM / RPD). Google docs no longer publish a guaranteed free-tier table — project limits live in AI Studio. OmniRoute tables `provider_quota_state`, `api_key_token_limits`, `api_key_token_counters` were empty. Real local data: `~/.omniroute/storage.sqlite` → `call_logs` (tokens_in/out, status including 429). |
| Cloudflare Playground / CFP (`deepseek-*`, `gpt-oss-*` via mid combos) | **No** (not exposed to OmniRoute) | Usage only via `call_logs` rows with `provider=cloudflare-playground`. No remaining-balance field in local SQLite. |
| Claude Pro (premium subscription agents) | N/A (flat human subscription) | Not metered through OmniRoute. Report activity volume from Trinity, not a token balance. |

Community-measured Gemini free RPD ceilings (DEV Community measurement 2026-09-02; **not** Google-guaranteed for this project — label as proxy): Flash family ≈ 20 RPD; Flash-Lite family ≈ 500 RPD. RPM ≈ 5 (Flash) / 15 (Flash-Lite). Reset: midnight Pacific per Google docs.

## Process

### Step 0: Resolve live OmniRoute SQLite (no manual snapshot)

**Preferred (durable):** host bind mount of `~/.omniroute` → `/home/developer/.omniroute` (ro), set by `scripts/mount-omniroute-sqlite.sh`. Trinity recreates forward that bind. Do **not** rely on a one-time copy into `memory/`.

```bash
# Prefer live mount / OMNIROUTE_SQLITE. Reject stale memory/ snapshots when a
# live path exists. Never invent figures when nothing live is readable.
DB="${OMNIROUTE_SQLITE:-}"
if [ -z "$DB" ]; then
  for candidate in \
      "$HOME/.omniroute/storage.sqlite" \
      "/Users/hamidrezamatiny/.omniroute/storage.sqlite"; do
    if [ -f "$candidate" ]; then DB="$candidate"; break; fi
  done
fi
# Fallback only if live mount is absent (legacy snapshot) — label as STALE RISK
if [ -z "$DB" ] || [ ! -f "$DB" ]; then
  if [ -f "$HOME/memory/omniroute-storage.sqlite" ]; then
    DB="$HOME/memory/omniroute-storage.sqlite"
    echo "WARN: using memory/omniroute-storage.sqlite snapshot (may be stale). Re-run host scripts/mount-omniroute-sqlite.sh for live data."
  fi
fi
test -n "$DB" && test -f "$DB" || {
  echo "FAIL: OmniRoute SQLite missing. Expected live mount at ~/.omniroute/storage.sqlite (host scripts/mount-omniroute-sqlite.sh). Do not report as data loss — host DB may still exist outside the container."
  exit 1
}
echo "Using OmniRoute SQLite: $DB"
# Freshness check: mtime should move with host activity; if using memory/ snapshot, say so in the report.
stat -c '%y' "$DB" 2>/dev/null || stat -f '%Sm' "$DB"
```

If `OMNIROUTE_API_URL` admin/management token can return a real quota payload in the future, prefer that and cite the endpoint. Do not use the runtime chat API key as a management token (it returns `Invalid management token`).

### Step 1: Confirm data source

Use the `$DB` resolved in Step 0. Cite the path in the report (live mount vs legacy snapshot).

### Step 2: Pull real usage windows

From `call_logs`, for today / last 7 days / calendar month:

- Requests and tokens by `provider` + `model`
- Count of `status=429` (quota/rate exhaustion signal)
- Shared `api_key_name` concurrency (stampede risk)

### Step 3: Compute horizons (honest labeling)

For each provider:

1. **Remaining today**
   - If a true balance exists → report it.
   - Else Gemini proxy: `RPD_ceiling_proxy − today's request count for that model family` (successful + 429 both consume RPD when Google counted them — if unclear, show used + 429 separately and remaining as `proxy_ceiling − used_ok` with a caveat).
   - If 429s already dominate today → state **exhausted / rate-limited today**, not a fake remaining number.
2. **Remaining this week** — only if a weekly balance exists. Otherwise: **not queryable**; show 7-day consumption from `call_logs` and say week remaining is N/A (rate limits reset daily/minute, not weekly).
3. **Remaining this month** — only if a monthly balance exists. Otherwise: **not queryable**; show MTD consumption; say no monthly balance API.

Never invent a precise remaining number when the source is rate-limit-only.

### Step 4: Stampede / concurrency note

If multiple agents share one `api_key_name` and today's 429 count is material, flag: shared free key + concurrent load. Point to `/daily-allocation` stagger rules.

### Step 5: Persist + Slack

Append a dated block to `memory/token-budget-log.md`. Post the same text to Slack `#aegis-infra` via `list_channel_groups` + `send_group_message`. Optionally `mcp__trinity__report` with `report_type: aegis_infra.token_budget`, `display_hint: markdown`.

### Step 6: Capacity HOLD / lift (mandatory teeth)

Do **not** end on advisory “HOLD” prose alone.

1. If today's evidence meets `/capacity-hold` **apply** threshold → run `/capacity-hold apply` in the same turn (real `toggle_agent_schedule` calls). Cite the paused schedule_ids in the Slack close-out.
2. Else if `memory/capacity-hold.md` has `status: active` and evidence meets **lift** threshold → run `/capacity-hold lift`.
3. Else → no schedule changes; say so explicitly.

See `docs/a2a-routing.md` Protocol C. Never pause Daily token budget / Daily allocation.

## Outputs

- Console report with per-provider today/week/month (real or explicitly N/A + proxy)
- Updated `memory/token-budget-log.md`
- Slack close-out in `#aegis-infra`
- When Step 6 fires: updated `memory/capacity-hold.md` + real schedule toggles
---

## Final step — Slack completed-task close-out (mandatory)

Post a real close-out to `#aegis-infra` covering ask / who / what / outcome / delivery confirmation. Trinity `report` is not a substitute.
