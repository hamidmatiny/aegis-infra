---
name: reconcile-docs
description: Check that CLAUDE.md, README, ARCHITECTURE/TARGET-ARCHITECTURE, skills, and subagents are mutually consistent — reports drift and applies approved fixes. Run after shipping a capability or on a schedule.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-09-13
  author: aegis-infra
  changelog:
    - "1.0: Initial version — dependency-graph-driven coherence check across docs, skills, and subagents"
---

# Reconcile Docs

> ℹ️ **First, set expectations:** before anything else, print one short line with this skill's version and its most recent change — the top entry of `metadata.changelog` above — e.g. `reconcile-docs vX.Y — recent: <summary>`. Then proceed.

Keep this agent's documentation honest. This skill reads the **Artifact Dependency Graph** in `CLAUDE.md` and checks that every artifact agrees with its sources — then reports drift and, interactively, applies approved fixes.

**Direction rule (from the graph):** the *source* wins.
- **Descriptive targets** (`README.md`, `ARCHITECTURE.md`) must match reality — when they disagree with their sources (CLAUDE.md, the skills, the subagents, the code), **fix the target.**
- **Prescriptive sources** (`CLAUDE.md`, `TARGET-ARCHITECTURE.md`) define intent — when they're out of date, **flag for a human.** Never silently rewrite intent to match a possibly-buggy implementation.

## Process

### Step 1: Load the graph

Read `CLAUDE.md` and parse the `## Artifact Dependency Graph` (the `artifacts:` and `sync_skills:` blocks). This is the spec for what depends on what.

### Step 2: Gather reality

```bash
find .claude/skills -name SKILL.md 2>/dev/null
ls .claude/agents/*.md 2>/dev/null
ls README.md ARCHITECTURE.md TARGET-ARCHITECTURE.md template.yaml 2>/dev/null
ls memory/*.md 2>/dev/null
```

Read `README.md`, `ARCHITECTURE.md`, `TARGET-ARCHITECTURE.md`, and the `schedules:` block in `template.yaml`. Note each skill's name/description from its frontmatter and each subagent's purpose.

### Step 3: Check coherence

Evaluate each, recording CONSISTENT / DRIFT / MISSING:

1. **CLAUDE.md ↔ skills** — every skill in `.claude/skills/` is listed in Core Capabilities and Request Dispatch; every listed skill exists; descriptions agree.
2. **README ↔ reality** — README capabilities/skills table matches the actual skills and subagents.
3. **ARCHITECTURE ↔ reality** — components described (skills, subagents, data, schedules) all exist on disk; nothing real is undocumented. In particular, check whether `memory/tier-assignments.md`, `memory/usage-log.md`, and `memory/pricing-checks.md` exist yet and whether ARCHITECTURE.md correctly describes them as created-on-first-run vs. already present.
4. **TARGET-ARCHITECTURE ↔ ARCHITECTURE** — no item described as shipped/live in ARCHITECTURE is still sitting in TARGET as "planned." Anything now implemented → propose moving it from target into current.
5. **Subagents ↔ docs** — every `.claude/agents/*` is referenced in CLAUDE.md/ARCHITECTURE; nothing referenced is missing.
6. **Schedules ↔ template.yaml** — the Recommended Schedules table in CLAUDE.md matches the `schedules:` block.
7. **Guidelines ↔ behavior** — guidelines don't contradict what the skills actually do — in particular, confirm no skill silently applies a tier/config change without an approval step, since that's this agent's core operating rule.

### Step 4: Report

Produce a drift report — **this mode is read-only and safe to run on a schedule.**

```
## Doc Reconciliation: AEGIS Infra

| # | Check | Status | Drift | Fix side |
|---|-------|--------|-------|----------|
| 1 | CLAUDE.md ↔ skills | DRIFT | /foo exists but isn't in Core Capabilities | target (CLAUDE.md*) |
| 2 | ARCHITECTURE ↔ reality | DRIFT | subagent `bar` not documented | target (ARCHITECTURE.md) |

\* CLAUDE.md is prescriptive — flag, don't auto-edit.
```

If everything is CONSISTENT, say so and stop.

### Step 5: Apply (interactive only)

**Skip this step when running on a schedule** — scheduled runs report only (no approval gate). When run interactively and drift exists, propose exact edits and confirm:

Use AskUserQuestion:
- **Question:** "Which fixes should I apply?"
- **Header:** "Apply Fixes"
- **Options:** Apply all (descriptive targets only) / Let me pick / Just the report

Apply approved edits to **descriptive targets** (`README.md`, `ARCHITECTURE.md`) — and, when a target item has shipped, move it from `TARGET-ARCHITECTURE.md` into `ARCHITECTURE.md`. For drift that implicates a **prescriptive source** (CLAUDE.md, TARGET-ARCHITECTURE.md), present it as a recommendation for the user to decide — do not auto-edit.

## Outputs

- A coherence report (always)
- Updated `README.md` / `ARCHITECTURE.md` when fixes are approved
- Flagged recommendations for any CLAUDE.md / TARGET-ARCHITECTURE.md drift
