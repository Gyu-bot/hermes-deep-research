#!/usr/bin/env python3
"""Record and verify the final report document-readiness gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
PRE_DOCUMENT = "report.pre-document.md"
CANDIDATE = "report.document-candidate.md"
HUMAN_GATE = "report.document-readiness-gate.md"
READY = "report.document-ready.md"
BINDING = "report.document-readiness-gate.json"


class GateError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write(
        path,
        (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def confined_path(run_dir: Path, value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise GateError(f"{label} must be a non-empty path")
    path = Path(value)
    path = (run_dir / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        path.relative_to(run_dir)
    except ValueError as error:
        raise GateError(f"{label} escapes the run directory") from error
    return path


def require_file(run_dir: Path, name: str) -> Path:
    path = confined_path(run_dir, name, name)
    if not path.is_file():
        raise GateError(f"missing {name}")
    return path


def final_verdicts(markdown: str) -> set[str]:
    lines = []
    for raw_line in markdown.splitlines():
        line = re.sub(r"^(?:#{1,6}|[-*+>])\s*", "", raw_line.strip())
        lines.append(line.replace("**", "").replace("__", "").replace("`", "").strip())

    verdicts = set()
    inline = re.compile(
        r"^\|?\s*final(?:\s+verdict)?\s*(?:\||:|[-—])?\s*(PASS|FAIL)\s*\|?\s*[.!]?\s*$",
        re.IGNORECASE,
    )
    for index, line in enumerate(lines):
        match = inline.fullmatch(line)
        if match:
            verdicts.add(match.group(1).upper())
        if line.casefold() in {"final", "final verdict"}:
            for following in lines[index + 1 :]:
                if following:
                    if re.fullmatch(
                        r"(?:\*\*)?(PASS|FAIL)(?:\*\*)?[.!]?",
                        following,
                        re.IGNORECASE,
                    ):
                        verdicts.add(following.rstrip(".! ").upper())
                    break
    return verdicts


def checked_at(value: str | None) -> str:
    if value is not None and not value.strip():
        raise GateError("checked_at must not be empty")
    return value.strip() if value is not None else now()


def base_binding(
    verdict: str, when: str | None, research_status: str | None
) -> dict[str, Any]:
    binding = {
        "schema_version": SCHEMA_VERSION,
        "verdict": verdict,
        "candidate_path": CANDIDATE,
        "ready_path": READY,
        "checked_at": checked_at(when),
    }
    if research_status is not None:
        if not research_status.strip():
            raise GateError("research_status must not be empty")
        binding["research_status"] = research_status.strip()
    return binding


def record_pass(
    run_dir: Path, *, when: str | None = None, research_status: str | None = None
) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    require_file(run_dir, PRE_DOCUMENT)
    candidate = require_file(run_dir, CANDIDATE)
    human_gate = require_file(run_dir, HUMAN_GATE)
    try:
        verdicts = final_verdicts(human_gate.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        raise GateError(f"{HUMAN_GATE} must be UTF-8") from error
    if "PASS" not in verdicts or "FAIL" in verdicts:
        raise GateError(f"{HUMAN_GATE} must contain final PASS and no final FAIL")

    data = candidate.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    binding = base_binding("PASS", when, research_status)
    binding["sha256"] = digest
    atomic_write(run_dir / READY, data)
    atomic_json(run_dir / BINDING, binding)
    return binding


def record_fail(
    run_dir: Path,
    reason: str,
    *,
    when: str | None = None,
    research_status: str | None = None,
) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    if not reason.strip():
        raise GateError("reason must not be empty")
    binding = base_binding("FAIL", when, research_status)
    binding["reason"] = reason.strip()
    try:
        candidate = confined_path(run_dir, CANDIDATE, CANDIDATE)
        candidate_hash = sha256(candidate) if candidate.is_file() else None
    except (GateError, OSError):
        candidate_hash = None
    binding["candidate_sha256"] = candidate_hash
    atomic_json(run_dir / BINDING, binding)
    return binding


def load_binding(path: Path) -> dict[str, Any]:
    try:
        binding = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise GateError(f"missing {BINDING}") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GateError(f"invalid JSON in {BINDING}: {error}") from error
    if not isinstance(binding, dict):
        raise GateError(f"{BINDING} must contain an object")
    return binding


def verify_gate(run_dir: Path) -> dict[str, Any]:
    run_dir = run_dir.expanduser().resolve()
    binding = load_binding(confined_path(run_dir, BINDING, BINDING))
    schema_version = binding.get("schema_version")
    if type(schema_version) is not int or schema_version != SCHEMA_VERSION:
        raise GateError("unsupported gate binding schema_version")
    if binding.get("verdict") != "PASS":
        raise GateError("current gate binding is not PASS")
    checked = binding.get("checked_at")
    if not isinstance(checked, str) or not checked.strip():
        raise GateError("gate binding has an invalid checked_at")
    if binding.get("candidate_path") != CANDIDATE or binding.get("ready_path") != READY:
        raise GateError("gate binding paths do not match the report artifacts")

    candidate = confined_path(run_dir, binding["candidate_path"], "candidate_path")
    ready = confined_path(run_dir, binding["ready_path"], "ready_path")
    if not candidate.is_file() or not ready.is_file():
        raise GateError("candidate and ready files must both exist")
    bound_hash = binding.get("sha256")
    if not isinstance(bound_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", bound_hash):
        raise GateError("gate binding has an invalid sha256")
    if sha256(candidate) != bound_hash or sha256(ready) != bound_hash:
        raise GateError("candidate or ready hash does not match the gate binding")

    human_gate = require_file(run_dir, HUMAN_GATE)
    try:
        verdicts = final_verdicts(human_gate.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        raise GateError(f"{HUMAN_GATE} must be UTF-8") from error
    if "PASS" not in verdicts or "FAIL" in verdicts:
        raise GateError(f"{HUMAN_GATE} no longer has final PASS without final FAIL")
    return binding


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("pass", "fail"):
        child = subparsers.add_parser(command)
        child.add_argument("run_dir", type=Path)
        child.add_argument("--checked-at")
        child.add_argument("--research-status")
        if command == "fail":
            child.add_argument("--reason", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("run_dir", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "pass":
            record_pass(
                args.run_dir,
                when=args.checked_at,
                research_status=args.research_status,
            )
        elif args.command == "fail":
            record_fail(
                args.run_dir,
                args.reason,
                when=args.checked_at,
                research_status=args.research_status,
            )
        else:
            verify_gate(args.run_dir)
    except (GateError, OSError) as error:
        print(f"error: {error}")
        return 1
    print(f"{args.command}: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
