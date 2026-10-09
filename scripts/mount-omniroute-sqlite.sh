#!/usr/bin/env bash
# Mount the host's live OmniRoute SQLite into agent-aegis-infra (read-only).
#
# Preferred durable access for /token-budget and /daily-allocation:
#   host ~/.omniroute  ->  container /home/developer/.omniroute  (ro)
#
# Trinity's recreate_container_with_updated_config forwards existing bind
# mounts, so this survives normal Trinity recreates. A full delete+redeploy
# from scratch drops it — re-run this script.
#
# Usage (Trinity host with Docker access):
#   ./scripts/mount-omniroute-sqlite.sh
#
# Idempotent: exits 0 if the live mount is already present.

set -euo pipefail

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:${PATH:-}"

AGENT_CONTAINER="${AGENT_CONTAINER:-agent-aegis-infra}"
HOST_OMNIROUTE="${HOST_OMNIROUTE:-$HOME/.omniroute}"
CONTAINER_MOUNT="${CONTAINER_MOUNT:-/home/developer/.omniroute}"
SQLITE_ENV_VALUE="${SQLITE_ENV_VALUE:-/home/developer/.omniroute/storage.sqlite}"

if [[ ! -f "$HOST_OMNIROUTE/storage.sqlite" ]]; then
  echo "FAIL: host DB missing at $HOST_OMNIROUTE/storage.sqlite" >&2
  exit 1
fi

if ! docker inspect "$AGENT_CONTAINER" >/dev/null 2>&1; then
  echo "FAIL: container $AGENT_CONTAINER not found — start it via Trinity first" >&2
  exit 1
fi

already=$(docker inspect "$AGENT_CONTAINER" --format '{{range .Mounts}}{{println .Destination}}{{end}}' \
  | grep -cx "$CONTAINER_MOUNT" || true)
if [[ "$already" == "1" ]]; then
  echo "OK: $CONTAINER_MOUNT already mounted"
  docker exec "$AGENT_CONTAINER" python3 -c \
    "import sqlite3,os;p=os.environ.get('OMNIROUTE_SQLITE','$SQLITE_ENV_VALUE');c=sqlite3.connect(f'file:{p}?mode=ro',uri=True);print('call_logs',c.execute('select count(*) from call_logs').fetchone()[0])"
  exit 0
fi

# Refuse if a real Claude task is in flight
if docker exec "$AGENT_CONTAINER" sh -c 'ps -eo args | grep -E "^claude |claude --print" | grep -v grep' >/dev/null 2>&1; then
  echo "FAIL: $AGENT_CONTAINER has a live claude task — wait until idle, then re-run" >&2
  exit 2
fi

echo "Recreating $AGENT_CONTAINER with bind $HOST_OMNIROUTE -> $CONTAINER_MOUNT (ro)"
python3 - "$AGENT_CONTAINER" "$HOST_OMNIROUTE" "$CONTAINER_MOUNT" "$SQLITE_ENV_VALUE" <<'PY'
import json, os, subprocess, sys, time

agent, host_omni, c_mount, sqlite_env = sys.argv[1:5]

def sh(*args, check=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit((r.stderr or r.stdout).strip() or f"failed: {args}")
    return r.stdout.strip()

inspect = json.loads(sh("docker", "inspect", agent))[0]
cfg, hc = inspect["Config"], inspect["HostConfig"]
nets = list(inspect["NetworkSettings"]["Networks"])

host_port = None
cport = "22"
for p, binds in (inspect["NetworkSettings"].get("Ports") or {}).items():
    if binds:
        host_port = binds[0].get("HostPort")
        cport = p.split("/")[0]
        break

sh("docker", "stop", "-t", "15", agent)
time.sleep(2)
sh("docker", "rm", agent)

args = [
    "docker", "create", "--name", agent, "--hostname", "aegis-infra",
    "--restart", "unless-stopped",
]
if hc.get("NanoCpus"):
    args += ["--cpus", str(hc["NanoCpus"] / 1e9)]
if hc.get("Memory"):
    args += ["--memory", str(hc["Memory"])]
for cap in hc.get("CapDrop") or []:
    args += ["--cap-drop", cap]
for opt in hc.get("SecurityOpt") or []:
    args += ["--security-opt", opt]
for path, opts in (hc.get("Tmpfs") or {}).items():
    args += ["--tmpfs", f"{path}:{opts}" if opts else path]
for k, v in (cfg.get("Labels") or {}).items():
    args += ["--label", f"{k}={v}"]
for e in cfg.get("Env") or []:
    if e.startswith("OMNIROUTE_SQLITE="):
        continue
    args += ["-e", e]
args += ["-e", f"OMNIROUTE_SQLITE={sqlite_env}"]

# Keep non-omniroute mounts; always ensure workspace + live omniroute
seen = set()
for m in inspect.get("Mounts") or []:
    dest = m["Destination"]
    if dest == c_mount:
        continue
    mode = "rw" if m.get("RW", True) else "ro"
    src = m["Name"] if m["Type"] == "volume" else m["Source"]
    args += ["-v", f"{src}:{dest}:{mode}"]
    seen.add(dest)
if "/home/developer" not in seen:
    args += ["-v", "agent-aegis-infra-workspace:/home/developer:rw"]
args += ["-v", f"{host_omni}:{c_mount}:ro"]
if host_port:
    args += ["-p", f"{host_port}:{cport}"]
args.append(cfg["Image"])

print("created", sh(*args)[:12])
for net in nets:
    sh("docker", "network", "connect", net, agent)
sh("docker", "start", agent)
time.sleep(3)
print(sh("docker", "inspect", "-f",
         "{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}\n{{end}}", agent))
print(sh("docker", "exec", agent, "python3", "-c",
         f"import sqlite3,os;p=os.environ.get('OMNIROUTE_SQLITE','{sqlite_env}');"
         "c=sqlite3.connect(f'file:{p}?mode=ro',uri=True);"
         "print('env',os.environ.get('OMNIROUTE_SQLITE'));"
         "print('call_logs',c.execute('select count(*) from call_logs').fetchone()[0])"))
PY

echo "DONE: live OmniRoute SQLite mounted read-only"
