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

*Pulled from Trinity `GET /api/agents` + `GET /api/agents/permissions-edges` on 2026-09-14. Re-check with those APIs before proposing permission changes — this file can go stale.*

| Branch | Manager (today) | Agents in branch | Same-branch direct | Notes |
|--------|-----------------|------------------|--------------------|-------|
| Executive | `aegis-ceo` (founder-facing; peers with VP) | `aegis-ceo`, `the-brain` (VP) | **Wired** `aegis-ceo ↔ the-brain` | Only branch with 2+ members as of 2026-09-14 |
| Infrastructure & Compute | `aegis-ceo` | `aegis-infra` | N/A (1 member) | |
| Cybersecurity | `aegis-ceo` | `aegis-threat-intel` | N/A (1 member) | |
| Finance | `aegis-ceo` | `aegis-analyst` | N/A (1 member) | |
| Engineering | `aegis-ceo` | `aegis-core-infra` | N/A (1 member) | |
| Data / Quality | `aegis-ceo` | `aegis-data-quality` | N/A (1 member) | Live 2026-09-14 (`github:hamidmatiny/aegis-data-quality@main`); free-pool OmniRoute |

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
| `the-brain` → `aegis-ceo` | VP ↔ CEO (also same-branch peer) | **Granted** |
| `aegis-ceo` → `the-brain` | CEO ↔ VP | **Granted** |

## Forbidden by default

Any direct edge where `branch(source) != branch(target)` and neither side is acting as the **manager of record** for the other's branch.

Examples that must **not** be added:

- `aegis-analyst` → `aegis-threat-intel` (Finance → Cyber)
- `aegis-analyst` → `aegis-core-infra` (Finance → Engineering)
- `aegis-infra` → `aegis-core-infra` (Infra → Engineering)
- `aegis-threat-intel` → `aegis-analyst` (Cyber → Finance)

## Approved exception (the only one)

Hamid’s decision (2026-09-14): **keep** this edge. It is the **only** approved direct cross-branch A2A permission. Any other specialist→specialist grant that crosses branches must still be refused and routed through the requester’s manager (`aegis-ceo` today).

| Edge | Skill / purpose | Why exempted | Status |
|------|-----------------|--------------|--------|
| `aegis-analyst` → `aegis-infra` | Finance `/check-revenue` Step 5 → Infra `/verify-revenue-claim` (claim + cited sources only; independent free-pool verify-before-publish) | Narrow, single-purpose verification link that predates the hybrid protocol. Not a general Finance↔Infra chat channel — no other asks may use this edge. Routing verify through CEO would put the publisher’s manager on the critical path of an *independent* check, which defeats the point of the verify loop. | **Approved standing exception** — do not copy for other skills or branches |

**Not covered by this exception:** reverse edge (`aegis-infra` → `aegis-analyst`), any other Finance→\* edge, or expanding this permission into ad-hoc cross-branch work. Those stay manager-routed.

## Checklist before proposing any new A2A permission

1. Read this table (and re-pull `permissions-edges` if older than a day).
2. Same branch? → peer grant both directions is OK.
3. Cross branch? → refuse direct grant; route via the `manager` column for the requester's branch (today: always `aegis-ceo`).
4. New department head hired? → update this table's manager cell first, then adjust edges.
