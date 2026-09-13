# AEGIS Infra Target Architecture

**What this is:** where the agent is deliberately headed. The companion to **`ARCHITECTURE.md`** (what runs today). When something here ships, it moves *out* of this doc and *into* `ARCHITECTURE.md`.

**Last updated:** 2026-09-13

## Direction

Stay narrow and boring. This agent's entire value is that it is the one place tier/model decisions and their real cost get made and recorded — it should never grow into a second analysis or customer-facing agent, and it should never need premium-tier reasoning to do its own job. Every capability added here should make some other agent's assignment more correct or cheaper, not add scope to what this agent itself does.

## Planned Capabilities

- **Scheduled `/propose-skill-upgrade`** — skill exists (manual). Target: light cadence (e.g. monthly) once Hamid wants recurrence. Ship `enabled: false` until then.
- **Expand independent verification** beyond `aegis-analyst` (threat-intel escalations, VP synthesis) after a proven PASS/FAIL cycle on revenue.
- **Structured `memory/MEMORY.md` on other agents** — infra pilot applied; expand one agent at a time after approval.
- **Automated anomaly escalation** — today `/track-usage` flags anomalies for a human to read; the target is a direct notification path to `aegis-ceo` (via `mcp__trinity__send_message` or an `agent.task.*` event subscription) so a real spike doesn't wait for someone to open the dashboard. Depends on: enough real usage-log history to know what "anomalous" actually looks like for this fleet, so the threshold isn't guessed.
- **OmniRoute config-as-code** — once `/audit-omniroute` has run enough times to establish a stable, known-good config, move from "audit and describe" to "audit and diff against a committed desired-state file" (still proposal-only — this agent doesn't gain write access to OmniRoute without a separate, explicit decision). Depends on: OmniRoute's admin API actually being confirmed stable enough to diff against.
- **Per-agent budget caps, not just visibility** — today usage tracking is observational. A future version could propose (not enforce) soft budget caps per agent, flagged the same way anomalies are today. Depends on: enough `/track-usage` history to know what a sane cap even looks like per role.

Next ideas, unordered: a lightweight cost-per-task estimate (so a tier proposal can say "~$X per typical run" instead of only "mid-cost"), and folding Cursor/other non-pluggable subscriptions into the audit as an explicit "not applicable to routing" list rather than something a future run has to be reminded of separately.
