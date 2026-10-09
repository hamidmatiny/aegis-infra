---
name: audit-omniroute
description: Check what's actually installed and configured for OmniRoute right now — don't assume it's live just because it's the intended mechanism
allowed-tools: Read, Write, Bash, Glob, Grep, WebFetch, AskUserQuestion, mcp__trinity__list_channel_groups, mcp__trinity__send_group_message, mcp__trinity__report
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-09-13
  author: aegis-infra
---

# Audit OmniRoute

## Purpose

Establish the actual, current state of OmniRoute (github.com/diegosouzapw/OmniRoute) — what's installed, what's configured, and what isn't — as ground truth for every other decision this agent makes. "OmniRoute is the intended mechanism" is a fact about intent, not about whether it's running. Never report it as configured without having actually checked.

## Process

### Step 1: Check for a local install

```bash
# Common places a locally-run gateway might live — adjust as you learn the real layout
which omniroute 2>/dev/null
ps aux | grep -i omniroute | grep -v grep
docker ps --filter "name=omniroute" 2>/dev/null
find "$HOME" -maxdepth 3 -iname "*omniroute*" 2>/dev/null
```

Report exactly what you find — a running process, a stopped one, a cloned-but-unrun repo, or nothing at all. Don't infer "installed" from a directory existing if nothing is actually running.

### Step 2: Check declared credentials

Read this agent's `.env` (if present) for `OMNIROUTE_API_URL` / `OMNIROUTE_API_KEY`. If unset, that alone answers "is OmniRoute wired up for this agent" — no.

### Step 3: Probe the running instance (if `OMNIROUTE_API_URL` is set)

Try a basic reachability check first:

```bash
curl -sS -m 5 "${OMNIROUTE_API_URL%/}/health" 2>&1 || curl -sS -m 5 "${OMNIROUTE_API_URL}" 2>&1
```

If it responds, use `WebFetch` against `${OMNIROUTE_API_URL}` and, if available, the project's own README/docs (fetch `https://github.com/diegosouzapw/OmniRoute` or its raw README) to identify the actual admin/config endpoints for this version — **don't guess at API shape from a template**. Once you know the real endpoints, check for:

- Configured providers (which ones, free vs. paid)
- Routing combos / fallback chains currently defined
- Free-tier pools currently active and their known limits
- Any providers referenced in this fleet's plans (Anthropic, Gemini, etc.) that are declared but not actually reachable (bad key, wrong URL, etc.)

If it doesn't respond, or `OMNIROUTE_API_URL` is unset, stop here — don't fabricate a "here's what's configured" answer from memory of what OmniRoute *should* look like.

### Step 4: Compare against what's assumed elsewhere

Check `memory/tier-assignments.md` (if it exists — see `/propose-agent-tier`) for agents already assumed to be routed through OmniRoute's mid-cost or free-pool tiers. Flag any assignment that assumes a provider/pool this audit could not confirm is actually live.

### Step 4b: Mid-cost long-prompt health + scout restore (mandatory while exception open)

Live mid combo `sonnet` / `aegis-mid` is Gemini 3.1 Pro → CFP gpt-oss → CFP DeepSeek. CFP hops reject prompts >6000 characters. Trinity agent system prompts exceed that, so **when Pro is quota-blocked, every mid agent (`the-brain`, `aegis-core-infra`, `aegis-scout` on mid) fails the same way** — not scout-specific.

On every audit while `memory/tier-assignments.md` still marks `aegis-scout` on temporary free alias `claude-sonnet-4-6`:

1. Probe `gemini/gemini-3.1-pro-preview` short + ~10k-char.
2. Probe `sonnet` with ~10k-char; record whether it lands on Pro or dies on CFP `Prompt too long (max 6000)`.
3. If Pro long-prompt works: flip `aegis-scout` models back to `sonnet`, export credentials, restart, verify, update `memory/tier-assignments.md`, Slack `#aegis-infra`.
4. If not: leave free alias, re-arm / confirm infra reminder `MID-COST RECOVERY CHECK` (do not rely on memory alone).

Durable fix to propose (do not silently apply OmniRoute config without approval): prompt-size-aware mid routing that **skips 6k-cap CFP hops** for large prompts (fail closed or explicit long-context fallback), instead of per-agent remaps.

### Step 5: Report findings

Present a plain summary:

```
## OmniRoute Audit — [date]

**Installed:** yes / no / partially (explain)
**Reachable:** yes / no (from OMNIROUTE_API_URL)
**Configured providers:** [list, or "unknown — could not reach admin API"]
**Free-tier pools active:** [list, or "unknown"]
**Gaps found:** [anything assumed elsewhere that this audit couldn't confirm]
**Recommendation:** [what needs to happen before relying on this for a real tier assignment]
```

If running on Trinity and `mcp__trinity__report` is available, publish this as `report_type: aegis_infra.omniroute_audit`, `display_hint: markdown`, with the summary above as the payload. Skip silently if the tool isn't available.

### Step 6: Deliver to Slack `#aegis-infra` (outbound only)

