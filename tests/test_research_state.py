import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import scripts.research_state as research_state
from scripts.research_state import (
    ValidationError,
    cleanup_run,
    create_run,
    init_run,
    main,
    validate_run,
)


class ResearchStateTest(unittest.TestCase):
    def init_test_run(self, temporary, mode="deep", axes=None):
        hermes_home = Path(temporary) / "hermes-home"
        with patch.dict(os.environ, {"HERMES_HOME": str(hermes_home)}):
            run_dir = research_state.research_base() / "run"
            state = init_run(
                run_dir, "A useful question", mode, [] if axes is None else axes
            )
        return run_dir, state

    def test_mode_defaults_create_valid_runs(self):
        expected = {
            "quick": (1800, 1, 8, 8),
            "deep": (10800, 4, 20, 20),
            "exhaustive": (21600, 8, 40, 40),
        }
        for mode, defaults in expected.items():
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                run_dir, state = self.init_test_run(temporary, mode, ["Evidence"])
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

    def test_create_run_is_unique_and_confined_to_hermes_home(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"HERMES_HOME": temporary}
        ):
            first, state = create_run("market-analysis", "Question", "quick", [])
            second, _ = create_run("market-analysis", "Question", "quick", [])
            base = (Path(temporary) / "research/hermes-deep-research").resolve()

            self.assertTrue(first.is_absolute())
            self.assertEqual(first.parent, base)
            self.assertNotEqual(first, second)
            self.assertTrue(first.name.startswith("market-analysis-"))
            self.assertEqual(state["tmp_path"], "tmp")
            for path in (
                "notes",
                "lanes",
                "tmp/workspace",
                "tmp/raw-pages",
                "tmp/raw-data",
                "tmp/downloads",
                "tmp/extracts",
                "tmp/scratch",
                "tmp/lanes",
            ):
                self.assertTrue((first / path).is_dir(), path)
            self.assertEqual(validate_run(first)["query"], "Question")

    def test_create_command_prints_absolute_path(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"HERMES_HOME": temporary}
        ), patch(
            "sys.argv",
            ["research_state.py", "create", "printed-path", "--query", "Question"],
        ):
            output = StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(), 0)
            self.assertTrue(Path(output.getvalue().strip()).is_absolute())

    def test_create_run_uses_default_hermes_home(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"HOME": temporary}, clear=True
        ):
            run_dir, _ = create_run("fallback-home", "Question", "quick", [])
            self.assertEqual(
                run_dir.parent,
                (Path(temporary) / ".hermes/research/hermes-deep-research").resolve(),
            )

    def test_create_run_rejects_relative_hermes_home(self):
        with patch.dict(os.environ, {"HERMES_HOME": "relative-home"}):
            with self.assertRaises(ValidationError):
                create_run("safe-slug", "Question", "quick", [])

    def test_create_run_rejects_unsafe_slugs_without_creating_base(self):
        unsafe = ("", " ", ".", "..", "../escape", "a/b", "a\\b", ".hidden", "bad slug")
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"HERMES_HOME": temporary}
        ):
            base = Path(temporary) / "research/hermes-deep-research"
            for slug in unsafe:
                with self.subTest(slug=slug), self.assertRaises(ValidationError):
                    create_run(slug, "Question", "quick", [])
            self.assertFalse(base.exists())

    def test_init_run_rejects_creation_outside_research_base(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"HERMES_HOME": str(Path(temporary) / "hermes-home")}
        ):
            outside = Path(temporary) / "outside-run"
            with self.assertRaises(ValidationError):
                init_run(outside, "A useful question", "deep", [])
            self.assertFalse(outside.exists())

    def test_validation_rejects_durable_paths_inside_tmp(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, state = self.init_test_run(temporary, axes=["Evidence"])

            disposable_report = run_dir / "tmp/workspace/report.md"
            disposable_report.write_text("not durable")
            state["report_path"] = "tmp/workspace/report.md"
            (run_dir / "state.json").write_text(json.dumps(state))
            with self.assertRaises(ValidationError):
                validate_run(run_dir)

            state["report_path"] = "report.md"
            state["axes"][0]["note_path"] = "tmp/scratch/note.md"
            (run_dir / "state.json").write_text(json.dumps(state))
            with self.assertRaises(ValidationError):
                validate_run(run_dir)

    def test_validation_accepts_legacy_run_without_new_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, state = self.init_test_run(temporary)
            state.pop("tmp_path")
            (run_dir / "state.json").write_text(json.dumps(state))
            shutil.rmtree(run_dir / "tmp")
            (run_dir / "lanes").rmdir()
            legacy_run = Path(temporary) / "legacy-run"
            run_dir.rename(legacy_run)

            self.assertEqual(validate_run(legacy_run)["query"], "A useful question")

    def test_cleanup_is_dry_run_by_default_and_preserves_durable_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, state = self.init_test_run(temporary)
            state["status"] = "failed"
            (run_dir / "state.json").write_text(json.dumps(state))

            durable = {
                "report.pre-polish.md": "durable report variant",
                "notes/integrated.md": "durable parent note",
                "lanes/wave-1/lane-1/result.md": "durable lane result",
            }
            for path, content in durable.items():
                target = run_dir / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            for directory in (
                "workspace",
                "raw-pages",
                "raw-data",
                "downloads",
                "extracts",
                "scratch",
                "lanes/wave-1/lane-1",
            ):
                target = run_dir / "tmp" / directory / "work"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("x")

            before = {
                path: (run_dir / path).read_bytes()
                for path in ("state.json", "sources.json", "report.md", *durable)
            }
            output = StringIO()
            with patch("sys.argv", ["research_state.py", "cleanup", str(run_dir)]), redirect_stdout(
                output
            ):
                self.assertEqual(main(), 0)
            self.assertIn("cleanup dry-run: 7 files, 7 bytes", output.getvalue())
            self.assertTrue((run_dir / "tmp/scratch/work").exists())

            self.assertEqual(cleanup_run(run_dir, apply=True)[:2], (7, 7))
            for path, content in before.items():
                self.assertEqual((run_dir / path).read_bytes(), content)
            for directory in (
                "workspace",
                "raw-pages",
                "raw-data",
                "downloads",
                "extracts",
                "scratch",
                "lanes",
            ):
                self.assertEqual(list((run_dir / "tmp" / directory).iterdir()), [])
            self.assertEqual(cleanup_run(run_dir, apply=True)[:2], (0, 0))

    def test_cleanup_refuses_active_or_unsafe_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, state = self.init_test_run(temporary)
            for status in ("researching", "synthesizing"):
                state["status"] = status
                (run_dir / "state.json").write_text(json.dumps(state))
                with self.assertRaises(ValidationError):
                    cleanup_run(run_dir, apply=True)

            state["status"] = "failed"
            state["tmp_path"] = "notes"
            (run_dir / "state.json").write_text(json.dumps(state))
            marker = run_dir / "notes/keep.md"
            marker.write_text("keep")
            with self.assertRaises(ValidationError):
                cleanup_run(run_dir, apply=True)
            self.assertEqual(marker.read_text(), "keep")

            state["tmp_path"] = "tmp"
            (run_dir / "state.json").write_text(json.dumps(state))
            shutil.rmtree(run_dir / "tmp")
            (run_dir / "tmp").symlink_to(run_dir / "notes", target_is_directory=True)
            with self.assertRaises(ValidationError):
                cleanup_run(run_dir, apply=True)
            self.assertEqual(marker.read_text(), "keep")

    def test_cleanup_refuses_tmp_symlink_swap_after_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, state = self.init_test_run(temporary)
            state["status"] = "failed"
            (run_dir / "state.json").write_text(json.dumps(state))
            (run_dir / "tmp/workspace/disposable").write_text("x")
            outside = root / "outside"
            outside.mkdir()
            marker = outside / "keep"
            marker.write_text("keep")
            detached_tmp = root / "detached-tmp"
            real_snapshot = research_state.snapshot_temporary_tree

            def swap_tmp(directory_fd):
                snapshot = real_snapshot(directory_fd)
                (run_dir / "tmp").rename(detached_tmp)
                (run_dir / "tmp").symlink_to(outside, target_is_directory=True)
                return snapshot

            with patch(
                "scripts.research_state.snapshot_temporary_tree", side_effect=swap_tmp
            ), self.assertRaises(ValidationError):
                cleanup_run(run_dir, apply=True)

            self.assertEqual(marker.read_text(), "keep")
            self.assertTrue((detached_tmp / "workspace/disposable").exists())

    def test_cleanup_refuses_real_child_directory_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, state = self.init_test_run(temporary)
            state["status"] = "failed"
            (run_dir / "state.json").write_text(json.dumps(state))
            (run_dir / "tmp/workspace/disposable").write_text("x")
            detached_workspace = root / "detached-workspace"
            outside = root / "outside"
            outside.mkdir()
            marker = outside / "KEEP"
            marker.write_text("keep")
            real_snapshot = research_state.snapshot_temporary_tree

            def swap_child(directory_fd):
                snapshot = real_snapshot(directory_fd)
                (run_dir / "tmp/workspace").rename(detached_workspace)
                outside.rename(run_dir / "tmp/workspace")
                return snapshot

            with patch(
                "scripts.research_state.snapshot_temporary_tree", side_effect=swap_child
            ), self.assertRaises(ValidationError):
                cleanup_run(run_dir, apply=True)

            self.assertEqual((run_dir / "tmp/workspace/KEEP").read_text(), "keep")
            self.assertTrue((detached_workspace / "disposable").exists())

    def test_cleanup_refuses_real_tmp_replacement_before_descriptor_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, state = self.init_test_run(temporary)
            state["status"] = "failed"
            (run_dir / "state.json").write_text(json.dumps(state))
            detached_tmp = root / "detached-tmp"
            outside_tmp = root / "outside-tmp"
            outside_tmp.mkdir()
            marker = outside_tmp / "KEEP"
            marker.write_text("keep")
            real_open = research_state._open_snapshotted_directory
            swapped = False

            def swap_before_open(path, expected, label, dir_fd=None):
                nonlocal swapped
                if label == "tmp" and not swapped:
                    swapped = True
                    (run_dir / "tmp").rename(detached_tmp)
                    outside_tmp.rename(run_dir / "tmp")
                return real_open(path, expected, label, dir_fd)

            with patch(
                "scripts.research_state._open_snapshotted_directory",
                side_effect=swap_before_open,
            ), self.assertRaises(ValidationError):
                cleanup_run(run_dir, apply=True)

            self.assertEqual((run_dir / "tmp/KEEP").read_text(), "keep")

    def test_cleanup_refuses_real_run_replacement_before_descriptor_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir, state = self.init_test_run(temporary)
            state["status"] = "failed"
            (run_dir / "state.json").write_text(json.dumps(state))
            detached_run = root / "detached-run"
            outside_run = root / "outside-run"
            outside_run.mkdir()
            marker = outside_run / "KEEP"
            marker.write_text("keep")
            real_open = research_state._open_snapshotted_directory
            swapped = False

            def swap_before_open(path, expected, label, dir_fd=None):
                nonlocal swapped
                if label == "run_dir" and not swapped:
                    swapped = True
                    run_dir.rename(detached_run)
                    outside_run.rename(run_dir)
                return real_open(path, expected, label, dir_fd)

            with patch(
                "scripts.research_state._open_snapshotted_directory",
                side_effect=swap_before_open,
            ), self.assertRaises(ValidationError):
                cleanup_run(run_dir, apply=True)

            self.assertEqual((run_dir / "KEEP").read_text(), "keep")

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
                run_dir, state = self.init_test_run(temporary, axes=["Evidence"])
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
                run_dir, state = self.init_test_run(temporary, axes=["Evidence"])
                state["axes"][0][field] = value
                (run_dir / "state.json").write_text(json.dumps(state))

                with self.assertRaises(ValidationError):
                    validate_run(run_dir)

    def test_completed_or_partial_requires_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir, state = self.init_test_run(temporary)

            for status in ("completed", "partial"):
                state["status"] = status
                (run_dir / "state.json").write_text(json.dumps(state))
                with self.assertRaises(ValidationError):
                    validate_run(run_dir)

            (run_dir / "report.md").write_text("# Result\n")
            self.assertEqual(validate_run(run_dir)["status"], "partial")


if __name__ == "__main__":
    unittest.main()
