import json
import tempfile
import unittest
from pathlib import Path

from scripts.research_state import ValidationError, init_run, validate_run


class ResearchStateTest(unittest.TestCase):
    def test_mode_defaults_create_valid_runs(self):
        expected = {
            "quick": (1800, 1, 8, 8),
            "deep": (10800, 4, 20, 20),
            "exhaustive": (21600, 8, 40, 40),
        }
        for mode, defaults in expected.items():
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                run_dir = Path(temporary) / "run"
                state = init_run(run_dir, "A useful question", mode, ["Evidence"])
                planning = state["planning"]

                self.assertEqual(
                    (
                        planning["total_budget_seconds"],
                        planning["max_waves"],
                        planning["query_ceiling_per_axis"],
                        planning["original_fetch_ceiling_per_axis"],
                    ),
                    defaults,
                )
                self.assertEqual(planning["current_wave"], 0)
                self.assertEqual(planning["synthesis_reserve_ratio"], 0.2)
                self.assertEqual(planning["budget_reallocations"], [])
                self.assertEqual(
                    state["axes"][0],
                    {
                        "id": "axis-1",
                        "question": "Evidence",
                        "status": "pending",
                        "queries_used": 0,
                        "original_fetches_used": 0,
                        "coverage": "pending",
                        "note_path": "notes/axis-1.md",
                    },
                )
                self.assertEqual(validate_run(run_dir)["status"], "researching")
                self.assertEqual(json.loads((run_dir / "sources.json").read_text()), [])
                self.assertTrue((run_dir / "notes").is_dir())

    def test_planning_validation(self):
        invalid_values = (
            ("total_budget_seconds", True),
            ("max_waves", 0),
            ("current_wave", -1),
            ("current_wave", 5),
            ("query_ceiling_per_axis", -1),
            ("original_fetch_ceiling_per_axis", 1.5),
            ("synthesis_reserve_ratio", 0.19),
            ("budget_reallocations", [{}]),
        )
        for field, value in invalid_values:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                run_dir = Path(temporary) / "run"
                state = init_run(run_dir, "A useful question", "deep", ["Evidence"])
                state["planning"][field] = value
                (run_dir / "state.json").write_text(json.dumps(state))

                with self.assertRaises(ValidationError):
                    validate_run(run_dir)

    def test_axis_bookkeeping_validation(self):
        invalid_values = (
            ("queries_used", True),
            ("queries_used", -1),
            ("original_fetches_used", "1"),
            ("coverage", ""),
            ("note_path", "../outside.md"),
        )
        for field, value in invalid_values:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                run_dir = Path(temporary) / "run"
                state = init_run(run_dir, "A useful question", "deep", ["Evidence"])
                state["axes"][0][field] = value
                (run_dir / "state.json").write_text(json.dumps(state))

                with self.assertRaises(ValidationError):
                    validate_run(run_dir)

    def test_completed_or_partial_requires_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            state = init_run(run_dir, "A useful question", "deep", [])

            for status in ("completed", "partial"):
                state["status"] = status
                (run_dir / "state.json").write_text(json.dumps(state))
                with self.assertRaises(ValidationError):
                    validate_run(run_dir)

            (run_dir / "report.md").write_text("# Result\n")
            self.assertEqual(validate_run(run_dir)["status"], "partial")


if __name__ == "__main__":
    unittest.main()
