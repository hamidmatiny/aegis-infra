#!/usr/bin/env python3
"""One nightly improvement batch, sized to the measured paid window.

The free-pool floor stays one slot. This script is the paid batch:
several Track B agents per night, failures first, so all 16 get a real
change every 2-3 days. It refuses to run on the Claude subscription
during Hamid's working hours, after a session-limit signal, or while
aegis-ceo or aegis-redteam is using that subscription.
"""

from __future__ import annotations

FLEET = (
    "aegis-analyst",
    "aegis-growth",
    "aegis-data-quality",
    "aegis-scout",
    "aegis-product-eng",
    "aegis-gateway",
    "aegis-policy-engine",
    "aegis-model-router",
    "aegis-agent-gate",
    "aegis-audit",
    "aegis-core-infra",
    "aegis-threat-intel",
    "aegis-infra",
    "aegis-ceo",
    "aegis-redteam",
    "the-brain",
)

# 16 agents, one improvement each every 2 nights. Measured 2026-10-09: one focused session is
# 10-15 min of real work (46 turns, ~20k output tokens on Opus). Two run at once (PARALLEL in
# nightly_runner), so 8 fit in the 210 idle-window minutes with room for the 25-min cap.
# After a usage-limit signal the runner drops to one at a time and the batch carries over.
BATCH_SIZE = 8

# UTC. 02:00-03:30 is between the 01:00 ADT redteam batch and Hamid's morning.
# 05:15-07:15 is after the 04:00 UTC redteam batch and before the 07:30 CEO pulse.
IDLE_WINDOWS_UTC = (((2, 0), (3, 30)), ((5, 15), (7, 15)))


def _minutes(hour: int, minute: int) -> int:
    return hour * 60 + minute


def in_idle_window(hour: int, minute: int) -> bool:
    now = _minutes(hour, minute)
    for (sh, sm), (eh, em) in IDLE_WINDOWS_UTC:
        if _minutes(sh, sm) <= now < _minutes(eh, em):
            return True
    return False


def in_working_hours(hour: int, minute: int) -> bool:
    """09:00-02:00 ADT, which is 12:00-02:00 UTC. His evening counts."""
    return hour >= 12 or hour < 2


def select_batch(failures: list[str], already_done: list[str] | None = None, size: int = BATCH_SIZE) -> list[str]:
    done = set(already_done or [])
    ordered = [name for name in failures if name not in done]
    for name in FLEET:
        if name not in done and name not in ordered:
            ordered.append(name)
    return ordered[:size]


def decide(
    hour: int,
    minute: int,
    *,
    failures: list[str],
    subscription_limited: bool,
    priority_running: bool,
) -> dict:
    """Claude subscription only. Cursor is at its monthly limit; add it back after Hamid confirms the reset."""
    batch = select_batch(failures)
    if in_working_hours(hour, minute) or not in_idle_window(hour, minute):
        return {"run": False, "capacity": "claude-subscription", "batch": [], "reason": "outside the idle window"}
    if subscription_limited:
        return {"run": False, "capacity": "claude-subscription", "batch": [], "reason": "session limit — resume next window"}
    if priority_running:
        return {"run": False, "capacity": "claude-subscription", "batch": [], "reason": "aegis-ceo or aegis-redteam is using the subscription"}
    return {"run": True, "capacity": "claude-subscription", "batch": batch, "reason": "idle window"}
