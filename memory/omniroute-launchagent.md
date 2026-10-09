# OmniRoute LaunchAgent supervision

**Installed:** 2026-09-18 (after unsupervised SIGTERM at 00:40:18Z took the fleet dark)

| Item | Value |
|------|-------|
| Label | `com.aegis.omniroute` |
| Plist | `~/Library/LaunchAgents/com.aegis.omniroute.plist` |
| Wrapper | `~/Library/Application Support/aegis-omniroute/run-omniroute.sh` |
| Logs | `~/Library/Logs/aegis-omniroute/{stdout,stderr}.log` |
| Port / bind | `20129` / `0.0.0.0` |
| KeepAlive | `true` (proven: kill parent → relaunch within ~2s, exit 143) |

## Ops

```bash
launchctl print "gui/$(id -u)/com.aegis.omniroute"
# unload (stops supervision): launchctl bootout "gui/$(id -u)/com.aegis.omniroute"
# reload: launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.aegis.omniroute.plist
```

Do **not** run ad-hoc `omniroute serve --daemon` alongside this — LaunchAgent owns the process. Prefer `launchctl kickstart -k gui/$(id -u)/com.aegis.omniroute` for intentional restarts.

## 2026-09-22 — unreachable was host sleep, not a crash loop

The LaunchAgent process that started 2026-09-20 15:04 local was still the same pid on 2026-09-22. `call_logs` had no multi-hour outage; the gaps match the Mac's idle-sleep / dark-wake cycle (`pmset`: display off 2026-09-22 02:02 -0300, Idle Sleep 02:13, user Wake 08:18:19). While the host sleeps, nothing is listening on `:20129`, so a health check reports connection refused. Restarting the LaunchAgent does not fix that.

`com.aegis.trinity-awake` runs `caffeinate -i -m -s` so idle sleep does not freeze Trinity and OmniRoute. Unload it if the battery cost is unacceptable: `launchctl bootout "gui/$(id -u)/com.aegis.trinity-awake"`.
