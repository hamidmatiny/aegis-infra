#!/usr/bin/env python3
"""Inputs for /daily-allocation and the other roster-dependent skills. No model call.

Reads two files the host capacity watcher publishes into memory/ every minute:
  memory/fleet-roster.json     all agents from Trinity agent_ownership (not list_agents)
  memory/capacity-state.json   the watcher's own 429-only signals and SI gate

Why this exists: on 2026-10-09 /daily-allocation counted 530 errors across
429/503/504, set si_budget 0 for the whole fleet, and covered "7 active fleet
agents" from list_agents. list_agents on this agent's key returns outbound A2A
peers only, and 503/504 are upstream noise the capacity watcher ignores.

  python3 scripts/allocation_inputs.py          # JSON for the skill
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / "memory" / "fleet-roster.json"
CAPACITY = ROOT / "memory" / "capacity-state.json"
MAX_AGE = timedelta(minutes=15)
# Subscription agents do not share the free-pool key, so they never take a free-pool SI slot.
SUBSCRIPTION = ("aegis-ceo", "aegis-redteam")


def _age(written_at: str | None, now: datetime) -> timedelta | None:
    if not written_at:
        return None
    try:
        ts = datetime.strptime(written_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return now - ts


def build(roster: dict | None, capacity: dict | None, now: datetime) -> dict:
    problems = []
    agents = list((roster or {}).get("agents") or [])
    if not agents:
        problems.append("memory/fleet-roster.json missing or empty: do not fall back to list_agents")
    else:
        age = _age(roster.get("written_at"), now)
        if age is None or age > MAX_AGE:
            problems.append(f"fleet-roster.json is stale (written_at {roster.get('written_at')})")

    if not capacity:
        si, reason = "unknown", "memory/capacity-state.json missing: host watcher not publishing"
    else:
        age = _age(capacity.get("written_at"), now)
        if age is None or age > MAX_AGE:
            si, reason = "unknown", f"capacity-state.json is stale (written_at {capacity.get('written_at')})"
        else:
            si, reason = capacity.get("si", "unknown"), capacity.get("reason", "")
    if si == "unknown":
        problems.append(reason)

    return {
        "now": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "roster_count": len(agents),
        "roster": agents,
        "free_pool_si_candidates": [a for a in agents if a not in SUBSCRIPTION],
        "si": si,
        "si_reason": reason,
        "status_counts_today": (capacity or {}).get("today_status_counts", {}),
        "rule": "SI is deferred only by the capacity watcher's 429 rule or an active hold. 503/504 never defer SI.",
        "problems": problems,
    }


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main() -> int:
    out = build(_read(ROSTER), _read(CAPACITY), datetime.now(timezone.utc))
    print(json.dumps(out, indent=2))
    return 1 if out["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
