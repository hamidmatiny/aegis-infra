#!/usr/bin/env python3
"""Host-side Protocol C circuit breaker.

The daily /token-budget skill is an LLM job on the same free Gemini pool it is
supposed to protect. When that pool is exhausted the skill cannot run, so a
burst between the 07:00 UTC check and the next morning never pauses schedules.

This process reads OmniRoute call_logs directly (no model call) and toggles
Trinity schedules. It does not buy quota.

Trip when either is true for the current UTC day:
  - 429 count >= 100 (existing daily threshold), or
  - 40 responses with status 429 inside any 10-minute window.

503 and 504 stay in the two-hour lift counter so a hold is not lifted during
an upstream spike, but they do not open a hold. On 2026-10-08 the mixed
counter tripped at 16:44Z on 4x429 plus 36x503/504 (Gemini "high demand" and
local queue expiry from the restart trigger loop). The day's 429 count was
35, and the busiest 10 minutes held 25x429. A day shaped like 2026-09-25
(1,315 rate-limit responses) still trips on the daily 429 threshold.

Never pauses: aegis-ceo, aegis-redteam (subscription; live attack batch),
aegis-infra "Daily token budget", aegis-infra "Daily allocation".
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB = Path(os.environ.get("OMNIROUTE_SQLITE", Path.home() / ".omniroute" / "storage.sqlite"))
STATE = Path.home() / "Library/Application Support/aegis-capacity-watch/state.json"
TRINITY = os.environ.get("TRINITY_URL", "http://127.0.0.1:8000")
BURST_WINDOW = timedelta(minutes=10)
BURST_COUNT = 40
DAILY_429 = 100
LIFT_429 = 40
LIFT_2H_ERRORS = 20
ERROR_STATUSES = (429, 503, 504)
BURST_STATUSES = (429,)
NEVER_AGENTS = {"aegis-ceo", "aegis-redteam", "trinity-system"}
NEVER_SCHEDULE_NAMES = {"Daily token budget", "Daily allocation"}


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def load_events(con: sqlite3.Connection, start: datetime, end: datetime):
    rows = con.execute(
        """
        select timestamp, status from call_logs
        where timestamp >= ? and timestamp < ?
        order by timestamp
        """,
        (start.strftime("%Y-%m-%dT%H:%M:%S"), end.strftime("%Y-%m-%dT%H:%M:%S")),
    ).fetchall()
    return [(_parse(ts), int(status)) for ts, status in rows]


def first_trip(events):
    """Return (timestamp, reason) of the first causal trip, or (None, None)."""
    daily_429 = 0
    err_times = []
    j = 0
    for ts, status in events:
        if status == 429:
            daily_429 += 1
            if daily_429 == DAILY_429:
                return ts, f"daily_429={daily_429}"
        if status in BURST_STATUSES:
            err_times.append(ts)
            cutoff = ts - BURST_WINDOW
            while j < len(err_times) and err_times[j] < cutoff:
                j += 1
            n = len(err_times) - j
            if n >= BURST_COUNT:
                return ts, f"burst_{BURST_COUNT}_in_{int(BURST_WINDOW.total_seconds() // 60)}m count={n}"
    return None, None


def live_signals(events, now: datetime):
    daily_429 = sum(1 for _, s in events if s == 429)
    cutoff = now - BURST_WINDOW
    burst = sum(1 for ts, s in events if s in BURST_STATUSES and ts >= cutoff)
    two_h = now - timedelta(hours=2)
    recent_err = sum(1 for ts, s in events if s in ERROR_STATUSES and ts >= two_h)
    hold = daily_429 >= DAILY_429 or burst >= BURST_COUNT
    return {
        "daily_429": daily_429,
        "burst_10m": burst,
        "errors_2h": recent_err,
        "hold": hold,
        "lift": daily_429 < LIFT_429 and recent_err < LIFT_2H_ERRORS,
    }


def replay(day: str) -> int:
    start = _parse(day + "T00:00:00")
    end = start + timedelta(days=1)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    events = load_events(con, start, end)
    ts, reason = first_trip(events)
    daily = sum(1 for _, s in events if s == 429)
    print(json.dumps({
        "day": day,
        "events": len(events),
        "daily_429": daily,
        "trip_at": ts.strftime("%Y-%m-%dT%H:%M:%SZ") if ts else None,
        "reason": reason,
    }))
    return 0 if ts else 1


def _env_from_container() -> dict:
    raw = subprocess.check_output(["docker", "exec", "trinity-backend", "printenv"], text=True)
    env = {}
    for line in raw.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k] = v
    return env


def trinity_token() -> str:
    env = _env_from_container()
    user = env.get("ADMIN_USERNAME", "admin")
    password = env["ADMIN_PASSWORD"]
    data = urllib.parse.urlencode({"username": user, "password": password}).encode()
    req = urllib.request.Request(TRINITY + "/api/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())["access_token"]


def api(token: str, method: str, path: str):
    req = urllib.request.Request(
        TRINITY + path,
        method=method,
        headers={"Authorization": "Bearer " + token},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:300]}


def list_schedules(token: str):
    status, agents = api(token, "GET", "/api/agents")
    if status != 200:
        raise SystemExit(f"list agents failed: {status}")
    out = []
    for agent in agents:
        name = agent.get("name") or agent.get("agent_name")
        if not name or name in NEVER_AGENTS or agent.get("is_system"):
            continue
        st, schedules = api(token, "GET", f"/api/agents/{name}/schedules")
        if st != 200:
            out.append({"agent": name, "error": st, "body": schedules})
            continue
        for s in schedules:
            sname = s.get("name") or ""
            if sname in NEVER_SCHEDULE_NAMES:
                continue
            out.append({
                "agent": name,
                "id": s.get("id"),
                "name": sname,
                "enabled": bool(s.get("enabled")),
            })
    return out


def load_state() -> dict:
    if not STATE.exists():
        return {"status": "inactive", "paused": []}
    return json.loads(STATE.read_text())


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def publish_roster() -> dict:
    """Full fleet count from Trinity ownership. Not the agent-scoped list_agents view."""
    script = (
        "import sqlite3\n"
        "c=sqlite3.connect('/data/trinity.db')\n"
        "rows=c.execute('select agent_name from agent_ownership "
        "where deleted_at is null and ifnull(is_system,0)=0 order by agent_name')\n"
        "print('\\n'.join(r[0] for r in rows))\n"
    )
    raw = subprocess.check_output(
        ["docker", "exec", "-i", "trinity-backend", "python3", "-"],
        input=script,
        text=True,
    )
    names = [n for n in raw.splitlines() if n.strip()]
    payload = {
        "source": "agent_ownership",
        "exclude": ["trinity-system"],
        "count": len(names),
        "agents": names,
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    body = json.dumps(payload, indent=2) + "\n"
    dest = Path("/Users/hamidrezamatiny/Cursor/aegis-infra/memory/fleet-roster.json")
    dest.write_text(body)
    subprocess.run(
        ["docker", "exec", "-i", "agent-aegis-infra", "tee", "/home/developer/memory/fleet-roster.json"],
        input=body, text=True, capture_output=True, check=False,
    )
    return payload


def apply_or_lift(execute: bool) -> int:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    events = load_events(con, start, end)
    signals = live_signals(events, now)
    state = load_state()
    token = trinity_token()
    schedules = list_schedules(token)
    enabled = [s for s in schedules if s.get("enabled") and s.get("id")]
    result = {
        "now": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signals": signals,
        "watcher_status": state.get("status"),
        "enabled_holdable": len(enabled),
        "action": "none",
    }
    if signals["hold"] and state.get("status") != "active":
        result["action"] = "apply"
        paused = []
        for s in enabled:
            if not execute:
                paused.append({**s, "api": "dry-run"})
                continue
            code, body = api(token, "POST", f"/api/agents/{s['agent']}/schedules/{s['id']}/disable")
            paused.append({**s, "api_status": code, "api": body})
        if execute:
            # re-read to prove the toggle stuck
            after = list_schedules(token)
            still_on = [s for s in after if s.get("enabled") and s.get("id")]
            state = {
                "status": "active",
                "applied_at": result["now"],
                "reason": signals,
                "paused": [
                    {"agent": p["agent"], "id": p["id"], "name": p["name"], "api_status": p.get("api_status")}
                    for p in paused
                ],
                "still_enabled_after": [
                    {"agent": s["agent"], "id": s["id"], "name": s["name"]} for s in still_on
                ],
            }
            save_state(state)
            result["still_enabled_after"] = state["still_enabled_after"]
        result["paused"] = paused
    elif state.get("status") == "active" and signals["lift"]:
        result["action"] = "lift"
        lifted = []
        for s in state.get("paused") or []:
            if not execute:
                lifted.append({**s, "api": "dry-run"})
                continue
            code, body = api(token, "POST", f"/api/agents/{s['agent']}/schedules/{s['id']}/enable")
            lifted.append({**s, "api_status": code, "api": body})
        if execute:
            state = {
                "status": "lifted",
                "lifted_at": result["now"],
                "reason": signals,
                "paused": [],
                "last_lifted": lifted,
            }
            save_state(state)
        result["lifted"] = lifted
    elif state.get("status") == "active":
        result["action"] = "hold-remains"
        result["paused_ids"] = [p.get("id") for p in state.get("paused") or []]
    try:
        result["roster"] = publish_roster()
    except Exception as exc:
        result["roster_error"] = str(exc)[:200]
    print(json.dumps(result, indent=2))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--replay":
        if not DB.exists():
            print(f"missing sqlite {DB}", file=sys.stderr)
            return 1
        return replay(argv[2])
    if len(argv) != 2 or argv[1] not in {"--dry-run", "--apply"}:
        print("usage: capacity-watch.py --replay YYYY-MM-DD | --dry-run | --apply", file=sys.stderr)
        return 2
    if not DB.exists():
        print(f"missing sqlite {DB}", file=sys.stderr)
        return 1
    return apply_or_lift(execute=argv[1] == "--apply")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
