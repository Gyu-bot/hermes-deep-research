#!/usr/bin/env python3
"""Create, inspect, and validate a simple Hermes deep-research run."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUSES = {
    "researching",
    "synthesizing",
    "completed",
    "partial",
    "failed",
    "cancelled",
}
MODES = {"quick", "deep", "exhaustive"}
MODE_DEFAULTS = {
    "quick": {
        "total_budget_seconds": 1800,
        "max_waves": 1,
        "query_ceiling_per_axis": 8,
        "original_fetch_ceiling_per_axis": 8,
    },
    "deep": {
        "total_budget_seconds": 10800,
        "max_waves": 4,
        "query_ceiling_per_axis": 20,
        "original_fetch_ceiling_per_axis": 20,
    },
    "exhaustive": {
        "total_budget_seconds": 21600,
        "max_waves": 8,
        "query_ceiling_per_axis": 40,
        "original_fetch_ceiling_per_axis": 40,
    },
}
REQUIRED = {
    "status": str,
    "query": str,
    "mode": str,
    "planning": dict,
    "axes": list,
    "waves": list,
    "next_actions": list,
    "limitations": list,
    "report_path": str,
    "timestamps": dict,
}


class ValidationError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def atomic_json(path: Path, value: Any) -> None:
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def init_run(run_dir: Path, query: str, mode: str, axes: list[str]) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    if mode not in MODES:
        raise ValidationError(f"mode must be one of: {', '.join(sorted(MODES))}")
    if not query.strip():
        raise ValidationError("query must not be empty")
    if (run_dir / "state.json").exists():
        raise ValidationError(f"run already exists: {run_dir}")

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "notes").mkdir(exist_ok=True)
    timestamp = now()
    axes = [axis.strip() for axis in axes if axis.strip()]
    state = {
        "status": "researching",
        "query": query.strip(),
        "mode": mode,
        "planning": {
            **MODE_DEFAULTS[mode],
            "current_wave": 0,
            "synthesis_reserve_ratio": 0.2,
            "budget_reallocations": [],
        },
        "axes": [
            {
                "id": f"axis-{index}",
                "question": question,
                "status": "pending",
                "queries_used": 0,
                "original_fetches_used": 0,
                "coverage": "pending",
                "note_path": f"notes/axis-{index}.md",
            }
            for index, question in enumerate(axes, 1)
        ],
        "waves": [],
        "next_actions": ["Define research axes"] if not axes else ["Research pending axes"],
        "limitations": [],
        "report_path": "report.md",
        "timestamps": {"created_at": timestamp, "updated_at": timestamp},
    }
    atomic_json(run_dir / "sources.json", [])
    atomic_write(run_dir / "report.md", "")
    atomic_json(run_dir / "state.json", state)
    return state


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValidationError(f"missing {path.name}") from error
    except json.JSONDecodeError as error:
        raise ValidationError(f"invalid JSON in {path.name}: {error}") from error


def validate_run(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    state = load_json(run_dir / "state.json")
    if not isinstance(state, dict):
        raise ValidationError("state.json must contain an object")
    for field, expected in REQUIRED.items():
        if field not in state:
            raise ValidationError(f"state.json is missing {field}")
        if not isinstance(state[field], expected):
            raise ValidationError(f"{field} must be {expected.__name__}")
    if state["status"] not in STATUSES:
        raise ValidationError(f"unknown status: {state['status']}")
    if state["mode"] not in MODES:
        raise ValidationError(f"unknown mode: {state['mode']}")
    if not state["query"].strip():
        raise ValidationError("query must not be empty")
    planning = state["planning"]
    for field in (
        "total_budget_seconds",
        "max_waves",
        "current_wave",
        "query_ceiling_per_axis",
        "original_fetch_ceiling_per_axis",
    ):
        if field not in planning or not is_int(planning[field]):
            raise ValidationError(f"planning.{field} must be an integer")
    for field in (
        "total_budget_seconds",
        "max_waves",
        "query_ceiling_per_axis",
        "original_fetch_ceiling_per_axis",
    ):
        if planning[field] < 1:
            raise ValidationError(f"planning.{field} must be positive")
    if planning["current_wave"] < 0:
        raise ValidationError("planning.current_wave must be non-negative")
    if planning["current_wave"] > planning["max_waves"]:
        raise ValidationError("planning.current_wave must not exceed planning.max_waves")
    reserve = planning.get("synthesis_reserve_ratio")
    if (
        isinstance(reserve, bool)
        or not isinstance(reserve, (int, float))
        or not 0.2 <= reserve < 1
    ):
        raise ValidationError("planning.synthesis_reserve_ratio must be at least 0.2 and below 1")
    reallocations = planning.get("budget_reallocations")
    if not isinstance(reallocations, list) or not all(
        isinstance(item, dict)
        and isinstance(item.get("reason"), str)
        and item["reason"].strip()
        for item in reallocations
    ):
        raise ValidationError("planning.budget_reallocations must contain objects with reasons")
    for index, axis in enumerate(state["axes"], 1):
        if not isinstance(axis, dict):
            raise ValidationError(f"axes[{index}] must be an object")
        for field in ("id", "question", "status", "coverage", "note_path"):
            if not isinstance(axis.get(field), str) or not axis[field].strip():
                raise ValidationError(f"axes[{index}].{field} must be a non-empty string")
        for field in ("queries_used", "original_fetches_used"):
            if not is_int(axis.get(field)) or axis[field] < 0:
                raise ValidationError(f"axes[{index}].{field} must be a non-negative integer")
        note_path = Path(axis["note_path"])
        if note_path.is_absolute():
            raise ValidationError(f"axes[{index}].note_path must be relative")
        try:
            (run_dir / note_path).resolve().relative_to(run_dir)
        except ValueError as error:
            raise ValidationError(f"axes[{index}].note_path escapes the run directory") from error
    if not all(isinstance(item, str) for item in state["next_actions"] + state["limitations"]):
        raise ValidationError("next_actions and limitations must contain strings")
    if not (run_dir / "notes").is_dir():
        raise ValidationError("missing notes directory")
    if not isinstance(load_json(run_dir / "sources.json"), list):
        raise ValidationError("sources.json must contain a list")

    report = Path(state["report_path"])
    if report.is_absolute():
        raise ValidationError("report_path must be relative to the run directory")
    report = (run_dir / report).resolve()
    try:
        report.relative_to(run_dir)
    except ValueError as error:
        raise ValidationError("report_path escapes the run directory") from error
    if not report.is_file():
        raise ValidationError("report file is missing")
    if state["status"] in {"completed", "partial"} and not report.read_text(
        encoding="utf-8"
    ).strip():
        raise ValidationError(f"{state['status']} run requires a non-empty report")
    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init")
    init.add_argument("run_dir", type=Path)
    init.add_argument("--query", required=True)
    init.add_argument("--mode", choices=sorted(MODES), default="deep")
    init.add_argument("--axis", action="append", default=[])
    for command in ("status", "validate"):
        child = subparsers.add_parser(command)
        child.add_argument("run_dir", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "init":
            state = init_run(args.run_dir, args.query, args.mode, args.axis)
        else:
            state = validate_run(args.run_dir)
    except ValidationError as error:
        print(f"error: {error}")
        return 1
    if args.command == "status":
        print(json.dumps(state, ensure_ascii=False, indent=2))
    else:
        print(f"{args.command}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
