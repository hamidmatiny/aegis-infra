import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nightly_improvement as ni


FAILURES = [
    "aegis-analyst",
    "aegis-growth",
    "aegis-data-quality",
    "aegis-scout",
    "aegis-product-eng",
    "aegis-gateway",
    "aegis-policy-engine",
    "aegis-model-router",
    "aegis-agent-gate",
]


class NightlyImprovementTest(unittest.TestCase):
    def test_fleet_is_sixteen(self):
        self.assertEqual(len(ni.FLEET), 16)
        self.assertEqual(len(set(ni.FLEET)), 16)

    def test_failures_go_first_and_batch_is_six(self):
        batch = ni.select_batch(FAILURES)
        self.assertEqual(batch[:2], ["aegis-analyst", "aegis-growth"])
        self.assertEqual(len(batch), 6)
        self.assertEqual(batch, FAILURES[:6])

    def test_three_nights_cover_the_roster(self):
        done = []
        for _ in range(3):
            done.extend(ni.select_batch(FAILURES, done))
        self.assertEqual(set(done), set(ni.FLEET))

    def test_working_hours_and_priority_block_the_subscription(self):
        evening = ni.decide(20, 2, failures=FAILURES, subscription_limited=False, priority_running=True)
        self.assertFalse(evening["run"])
        limited = ni.decide(2, 30, failures=FAILURES, subscription_limited=True, priority_running=False)
        self.assertTrue(limited["reason"].startswith("session limit"))
        idle = ni.decide(2, 30, failures=FAILURES, subscription_limited=False, priority_running=False)
        self.assertTrue(idle["run"])
        self.assertEqual(idle["capacity"], "claude-subscription")
        self.assertEqual(idle["batch"][0], "aegis-analyst")

    def test_directed_session_does_not_claim_the_claude_window(self):
        now = ni.decide(20, 2, failures=FAILURES, subscription_limited=False, priority_running=True, directed=True)
        self.assertTrue(now["run"])
        self.assertEqual(now["capacity"], "cursor-directed")


if __name__ == "__main__":
    unittest.main()
