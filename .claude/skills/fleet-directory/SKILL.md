---
name: fleet-directory
description: Answer which Slack channel belongs to which fleet agent — from real docs/bindings only, never invent channel names
allowed-tools: Read, Bash, Grep, mcp__trinity__list_channel_groups
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-09-14
  author: aegis-infra
---

# Fleet Directory

## Purpose

Answer questions like "which channel is aegis-analyst in?" or "list all fleet channels" using **real** data only. This skill runs when Hamid asks in `#fleet-directory` (or `#aegis-infra`).

## Sources (in order)

1. **`docs/slack-channel-pattern.md`** — Naming table (fleet convention source of truth this agent maintains).
2. **Live bindings (preferred cross-check)** — `mcp__trinity__list_channel_groups` with `channel_type: "slack"` when available. If a live binding disagrees with the doc table, **say both** and flag the doc as stale — never silently invent a third name.

## Process

### Step 1: Read the naming table

```bash
# From this agent's workspace root
sed -n '/^## Naming$/,/^## /p' docs/slack-channel-pattern.md | head -n -1
```

Or `Read` that file and extract the Naming section.

### Step 2: Optional live cross-check

If `mcp__trinity__list_channel_groups` works, list Slack groups and note each agent ↔ channel name/id. Use this to confirm the answer, not to guess missing agents.

### Step 3: Answer

- One agent asked → reply with that agent's channel (e.g. `aegis-analyst → #aegis-analyst`).
- "List all" → paste the full agent → channel map from the doc (plus `#fleet-directory` as this directory channel bound to `aegis-infra`).
- Unknown agent → say it is **not** in the naming table / live bindings — do **not** invent `#something`.

## Hard rules

- Never invent or default a channel name.
- Never treat Slack as a control plane (no tier/auth changes from a directory question).
- Outbound/directory Q&A only.

## Known failure modes

### FM-1 — Answering from memory

**What went wrong:** Stating a channel name because it "usually matches the agent name" without reading the doc or live bindings.

**Correct behavior:** Always read `docs/slack-channel-pattern.md` (and live list when available) in this run before answering.
