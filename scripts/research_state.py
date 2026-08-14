#!/usr/bin/env python3
"""Create, inspect, validate, and clean up a Hermes deep-research run."""

from __future__ import annotations

import argparse
import json
import os
import stat
import tempfile
from dataclasses import dataclass
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
TMP_PATH = "tmp"
TMP_SUBDIRS = (
    "workspace",
    "raw-pages",
    "raw-data",
    "downloads",
    "extracts",
    "scratch",
    "lanes",
)
RUN_LAYOUT = ("notes", "lanes", *(f"{TMP_PATH}/{path}" for path in TMP_SUBDIRS))
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


def validate_init_args(query: str, mode: str) -> None:
    if mode not in MODES:
        raise ValidationError(f"mode must be one of: {', '.join(sorted(MODES))}")
    if not query.strip():
        raise ValidationError("query must not be empty")


def validate_slug(slug: str) -> str:
    if (
        not slug
        or slug != slug.strip()
        or not slug[0].isalnum()
        or not slug[-1].isalnum()
        or any(not (character.isalnum() or character in "-_") for character in slug)
    ):
        raise ValidationError(
            "slug must contain only letters, numbers, hyphens, or underscores "
            "and start and end with a letter or number"
        )
    return slug


def research_base() -> Path:
    configured = os.environ.get("HERMES_HOME")
    hermes_home = Path(configured).expanduser() if configured else Path.home() / ".hermes"
    if not hermes_home.is_absolute():
        raise ValidationError("HERMES_HOME must be an absolute path")
    return (hermes_home / "research/hermes-deep-research").resolve()


def create_run(slug: str, query: str, mode: str, axes: list[str]) -> tuple[Path, dict[str, Any]]:
    slug = validate_slug(slug)
    validate_init_args(query, mode)
    base = research_base()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    base.mkdir(parents=True, exist_ok=True)
    run_dir = base / f"{slug}-{stamp}"
    suffix = 1
    while True:
        try:
            run_dir.mkdir()
            break
        except FileExistsError:
            suffix += 1
            run_dir = base / f"{slug}-{stamp}-{suffix}"
    return run_dir, init_run(run_dir, query, mode, axes)


def init_run(run_dir: Path, query: str, mode: str, axes: list[str]) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    validate_init_args(query, mode)
    base = research_base()
    if run_dir.parent != base:
        raise ValidationError(f"new runs must be direct children of {base}")
    if (run_dir / "state.json").exists():
        raise ValidationError(f"run already exists: {run_dir}")

    run_dir.mkdir(parents=True, exist_ok=True)
    for directory in RUN_LAYOUT:
        (run_dir / directory).mkdir(parents=True, exist_ok=True)
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
        "tmp_path": TMP_PATH,
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


def validate_relative_path(
    run_dir: Path, value: Any, field: str, *, durable: bool = False
) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute():
        raise ValidationError(f"{field} must be relative to the run directory")
    path = (run_dir / path).resolve()
    try:
        relative = path.relative_to(run_dir)
    except ValueError as error:
        raise ValidationError(f"{field} escapes the run directory") from error
    if durable and relative.parts and relative.parts[0] == TMP_PATH:
        raise ValidationError(f"{field} must not be inside disposable {TMP_PATH}/")
    return path


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
        validate_relative_path(
            run_dir,
            axis["note_path"],
            f"axes[{index}].note_path",
            durable=True,
        )
    if not all(isinstance(item, str) for item in state["next_actions"] + state["limitations"]):
        raise ValidationError("next_actions and limitations must contain strings")
    if not (run_dir / "notes").is_dir():
        raise ValidationError("missing notes directory")
    if not isinstance(load_json(run_dir / "sources.json"), list):
        raise ValidationError("sources.json must contain a list")

    if "tmp_path" in state:
        if state["tmp_path"] != TMP_PATH:
            raise ValidationError(f"tmp_path must be {TMP_PATH!r}")
        tmp_entry = run_dir / TMP_PATH
        if tmp_entry.is_symlink():
            raise ValidationError("tmp_path directory is missing or unsafe")
        temporary = validate_relative_path(run_dir, state["tmp_path"], "tmp_path")
        if temporary != tmp_entry or not temporary.is_dir():
            raise ValidationError("tmp_path directory is missing or unsafe")
        for directory in TMP_SUBDIRS:
            child = temporary / directory
            if child.is_symlink() or not child.is_dir():
                raise ValidationError(f"missing temporary directory: {directory}")

    report = validate_relative_path(
        run_dir, state["report_path"], "report_path", durable=True
    )
    if not report.is_file():
        raise ValidationError("report file is missing")
    if state["status"] in {"completed", "partial"} and not report.read_text(
        encoding="utf-8"
    ).strip():
        raise ValidationError(f"{state['status']} run requires a non-empty report")
    return state


