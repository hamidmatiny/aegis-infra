import importlib.util
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import allocation_inputs as ai

spec = importlib.util.spec_from_file_location("capacity_watch", ROOT / "scripts" / "capacity-watch.py")
cw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cw)

NOW = datetime(2026, 10, 9, 11, 12, tzinfo=timezone.utc)
STAMP = NOW.strftime("%Y-%m-%dT%H:%M:%SZ")
ROSTER = {"agents": [f"agent-{i:02d}" for i in range(14)] + ["aegis-ceo", "aegis-redteam"], "written_at": STAMP}


def events(n429=0, n503=0, n504=0, spread_minutes=600):
    out = []
    total = n429 + n503 + n504
    codes = [429] * n429 + [503] * n503 + [504] * n504
    for i, code in enumerate(codes):
        out.append((NOW - timedelta(minutes=spread_minutes * (i + 1) / max(total, 1)), code))
    return sorted(out)


class SiGateTest(unittest.TestCase):
    def test_upstream_5xx_do_not_defer_si(self):
        # 2026-10-09 11:12Z: 530 errors, almost all 503/504, set si_budget 0 for the whole fleet.
        cap = cw.capacity_state(events(n429=12, n503=300, n504=218), NOW, "lifted")
        self.assertEqual(cap["si"], "open")
        self.assertEqual(cap["today_status_counts"], {"429": 12, "503": 300, "504": 218})
        out = ai.build(ROSTER, cap, NOW)
        self.assertEqual(out["si"], "open")
        self.assertEqual(out["problems"], [])

    def test_429_trip_defers_si(self):
        cap = cw.capacity_state(events(n429=120), NOW, "lifted")
        self.assertEqual(cap["si"], "deferred")
        burst = cw.capacity_state(events(n429=45, spread_minutes=8), NOW, "lifted")
        self.assertEqual(burst["si"], "deferred")

    def test_active_hold_defers_si(self):
        cap = cw.capacity_state(events(), NOW, "active")
        self.assertEqual(cap["si"], "deferred")

    def test_roster_is_the_full_fleet_not_list_agents(self):
        out = ai.build(ROSTER, cw.capacity_state(events(), NOW, None), NOW)
        self.assertEqual(out["roster_count"], 16)
        self.assertNotIn("aegis-ceo", out["free_pool_si_candidates"])
        self.assertEqual(len(out["free_pool_si_candidates"]), 14)

    def test_missing_or_stale_inputs_are_problems_not_guesses(self):
        self.assertTrue(ai.build(None, None, NOW)["problems"])
        old = dict(ROSTER, written_at="2026-10-08T00:00:00Z")
        out = ai.build(old, cw.capacity_state(events(), NOW, None), NOW)
        self.assertTrue(any("stale" in p for p in out["problems"]))
        stale_cap = dict(cw.capacity_state(events(), NOW, None), written_at="2026-10-08T00:00:00Z")
        self.assertEqual(ai.build(ROSTER, stale_cap, NOW)["si"], "unknown")


if __name__ == "__main__":
    unittest.main()
