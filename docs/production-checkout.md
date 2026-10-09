# Production checkout

The Oracle VM checkout of `hamidmatiny/aegis` is back on **`main`** (2026-10-09).

| | |
|---|---|
| Branch | `main` |
| Commit on the VM | see the history below; always the head of `main` after a redeploy |
| Redeploy | `git fetch && git merge --ff-only origin/main`, then `sudo docker compose -f docker-compose.yml -f deploy/oracle/docker-compose.demo.yml up -d --build input-defense output-defense` |
| VM-only change | `deploy/oracle/setup.sh` carries an uncommitted edit (rebuild `smb-portal` on `up`). A copy of the diff is in `~/setup.sh.local-*.patch` on the VM. |

## History

| When (UTC) | Commit | Why |
|---|---|---|
| 2026-10-08 | `d9132a3` on `fix/xml-config-credential-framing` | PR #96 deployed before merge to close BYPASS-005/006 |
| 2026-10-09 12:26 | `caea7c8` main | https://github.com/hamidmatiny/aegis/pull/96 merged (CodeRabbit APPROVED, CI green, auto-merge) |
| 2026-10-09 14:27 | `6f37d54` main | https://github.com/hamidmatiny/aegis/pull/97 merged (CodeRabbit APPROVED 69233b5, CI green, auto-merge) |
| 2026-10-09 17:57 | `5341c5a` main | https://github.com/hamidmatiny/aegis/pull/98 merged (CodeRabbit APPROVED f9a358d, CI green, auto-merge) |
| 2026-10-09 20:30 | `4e65bcc` main | https://github.com/hamidmatiny/aegis/pull/99 merged (CodeRabbit APPROVED 437c001, CI green, auto-merge); the 33 output-only attacks now 403 at the input layer live |

Never deploy a PR branch again without recording it here, and return to `main` once the PR merges.
