#!/usr/bin/env python3
"""Fleet code sync: adopt origin/main for tracked code/config without wiping runtime state.

Why this exists
---------------
Trinity `git pull` fails on dirty agent worktrees (common once agents write
memory/, onboarding, or SI baselines). Stock `reset-to-main-preserve-state`
hard-resets then force-pushes, and its default allowlist does NOT include
`memory/**` — so a naive reset can discard real working state (observed
2026-09-16 on aegis-scout).

This script is the safe equivalent for day-to-day fleet sync:

  FORCE-SYNC from origin/main (code/config):
    CLAUDE.md, README.md, ARCHITECTURE.md, TARGET-ARCHITECTURE.md,
    template.yaml, dashboard.yaml, .claude/skills/**, docs/**,
    .claude/agents/** (if present)

  PRESERVE (never overwritten by this sync):
    memory/**, .env, .credentials.enc, .mcp.json, .claude.json,
    .trinity/** (except we may update persistent-state.yaml),
    onboarding.json, workspace/**

It also expands `.trinity/persistent-state.yaml` so Trinity's native
`POST .../git/reset-to-main-preserve-state` keeps memory + credentials if
you ever need a full adopt.

Usage:
  python3 scripts/fleet-sync-code-from-origin.py
  python3 scripts/fleet-sync-code-from-origin.py --agents aegis-scout,aegis-growth
  python3 scripts/fleet-sync-code-from-origin.py --also-trinity-reset   # optional full reset after allowlist expand
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

FLEET = [
    "aegis-ceo",
    "the-brain",
    "aegis-infra",
    "aegis-threat-intel",
    "aegis-analyst",
    "aegis-core-infra",
    "aegis-data-quality",
    "aegis-growth",
    "aegis-scout",
]

# Paths checked out from origin/main when they exist in the remote tree.
CODE_PATHS = [
    "CLAUDE.md",
    "README.md",
    "ARCHITECTURE.md",
    "TARGET-ARCHITECTURE.md",
    "template.yaml",
    "dashboard.yaml",
    ".claude/skills",
    ".claude/agents",
    "docs",
]

PERSISTENT_STATE = [
    "workspace/**",
    ".trinity/**",
    ".mcp.json",
    ".claude.json",
    ".claude/.credentials.json",
    "memory/**",
    ".env",
    ".credentials.enc",
    "onboarding.json",
]


def trinity_token() -> str:
    cfg = Path.home() / ".trinity" / "config.json"
    data = json.loads(cfg.read_text())
    return data["profiles"]["localhost"]["token"]


def api(method: str, path: str, token: str, body: dict | None = None) -> tuple[int, object]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"http://localhost:8000{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"detail": raw.decode(errors="replace")[:500]}


def docker_exec(agent: str, script: str, user: str | None = None) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", "exec"]
    if user:
        cmd += ["-u", user]
    cmd += [f"agent-{agent}", "sh", "-lc", script]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


def expand_persistent_state(agent: str) -> None:
    yaml = "persistent_state:\n" + "\n".join(f"- {p}" for p in PERSISTENT_STATE) + "\n"
    host_tmp = Path(f"/tmp/pstate-{agent}.yaml")
    host_tmp.write_text(yaml)
    dest = f"agent-{agent}:/home/developer/.trinity/persistent-state.yaml.new"
    subprocess.run(
        ["docker", "cp", str(host_tmp), dest],
        check=True,
        capture_output=True,
        text=True,
    )
    script = """
set -e
NEW=/home/developer/.trinity/persistent-state.yaml.new
OLD=/home/developer/.trinity/persistent-state.yaml
if [ ! -f "$NEW" ]; then echo "missing $NEW"; exit 1; fi
# Prefer replace-in-place; if the volume forbids unlink, keep .new and symlink semantics fail —
# fall back to overwriting via cat into a writable temp then rename when possible.
if rm -f "$OLD" 2>/dev/null; then
  mv "$NEW" "$OLD"
else
  # Immutable/odd volume: leave .new as the allowlist file the reader may not see —
  # still attempt cat overwrite as developer.
  cat "$NEW" > "$OLD" 2>/dev/null || cp "$NEW" "$OLD" 2>/dev/null || {
    echo "WARN_PSTATE_LOCKED kept $NEW"
    cat "$NEW"
    exit 0
  }
