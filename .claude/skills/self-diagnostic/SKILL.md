---
name: self-diagnostic
description: Run self-diagnostics on the agent to verify skills, commands, agents, and dependencies are working. Use when troubleshooting, after configuration changes, or for regular health checks.
allowed-tools: Read, Bash, Grep, Glob, Task
category: workspace
metadata:
  version: "1.0"
  changelog:
    - "1.0: Promoted to trinity-skills library (2026-08-04)"
---

# Agent Self-Diagnostic

Run comprehensive diagnostics to verify all agent components are functioning correctly.

## Quick Start

Run full diagnostics:
```
/self-diagnostic
```

Run specific test category:
```
/self-diagnostic skills-only
/self-diagnostic commands-only
/self-diagnostic agents-only
/self-diagnostic dependencies-only
```

## Arguments

$ARGUMENTS

## Safety Principles

**CRITICAL: These diagnostics are READ-ONLY and NEVER modify data.**

- All tests use read-only operations (list, read, check)
- NO file creation during tests
- NO API calls to paid services
- Test outputs go to `/tmp/agent-diagnostic/` only

---

## Diagnostic Categories

### 1. Infrastructure Tests

Verify core directories exist:

```bash
# Test 1.1: Check .claude directory exists
AGENT_ROOT="${AGENT_ROOT:-.}"
test -d "$AGENT_ROOT/.claude" && echo "PASS: .claude directory exists" || echo "FAIL: .claude directory missing"

# Test 1.2: Check skills directory
test -d "$AGENT_ROOT/.claude/skills" && echo "PASS: skills directory exists" || echo "FAIL: skills directory missing"

# Test 1.3: Check commands directory
test -d "$AGENT_ROOT/.claude/commands" && echo "PASS: commands directory exists" || echo "INFO: commands directory not present"

# Test 1.4: Check agents directory
test -d "$AGENT_ROOT/.claude/agents" && echo "PASS: agents directory exists" || echo "INFO: agents directory not present"
```

### 2. Dependency Tests

Verify external dependencies are installed:

```bash
# Test 2.1: Python available
python3 --version 2>/dev/null && echo "PASS: Python3 available" || echo "FAIL: Python3 not found"

# Test 2.2: Node.js available (optional)
node --version 2>/dev/null && echo "PASS: Node.js available" || echo "INFO: Node.js not found"

# Test 2.3: uv package manager (optional)
uv --version 2>/dev/null && echo "PASS: uv available" || echo "INFO: uv not found (install: curl -LsSf https://astral.sh/uv/install.sh | sh)"

# Test 2.4: Git available
git --version 2>/dev/null && echo "PASS: Git available" || echo "FAIL: Git not found"
```

### 3. Skills Validation Tests

Verify skills are properly configured:

```bash
AGENT_ROOT="${AGENT_ROOT:-.}"

# Test 3.1: List all skills and validate structure
for skill_dir in "$AGENT_ROOT"/.claude/skills/*/; do
  if [ -d "$skill_dir" ]; then
    skill_name=$(basename "$skill_dir")
    if [ -f "${skill_dir}SKILL.md" ]; then
      # Check for required frontmatter
      if head -1 "${skill_dir}SKILL.md" | grep -q "^---"; then
        if grep -q "^name:" "${skill_dir}SKILL.md" && grep -q "^description:" "${skill_dir}SKILL.md"; then
          echo "PASS: Skill '$skill_name' - valid metadata"
        else
          echo "FAIL: Skill '$skill_name' - missing name or description"
        fi
      else
        echo "FAIL: Skill '$skill_name' - missing frontmatter"
      fi
    else
      echo "FAIL: Skill '$skill_name' - missing SKILL.md"
    fi
  fi
done
```

### 4. Commands Validation Tests

Verify commands are properly configured:

```bash
AGENT_ROOT="${AGENT_ROOT:-.}"

# Test 4.1: List all commands and validate structure
if [ -d "$AGENT_ROOT/.claude/commands" ]; then
  for cmd_file in "$AGENT_ROOT"/.claude/commands/*.md; do
    if [ -f "$cmd_file" ]; then
      cmd_name=$(basename "$cmd_file" .md)
      if head -1 "$cmd_file" | grep -q "^---"; then
        if grep -q "^description:" "$cmd_file"; then
          echo "PASS: Command '/$cmd_name' - valid metadata"
        else
          echo "FAIL: Command '/$cmd_name' - missing description"
        fi
      else
        echo "FAIL: Command '/$cmd_name' - missing frontmatter"
      fi
    fi
  done
else
  echo "INFO: No commands directory found"
fi
```

### 5. Agents Validation Tests

Verify sub-agents are properly configured:

```bash
AGENT_ROOT="${AGENT_ROOT:-.}"

# Test 5.1: List all agents and validate structure
if [ -d "$AGENT_ROOT/.claude/agents" ]; then
  for agent_file in "$AGENT_ROOT"/.claude/agents/*.md; do
    if [ -f "$agent_file" ]; then
      agent_name=$(basename "$agent_file" .md)
      if head -1 "$agent_file" | grep -q "^---"; then
        if grep -q "^name:" "$agent_file" || grep -q "^description:" "$agent_file"; then
          echo "PASS: Agent '$agent_name' - valid metadata"
        else
          echo "FAIL: Agent '$agent_name' - missing name or description"
        fi
      else
        echo "FAIL: Agent '$agent_name' - missing frontmatter"
      fi
    fi
  done
else
  echo "INFO: No agents directory found"
fi
```

---

## Output Format

Present results as:

```markdown
# Agent Self-Diagnostic Report
**Run Date:** [current date/time]
**Agent Root:** [path]

## Summary
| Category | Passed | Failed | Info |
|----------|--------|--------|------|
| Infrastructure | X | X | X |
| Dependencies | X | X | X |
| Skills | X | X | X |
| Commands | X | X | X |
| Agents | X | X | X |

## Detailed Results

### Infrastructure Tests
[Results...]

### Dependency Tests
[Results...]

### Skills Validation
[Results...]

### Commands Validation
[Results...]

### Agents Validation
[Results...]

## Recommendations
[Any issues found and suggested fixes]
```

---

## Argument Handling

Based on $ARGUMENTS:

- **No arguments or "full"**: Run all tests
- **"skills-only"**: Only test skills validation
- **"commands-only"**: Only test commands validation
- **"agents-only"**: Only test agents validation
- **"dependencies-only"**: Only test infrastructure + dependencies
- **"quick"**: Only run validation tests (skip functional)

---

## Extending This Diagnostic

To add custom tests for your agent:

1. Create a `custom-tests.sh` in this skill directory
2. The diagnostic will source and run it if present
3. Use the same PASS/FAIL/INFO output format

Example custom test:
```bash
# custom-tests.sh
# Test custom integration
if curl -s --max-time 5 "https://your-api.com/health" | grep -q "ok"; then
  echo "PASS: Custom API reachable"
else
  echo "FAIL: Custom API unreachable"
fi
```
