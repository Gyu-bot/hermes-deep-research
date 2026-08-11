import json
import tempfile
import unittest
from pathlib import Path

from scripts.document_gate import (
    BINDING,
    CANDIDATE,
    HUMAN_GATE,
    PRE_DOCUMENT,
    READY,
    GateError,
    record_fail,
    record_pass,
    verify_gate,
)


class DocumentGateTest(unittest.TestCase):
    checked_at = "2026-08-11T12:00:00+00:00"

    def make_run(self, temporary: str, verdict: str = "PASS") -> Path:
        run_dir = Path(temporary) / "run"
        run_dir.mkdir()
        (run_dir / PRE_DOCUMENT).write_text("# Accepted research\n", encoding="utf-8")
        (run_dir / CANDIDATE).write_bytes("# 최종 보고서\r\n본문\n".encode())
        (run_dir / HUMAN_GATE).write_text(
            f"# Document readiness\n\nFinal verdict: **{verdict}**\n",
            encoding="utf-8",
        )
        return run_dir

    def test_pass_creates_byte_identical_ready_binding_and_verifies(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(temporary)
            binding = record_pass(
                run_dir,
                when=self.checked_at,
                research_status="completed",
            )

            self.assertEqual(
                (run_dir / READY).read_bytes(),
                (run_dir / CANDIDATE).read_bytes(),
            )
            self.assertEqual(json.loads((run_dir / BINDING).read_text()), binding)
            self.assertEqual(binding["verdict"], "PASS")
            self.assertEqual(binding["checked_at"], self.checked_at)
            self.assertEqual(binding["research_status"], "completed")
            self.assertEqual(verify_gate(run_dir), binding)

    def test_later_fail_leaves_stale_ready_but_verify_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(temporary)
            record_pass(run_dir, when=self.checked_at)
            ready = (run_dir / READY).read_bytes()

            binding = record_fail(
                run_dir,
                "Readability regression",
                when="2026-08-11T12:01:00+00:00",
            )

            self.assertEqual((run_dir / READY).read_bytes(), ready)
            self.assertEqual(binding["verdict"], "FAIL")
            self.assertIsNotNone(binding["candidate_sha256"])
            with self.assertRaises(GateError):
                verify_gate(run_dir)

    def test_candidate_mutation_fails_verify(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(temporary)
            record_pass(run_dir, when=self.checked_at)
            (run_dir / CANDIDATE).write_text("changed", encoding="utf-8")

            with self.assertRaises(GateError):
                verify_gate(run_dir)

    def test_ready_mutation_fails_verify(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(temporary)
            record_pass(run_dir, when=self.checked_at)
            (run_dir / READY).write_text("changed", encoding="utf-8")

            with self.assertRaises(GateError):
                verify_gate(run_dir)

    def test_path_traversal_in_binding_fails_verify(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(temporary)
            record_pass(run_dir, when=self.checked_at)
            binding_path = run_dir / BINDING
            binding = json.loads(binding_path.read_text())
            binding["candidate_path"] = "../outside.md"
            binding_path.write_text(json.dumps(binding), encoding="utf-8")

            with self.assertRaises(GateError):
                verify_gate(run_dir)

    def test_markdown_fail_cannot_be_recorded_as_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(temporary)
            (run_dir / HUMAN_GATE).write_text(
                "Final verdict: PASS\n\nFinal verdict: FAIL\n",
                encoding="utf-8",
            )

            with self.assertRaises(GateError):
                record_pass(run_dir)
            self.assertFalse((run_dir / READY).exists())
            self.assertFalse((run_dir / BINDING).exists())


if __name__ == "__main__":
    unittest.main()
