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
        # 2026-10-09 the Mac woke at 11:01Z; the review must still happen then.
        self.assertEqual(nr.pick_step(at(8, 45)), "morning")
        self.assertEqual(nr.pick_step(at(11, 1)), "morning")
        self.assertEqual(nr.pick_step(at(7, 20)), "morning")
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


class NightlyHardeningTest(unittest.TestCase):
    def setUp(self):
        import subprocess
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "agent"
        self.repo.mkdir()
        run = lambda *a: subprocess.run(a, cwd=self.repo, check=True, capture_output=True)
        self.git = run
        run("git", "init", "-q")
        (self.repo / ".claude/skills/check").mkdir(parents=True)
        (self.repo / ".claude/skills/check/SKILL.md").write_text("old\n")
        run("git", "add", "-A")
        run("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")

    def tearDown(self):
        self.tmp.cleanup()

    def test_staged_skill_is_moved_into_claude_skills(self):
        (self.repo / "skill-staging/check").mkdir(parents=True)
        (self.repo / "skill-staging/check/SKILL.md").write_text("new\n")
        self.git("git", "add", "-A")
        self.git("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "session")
        moved = nr.promote_staged_skills(self.repo)
        self.assertEqual(moved, [".claude/skills/check/SKILL.md"])
        self.assertEqual((self.repo / ".claude/skills/check/SKILL.md").read_text(), "new\n")
        self.assertFalse((self.repo / "skill-staging").exists())
        files, _ = nr.changed_files(self.repo, "HEAD~1")
        self.assertEqual(files, [".claude/skills/check/SKILL.md"])
        self.assertEqual(nr.outside_scope(files), [])

    def test_no_staging_is_a_no_op(self):
        self.assertEqual(nr.promote_staged_skills(self.repo), [])

    def test_discovery_error_is_not_before_evidence(self):
        # aegis-analyst PR #1's "fails on base" was this harness error, not a failing test.
        self.assertTrue(nr.HARNESS_ERROR.search("ImportError: Start directory is not importable: '/x/tests'"))
        self.assertFalse(nr.HARNESS_ERROR.search("FAILED (failures=1)"))

    def test_parallel_drops_to_one_after_a_limit(self):
        with mock.patch.object(nr, "load_json", return_value={}):
            self.assertEqual(nr.parallel_now(at(2, 0)), 2)
        with mock.patch.object(nr, "load_json", return_value={"seen": "2026-10-09T00:30:00Z"}):
            self.assertEqual(nr.parallel_now(at(2, 0)), 1)
        with mock.patch.object(nr, "load_json", return_value={"seen": "2026-10-07T00:30:00Z"}):
            self.assertEqual(nr.parallel_now(at(2, 0)), 2)

    def test_review_picks_up_an_earlier_night(self):
        state = {"days": {}, "entries": [
            {"agent": "aegis-analyst", "night": "2026-10-08", "status": "proposed", "pr": "u1"},
            {"agent": "aegis-growth", "night": "2026-10-09", "status": "proposed", "pr": "u2", "review_sent": {"at": "x"}},
        ]}
        sent = {}
        def fake_api(method, path, body=None):
            sent["message"] = body["message"]
            return 200, {"execution_id": "e1"}
        with mock.patch.object(nr, "ledger", return_value=state), \
             mock.patch.object(nr, "priority_busy", return_value=(False, "")), \
             mock.patch.object(nr, "trinity_db", return_value=[]), \
             mock.patch.object(nr, "trinity_api", side_effect=fake_api), \
             mock.patch.object(nr, "save_json"):
            out = nr.step_review(at(11, 1), dry=False)
        self.assertIn("sent aegis-ceo 1 PRs", out)
        self.assertIn("u1", sent["message"])
        self.assertNotIn("u2", sent["message"])
        self.assertEqual(state["entries"][0]["review_sent"]["execution"], "e1")


if __name__ == "__main__":
    unittest.main()
