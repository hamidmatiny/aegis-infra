#!/usr/bin/env python3
"""Nightly improvement runner. Runs on the Mac host every 15 minutes (launchd).

Each tick does at most one step, chosen by UTC time:

  run      02:00-03:30, 05:15-07:15  improve the next agent in tonight's batch
  review   08:40-09:30               aegis-ceo merges or closes tonight's PRs
  deploy   after review              merged changes pulled into the agent container
  summary  10:00 onward, once a day  one post in #aegis-infra
  verify   every tick                next real scheduled run vs the 3 before; revert if worse

Capacity is the Claude subscription only, through the host's claude.ai login.
ANTHROPIC_API_KEY and friends are stripped from the child environment so a
stray key can never turn this into API billing. Cursor is not used.

Guards (from nightly_improvement.decide): never in Hamid's working hours,
stop on any usage-limit signal, yield to aegis-ceo and aegis-redteam.
Only Track B repos, and only .claude/skills/, scripts/, tests/ inside them.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nightly_improvement as ni  # noqa: E402

OWNER = "hamidmatiny"
LABEL = "nightly-improvement"
STATE_DIR = Path.home() / "Library/Application Support/aegis-nightly"
LEDGER = STATE_DIR / "ledger.json"
LIMIT = STATE_DIR / "limit.json"
LOCK = STATE_DIR / "runner.lock"
WORK = Path.home() / "aegis-nightly"
TRINITY = os.environ.get("TRINITY_URL", "http://127.0.0.1:8000")
INFRA_SLACK_CHANNEL = "C0C1FN1US4E"  # #aegis-infra, bound to aegis-infra
PRIORITY = ("aegis-ceo", "aegis-redteam")
ALLOWED_PREFIXES = (".claude/skills/", "scripts/", "tests/")
MAX_CHANGED_LINES = 400
SESSION_TIMEOUT_S = 25 * 60
PRIORITY_LEAD = timedelta(minutes=30)
LIMIT_PATTERN = re.compile(
    r"usage limit|session limit|hit your limit|limit reached|rate_limit_error|reset(?:s)? at \d", re.I
)
STRICT_CLOSEOUT = '"name": "mcp__trinity__send_group_message"'
# Never handed to the claude child: any of these would bill the API instead of the subscription.
STRIPPED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def night_of(dt: datetime) -> str:
    """Runs between 02:00 and 07:15 UTC belong to that UTC date."""
    return dt.strftime("%Y-%m-%d")


# ---------------------------------------------------------------- state


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True))
    tmp.replace(path)


def ledger() -> dict:
    return load_json(LEDGER, {"entries": [], "days": {}})


def log(msg: str) -> None:
    print(f"{iso(now_utc())} {msg}", flush=True)


# ---------------------------------------------------------------- shell helpers


def sh(cmd: list[str], cwd: Path | None = None, timeout: int = 300, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)


def trinity_db(sql: str, params: tuple = ()) -> list[dict]:
    """Read-only query against Trinity's DB inside trinity-backend."""
    script = (
        "import json,sqlite3,sys\n"
        "q=json.load(sys.stdin)\n"
        "con=sqlite3.connect('file:/data/trinity.db?mode=ro',uri=True)\n"
        "con.row_factory=sqlite3.Row\n"
        "print(json.dumps([dict(r) for r in con.execute(q['sql'],q['params'])]))\n"
    )
    proc = subprocess.run(
        ["docker", "exec", "-i", "trinity-backend", "python3", "-c", script],
        input=json.dumps({"sql": sql, "params": list(params)}),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"trinity db query failed: {proc.stderr.strip()[:300]}")
    return json.loads(proc.stdout)


def _capacity_watch():
    spec = importlib.util.spec_from_file_location("capacity_watch", HERE / "capacity-watch.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["capacity_watch"] = mod
    spec.loader.exec_module(mod)
    return mod


def trinity_api(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    token = _capacity_watch().trinity_token()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        TRINITY + path,
        data=data,
        method=method,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:500]}


# ---------------------------------------------------------------- guards