@dataclass(frozen=True)
class FileIdentity:
    device: int
    inode: int
    kind: int

    @classmethod
    def from_stat(cls, value: os.stat_result) -> FileIdentity:
        return cls(value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode))

    @property
    def is_directory(self) -> bool:
        return self.kind == stat.S_IFDIR


@dataclass(frozen=True)
class TemporarySnapshot:
    identity: FileIdentity
    size: int
    entries: tuple[tuple[str, TemporarySnapshot], ...] | None

    def usage(self) -> tuple[int, int]:
        if self.entries is None:
            return 1, self.size
        files = bytes_used = 0
        for _, entry in self.entries:
            child_files, child_bytes = entry.usage()
            files += child_files
            bytes_used += child_bytes
        return files, bytes_used


def open_directory(path: str | Path, dir_fd: int | None = None) -> int:
    try:
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    except AttributeError as error:
        raise ValidationError("secure cleanup is not supported on this platform") from error
    if (
        os.listdir not in os.supports_fd
        or os.stat not in os.supports_follow_symlinks
        or any(
            function not in os.supports_dir_fd
            for function in (os.open, os.stat, os.unlink, os.rmdir, os.mkdir)
        )
    ):
        raise ValidationError("secure cleanup is not supported on this platform")
    return os.open(path, flags, dir_fd=dir_fd)


def _identity(path: str | Path, label: str, dir_fd: int | None = None) -> FileIdentity:
    try:
        value = os.stat(path, dir_fd=dir_fd, follow_symlinks=False)
    except OSError as error:
        raise ValidationError(f"cleanup snapshot changed at {label}") from error
    return FileIdentity.from_stat(value)


def _fd_identity(directory_fd: int, label: str) -> FileIdentity:
    try:
        return FileIdentity.from_stat(os.fstat(directory_fd))
    except OSError as error:
        raise ValidationError(f"cleanup snapshot changed at {label}") from error


def _require_identity(expected: FileIdentity, actual: FileIdentity, label: str) -> None:
    if actual != expected:
        raise ValidationError(f"cleanup snapshot changed at {label}")


def _require_names(
    directory_fd: int, expected: set[str], label: str
) -> None:
    try:
        actual = set(os.listdir(directory_fd))
    except OSError as error:
        raise ValidationError(f"cleanup snapshot changed at {label}") from error
    if actual != expected:
        raise ValidationError(f"cleanup snapshot changed at {label}")


def _open_snapshotted_directory(
    path: str | Path,
    expected: FileIdentity,
    label: str,
    dir_fd: int | None = None,
) -> int:
    _require_identity(expected, _identity(path, label, dir_fd), label)
    try:
        directory_fd = open_directory(path, dir_fd)
    except (OSError, ValidationError) as error:
        raise ValidationError(f"cleanup snapshot changed at {label}") from error
    try:
        _require_identity(expected, _fd_identity(directory_fd, label), label)
    except BaseException:
        os.close(directory_fd)
        raise
    return directory_fd


