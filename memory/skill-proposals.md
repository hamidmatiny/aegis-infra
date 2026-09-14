# Skill Upgrade Proposals

Running record of proposed / approved / declined skill, verification, and memory-structure upgrades. Appended by `/propose-skill-upgrade`. Same explicit **approved** / **approve** gate as `memory/tier-assignments.md` — silence is not approval.

---

## Proposal SU-2026-09-13-1 — Independent verification for `aegis-analyst` revenue reports (pilot)

**Status:** approved (2026-09-13) by Hamid — **applied** (2026-09-13)  
**Agent:** `aegis-analyst` (fleet-first pilot; not fleet-wide)

**Gap:** Revenue/MRR figures leave the fleet and reach Hamid / `aegis-ceo` with no second check that the claimed numbers are supported by the cited corp-orchestrator payload. A producer that grades its own report in the same context is biased toward agreeing with itself.

**Why now:** Analyst is the only agent whose primary product is a money number ($29.00 CAD / 1 subscriber was the verified baseline in its CLAUDE.md). Wrong MRR is high-cost for decision-making; a cheap structural check is proportionate. Other outbound reports (threat-intel escalations, VP synthesis) can follow once this pilot works.

**Applied as:**

1. `aegis-analyst` `/check-revenue` — draft claim → Step 5 independent verify via `chat_with_agent` → `aegis-infra` `/verify-revenue-claim` (claim + sources only) → publish only on `PASS`.
2. New skill `aegis-infra` `/verify-revenue-claim` — structural PASS/FAIL only.
3. Local runs without Trinity chat skip verify and must say so — no fake PASS.

**Tier/cost:** free-pool verifier call.  
**Pilot scope:** `aegis-analyst` only until a real PASS/FAIL cycle is proven.

---

## Proposal SU-2026-09-13-2 — Structured memory standard (pilot: `aegis-infra`)

**Status:** approved (2026-09-13) by Hamid — **applied** (2026-09-13)  
**Agent:** `aegis-infra` first; other agents only after further approval

**Gap:** Loose topic logs without a consult-first spine.

**Applied as:** created `memory/MEMORY.md` (Verified facts / Rules / Open / Last session summary). Topic logs (`tier-assignments.md`, `usage-log.md`, `pricing-checks.md`, `skill-proposals.md`) kept as append-only satellites.

---

## Proposal SU-2026-09-13-3 — P0 fail-closed wording (check-revenue + VP synthesize)

**Status:** approved (2026-09-13) by Hamid — **applied** (2026-09-13)  
**Agents:** `aegis-analyst`, `the-brain`  
**Type:** narrow logic / wording fix — **no new capability**

### (a) `aegis-analyst` `/check-revenue` — applied

Publish only after explicit `PASS:`. Skip/deny/timeout are never publish-worthy. Step 6/7 wording updated; residual "or explicit skip" removed.

### (b) `the-brain` `/synthesize` — applied

Pull gate: exit 0 + four SHAs required; else abort with `status: pull-failed`. Skill written into live `agent-the-brain` container (upstream is read-only Cornelius — **volume-local until own-repo bind**; survives normal restarts, at risk on recreate from template).

---

## DN-2026-09-13-1 — `aegis-analyst` `/escalate-anomaly` delivery

**Decision:** Option A (2026-09-13) — **applied**  
- Granted `aegis-analyst` → `aegis-ceo` A2A permission  
- Skill uses `mcp__trinity__chat_with_agent`; claim escalated only after confirmed delivery; on failure: "flagged, delivery failed"

## DN-2026-09-13-2 — `aegis-threat-intel` `/scan-threats` delivery

**Decision:** Option B + mandatory queue on chat failure (2026-09-13) — **applied**  
- Granted `aegis-threat-intel` → `aegis-ceo` A2A permission  
- Claim CEO notified only after confirmed delivery  
- Operator-queue alert **mandatory** when ceo-chat fails (not only "if urgent")  
- `CLAUDE.md` escalation channels + `/scan-threats` Step 7 updated

---

## Proposal SU-2026-09-13-4 — Per-task Slack performance report (fleet channel template)

**Status:** proposed (2026-09-13) — **not applied**  
**Agents:** fleet (pilot candidate: `aegis-infra` or `aegis-analyst` first)  
**Type:** new outbound skill step / shared report format — propose only

