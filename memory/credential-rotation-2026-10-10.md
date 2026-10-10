# Credential rotation 2026-10-10 (no values recorded here)

Trigger: the-brain's public git history carried 4 encrypted `.credentials.enc` versions (2026-09-14 x3, 2026-09-15). The decryption key (`CREDENTIAL_ENCRYPTION_KEY`) was never published (full-history search of all 50 public repos, public gists, local image metadata). All secrets inside were still live, so they were rotated.

| Secret | Holders | Done | Evidence (fingerprints only) |
|---|---|---|---|
| OmniRoute key for fleet agents (`OMNIROUTE_API_KEY` = `ANTHROPIC_API_KEY`) | analyst, core-infra, data-quality, growth, scout, threat-intel, the-brain | New OmniRoute key `aegis-fleet-agents` (id bd471907) via `POST /api/keys`; installed + credentials exported | Old value was not a registered OmniRoute key (OmniRoute accepts loopback/Docker-bridge calls without a key; LAN gets 401), so there was nothing to revoke. Calls now log `api_key_name=aegis-fleet-agents`. |
| `CORP_READONLY_TOKEN` (corp-orchestrator read-only) | VM `~/aegis/.env`; analyst, growth, the-brain (`CORP_READONLY_TOKEN`), ceo (`CORP_ORCHESTRATOR_API_TOKEN`) | New random token on the VM, corp-orchestrator recreated, 4 containers updated + exported | old token GET /v1/agents -> 401; new -> 200 from all 4 |
| the-brain Trinity MCP key | the-brain `.mcp.json` | `POST /api/agents/the-brain/mcp-key/regenerate` (superseded key deleted, container recreated) | verify 200 |
| Trinity AEGIS Slack bot token (`FLEET_KG_SLACK_BOT_TOKEN` = Trinity workspace bot token) | Trinity `slack_workspaces`, the-brain `.env` | Done 00:53Z: old token revoked with `auth.revoke` (then `account_inactive`); Hamid approved Trinity's OAuth install (`POST /api/settings/slack/install`, callback stored the new bot token); copied from Trinity's record into the-brain `.env` + exported | `auth.test` ok on the new token; bot rejoined 17 bound channels (`conversations.join`, revocation had removed it); test post from all 16 agents HTTP 200. The install was approved twice (00:49:40Z, 00:53:44Z): the first issued token was overwritten before it could be checked. |

Also: aegis commit b56ec9b (2026-08-14) published an age private key with a `.env.enc` encrypted to it; every real secret in that file had already been rotated. History rewrites for the-brain (drop `.credentials.enc`) and aegis (strip those two blobs) are prepared; Hamid runs the force-push.
