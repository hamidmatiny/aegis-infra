import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_revenue_claim as vrc

SUMMARY = {"mrr_snapshot": {"mrr_display": "$1,234.50", "mrr_cents": 123450, "currency": "USD"},
           "paying_subscribers": 7}
TRAJECTORY = {"entries": [{"date": "2026-10-09", "signups": 3}]}


def payload(**claim):
    return {"claim": claim, "sources": {"summary": SUMMARY, "trajectory": TRAJECTORY}}


def skill_text():
    # The nightly runner moves skill-staging/ into .claude/skills/ before tests run.
    for base in ("skill-staging", ".claude/skills"):
        path = ROOT / base / "verify-revenue-claim" / "SKILL.md"
        if path.exists():
            return path.read_text()
    raise AssertionError("verify-revenue-claim SKILL.md not found")


class VerifyRevenueClaimTest(unittest.TestCase):
    def test_matching_claim_passes(self):
        out = vrc.check(payload(mrr=1234.5, currency="USD", paying_subscribers=7, signups=3))
        self.assertTrue(out.startswith("PASS: claim matches cited sources"), out)
        self.assertIn("MRR 1234.5 USD", out)

    def test_mrr_mismatch_fails_with_both_values(self):
        out = vrc.check(payload(mrr=1300, currency="USD"))
        self.assertEqual(out, "FAIL: mrr claimed 1300 but source shows 1234.5")

    def test_currency_and_count_mismatches_fail(self):
        self.assertTrue(vrc.check(payload(mrr=1234.5, currency="EUR")).startswith("FAIL: currency"))
        self.assertEqual(vrc.check(payload(paying_subscribers=8)),
                         "FAIL: paying_subscribers claimed 8 but source shows 7")
        self.assertEqual(vrc.check(payload(signups=4)), "FAIL: signups claimed 4 but source shows 3")

    def test_not_returned_contradicted_by_source_fails(self):
        out = vrc.check(payload(mrr=1234.5, not_returned=["signups"]))
        self.assertTrue(out.startswith("FAIL: signups claimed not returned"), out)
        ok = vrc.check({"claim": {"mrr": 1234.5, "not_returned": ["signups"]},
                        "sources": {"summary": SUMMARY}})
        self.assertTrue(ok.startswith("PASS"), ok)

    def test_missing_inputs_fail_without_guessing(self):
        self.assertEqual(vrc.check({"claim": {"mrr": 1}}), "FAIL: missing claim or sources")
        self.assertEqual(vrc.check({}), "FAIL: missing claim or sources")
        out = vrc.check({"claim": {"mrr": 5}, "sources": {"summary": {"paying_subscribers": 1}}})
        self.assertIn("no MRR field", out)

    def test_cli_prints_one_line(self):
        proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_revenue_claim.py")],
                              input=json.dumps(payload(mrr=1234.5)), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(len(proc.stdout.strip().splitlines()), 1)
        self.assertTrue(proc.stdout.startswith("PASS"))

    def test_skill_calls_script_and_requires_slack_closeout(self):
        # 2026-10-09: A2A-triggered runs ended on the "no preamble" reply with no #aegis-infra close-out.
        text = skill_text()
        self.assertIn("scripts/verify_revenue_claim.py", text)
        self.assertIn("Final step — Slack completed-task close-out", text)
        self.assertIn("mcp__trinity__send_group_message", text)


if __name__ == "__main__":
    unittest.main()
