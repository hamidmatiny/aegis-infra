# Fleet git sync (dirty-worktree safe)

## Problem

Live agents often have dirty git worktrees (`memory/**`, SI notes, local skill edits). Trinity `POST .../git/pull` then fails with “cannot pull with rebase: You have unstaged changes,” so `origin/main` fixes never land unless someone hand-writes files into the container.

Stock `POST .../git/reset-to-main-preserve-state` hard-resets + force-pushes, but the default `.trinity/persistent-state.yaml` allowlist does **not** include `memory/**` — a naive reset can wipe real baselines (happened to `aegis-scout` on 2026-09-16).

## Mechanism

`scripts/fleet-sync-code-from-origin.py`:

1. Expands persistent-state allowlist (when the volume allows) to preserve runtime state for Trinity’s native reset.
2. `git fetch origin main` + `git checkout origin/main -- <code paths only>` inside each container.

### Force-synced from `origin/main`

`CLAUDE.md`, `README.md`, `ARCHITECTURE.md`, `TARGET-ARCHITECTURE.md`, `template.yaml`, `dashboard.yaml`, `.claude/skills/**`, `.claude/agents/**`, `docs/**`

### Preserved (never overwritten by this sync)

`memory/**`, `.env`, `.credentials.enc`, `.mcp.json`, `.claude.json`, `.trinity/**`, `onboarding.json`, `workspace/**`

## Usage

```bash
python3 scripts/fleet-sync-code-from-origin.py
python3 scripts/fleet-sync-code-from-origin.py --agents aegis-scout,aegis-growth
# Optional: after allowlist expand, also call Trinity full reset (force-push):
python3 scripts/fleet-sync-code-from-origin.py --also-trinity-reset
```

Prefer the default path-scoped sync for day-to-day. Use `--also-trinity-reset` only when you need a full adopt and have confirmed memory is on the allowlist.