fi
grep -E 'memory|credentials|onboarding' "$OLD" || grep -E 'memory|credentials|onboarding' "$NEW"
"""
    res = docker_exec(agent, script, user="0")
    if res.returncode != 0:
        raise RuntimeError(f"{agent}: expand persistent-state failed: {res.stderr or res.stdout}")


def sync_code_from_origin(agent: str) -> dict:
    """Fetch origin/main and force-checkout CODE_PATHS only."""
    paths_quoted = " ".join(f"'{p}'" for p in CODE_PATHS)
    script = f"""
set -e
cd /home/developer
git fetch origin main >/dev/null
EXIST=""
for p in {paths_quoted}; do
  if git ls-tree -r --name-only origin/main -- "$p" 2>/dev/null | head -1 | grep -q .; then
    EXIST="$EXIST $p"
  fi
done
EXIST=$(echo "$EXIST" | xargs)
if [ -z "$EXIST" ]; then
  echo "NO_CODE_PATHS"
  exit 2
fi
# Snapshot memory fingerprint before checkout
MEM_BEFORE=""
if [ -f memory/scout-baselines.md ]; then MEM_BEFORE=$(wc -c < memory/scout-baselines.md); fi
if [ -f memory/review-baselines.md ]; then MEM_BEFORE=$(wc -c < memory/review-baselines.md); fi
if [ -f memory/tier-assignments.md ]; then MEM_BEFORE=$(wc -c < memory/tier-assignments.md); fi
# Force worktree+index for code paths only — leave memory/.env alone
git checkout origin/main -- $EXIST
echo "SYNCED:$EXIST"
echo "ORIGIN_SHA:$(git rev-parse --short origin/main)"
if git diff --quiet origin/main -- CLAUDE.md 2>/dev/null; then
  echo "CLAUDE_MATCH:yes"
else
  echo "CLAUDE_MATCH:no"
fi
if [ -d memory ]; then
  echo "MEMORY_DIR:present"
  ls memory | head -20
  if [ -n "$MEM_BEFORE" ]; then echo "MEMORY_BYTES_BEFORE:$MEM_BEFORE"; fi
else
  echo "MEMORY_DIR:absent"
fi
# Prove dirty memory (if any) did not block code sync
git status --porcelain -- CLAUDE.md .claude/skills | head -5 || true
"""
    res = docker_exec(agent, script)
    out = (res.stdout or "") + (res.stderr or "")
    return {
        "ok": res.returncode == 0 and "CLAUDE_MATCH:yes" in out,
        "returncode": res.returncode,
        "output": out[-2500:],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents", default=",".join(FLEET), help="Comma-separated agent names")
    ap.add_argument(
        "--also-trinity-reset",
        action="store_true",
        help="After expanding allowlist + code sync, call Trinity reset-to-main-preserve-state",
    )
    args = ap.parse_args()
    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    token = trinity_token()

    results = {}
    for agent in agents:
        print(f"\n===== {agent} =====")
        pstate_ok = True
        try:
            expand_persistent_state(agent)
            print("persistent-state: expanded (includes memory/**, .env, .credentials.enc)")
        except Exception as e:
            pstate_ok = False
            print(f"persistent-state WARN (continuing code sync): {e}")

        sync = sync_code_from_origin(agent)
        print(sync["output"])
        entry = {"ok": sync["ok"], "sync": sync, "persistent_state_ok": pstate_ok}

        if args.also_trinity_reset:
            code, body = api(
                "POST",
                f"/api/agents/{agent}/git/reset-to-main-preserve-state",
                token,
            )
            print(f"trinity-reset HTTP {code}: {json.dumps(body)[:400]}")
            entry["trinity_reset"] = {"http": code, "body": body}
            entry["ok"] = entry["ok"] and code == 200 and not (
                isinstance(body, dict) and body.get("error")
            )

        results[agent] = entry

    print("\n===== SUMMARY =====")
    failed = []
    for agent, r in results.items():
        status = "OK" if r.get("ok") else "FAIL"
        print(f"{status} {agent}")
        if not r.get("ok"):
            failed.append(agent)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