Push the **same real audit summary** to the bound Slack channel so Hamid sees ground truth without a terminal:

1. `mcp__trinity__list_channel_groups` with `channel_type: "slack"`.
2. `mcp__trinity__send_group_message` with that `chat_id` and the Step 5 summary — not a placeholder.
3. If Slack fails, say so plainly; do not claim delivery.

Outbound visibility for Hamid — and Hamid may also ask you to run this skill via Slack. Slack is not an approval surface for reconfiguring OmniRoute; live config changes still need explicit approve.

### Step 7: Escalate, don't fix silently

If OmniRoute needs configuration changes to close a gap, **propose** the change and ask before applying it — this skill is read-only by design. Installing, reconfiguring, or restarting OmniRoute is a change to shared fleet infrastructure and needs Hamid's or the CEO's go-ahead per this agent's operating rules.

## Known failure modes

### FM-1 — OmniRoute `.env` durability vs restart

**What went wrong:** Free-pool agents looked healthy until a subscription was reassigned, platform Anthropic API key was re-enabled, or the agent volume was wiped without `.credentials.enc`. Trinity DB flags (`no subscription` + `use_platform_api_key=false`) alone are not enough — without re-injected OmniRoute `.env` (usually restored from `.credentials.enc` on start), chat falls back to broken/wrong auth.

**Correct behavior:** Every audit of a free-pool or mid-cost OmniRoute agent must check: OmniRoute reachable, agent `.env` / credentials present, and preferably a recent OmniRoute log line showing the expected provider. Flag missing `.credentials.enc` as a durability gap. README "Known gotcha: free-pool auth durability" is the human checklist.

### FM-2 — Mid-cost Trinity model alias does not survive restart

**What went wrong:** `the-brain` (VP) mid-cost requires Trinity chat model alias `sonnet` (mapped in OmniRoute to a mid-cost combo). `PUT /api/agents/<name>/model` is **in-memory** on the agent-server — after restart the agent silently falls back to the default Claude ID, which OmniRoute free-pool remaps to flash-lite.

**Correct behavior:** When auditing mid-cost agents, verify the live chat `model` / `model_name` matches the intended alias after any restart. Until durable `AGENT_RUNTIME_MODEL` exists, call out re-apply via `PUT /api/agents/<name>/model` as required ops, not optional polish.

### FM-2b — Mid-cost fallback must not collapse to flash

**What went wrong:** When Gemini Pro quota cooled, mid agents were served flash / flash-lite because `sonnet`/`aegis-mid` were single-step flash (or Claude alias combos pointed at flash-lite) and/or agent `.env` set `ANTHROPIC_DEFAULT_SONNET_MODEL` to a flash model ID.

**Correct behavior:** Audit must confirm combos `sonnet` and `aegis-mid` priority chain is mid-strength only (CFP DeepSeek Pro → GPT-OSS → Gemini Pro — **no** flash). Spot-check a recent call log for mid agents: served model must not be `*flash*`. Fail-closed (429/503) when all mid targets are unavailable is acceptable; silent free-pool collapse is not. Note remaining gap: no Anthropic/OpenAI API-key provider connected yet for a paid Claude/GPT mid rail.

### FM-2c — Mid-cost CFP hops reject Trinity-sized prompts (6k cap)

**What went wrong (2026-09-16):** When `gemini-3.1-pro-preview` is quota-blocked, `sonnet`/`aegis-mid` fall through to CFP gpt-oss / DeepSeek, which return `Prompt too long (max 6000 characters)`. Trinity Claude Code system prompts exceed 6k, so mid agents fail closed on real work — confirmed for the shared combo used by `the-brain`, `aegis-core-infra`, and `aegis-scout`. Temporary per-agent remap of scout to free alias `claude-sonnet-4-6` is a workaround, not a durable fix.

**Correct behavior:** Audit Step 4b probes Pro + long `sonnet`. Propose OmniRoute prompt-size-aware mid routing (skip 6k-cap CFP for large prompts). Restore scout to `sonnet` when Pro long-prompt works (reminder `rem_fcab848e2aa940f8b21c1e6f7da17bae`).

### FM-3 — Reporting "configured" from intent or a directory alone

**What went wrong:** Treating "OmniRoute is the intended mechanism" or a cloned repo path as proof it is live.

**Correct behavior:** Reachability + configured providers/pools from a real probe, or explicitly "unknown / not reachable." Never invent admin API shape from a template.

### Final step: Slack completed-task close-out (mandatory)

Every run — success or failure — ends with a real post to `#aegis-infra` via `list_channel_groups` (`channel_type: "slack"`) then `send_group_message`. Include: what was asked, who asked, what you did, real outcome, who you reported to. Trinity `report` is not a substitute. See CLAUDE.md § Slack completed-task close-out.

## Outputs

- A ground-truth audit report (chat and, on Trinity, a published report)
- A real Slack message in `#aegis-infra` with that same summary (when Slack is bound)
- No configuration changes applied without explicit approval
