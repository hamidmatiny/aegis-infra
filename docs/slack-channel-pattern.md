# Slack channel pattern (fleet default)

One Slack app for the whole fleet. One dedicated channel per agent. Plus `#fleet-directory` — a second binding on `aegis-infra` for "which channel is who?" lookup.

## Rule

**Never create a second Slack app per agent.** The workspace already has **Trinity AEGIS** installed once (Socket Mode). Every new agent gets its own public channel and a Trinity binding to that channel.

**Second binding note:** Trinity's convenience endpoint `POST /api/agents/{name}/slack/channel` returns `already_bound` if the agent already has a channel — that is an API idempotency/product guard, **not** a DB uniqueness on `agent_name`. The table `slack_channel_agents` is `UNIQUE(team_id, slack_channel_id)` only (one agent per channel). A second channel for the same agent is schema-legal; `#fleet-directory` was bound to `aegis-infra` that way. Caveat: UI `GET .../slack/channel` and `unbind` still treat "the" agent binding as singular (unbind removes all rows for that agent in the workspace).

## Input authority (Hamid)

Slack @mentions from **Hamid** (verified owner email) in a bound channel are real instructions — same authority as Trinity Chat. Agents must still obey every propose→**approved** / **approve** gate; Slack is not a bypass.

**Membership reality:** channels are **public**. As of 2026-09-14 the Aegis Slack workspace has a single human (`hamidmatiny`); only Hamid is treated as a trusted instructor. Anyone later added to the workspace can join these channels and @mention the bot — those senders stay on Trinity's restricted public tool allowlist and must not be treated as Hamid.

Platform note: Trinity defaults Slack to `channel_allowed_tools=WebSearch,WebFetch`. Owner/shared senders who pass `email_has_agent_access` get full tools (same as authenticated chat) via the message router — strangers do not.

## Naming

Match the Trinity agent name for dedicated channels:

```text
agent name           →  Slack channel
aegis-ceo             →  #aegis-ceo
aegis-infra           →  #aegis-infra
aegis-threat-intel    →  #aegis-threat-intel
aegis-analyst         →  #aegis-analyst
aegis-core-infra      →  #aegis-core-infra
the-brain             →  #the-brain
(directory)           →  #fleet-directory   (also bound to aegis-infra; ask /fleet-directory here)
```

## New-agent checklist

1. Confirm the workspace Slack app is already installed in Trinity Settings (Client ID/Secret, Signing Secret, App Token, Socket Mode connected, Install to Workspace done once).
2. Create + bind the channel for the new agent (same bot — no new OAuth):

   ```bash
   # Auth as Trinity admin, then:
   curl -s -X POST "http://localhost:8000/api/agents/<agent-name>/slack/channel" \
     -H "Authorization: Bearer $TOKEN"
   ```

   Trinity calls Slack `conversations.create` with the **existing** workspace bot token, names the channel after the agent, and records the binding. The bot is the channel creator, so it is already a member — no separate “invite bot” step and no second app install.

3. Enable proactive (outbound) messages:

   ```bash
   curl -s -X PUT \
     "http://localhost:8000/api/agents/<agent-name>/slack/channels/<channel_id>/proactive" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"allow_proactive": true}'
   ```

4. Wire report-producing skills to post via Trinity MCP (same pattern as `aegis-ceo`’s `/daily-trajectory-review`):

   - `mcp__trinity__list_channel_groups` (`channel_type: "slack"`)
   - `mcp__trinity__send_group_message` with the real summary text

   For `aegis-infra`, that is at least `/track-usage`, `/review-pricing`, and `/audit-omniroute`. Hamid may also **invoke** those skills via Slack (same authority as Trinity Chat). Propose→approve for live config/tier/auth changes still applies — Slack is not an approval bypass.

5. Smoke-test: trigger one wired skill (or a proactive API post) and confirm a real message appears in the new channel — not a placeholder.

## What this is not

- Not a new Slack app / OAuth install per hire
- Not a substitute for `agent-gate` / human approval on spend or auth flips
- Not a bypass of propose→**approved** / **approve** — Slack carries Hamid's instructions, not automatic approval of gated actions
