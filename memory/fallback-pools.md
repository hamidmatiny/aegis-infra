# OmniRoute fallback-pool diversification

**Created:** 2026-09-17  
**Owner:** `aegis-infra`  
**Goal:** Stop same-tier agents from sharing one ordered fallback chain (thundering-herd when primary exhausts).

## What was confirmed usable (live probes 2026-09-17)

### Free-pool (comparable Gemini free models)

| Model | Probe | Notes |
|-------|-------|-------|
| `gemini/gemini-flash-lite-latest` | OK | High volume primary |
| `gemini/gemini-2.0-flash-lite` | OK | Distinct rate-limit bucket vs lite-latest in practice |
| `gemini/gemini-flash-latest` | OK | Slightly heavier flash |
| `gemini/gemini-3.6-flash` | OK | Alternate flash primary |
| `gemini/gemini-3.7-flash` | Often cooldown | Keep in pool; not sole primary |
| `opencode/big-pickle` | **FAIL 403** | Free tier only inside OpenCode — **not** usable via OmniRoute |
| `opencode/muse-spark-1.2` | **FAIL 402** | Needs OpenCode API key — not wired |

**Provider reality:** only one active `provider_connections` row (`gemini`). Free diversification is **per-model ordering** on the shared Gemini key (real help when one model is cooling while another still serves). Cross-provider free alternatives are **not** available today without new credentials.

### Mid-cost (confirmed)

| Model | Probe | Notes |
|-------|-------|-------|
| `cfp/deepseek-ai/deepseek-v4-pro-0813` | OK | Cloudflare Playground (noauth) |
| `cfp/openai/gpt-oss-120b` | OK | Cloudflare Playground (noauth) |
| `gemini/gemini-3.1-pro-preview` | Often 429/cooldown | Keep in pool; do not make every agent Pro-first |

**Long-prompt policy (fixed 2026-09-17):** Trinity mid lanes (`sonnet` / `aegis-mid` / `aegis-mid-*`) are **Gemini 3.1 Pro only**. CFP’s 6k-char cap cannot serve Claude Code system prompts; cascading into CFP caused hangs/`Prompt too long`. Short-only CFP diversification lives under `aegis-mid-cfp-oss` / `aegis-mid-cfp-ds` — **created but unassigned** (0 call_logs hits). 2026-09-17 size check: matched successful mid calls for `the-brain` / `aegis-core-infra` are typically **50k–90k `tokens_in`** even for “tiny” ad-hoc turns (Claude Code system+tools context), so CFP short lanes are **not** a safe Pro fallback for those agents. Real mid fallback needs another long-context provider, not CFP.

### OmniRoute strategies available (CLI)

`priority`, `weighted`, `round-robin`, `p2c`, `least-used`, `cost-optimized`, etc.  
**Choice for fleet:** per-agent **priority** permutations (structured, predictable). Shared `least-used` alone would still let a stampede converge under simultaneous failover.

## Pool design

### Mid pool (Trinity agents — long-context)

| Combo | Order |
|-------|-------|
| `aegis-mid-oss` | `gemini-3.5-flash-lite` → `gemini-3.1-flash-lite` → `gemini-3.7-flash` (free-tier rebalance 2026-09-22; was Pro-only) |
| `aegis-mid-ds` | `gemini-3.1-flash-lite` → `gemini-3.5-flash-lite` → `gemini-3.7-flash` |
| `aegis-mid` | `gemini-3.7-flash` → `gemini-3.5-flash-lite` → `gemini-3.1-flash-lite` |
| `aegis-mid-pro` / `sonnet` | still **Gemini 3.1 Pro only** — free tier not available; left unused |
| `aegis-mid-cfp-oss` | gpt-oss → DeepSeek (**short prompts only**) |
| `aegis-mid-cfp-ds` | DeepSeek → gpt-oss (**short prompts only**) |

Per-agent `ANTHROPIC_MODEL` still selects which mid *lane name* the agent requests (`aegis-mid-oss` vs `aegis-mid-ds` vs …). Lane names remain for ops clarity and future re-diversification when a second long-context provider is available. **Do not** set Trinity `agent_schedules.model` to a custom combo name — Claude Code rejects unknown `--model` values (`unrecognized_model`); leave schedule `model` null so headless uses `ANTHROPIC_MODEL` from `.env`.

### Free pool (Gemini free models; rotated primary)