def _snapshot_directory(directory_fd: int, label: str) -> TemporarySnapshot:
    identity = _fd_identity(directory_fd, label)
    try:
        names = tuple(sorted(os.listdir(directory_fd)))
    except OSError as error:
        raise ValidationError(f"cleanup snapshot changed at {label}") from error
    entries: list[tuple[str, TemporarySnapshot]] = []
    for name in names:
        child_label = f"{label}/{name}"
        child_identity = _identity(name, child_label, directory_fd)
        if not child_identity.is_directory:
            try:
                size = os.stat(
                    name, dir_fd=directory_fd, follow_symlinks=False
                ).st_size
            except OSError as error:
                raise ValidationError(f"cleanup snapshot changed at {child_label}") from error
            entries.append((name, TemporarySnapshot(child_identity, size, None)))
            continue
        child_fd = _open_snapshotted_directory(
            name, child_identity, child_label, directory_fd
        )
        try:
            entries.append((name, _snapshot_directory(child_fd, child_label)))
        finally:
            os.close(child_fd)
    _require_identity(identity, _fd_identity(directory_fd, label), label)
    _require_names(directory_fd, set(names), label)
    return TemporarySnapshot(identity, 0, tuple(entries))


def snapshot_temporary_tree(directory_fd: int) -> TemporarySnapshot:
    return _snapshot_directory(directory_fd, TMP_PATH)


def _verify_temporary_snapshot(
    directory_fd: int, snapshot: TemporarySnapshot, label: str = TMP_PATH
) -> None:
    _require_identity(snapshot.identity, _fd_identity(directory_fd, label), label)
    entries = snapshot.entries or ()
    _require_names(directory_fd, {name for name, _ in entries}, label)
    for name, child in entries:
        child_label = f"{label}/{name}"
        _require_identity(
            child.identity, _identity(name, child_label, directory_fd), child_label
        )
        if child.entries is None:
            continue
        child_fd = _open_snapshotted_directory(
            name, child.identity, child_label, directory_fd
        )
        try:
            _verify_temporary_snapshot(child_fd, child, child_label)
            _require_identity(
                child.identity, _identity(name, child_label, directory_fd), child_label
            )
        finally:
            os.close(child_fd)
    _require_names(directory_fd, {name for name, _ in entries}, label)


def remove_temporary_contents(
    directory_fd: int, snapshot: TemporarySnapshot, label: str = TMP_PATH
) -> None:
    _require_identity(snapshot.identity, _fd_identity(directory_fd, label), label)
    entries = snapshot.entries or ()
    _require_names(directory_fd, {name for name, _ in entries}, label)
    for name, child in entries:
        child_label = f"{label}/{name}"
        _require_identity(
            child.identity, _identity(name, child_label, directory_fd), child_label
        )
        if child.entries is None:
            try:
                os.unlink(name, dir_fd=directory_fd)
            except OSError as error:
                raise ValidationError(f"cleanup snapshot changed at {child_label}") from error
            continue

        child_fd = _open_snapshotted_directory(
            name, child.identity, child_label, directory_fd
        )
        try:
            remove_temporary_contents(child_fd, child, child_label)
            try:
                current = _identity(name, child_label, directory_fd)
            except ValidationError as error:
                if isinstance(error.__cause__, FileNotFoundError):
                    continue
                raise
            _require_identity(child.identity, current, child_label)
            try:
                os.rmdir(name, dir_fd=directory_fd)
            except OSError as error:
                raise ValidationError(f"cleanup snapshot changed at {child_label}") from error
        finally:
            os.close(child_fd)
    _require_names(directory_fd, set(), label)


def _verify_cleanup_binding(
    run_dir: Path,
    run_fd: int,
    run_identity: FileIdentity,
    temporary_fd: int,
    temporary_identity: FileIdentity,
) -> None:
    _require_identity(run_identity, _identity(run_dir, "run_dir"), "run_dir")
    _require_identity(run_identity, _fd_identity(run_fd, "run_dir"), "run_dir")
    _require_identity(
        temporary_identity, _identity(TMP_PATH, TMP_PATH, run_fd), TMP_PATH
    )
    _require_identity(
        temporary_identity, _fd_identity(temporary_fd, TMP_PATH), TMP_PATH
    )


