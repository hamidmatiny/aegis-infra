# Fleet A2A routing table (Track B — personal Trinity fleet)

**Scope:** Hamid's personal agent company on Trinity. Not `corp-orchestrator` (Track A).

There are **two separate protocols**. Do not conflate them:

| Situation | Which protocol | What you do |
|-----------|----------------|-------------|
| "I need agent X to do a task / I need work from another branch" | **Task routing** (below) | Same-branch → message peer directly. Cross-branch → message **your manager**; manager forwards. |
| "I'm not sure whether I should do X" (judgment / ambiguity) | **Uncertainty escalation** (below) | Ask your **own manager** first; consult peers; escalate up the management chain; Hamid is **last** resort — never first. |

---

## Protocol A — Task routing (Hamid, 2026-09-14)

Use when the ask is a **routine work request**: run a playbook, fetch a number, review a diff, forward an assignment.

1. **Same branch → direct.** Peers in the same department/branch may message each other both ways via Trinity A2A permissions (`POST /api/agents/{name}/permissions/{other}`).
2. **Cross branch → manager-routed.** An agent must not message another branch's agent directly. It messages its **manager**; the manager messages the target branch's manager (or the agent, if the manager *is* that branch's head); the manager decides whether/how to forward — not a silent passthrough.

**Fail closed:** if branch membership is ambiguous, treat as cross-branch (manager-routed). Never propose a new direct cross-branch A2A edge; refuse and point at this table.

---

## Protocol B — Uncertainty / judgment-call escalation (Hamid, 2026-09-15)

Use when you face a **real decision you are unsure about** — "should I do this or not?" — not when you merely need someone else to execute a clear task.

**This does not override Protocol A.** Cross-branch *task* requests still go through managers. Uncertainty is about *whether to act*, not about who does the work.

### Order (mandatory)

1. **Ask your own manager first** (`manager` column in the roster table below — today usually `aegis-ceo`).
2. **Also consult peers:** same-branch colleagues at the **same or higher** career-ladder level as you; then other same-branch teammates. (Peers advise; they do not replace the manager.)
3. **If your manager cannot resolve it**, the manager escalates **up its own chain** — asks *its* manager, and so on.
4. **Only if the chain reaches `aegis-ceo` and the CEO also cannot resolve it** does the question go to **Hamid**. Hamid is the final fallback, not the first stop.

### Explicit anti-patterns

- Skipping the manager and asking Hamid first because it "feels faster"
- Treating a judgment call as a Protocol A cross-branch task and pinging an unrelated specialist for permission
- Self-authorizing a risky action because "peers seemed fine with it" without manager input when you were actually unsure

### Examples

| Ask | Protocol |
|-----|----------|
| "Please run `/check-revenue` and send me the number" | A — task routing |
| "Should I publish this revenue claim without a `PASS:` from infra verify because verify is timing out?" | B — uncertainty |
| "Forward this deploy-risk flag to core-infra" | A — task routing (manager forwards) |
| "I'm unsure whether this CVE is urgent enough to wake Hamid vs LOG-only" | B — uncertainty (ask manager first) |

## How to change a branch's manager later

When a branch gets a real department head (second-layer hire), update **only** that branch's `manager` cell below and grant/revoke the matching A2A edges (`specialist ↔ new-head`, `new-head ↔ aegis-ceo` as needed). Do not redesign the protocol.

## Live roster → branch → manager (ground truth)

*Pulled from Trinity `GET /api/agents` + tags/permissions on 2026-09-17 (product-eng manager hire). Prior snapshot 2026-09-14. Re-check with those APIs before proposing permission changes — this file can go stale.*

| Branch | Manager (today) | Agents in branch | Same-branch direct | Notes |
|--------|-----------------|------------------|--------------------|-------|
| Executive | `aegis-ceo` (founder-facing; peers with VP) | `aegis-ceo`, `the-brain` (VP) | **Wired** `aegis-ceo ↔ the-brain` | Only branch with 2+ members as of 2026-09-14 |
| Infrastructure & Compute | `aegis-ceo` | `aegis-infra` | N/A (1 member) | |
| Cybersecurity | `aegis-ceo` | `aegis-threat-intel`, `aegis-redteam` | Direct once both live (Protocol A + D) | Redteam hired 2026-09-20 — live gateway attacks |
| Finance | `aegis-ceo` | `aegis-analyst` | N/A (1 member) | |
| Engineering | `aegis-ceo` | `aegis-core-infra` | N/A (1 member) | Grid: `dept-engineering` |
| Product Engineering | **`aegis-product-eng`** → `aegis-ceo` | Manager: `aegis-product-eng`. ICs: `aegis-gateway`, `aegis-policy-engine`, `aegis-model-router`, `aegis-agent-gate`, `aegis-audit` | **Wired** IC↔manager + IC peer mesh; manager↔CEO. Direct IC↔CEO A2A **revoked** (middle hop real). | Manager hire 2026-09-17 (L5 structural exception). Grid: ICs `reports-to-aegis-product-eng`; manager `dept-product-engineering` + `reports-to-aegis-ceo`. |
| Data / Quality | `aegis-ceo` | `aegis-data-quality` | N/A (1 member) | Live 2026-09-14 (`github:hamidmatiny/aegis-data-quality@main`); free-pool OmniRoute |
| Growth / Marketing | `aegis-ceo` | `aegis-growth` | N/A (1 member) | Live; free-pool OmniRoute |
| Capability / Learning (service) | `aegis-ceo` | `aegis-scout` | N/A (1 member) | Live 2026-09-16 (`github:hamidmatiny/aegis-scout@main`); mid-cost OmniRoute; service role (not a manager). **Grid tags (2026-09-16):** `dept-scout` + `reports-to-aegis-ceo` (A2A ≠ department overlay — both required). |

`trinity-system` is platform infrastructure, **not** a fleet branch member. Do not put it on this table or grant it fleet A2A edges for protocol work.

## Manager hub edges (required)

Every specialist must be able to reach its manager, and the manager must be able to reach each specialist (for forwarding).

| Edge | Purpose | Status (2026-09-14) |
|------|---------|---------------------|
| `aegis-infra` → `aegis-ceo` | Infra escalates / asks manager | **Granted** |
| `aegis-ceo` → `aegis-infra` | Manager replies / assigns Infra | Present |
| `aegis-threat-intel` → `aegis-ceo` | TI escalates | Present |
| `aegis-ceo` → `aegis-threat-intel` | Manager forwards to TI | Present |
| `aegis-analyst` → `aegis-ceo` | Finance escalates | Present |
| `aegis-ceo` → `aegis-analyst` | Manager forwards to Finance | Present |
| `aegis-core-infra` → `aegis-ceo` | Engineering escalates | Present |
| `aegis-ceo` → `aegis-core-infra` | Manager forwards to Engineering | Present |
| `aegis-data-quality` → `aegis-ceo` | Data/Quality escalates | **Granted** |
| `aegis-ceo` → `aegis-data-quality` | Manager forwards to Data/Quality | **Granted** |
| `aegis-growth` → `aegis-ceo` | Growth escalates | **Granted** |
| `aegis-ceo` → `aegis-growth` | Manager forwards to Growth | **Granted** |
| `aegis-scout` → `aegis-ceo` | Scout assigns learning / escalates | **Granted** (2026-09-16) |
| `aegis-ceo` → `aegis-scout` | Manager replies / assigns Scout | **Granted** (2026-09-16) |
| `the-brain` → `aegis-ceo` | VP ↔ CEO (also same-branch peer) | **Granted** |
| `aegis-ceo` → `the-brain` | CEO ↔ VP | **Granted** |

| `aegis-product-eng` → `aegis-ceo` | PE Manager escalates / asks CEO | **Granted** (2026-09-17) |
| `aegis-ceo` → `aegis-product-eng` | CEO assigns / replies to PE Manager | **Granted** (2026-09-17) |
| each PE IC ↔ `aegis-product-eng` | IC↔manager hub (5 ICs) | **Granted** (2026-09-17) |
| PE IC ↔ `aegis-ceo` | Direct skip | **Revoked** (2026-09-17) — use manager |

## Forbidden by default

Any direct edge where `branch(source) != branch(target)` and neither side is acting as the **manager of record** for the other's branch.

Examples that must **not** be added:

- `aegis-analyst` → `aegis-threat-intel` (Finance → Cyber)
- `aegis-analyst` → `aegis-core-infra` (Finance → Engineering)
- `aegis-infra` → `aegis-core-infra` (Infra → Engineering)
- `aegis-threat-intel` → `aegis-analyst` (Cyber → Finance)

## Protocol C — Capacity HOLD / lift (Hamid, 2026-09-19)

**Problem:** On 2026-09-18 `aegis-infra` posted an explicit Slack HOLD under real free-pool exhaustion; nobody toggled schedules; autonomous work kept firing and close-out misses continued. Advisory text is not a safety mechanism.

**Authority:** `aegis-infra` **judges and executes**. It already owns capacity evidence (`/token-budget`, `/daily-allocation`). Requiring `aegis-ceo` to approve the pause before toggles recreated the failure mode. CEO is **notified after** apply/lift via `chat_with_agent` — not a gate.

**Mechanism:** skill `/capacity-hold` → `mcp__trinity__toggle_agent_schedule` on the HOLDable set (revenue check, infra-diff, threat scan, fleet review, growth check, SI slots, etc.). State + paused IDs live in `memory/capacity-hold.md` so lift only re-enables what this skill paused. Thresholds reuse token-budget judgment (see skill) — no second detector.

**Never pause:** infra `Daily token budget` and `Daily allocation` (recovery path).

**Standing A2A edges (narrow — schedule list/toggle only; not a general chat channel):**

| Edge | Purpose | Status |
|------|---------|--------|
| `aegis-infra` → `aegis-analyst` | HOLD/lift Finance schedules | **Granted** 2026-09-19 |
| `aegis-infra` → `aegis-core-infra` | HOLD/lift Engineering schedules | **Granted** 2026-09-19 |
| `aegis-infra` → `aegis-threat-intel` | HOLD/lift Cyber schedules | **Granted** 2026-09-19 |
| `aegis-infra` → `aegis-data-quality` | HOLD/lift Data/Quality schedules | **Granted** 2026-09-19 |
| `aegis-infra` → `aegis-growth` | HOLD/lift Growth schedules | **Granted** 2026-09-19 |
| `aegis-infra` → `aegis-ceo` | Post-HOLD notify (already existed) | Present |

Do **not** expand these edges into ad-hoc cross-branch tasking. Cross-branch work still uses Protocol A via CEO. Uncertainty about *whether* to HOLD still uses Protocol B if the threshold is ambiguous.

---

## Protocol D — Attack-technique handoff → `aegis-redteam` (Hamid, 2026-09-20)

**Problem:** Agents that encounter a newly published jailbreak / prompt-injection / PII-exfil technique during normal work (CVE feeds, papers, browsing, scout finds) had nowhere to put it. Knowledge died in a report.

**Sink:** `aegis-redteam` — tests the technique against the **live** gateway (`POST https://defenseaegis.org/v1/chat/completions`), logs pass/fail with transcripts, and on a **confirmed currently-working bypass** escalates to `aegis-ceo` as a **decision point** (new policy, new detection, enforcement fix) — not a soft log-only finding.

**How to hand off**

1. Prefer **manager-routed** (Protocol A): finder → own manager → `aegis-ceo` → `aegis-redteam` with the technique + source URL + example prompts.
2. **Standing exception edges** (narrow — technique handoff only, not general chat), once granted:

| Edge | Purpose | Status |
|------|---------|--------|
| `aegis-threat-intel` → `aegis-redteam` | TI finds attack technique in feeds | **Granted** 2026-09-20 |
| `aegis-scout` → `aegis-redteam` | Scout finds learning item that is an attack technique | **Granted** 2026-09-20 |
| `aegis-ceo` → `aegis-redteam` | Manager forward / assign attack batch | **Granted** 2026-09-20 |
| `aegis-redteam` → `aegis-ceo` | Confirmed bypass → CEO decision | **Granted** 2026-09-20 |

Same-branch Cyber peers (`aegis-threat-intel` ↔ `aegis-redteam`) may also use Protocol A direct once both are in Cybersecurity.

**Redteam obligations on receipt:** run `/ingest-technique` (or `/attack-gateway` for batches). Never claim tested without a live transcript. Confirmed bypass → `/file-bypass` + `chat_with_agent` → `aegis-ceo`.

**Org chart:** whole-company orientation (not just manager/reports) lives at [`docs/org-chart.md`](./org-chart.md).

---

## Approved exception (verify-before-publish)

Hamid’s decision (2026-09-14): **keep** this edge. Capacity HOLD edges above are a **second** standing exception (Protocol C). Any other specialist→specialist grant that crosses branches must still be refused and routed through the requester’s manager (`aegis-ceo` today).

| Edge | Skill / purpose | Why exempted | Status |
|------|-----------------|--------------|--------|
| `aegis-analyst` → `aegis-infra` | Finance `/check-revenue` Step 5 → Infra `/verify-revenue-claim` (claim + cited sources only; independent free-pool verify-before-publish) | Narrow, single-purpose verification link that predates the hybrid protocol. Not a general Finance↔Infra chat channel — no other asks may use this edge. Routing verify through CEO would put the publisher’s manager on the critical path of an *independent* check, which defeats the point of the verify loop. | **Approved standing exception** — do not copy for other skills or branches |

**Not covered by the verify exception:** reverse edge for general chat, any other Finance→\* edge, or expanding verify into ad-hoc cross-branch work. Those stay manager-routed. (Reverse `aegis-infra` → `aegis-analyst` **is** granted under Protocol C for schedule HOLD/lift only.)

## Standing onboarding edge — `/audit-omniroute` only (Hamid, 2026-09-23)

**Problem:** `aegis-data-quality` stopped mid-onboarding because `chat_with_agent` to `aegis-infra` `/audit-omniroute` returned Unauthorized. The OmniRoute API key was already present. The missing piece was the A2A edge. Asking Hamid again for every hire repeats that stall.

**Decision:** provisioning the shared OmniRoute `.env` (the existing post-create auth flip) **and** granting `<new-hire> → aegis-infra` is a standard onboarding step. It does not need a fresh Hamid approval. The edge is narrow: the new hire may call `/audit-omniroute` only. Every other cross-branch ask stays manager-routed under Protocol A.

| Edge | Purpose | Status |
|------|---------|--------|
| `aegis-data-quality` → `aegis-infra` | Onboarding `/audit-omniroute` | **Granted** 2026-09-23 |
| each future hire → `aegis-infra` | Same, granted during the OmniRoute flip | **Required at hire** — not a new approval |

Trinity `grant_default_permissions` stays a no-op. This is a fleet hire step, not a platform-wide auto-grant.

## Checklist before proposing any new A2A permission

1. Read this table (and re-pull `permissions-edges` if older than a day).
2. Same branch? → peer grant both directions is OK.
3. Cross branch? → refuse direct grant; route via the `manager` column for the requester's branch (today: always `aegis-ceo`). The standing `/audit-omniroute` hire edge above is the exception and is granted during onboarding, not proposed case by case.
4. New department head hired? → update this table's manager cell first, then adjust edges.