| Combo | Order |
|-------|-------|
| `aegis-free-lite` | flash-lite-latest → 3.1-flash-lite → 3.5-flash-lite → flash-latest |
| `aegis-free-20` | 2.0-flash-lite → flash-lite-latest → 3.6-flash |
| `aegis-free-36` | 3.6-flash → flash-lite-latest → 2.0-flash-lite |
| `aegis-free-latest` | flash-latest → flash-lite-latest → 2.0-flash-lite |
| `aegis-free-37` | 3.7-flash → 3.5-flash-lite → 3.1-flash-lite → 2.0-flash-lite |
| `aegis-free` (legacy) | flash-lite-latest → 2.0-flash-lite → 3.7-flash → 3.5-flash-lite → 3.1-flash-lite |
| `claude-sonnet-4-6` and the Claude alias combos that shared that chain | same three hops, then `gemini-3.5-flash-lite` → `gemini-3.1-flash-lite` so a 429 on the hot models continues |

## Per-agent assignment (ANTHROPIC_MODEL / DEFAULT_SONNET)

| Agent | Tier | Combo | Why this lane |
|-------|------|-------|----------------|
| `the-brain` | Free (was mid/Pro) | `aegis-mid-ds` | 2026-09-22: Pro has no free tier. Primary `gemini-3.1-flash-lite` |
| `aegis-core-infra` | Free (was mid/Pro) | `aegis-mid-oss` | Primary `gemini-3.5-flash-lite` |
| `aegis-product-eng` | Free (was mid/Pro) | `aegis-mid` | Split off `aegis-mid-oss` so it does not share core-infra's primary |
| `aegis-scout` | Mid (temp free) | `aegis-free-36` | Moved 2026-10-09 (see change log) |
| `aegis-infra` | Free | `aegis-free-lite` | Bookkeeping; lightest primary |
| `aegis-threat-intel` | Free | `aegis-free-20` | High-volume polling on 2.0 primary |
| `aegis-analyst` | Free | `aegis-free-36` | Structured reads on 3.6 primary |
| `aegis-data-quality` | Free | `aegis-free-36` | Moved off `aegis-free-latest` 2026-10-09 (see change log) |
| `aegis-growth` | Free | `aegis-free-37` | Own lane; falls back when 3.7 cools |
| `aegis-ceo` | Premium | (subscription) | Out of OmniRoute pools |

Haiku/small-fast default for OmniRoute agents: `aegis-free-lite`.

**Apply path:** `.env` `ANTHROPIC_MODEL` + `ANTHROPIC_DEFAULT_SONNET_MODEL` + Trinity `credentials/export` (Trinity PUT `/model` only accepts Claude aliases).

## Verification evidence (2026-09-17)

### Mid — different primaries under Pro exhaustion

Sequential short-prompt calls after OmniRoute reload:

| Combo | Upstream model (200) |
|-------|----------------------|
| `aegis-mid-ds` | `deepseek-ai/deepseek-v4-pro-0813` |
| `aegis-mid-oss` | `openai/gpt-oss-120b` |
| `aegis-mid-pro` | Pro **429**, then `openai/gpt-oss-120b` |

`call_logs` confirmed ds→DeepSeek and oss→gpt-oss — **not** all three racing to the same secondary.

### Free — different primaries under parallel load

Earlier parallel window:

| Combo | Upstream (200) |
|-------|----------------|
| `aegis-free-20` | `gemini-2.0-flash-lite` |
| `aegis-free-36` | `gemini-3.6-flash` |
| `aegis-free-lite` | `gemini-flash-lite-latest` (+ 2.0 fallback) |

Later parallel run showed more fallback onto 2.0 when lite/3.6 were stressed — expected; orderings still differ.

## Ops notes

- OmniRoute API for this fleet: `http://host.docker.internal:20129/v1` (keep `PORT=20129` on serve).
- After changing `ANTHROPIC_MODEL`, restart the agent container (or re-inject credentials) so Claude Code picks up `.env`.
- Do **not** put free-pool agents back on combo `sonnet` — that was mid-cost and amplified capacity storms.

## Change log