def cleanup_run(run_dir: Path, apply: bool = False) -> tuple[int, int, Path]:
    run_dir = run_dir.expanduser().resolve()
    temporary = run_dir / TMP_PATH
    run_identity = _identity(run_dir, "run_dir")
    temporary_identity = _identity(temporary, TMP_PATH)
    if not run_identity.is_directory or not temporary_identity.is_directory:
        raise ValidationError("cleanup target is not the run's canonical tmp directory")
    state = validate_run(run_dir)
    if state["status"] in {"researching", "synthesizing"}:
        raise ValidationError(f"cannot clean up while status is {state['status']}")
    if state.get("tmp_path") != TMP_PATH:
        raise ValidationError("cleanup requires a run with recorded tmp_path 'tmp'")

    run_fd = _open_snapshotted_directory(run_dir, run_identity, "run_dir")
    try:
        temporary_fd = _open_snapshotted_directory(
            TMP_PATH, temporary_identity, TMP_PATH, run_fd
        )
        try:
            snapshot = snapshot_temporary_tree(temporary_fd)
            files, bytes_used = snapshot.usage()
            _verify_cleanup_binding(
                run_dir, run_fd, run_identity, temporary_fd, temporary_identity
            )
            _verify_temporary_snapshot(temporary_fd, snapshot)
            if apply:
                _verify_cleanup_binding(
                    run_dir, run_fd, run_identity, temporary_fd, temporary_identity
                )
                remove_temporary_contents(temporary_fd, snapshot)
                _verify_cleanup_binding(
                    run_dir, run_fd, run_identity, temporary_fd, temporary_identity
                )
                for directory in TMP_SUBDIRS:
                    try:
                        os.mkdir(directory, dir_fd=temporary_fd)
                    except OSError as error:
                        raise ValidationError(
                            f"cleanup snapshot changed at {TMP_PATH}/{directory}"
                        ) from error
                _verify_cleanup_binding(
                    run_dir, run_fd, run_identity, temporary_fd, temporary_identity
                )
        finally:
            os.close(temporary_fd)
    finally:
        os.close(run_fd)
    return files, bytes_used, temporary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init")
    init.add_argument("run_dir", type=Path)
    init.add_argument("--query", required=True)
    init.add_argument("--mode", choices=sorted(MODES), default="deep")
    init.add_argument("--axis", action="append", default=[])
    create = subparsers.add_parser("create")
    create.add_argument("slug")
    create.add_argument("--query", required=True)
    create.add_argument("--mode", choices=sorted(MODES), default="deep")
    create.add_argument("--axis", action="append", default=[])
    cleanup = subparsers.add_parser("cleanup", help="report disposable usage; delete with --apply")
    cleanup.add_argument("run_dir", type=Path)
    cleanup.add_argument("--apply", action="store_true", help="delete recorded tmp contents")
    for command in ("status", "validate"):
        child = subparsers.add_parser(command)
        child.add_argument("run_dir", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "create":
            run_dir, state = create_run(args.slug, args.query, args.mode, args.axis)
        elif args.command == "init":
            state = init_run(args.run_dir, args.query, args.mode, args.axis)
        elif args.command == "cleanup":
            files, bytes_used, temporary = cleanup_run(args.run_dir, args.apply)
        else:
            state = validate_run(args.run_dir)
    except ValidationError as error:
        print(f"error: {error}")
        return 1
    if args.command == "create":
        print(run_dir)
    elif args.command == "cleanup":
        action = "deleted" if args.apply else "dry-run"
        print(f"cleanup {action}: {files} files, {bytes_used} bytes under {temporary}")
    elif args.command == "status":
        print(json.dumps(state, ensure_ascii=False, indent=2))
    else:
        print(f"{args.command}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