def subscription_limited(at: datetime) -> tuple[bool, str]:
    mark = load_json(LIMIT, {})
    until = mark.get("until")
    if until and until > iso(at):
        return True, f"own session hit a usage limit; paused until {until}"
    since = iso(at - timedelta(hours=5))
    rows = trinity_db(
        "select agent_name, started_at, coalesce(error,'') err, coalesce(response,'') resp "
        "from schedule_executions where agent_name in (?,?) and started_at >= ?",
        (*PRIORITY, since),
    )
    for r in rows:
        if LIMIT_PATTERN.search(r["err"]) or LIMIT_PATTERN.search(r["resp"][:2000]):
            return True, f"{r['agent_name']} hit a usage limit at {r['started_at']}"
    return False, ""


def priority_busy(at: datetime) -> tuple[bool, str]:
    running = trinity_db(
        "select agent_name, started_at from schedule_executions where agent_name in (?,?) and status='running'",
        PRIORITY,
    )
    if running:
        return True, f"{running[0]['agent_name']} is running since {running[0]['started_at']}"
    upcoming = trinity_db(
        "select agent_name, name, cron_expression from agent_schedules where agent_name in (?,?) and enabled=1",
        PRIORITY,
    )
    for s in upcoming:
        fire = next_fire(s["cron_expression"], at, PRIORITY_LEAD)
        if fire:
            return True, f"{s['agent_name']} '{s['name']}' starts at {iso(fire)}"
    return False, ""


def _cron_field(field: str, value: int) -> bool:
    for part in field.split(","):
        if part == "*":
            return True
        if part.startswith("*/") and value % int(part[2:]) == 0:
            return True
        if "-" in part:
            lo, hi = part.split("-", 1)
            if int(lo) <= value <= int(hi):
                return True
        elif part.isdigit() and int(part) == value:
            return True
    return False


def next_fire(cron: str, start: datetime, within: timedelta) -> datetime | None:
    """First minute in [start, start+within] matching a 5-field UTC cron (all priority schedules are UTC)."""
    fields = cron.split()
    if len(fields) != 5:
        return None
    minute, hour, dom, month, dow = fields
    t = start.replace(second=0, microsecond=0)
    while t <= start + within:
        if (_cron_field(minute, t.minute) and _cron_field(hour, t.hour) and _cron_field(dom, t.day)
                and _cron_field(month, t.month) and _cron_field(dow, (t.weekday() + 1) % 7)):
            return t
        t += timedelta(minutes=1)
    return None


def recent_failures(at: datetime) -> dict[str, list[dict]]:
    """Last 24h of real runs per agent that failed, timed out, or missed the strict close-out."""
    rows = trinity_db(
        "select agent_name, id, status, started_at, triggered_by, slack_closeout_status, "
        "substr(coalesce(error,''),1,200) err, "
        "instr(coalesce(execution_log,''), ?) > 0 strict_closeout "
        "from schedule_executions where started_at >= ? order by started_at",
        (STRICT_CLOSEOUT, iso(at - timedelta(hours=24))),
    )
    out: dict[str, list[dict]] = {}
    for r in rows:
        if r["agent_name"] not in ni.FLEET:
            continue
        bad = r["status"] != "success" or not r["strict_closeout"]
        if bad and r["status"] != "running":
            out.setdefault(r["agent_name"], []).append(r)
    return out


# ---------------------------------------------------------------- run step


def scout_pick(agent: str) -> str:
    """aegis-scout's latest assignment that names this agent, if scout has written one."""
    repo = clone("aegis-scout")
    if repo is None:
        return ""
    text = (repo / "memory/learning-assignments.md").read_text() if (repo / "memory/learning-assignments.md").exists() else ""
    blocks = [b.strip() for b in re.split(r"\n(?=#+ |- \*\*)", text) if agent in b]
    return blocks[-1][:1500] if blocks else ""


def clone(agent: str) -> Path | None:
    dest = WORK / agent
    if (dest / ".git").exists():
        ok = sh(["git", "fetch", "-q", "origin"], cwd=dest).returncode == 0
        ok = ok and sh(["git", "checkout", "-q", "-f", "main"], cwd=dest).returncode == 0
        ok = ok and sh(["git", "reset", "-q", "--hard", "origin/main"], cwd=dest).returncode == 0
        sh(["git", "clean", "-fdq"], cwd=dest)
        return dest if ok else None
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = sh(["gh", "repo", "clone", f"{OWNER}/{agent}", str(dest), "--", "-q"], timeout=600)
    return dest if proc.returncode == 0 else None