- 2026-09-17: Created diversified mid/free combos; assigned per-agent models; verified mid ds≠oss under Pro cooldown; documented rejected OpenCode options.
- 2026-09-23: Every combo config now sets `maxGlobalAttempts` to that combo's hop count, `maxRetries` 0, `maxSetRetries` 0 (one upstream call per hop, no second walk). Settings `modelLockout` is enabled for 429/502/503/504 with exponential cooldown (base 5s, doubles, cap 120s). A 429 that includes Google's "retry in Xs" uses that hint when it is longer than the base. Same-request fallback to the next model stays immediate.
- 2026-09-23 later: `aegis-free-37` (growth) and `aegis-free-lite` (infra) already had three hops, all in the hot set that was 429/503/504 together from 14:00Z to 15:30Z (`3.7-flash`, `flash-lite-latest`, `2.0-flash-lite`, `flash-latest`). Both chains now also fall through to `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite`, in opposite order, with `maxGlobalAttempts` 4. Primaries unchanged. A live probe at 15:55Z used the new hops and still returned 502, because those models were 503/504/429 at that moment too. This is a fallback for a partial cooldown, not new quota.
- 2026-09-22: `aegis-mid-oss` / `aegis-mid-ds` were not spare free quota. They were `gemini-3.1-pro-preview` only (pricing page: free tier not available; call log 143×429, 0×200 since Sept 16). Replaced those two plus `aegis-mid` with free Flash-Lite chains that returned HTTP 200 the same day. `aegis-product-eng` moved from `aegis-mid-oss` to `aegis-mid`. Shared `claude-sonnet-4-6` alias chain kept its three hot hops and gained `gemini-3.5-flash-lite` then `gemini-3.1-flash-lite` as further 429 fallbacks. No paid key. `sonnet` and `aegis-mid-pro` left on Pro and unused.
- 2026-10-09 13:05Z: `aegis-data-quality` -> `aegis-free-36`, `aegis-scout` -> `aegis-free-37` (Hamid chose this in the 2026-10-09 operator session). `aegis-free-latest`'s primary `gemini-flash-latest` hung to the 300 s client abort (HTTP 499) on most calls since 2026-10-08 (2026-10-09 00:00-13:00Z: 12 OK, 17 aborted, 16 errors of 45), and the hang never reaches the fallback hops. Neither agent had a strict close-out on record. Applied in `.env` (`ANTHROPIC_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL`) plus Trinity `credentials/export` (HTTP 200 each). Revert: restore `.tmp/env.before-lane-move-20261009` in each container and export again.
- 2026-10-09 14:40Z: `aegis-gateway`, `aegis-policy-engine`, `aegis-model-router`, `aegis-agent-gate`, `aegis-audit` and `aegis-scout` -> `aegis-free-36` (Hamid chose this in the same session). Since 12:00Z `gemini-3.7-flash` stalled ~300 s on 15 of 24 calls before OmniRoute fell back, so each turn cost ~5 min; gateway's dispatched audit `tW4ZlbB-G943_5u2A1hxLA` timed out at 3600 s. `gemini-3.6-flash` had 12 OK, 0 stalls. `aegis-growth` stays on `aegis-free-37`. Revert: restore `.tmp/env.before-lane-move-free36-20261009` and export again. Stall timeout: resolved 2026-10-09 19:13Z (see next entry).
- 2026-10-09 19:13Z: OmniRoute combo target timeout lowered from 310 s to **60 s** for every combo: `comboDefaults.targetTimeoutMs = 60000` via `PATCH /api/settings/combo-defaults` (OmniRoute v3.8.50; stored in `storage.sqlite` key_value `settings/comboDefaults`; per-combo `config.targetTimeoutMs` would override it, none set). The 310 s was `comboCooldownWait.budgetMs` (300 s) + 10 s, used only when `targetTimeoutMs` is unset. The timer covers time to the first response, so long streamed answers are not cut. Verified 19:17Z: `gemini-3.7-flash` cut at 60,004 ms then `gemini-3.5-flash-lite` 200 in 2.9 s; `gemini-3.6-flash` cut at 60,002 ms then `flash-lite-latest` 200 in 2.4 s. Revert: PATCH `{"comboDefaults":{}}`.
- Admin API auth from the Mac: the local CLI token (`x-omniroute-cli-token`, HMAC of the machine id) had never worked because the launcher's PATH lacked `/usr/sbin` (`ioreg`), so the server saw an empty machine id. Fixed in `run-omniroute.sh` (copy in `deploy/launchd/`), one restart at 19:10:23Z (back in 8 s).
