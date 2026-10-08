import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import nightly_runner as nr


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, 9, hour, minute, tzinfo=timezone.utc)


class NightlyRunnerTest(unittest.TestCase):
    def test_steps_follow_the_clock(self):
        self.assertEqual(nr.pick_step(at(2, 30)), "run")
        self.assertEqual(nr.pick_step(at(6, 0)), "run")
        self.assertEqual(nr.pick_step(at(8, 45)), "review")
        self.assertEqual(nr.pick_step(at(9, 40)), "deploy")
        self.assertEqual(nr.pick_step(at(10, 15)), "summary")
        self.assertEqual(nr.pick_step(at(14, 0)), "verify")
        self.assertEqual(nr.pick_step(at(4, 0)), "verify")

    def test_cron_lookahead(self):
        from datetime import timedelta

        lead = timedelta(minutes=30)
        self.assertEqual(nr.next_fire("30 */6 * * *", at(6, 10), lead), at(6, 30))
        self.assertIsNone(nr.next_fire("30 */6 * * *", at(2, 10), lead))
        self.assertEqual(nr.next_fire("0 */4 * * *", at(3, 45), lead), at(4, 0))
        self.assertEqual(nr.next_fire("30 7 * * *", at(7, 5), lead), at(7, 30))
        # 2026-10-12 is a Monday; cron weekday 1.
        monday = datetime(2026, 10, 12, 8, 50, tzinfo=timezone.utc)
        self.assertEqual(nr.next_fire("0 9 * * 1", monday, lead), monday.replace(hour=9, minute=0))
        self.assertIsNone(nr.next_fire("0 9 * * 1", at(8, 50), lead))

    def test_only_skills_scripts_tests(self):
        files = [".claude/skills/x/SKILL.md", "scripts/a.py", "tests/test_a.py", "CLAUDE.md", ".env"]
        self.assertEqual(nr.outside_scope(files), ["CLAUDE.md", ".env"])

    def test_child_env_never_carries_api_billing(self):
        env = {"ANTHROPIC_API_KEY": "x", "ANTHROPIC_BASE_URL": "y", "ANTHROPIC_AUTH_TOKEN": "z", "HOME": "/h"}
        with mock.patch.dict(os.environ, env, clear=True):
            child = nr.child_env()
        for key in nr.STRIPPED_ENV:
            self.assertNotIn(key, child)
        self.assertEqual(child["HOME"], "/h")

    def test_limit_signals(self):
        for text in ("Claude AI usage limit reached|1760000000", "You've hit your limit · resets 5am",
                     "session limit, reset 17:00 UTC", '{"type":"rate_limit_error"}'):
            self.assertTrue(nr.LIMIT_PATTERN.search(text), text)
        self.assertFalse(nr.LIMIT_PATTERN.search("Task execution timed out after 3600 seconds"))

    def test_no_cursor_in_command(self):
        source = Path(nr.__file__).read_text()
        self.assertNotIn("cursor-agent", source)
        self.assertNotIn("CURSOR_API_KEY", source)


if __name__ == "__main__":
    unittest.main()