def child_env() -> dict:
    env = {k: v for k, v in os.environ.items() if k not in STRIPPED_ENV}
    env["PATH"] = os.pathsep.join([str(Path.home() / ".local/bin"), "/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"])
    return env


PROMPT = """You are tonight's improvement session for the Track B agent `{agent}`.
The repo is your working directory. It is a fresh clone of {owner}/{agent} on a new branch `{branch}`.

Real runs of {agent} in the last 24 hours that failed, timed out, or missed the Slack close-out:
{failures}

aegis-scout's pick for this agent's next skill:
{pick}

Make exactly ONE concrete improvement that addresses the failures above (or, if there are none, scout's pick;
if neither exists, the agent's slowest or most token-heavy repetitive step). Good improvements:
- fix or tighten an existing skill in .claude/skills/
- add a new skill
- move repetitive deterministic work out of the LLM into a script in scripts/, and make the skill call it

Hard rules:
- Change only files under .claude/skills/, scripts/, tests/. Nothing else. Never touch CLAUDE.md, .env, .mcp.json.
- Keep the change small (under {max_lines} changed lines).
- Write a test in tests/test_*.py that the command `python3 -m unittest discover -s tests -t .` runs.
  The test must fail on the code before your change and pass after it. Make it import the code it tests
  via sys.path from the repo root, with no network and no secrets.
- Run that command and make it pass.
- Commit on the current branch with `git add` and `git commit`. Do not push. Do not switch branches.
- If you cannot find a real, testable improvement, make no commit and say why.

End your reply with one line of JSON, exactly:
{{"changed": true|false, "summary": "<one sentence: what changed and why>", "test": "<test file>"}}
"""