**Gap:** Each agent's Slack channel shows skill output when wired, but not a consistent per-task card of *who assigned it, who it worked with, who it handed results to, and outcome* — so Hamid can't scan a channel like an employee work log.

**Why now:** DN-1/DN-2 already depend on A2A `chat_with_agent` delivery confirmation; execution rows already carry assigner/trigger metadata. Hamid asked for a coworker-style trail in each agent's own channel. Must not invent fields (same discipline as the `paying_subscribers` comparison bug).

### Real data available today (Trinity `schedule_executions` / agent executions API)

| Report slot | Real fields (use only if present) | Do **not** invent |
|-------------|-----------------------------------|-------------------|
| Assigned-by | `triggered_by` (`chat` / `manual` / `mcp` / `agent` / `schedule` / `slack` / …); `source_user_email` + `source_user_id` when human; `source_agent_name` when A2A; `source_mcp_key_name` when MCP | A human name when only `source_agent_name` is set; "Hamid" when email is null |
| Collaborators | Child / peer executions where `source_agent_name` is this agent **or** this run's confirmed `chat_with_agent` / `call_a2a_agent` results that returned an `execution_id` | A collaborator list inferred from prose; agents mentioned in the prompt but never called |
| Handed-to | Confirmed outbound A2A targets from this run (same delivery-ack pattern as DN-1/DN-2) — agent name + exec id if returned | "escalated to ceo" without a confirmed send ack |
| Outcome | `status`, `duration_ms`, `error` (if any), `id` (execution id), optional `cost` / `model_used` when non-null | Success when status ≠ success; a fabricated summary of work not in `response` / skill output |

**Not first-class today:** a single `collaborators[]` column on the parent row. Collaborators must be assembled from confirmed tool/A2A results or related execution rows — if none, the report line is `collaborators: none` (explicit), never omitted-as-zero-people by defaulting.

### Proposed Slack template (post to **this agent's** bound channel only)

```text
Task report — {agent_name}
execution_id: {id}
assigned_by: {source_user_email | source_agent_name | "trigger:"+triggered_by}   # first non-null; else "not returned by API"
collaborators: {comma-separated agent names from confirmed A2A} | none
handed_to: {comma-separated confirmed outbound targets} | none
outcome: {status} · {duration_ms}ms
error: {error}          # only if status failed / error non-null
notes: {optional one-line skill title or schedule_id if not __manual__}
```

Rules:
- Omit a line only when the field is structurally N/A (e.g. no `error` on success) — never fill gaps with `0` / `"unknown"` / guessed names.
- Outbound-only; does **not** grant Slack inbound skill control.
- Fail-closed: if channel unbound or `send_group_message` fails, say so in Trinity report / operator queue — do not claim "posted to Slack."

**Proposed change:** new shared skill step (e.g. `/post-task-report`) or an end-of-skill block in each report-producing playbook; pilot on one agent after approval.

**Tier/cost if approved:** free-pool (formatting + one proactive Slack send).  
**Trinity mapping:** read own execution metadata via Trinity API/MCP; post via existing `list_channel_groups` + `send_group_message` (or `POST .../slack/channels/{id}/messages`). No new multi-channel binding required.  
**Pilot scope:** one agent (`aegis-infra` or `aegis-analyst`) until a real post is verified in-channel.  
**Depends on:** Hamid/`aegis-ceo` explicit **approved** / **approve**. Multi-channel "invite agent into any Slack thread" is **out of scope** (not supported by current Trinity create/bind API — see investigation).

Reply **approved** / **approve** to accept, or decline with a reason. Nothing is applied until then.

---

## Change log

- 2026-09-13: File created. Logged SU-2026-09-13-1 and SU-2026-09-13-2 as proposed.
- 2026-09-13: Both approved by Hamid; both applied (analyst verify step + infra `/verify-revenue-claim`; `memory/MEMORY.md` retrofit).
- 2026-09-13: Proposed SU-2026-09-13-3; logged DN-2026-09-13-1/2; standing fail-closed check in `/propose-skill-upgrade` Step 2b.
- 2026-09-13: SU-2026-09-13-3 approved+applied; DN-1 Option A and DN-2 Option B+mandatory queue approved+applied; A2A edges analyst→ceo and TI→ceo granted.
- 2026-09-14: Proposed SU-2026-09-13-4 (per-task Slack performance report) — not applied. Created Slack channels `#aegis-threat-intel`, `#aegis-analyst`, `#the-brain` (outbound proactive + smoke posts confirmed).
