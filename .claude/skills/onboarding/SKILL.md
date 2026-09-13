---
name: onboarding
description: Track your setup progress — shows what's done, what's next, and walks you through each step
allowed-tools: Read, Write, Edit, Bash, AskUserQuestion
user-invocable: true
metadata:
  version: "1.0"
  created: 2026-09-13
  author: aegis-infra
---

# Onboarding

Track and continue your setup progress. This skill reads `onboarding.json`, shows your current status, and walks you through the next incomplete step.

## Process

### Step 1: Load State

Read `onboarding.json` from the agent root directory. If it doesn't exist, inform the user that onboarding is complete or the file was removed.

### Step 2: Show Progress

Display a checklist grouped by phase. Mark the current phase with an arrow. Use checkboxes:

```
## AEGIS Infra — Setup Progress

### Phase 1: Local Setup  ← current
- [ ] Configure environment variables (.env)
- [ ] Run /audit-omniroute to establish real ground truth
- [ ] Run /propose-agent-tier for the next hire and get it approved
- [ ] Install recommended plugins

### Phase 2: Trinity Deployment
- [ ] Deploy to Trinity (as a free-pool agent)
- [ ] Run a skill remotely

### Phase 3: Schedules
- [ ] Confirm recommended schedules
- [ ] Verify first scheduled execution

**Progress: 0/8 complete**
```

### Step 3: Guide Next Step

Identify the first incomplete step in the current phase. Based on which step it is, provide specific guidance:

**For `env_configured`:**
- Check if `.env` exists. If not, guide: `cp .env.example .env` then fill in values.
- `OMNIROUTE_API_URL` is required if OmniRoute is meant to be audited/tracked from day one; `OMNIROUTE_API_KEY` only if that instance requires auth.
- After user confirms, mark done.

**For `first_skill_run`:**
- Tell the user to run `/audit-omniroute` — this establishes the ground truth everything else in this agent's job builds on.
- After it runs successfully (even if it reports gaps — that's a valid, useful result), mark done.

**For `first_proposal`:**
- Tell the user to run `/propose-agent-tier` for whichever agent is next in line to be hired.
- This step is done once a proposal has been made **and** a decision (approve or decline) has been recorded — not merely proposed.

**For `plugins_installed`:**
- Run the install commands for each plugin selected during setup:
  ```
  /plugin install agent-dev@abilityai
  /plugin install trinity@abilityai
  /plugin install utilities@abilityai
  ```
- Run each install command via Bash. Note successes and failures.
- After all attempted, mark done.

**For `onboarded` (Trinity phase):**
- Guide the user to run `/trinity:onboard`.
- Remind them this agent's own tier policy is free-pool — flag it if the deployment ends up on premium/subscription auth instead, since that would be the agent violating its own rule.
- After completion, mark done and advance phase.

**For `first_remote_run`:**
- Tell user to run `mcp__trinity__chat_with_agent` with the agent name and a skill, e.g. `/audit-omniroute`.
- After completion, mark done and advance phase.

**For `schedules_configured`:**
- Tell user the recommended schedules live in `template.yaml` (`schedules:`); deploying with `/trinity:onboard` reconciles them onto the instance. All ship `enabled: false` by design — confirm which ones should actually be turned on.
- To turn one on/off on the live agent, use `mcp__trinity__toggle_agent_schedule`.
- After completion, mark done.

**For `first_scheduled_run`:**
- Tell user to check `mcp__trinity__get_schedule_executions` for execution confirmation.
- After verified, mark done.

### Step 4: Update State

After each step is completed, update `onboarding.json`:
- Set the step's `done` to `true`
- If all steps in current phase are done, advance `phase` to the next phase
- If all phases complete, congratulate the user

### Step 5: Phase Transitions

When all steps in a phase are complete:

**Local → Trinity:**
```
## Local Setup Complete!

AEGIS Infra is fully configured and working locally — OmniRoute's real state is
known, and the first tier proposal has been made and decided.

Run /onboarding again when you're ready to deploy to Trinity.
```

**Trinity → Schedules:**
```
## Trinity Deployment Complete!

AEGIS Infra is live on Trinity. Now let's confirm which of the recommended
schedules should actually run.

Run /onboarding to configure them.
```

**All Complete:**
```
## Onboarding Complete!

AEGIS Infra is fully set up:
- ✓ Local environment configured
- ✓ OmniRoute audited, first tier proposal decided
- ✓ Deployed to Trinity (free-pool, per its own policy)
- ✓ Schedules running

You're all set. The onboarding.json file can be kept as a record or deleted.
```

## Outputs

- Updated `onboarding.json` with progress
- Step-by-step guidance for the current task
- Phase transition messages at milestones