def run_tests(repo: Path) -> tuple[bool, str]:
    if not (repo / "tests").is_dir():
        return False, "no tests/ directory"
    python = shutil.which("python3", path=child_env()["PATH"]) or sys.executable
    proc = sh([python, "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=repo, timeout=300, env=child_env())
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-3:]
    return proc.returncode == 0, " | ".join(tail)


def before_after(repo: Path, base: str, test_files: list[str]) -> dict:
    """Run the new tests against the base code (expect fail) and the branch (expect pass)."""
    after_ok, after_out = run_tests(repo)
    tmp = WORK / "_before"
    shutil.rmtree(tmp, ignore_errors=True)
    sh(["git", "worktree", "prune"], cwd=repo)
    sh(["git", "worktree", "add", "-q", "--detach", str(tmp), base], cwd=repo)
    for f in test_files:
        (tmp / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo / f, tmp / f)
    before_ok, before_out = run_tests(tmp)
    sh(["git", "worktree", "remove", "--force", str(tmp)], cwd=repo)
    return {"before_pass": before_ok, "before": before_out, "after_pass": after_ok, "after": after_out}


def changed_files(repo: Path, base: str) -> tuple[list[str], int]:
    names = sh(["git", "diff", "--name-only", f"{base}..HEAD"], cwd=repo).stdout.split()
    stat = sh(["git", "diff", "--numstat", f"{base}..HEAD"], cwd=repo).stdout.splitlines()
    lines = 0
    for row in stat:
        parts = row.split("\t")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            lines += int(parts[0]) + int(parts[1])
    return names, lines


def outside_scope(files: list[str]) -> list[str]:
    return [f for f in files if not f.startswith(ALLOWED_PREFIXES)]


def ensure_label(agent: str) -> None:
    sh(["gh", "label", "create", LABEL, "--repo", f"{OWNER}/{agent}", "--color", "0e8a16",
        "--description", "Nightly improvement batch; aegis-ceo approves"], timeout=60)


def improve(agent: str, failures: list[dict], at: datetime) -> dict:
    entry = {"agent": agent, "night": night_of(at), "started": iso(at), "capacity": "claude-subscription"}
    if agent == "aegis" or agent not in ni.FLEET:
        return {**entry, "status": "refused", "reason": "not a Track B agent repo"}
    repo = clone(agent)
    if repo is None:
        return {**entry, "status": "error", "reason": "clone failed"}
    base = sh(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    branch = f"nightly/{night_of(at)}-{agent}"
    sh(["git", "checkout", "-q", "-B", branch], cwd=repo)
    fail_text = "\n".join(
        f"- {f['started_at']} {f['status']} trigger={f['triggered_by']} closeout={f['slack_closeout_status']} "
        f"strict={'yes' if f['strict_closeout'] else 'no'} error={f['err'] or '-'}"
        for f in failures[-8:]
    ) or "- none"
    pick = scout_pick(agent) or "none recorded"
    prompt = PROMPT.format(agent=agent, owner=OWNER, branch=branch, failures=fail_text, pick=pick, max_lines=MAX_CHANGED_LINES)
    cmd = [
        "claude", "-p", prompt,
        "--output-format", "json",
        "--permission-mode", "acceptEdits",
        "--max-turns", "60",
        "--allowedTools",
        "Read", "Edit", "Write", "Glob", "Grep",
        "Bash(git add:*)", "Bash(git commit:*)", "Bash(git diff:*)", "Bash(git status:*)", "Bash(git log:*)",
        "Bash(python3 -m unittest:*)",
        "--disallowedTools", "WebFetch", "WebSearch", "Bash(git push:*)",
    ]
    try:
        proc = sh(cmd, cwd=repo, timeout=SESSION_TIMEOUT_S, env=child_env())
        raw = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        return {**entry, "status": "error", "reason": f"session exceeded {SESSION_TIMEOUT_S}s"}
    result_text = raw
    try:
        payload = json.loads(proc.stdout)
        result_text = str(payload.get("result", ""))
        entry["session_id"] = payload.get("session_id")
        if payload.get("is_error") and LIMIT_PATTERN.search(result_text):
            return {**entry, "status": "limit", "reason": result_text[:300]}
    except ValueError:
        if LIMIT_PATTERN.search(raw):
            return {**entry, "status": "limit", "reason": raw[:300]}
    if proc.returncode != 0:
        return {**entry, "status": "error", "reason": raw.strip()[-300:]}
    verdict = {}
    for line in reversed(result_text.strip().splitlines()):
        line = line.strip().strip("`")
        if line.startswith("{") and line.endswith("}"):
            try:
                verdict = json.loads(line)
                break
            except ValueError:
                continue
    entry["summary"] = verdict.get("summary", "")
    head = sh(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    if head == base:
        return {**entry, "status": "no_change", "reason": verdict.get("summary") or "session made no commit"}
    files, lines = changed_files(repo, base)
    bad = outside_scope(files)
    if bad:
        return {**entry, "status": "rejected", "reason": f"touched files outside skills/scripts/tests: {bad[:5]}"}
    if lines > MAX_CHANGED_LINES:
        return {**entry, "status": "rejected", "reason": f"{lines} changed lines exceeds {MAX_CHANGED_LINES}"}
    tests = [f for f in files if f.startswith("tests/") and Path(f).name.startswith("test_")]
    evidence = before_after(repo, base, tests)
    entry["evidence"] = evidence
    if not tests or not evidence["after_pass"] or evidence["before_pass"]:
        return {**entry, "status": "rejected",
                "reason": "before/after test did not show fail-then-pass", "files": files}
    push = sh(["git", "push", "-q", "-f", "origin", branch], cwd=repo, timeout=120)
    if push.returncode != 0:
        return {**entry, "status": "error", "reason": "push failed: " + push.stderr.strip()[:200]}
    ensure_label(agent)
    body = (
        f"Nightly improvement for `{agent}` ({night_of(at)}), Claude subscription, idle window.\n\n"
        f"**Change:** {entry['summary'] or '(see diff)'}\n\n"
        f"**Why — failed runs in the last 24h:**\n{fail_text}\n\n"
        f"**aegis-scout pick:** {pick[:500]}\n\n"
        f"**Before/after** (`python3 -m unittest discover -s tests -t .`, new tests: {', '.join(tests)}):\n"
        f"- base `{base[:7]}`: {'pass' if evidence['before_pass'] else 'FAIL'} — {evidence['before']}\n"
        f"- branch `{head[:7]}`: {'pass' if evidence['after_pass'] else 'FAIL'} — {evidence['after']}\n\n"
        f"Files: {', '.join(files)} ({lines} lines)\n\n"
        "aegis-ceo merges or closes this PR. After merge the change is pulled into the container, and the "
        "next real scheduled run is compared with the 3 runs before. If it is worse, the merge is reverted."
    )
    pr = sh(["gh", "pr", "create", "--repo", f"{OWNER}/{agent}", "--base", "main", "--head", branch,
             "--title", f"Nightly improvement: {entry['summary'][:80] or agent}", "--body", body, "--label", LABEL], timeout=120)
    if pr.returncode != 0:
        return {**entry, "status": "error", "reason": "pr create failed: " + pr.stderr.strip()[:200]}
    return {**entry, "status": "proposed", "pr": pr.stdout.strip(), "branch": branch, "commit": head,
            "base": base, "files": files, "lines": lines}


def step_run(at: datetime, dry: bool) -> str:
    state = ledger()
    night = night_of(at)
    day = state["days"].setdefault(night, {"batch": [], "done": []})
    limited, why_limited = subscription_limited(at)
    busy, why_busy = priority_busy(at)
    failures = recent_failures(at)
    recent = {e["agent"] for e in state["entries"]
              if e.get("status") in ("proposed", "approved", "deployed", "held")
              and e.get("night", "") >= night_of(at - timedelta(days=2))}
    if not day["batch"]:
        ordered_failures = sorted(failures, key=lambda a: -len(failures[a]))
        day["batch"] = ni.select_batch(ordered_failures, already_done=sorted(recent))
    decision = ni.decide(at.hour, at.minute, failures=list(failures), subscription_limited=limited, priority_running=busy)
    if not decision["run"]:
        reason = why_limited or why_busy or decision["reason"]
        save_json(LEDGER, state) if not dry else None
        return f"run: skip ({reason}); tonight's batch {day['batch']}"
    finish = at + timedelta(seconds=SESSION_TIMEOUT_S)
    if not ni.in_idle_window(finish.hour, finish.minute):
        save_json(LEDGER, state) if not dry else None
        return f"run: skip (a session started now could run past the idle window); batch {day['batch']}"
    todo = [a for a in day["batch"] if a not in day["done"]]
    if not todo:
        return f"run: batch done for {night}: {day['done']}"
    agent = todo[0]
    if dry:
        return f"run: would improve {agent} now; batch {day['batch']}"
    entry = improve(agent, failures.get(agent, []), at)
    state = ledger()  # re-read in case another step wrote meanwhile
    day = state["days"].setdefault(night, day)
    state["entries"].append(entry)
    if entry["status"] == "limit":
        save_json(LIMIT, {"until": iso(at + timedelta(hours=5)), "seen": iso(at), "detail": entry.get("reason", "")})
    else:
        day["done"].append(agent)
    save_json(LEDGER, state)
    return f"run: {agent} -> {entry['status']} {entry.get('pr', entry.get('reason', ''))}"


# ---------------------------------------------------------------- review / deploy / verify / summary


def pr_state(pr_url: str) -> dict:
    proc = sh(["gh", "pr", "view", pr_url, "--json", "state,mergedAt,mergeCommit,closedAt,comments"], timeout=60)
    return json.loads(proc.stdout) if proc.returncode == 0 else {}


def step_review(at: datetime, dry: bool) -> str:
    state = ledger()
    night = night_of(at)
    day = state["days"].setdefault(night, {"batch": [], "done": []})
    if day.get("review_sent"):
        return "review: already sent"
    proposed = [e for e in state["entries"] if e.get("night") == night and e.get("status") == "proposed"]
    if not proposed:
        return "review: nothing proposed tonight"
    busy, why = priority_busy(at)
    running = trinity_db("select 1 from schedule_executions where agent_name='aegis-ceo' and status='running'")
    if running:
        return f"review: waiting, aegis-ceo is busy ({why or 'running'})"
    prs = "\n".join(f"- {e['agent']}: {e['pr']}" for e in proposed)
    message = (
        "Nightly improvement approvals. Each PR below has the failures it addresses and a before/after test "
        "(new test fails on base, passes on branch). For each one, read the PR body and diff with "
        "`gh pr view <url>` and `gh pr diff <url>`. Approve only if the change is Track B (skills/scripts/tests), "
        "addresses the cited failures, and the evidence is real. Approve: `gh pr merge <url> --squash --delete-branch`. "
        "Reject: `gh pr close <url> --comment \"<reason>\"`. Do not edit the PRs. Reply with one line per PR: "
        "APPROVED or REJECTED and the reason.\n\n" + prs
    )
    if dry:
        return f"review: would send aegis-ceo {len(proposed)} PRs"
    code, body = trinity_api("POST", "/api/agents/aegis-ceo/task", {
        "message": message,
        "allowed_tools": ["Bash(gh pr view:*)", "Bash(gh pr diff:*)", "Bash(gh pr merge:*)", "Bash(gh pr close:*)"],
        "max_turns": 40,
        "async_mode": True,
    })
    state = ledger()
    state["days"].setdefault(night, day)["review_sent"] = {"at": iso(at), "http": code, "execution": body.get("execution_id")}
    save_json(LEDGER, state)
    return f"review: sent aegis-ceo {len(proposed)} PRs (HTTP {code})"


def step_deploy(at: datetime, dry: bool) -> str:
    state = ledger()
    out = []
    for e in state["entries"]:
        if e.get("status") != "proposed" or not e.get("pr"):
            continue
        st = pr_state(e["pr"])
        if st.get("state") == "CLOSED":
            reason = (st.get("comments") or [{}])[-1].get("body", "")[:300]
            e.update(status="rejected", reason=f"aegis-ceo closed the PR: {reason}", decided=iso(at))
            out.append(f"{e['agent']} rejected")
        elif st.get("state") == "MERGED":
            e.update(status="approved", merged_at=st.get("mergedAt"), merge_commit=(st.get("mergeCommit") or {}).get("oid"))
    for e in state["entries"]:
        if e.get("status") != "approved":
            continue
        if dry:
            out.append(f"would deploy {e['agent']}")
            continue
        code, body = trinity_api("POST", f"/api/agents/{e['agent']}/git/pull", {"strategy": "stash_reapply"})
        if code == 200:
            e.update(status="deployed", deployed_at=iso(now_utc()))
            out.append(f"{e['agent']} deployed")
        else:
            e.update(deploy_error=f"HTTP {code}: {str(body)[:200]}")
            out.append(f"{e['agent']} deploy blocked (HTTP {code})")
    if not dry:
        save_json(LEDGER, state)
    return "deploy: " + (", ".join(out) or "nothing to do")


def run_ok(r: dict) -> bool:
    return r["status"] == "success" and bool(r["strict_closeout"])


def step_verify(at: datetime, dry: bool) -> str:
    state = ledger()
    out = []
    for e in state["entries"]:
        if e.get("status") != "deployed":
            continue
        rows = trinity_db(
            "select id, status, started_at, triggered_by, instr(coalesce(execution_log,''), ?) > 0 strict_closeout "
            "from schedule_executions where agent_name=? and triggered_by='schedule' and status not in ('running','pending_retry') "
            "order by started_at",
            (STRICT_CLOSEOUT, e["agent"]),
        )
        before = [r for r in rows if r["started_at"] < e["deployed_at"]][-3:]
        after = [r for r in rows if r["started_at"] >= e["deployed_at"]]
        if not after:
            continue
        nxt = after[0]
        baseline_ok = sum(run_ok(r) for r in before)
        e["next_run"] = {"id": nxt["id"], "ok": run_ok(nxt), "baseline_ok": f"{baseline_ok}/{len(before)}"}
        if run_ok(nxt) or baseline_ok == 0:
            e["status"] = "held"
            out.append(f"{e['agent']} held ({nxt['id']})")
            continue
        reason = (f"next real run {nxt['id']} {nxt['status']}, strict close-out "
                  f"{'yes' if nxt['strict_closeout'] else 'no'}; baseline {baseline_ok}/{len(before)} ok")
        if dry:
            out.append(f"would revert {e['agent']}: {reason}")
            continue
        repo = clone(e["agent"])
        ok = repo is not None and e.get("merge_commit")
        if ok:
            ok = sh(["git", "revert", "--no-edit", e["merge_commit"]], cwd=repo).returncode == 0
            ok = ok and sh(["git", "push", "-q", "origin", "main"], cwd=repo, timeout=120).returncode == 0
        if ok:
            trinity_api("POST", f"/api/agents/{e['agent']}/git/pull", {"strategy": "stash_reapply"})
        e.update(status="reverted" if ok else "revert_failed", revert_reason=reason, reverted_at=iso(now_utc()))
        out.append(f"{e['agent']} {'reverted' if ok else 'REVERT FAILED'}: {reason}")
    if not dry:
        save_json(LEDGER, state)
    return "verify: " + (", ".join(out) or "no new real runs")


def summary_text(at: datetime) -> str:
    state = ledger()
    night = night_of(at)
    tonight = [e for e in state["entries"] if e.get("night") == night]
    lines = [f"Task: nightly improvement summary ({night})", "Capacity: Claude subscription only, idle windows 02:00-03:30 and 05:15-07:15 UTC"]
    improved = [e for e in tonight if e.get("status") in ("proposed", "approved", "deployed", "held")]
    lines.append(f"Improved overnight: {len(improved)} of {len(tonight)} attempted")
    for e in tonight:
        link = e.get("pr") or "-"
        lines.append(f"- {e['agent']}: {e['status']} {link} {e.get('summary') or e.get('reason', '')}".rstrip()[:400])
    checked = [e for e in state["entries"] if e.get("next_run") and e.get("night") < night]
    if checked:
        lines.append("Held on real runs:")
        for e in checked[-10:]:
            lines.append(f"- {e['agent']} ({e['night']}): {e['status']} next run {e['next_run']['id']} "
                         f"{'ok' if e['next_run']['ok'] else 'not ok'}, baseline {e['next_run']['baseline_ok']}")
    nxt = ni.select_batch(sorted(recent_failures(at)), already_done=[e["agent"] for e in improved])
    lines.append("Next: " + ", ".join(nxt))
    if at.weekday() == 0:
        counts: dict[str, int] = {}
        for e in state["entries"]:
            if e.get("status") in ("deployed", "held") and e.get("night", "") >= night_of(at - timedelta(days=7)):
                counts[e["agent"]] = counts.get(e["agent"], 0) + 1
        lines.append("Week: " + ", ".join(f"{a} {counts.get(a, 0)}" for a in ni.FLEET))
    return "\n".join(lines)


def step_summary(at: datetime, dry: bool) -> str:
    state = ledger()
    day = state["days"].setdefault(night_of(at), {"batch": [], "done": []})
    if day.get("summary_posted"):
        return "summary: already posted"
    text = summary_text(at)
    if dry:
        return "summary (dry):\n" + text
    code, body = trinity_api("POST", f"/api/agents/aegis-infra/slack/channels/{INFRA_SLACK_CHANNEL}/messages", {"message": text})
    state = ledger()
    state["days"].setdefault(night_of(at), day)["summary_posted"] = {"at": iso(at), "http": code}
    save_json(LEDGER, state)
    return f"summary: posted HTTP {code} {'' if code == 200 else str(body)[:200]}"


# ---------------------------------------------------------------- tick


def pick_step(at: datetime) -> str:
    minutes = at.hour * 60 + at.minute
    if ni.in_idle_window(at.hour, at.minute):
        return "run"
    if 8 * 60 + 40 <= minutes < 9 * 60 + 30:
        return "review"
    if 9 * 60 + 30 <= minutes < 10 * 60:
        return "deploy"
    if 10 * 60 <= minutes < 12 * 60:
        return "summary"
    return "verify"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--step", choices=["run", "review", "deploy", "verify", "summary"])
    parser.add_argument("--at", help="pretend UTC time, ISO (dry runs only)")
    args = parser.parse_args()
    at = now_utc()
    if args.at:
        if not args.dry_run:
            parser.error("--at only with --dry-run")
        at = datetime.fromisoformat(args.at.replace("Z", "+00:00"))
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOCK, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("another tick is still running")
            return 0
        step = args.step or pick_step(at)
        try:
            msgs = []
            if step in ("deploy", "summary"):
                msgs.append(step_deploy(at, args.dry_run))
            fn = {"run": step_run, "review": step_review, "deploy": None, "verify": step_verify, "summary": step_summary}[step]
            if fn:
                msgs.append(fn(at, args.dry_run))
            if step != "verify":
                msgs.append(step_verify(at, args.dry_run))
        except Exception as exc:  # one bad tick must not kill the agent
            log(f"{step}: error {type(exc).__name__}: {exc}")
            return 1
        for m in msgs:
            log(m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
