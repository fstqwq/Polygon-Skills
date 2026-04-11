#!/usr/bin/env python3
"""Standalone schema validator for problem repository config files.

Run from the problem repo root:

    python <skills>/polygon-spec/test_schema.py

Validates:
  - config/problem.json
  - config/build.json
  - tests/spec.json
  - solutions/*.desc
  - file-existence for all referenced paths

Exit code 0 = all checks pass, 1 = errors found.
No external dependencies required.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

VALID_MODES = {"pass-fail", "interactive"}
VALID_KINDS = {"manual", "gen"}
VALID_EXPECTED = {"accepted", "wrong_answer", "time_limit_exceeded", "run_time_error", "rejected"}
TEST_ID_RE = re.compile(r"^[0-9]{3}$")
SOURCE_PATH_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./-]{0,200}$")


def _errors_problem_json(root: Path) -> list[str]:
    path = root / "config" / "problem.json"
    if not path.exists():
        return ["config/problem.json: file missing"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"config/problem.json: invalid JSON â€?{exc}"]
    if not isinstance(data, dict):
        return ["config/problem.json: must be a JSON object"]
    errors: list[str] = []
    # mode
    mode = data.get("mode")
    if mode is None:
        errors.append("config/problem.json: missing required field 'mode'")
    elif mode not in VALID_MODES:
        errors.append(f"config/problem.json: invalid mode '{mode}' (expected {VALID_MODES})")
    # pass_limit
    pass_limit = data.get("pass_limit")
    if pass_limit is None:
        errors.append("config/problem.json: missing required field 'pass_limit'")
    elif not isinstance(pass_limit, int) or pass_limit < 1:
        errors.append(f"config/problem.json: pass_limit must be int >= 1, got {pass_limit!r}")
    # time_limit_ms
    tl = data.get("time_limit_ms")
    if tl is not None and (not isinstance(tl, int) or tl <= 0):
        errors.append(f"config/problem.json: time_limit_ms must be int > 0, got {tl!r}")
    # memory_limit_mb
    ml = data.get("memory_limit_mb")
    if ml is not None and (not isinstance(ml, int) or ml <= 0):
        errors.append(f"config/problem.json: memory_limit_mb must be int > 0, got {ml!r}")
    return errors


def _check_source_path(root: Path, path_value: str, field: str, config_file: str) -> list[str]:
    """Validate a repo-relative source path: format + existence."""
    if not path_value:
        return []
    errors: list[str] = []
    if not SOURCE_PATH_RE.fullmatch(path_value):
        errors.append(f"{config_file}: {field} has invalid path format '{path_value}'")
        return errors
    if ".." in path_value or path_value.startswith("/"):
        errors.append(f"{config_file}: {field} must be repo-relative, got '{path_value}'")
        return errors
    if not (root / path_value).exists():
        errors.append(f"{config_file}: {field} references missing file '{path_value}'")
    return errors


def _errors_build_json(root: Path) -> list[str]:
    path = root / "config" / "build.json"
    if not path.exists():
        return []  # build.json is optional before first component is added
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"config/build.json: invalid JSON â€?{exc}"]
    if not isinstance(data, dict):
        return ["config/build.json: must be a JSON object"]
    errors: list[str] = []
    source_fields = ["accepted_solution_source", "validator_source", "checker_source", "interactor_source"]
    for field in source_fields:
        value = data.get(field)
        if value is not None:
            if not isinstance(value, str):
                errors.append(f"config/build.json: {field} must be a string")
            else:
                errors.extend(_check_source_path(root, value, field, "config/build.json"))
    # generator_sources
    gen = data.get("generator_sources")
    if gen is not None:
        if not isinstance(gen, list):
            errors.append("config/build.json: generator_sources must be an array")
        else:
            for i, item in enumerate(gen):
                if not isinstance(item, str):
                    errors.append(f"config/build.json: generator_sources[{i}] must be a string")
                else:
                    errors.extend(_check_source_path(root, item, f"generator_sources[{i}]", "config/build.json"))
    return errors


def _errors_spec_json(root: Path) -> list[str]:
    path = root / "tests" / "spec.json"
    if not path.exists():
        return []  # spec.json is optional before tests are added
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"tests/spec.json: invalid JSON â€?{exc}"]
    if not isinstance(data, dict):
        return ["tests/spec.json: must be a JSON object"]
    errors: list[str] = []
    tests = data.get("tests")
    if tests is None:
        errors.append("tests/spec.json: missing 'tests' array")
        return errors
    if not isinstance(tests, list):
        errors.append("tests/spec.json: 'tests' must be an array")
        return errors
    seen_ids: set[str] = set()
    for i, entry in enumerate(tests):
        prefix = f"tests/spec.json: tests[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        # id
        tid = entry.get("id")
        if tid is None:
            errors.append(f"{prefix}: missing 'id'")
        elif not isinstance(tid, str) or not TEST_ID_RE.fullmatch(tid):
            errors.append(f"{prefix}: id must be 3-digit string, got {tid!r}")
        else:
            if tid in seen_ids:
                errors.append(f"{prefix}: duplicate id '{tid}'")
            seen_ids.add(tid)
        # kind
        kind = entry.get("kind")
        if kind is None:
            errors.append(f"{prefix}: missing 'kind'")
        elif kind not in VALID_KINDS:
            errors.append(f"{prefix}: invalid kind '{kind}' (expected {VALID_KINDS})")
        # sample
        sample = entry.get("sample")
        if sample is not None and not isinstance(sample, bool):
            errors.append(f"{prefix}: 'sample' must be a boolean")
        # manual test file existence
        if kind == "manual" and isinstance(tid, str) and TEST_ID_RE.fullmatch(tid):
            manual_path = root / "tests" / "manual" / f"{tid}.in"
            if not manual_path.exists():
                errors.append(f"{prefix}: manual test file 'tests/manual/{tid}.in' missing")
    # sequential id check
    id_list = sorted(seen_ids)
    for j, tid in enumerate(id_list):
        expected = f"{j + 1:03d}"
        if tid != expected:
            errors.append(f"tests/spec.json: ids not sequential â€?expected '{expected}', got '{tid}'")
            break
    return errors


def _errors_solution_descs(root: Path) -> list[str]:
    solutions_dir = root / "solutions"
    if not solutions_dir.is_dir():
        return []
    errors: list[str] = []
    for entry in sorted(solutions_dir.iterdir()):
        if not entry.name.endswith(".desc") or not entry.is_file():
            continue
        rel = f"solutions/{entry.name}"
        try:
            text = entry.read_text(encoding="utf-8")
        except OSError:
            errors.append(f"{rel}: unreadable")
            continue
        expected_value = ""
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("expected:"):
                expected_value = line.split(":", 1)[1].strip()
                break
        if not expected_value:
            errors.append(f"{rel}: missing 'expected:' line")
        elif expected_value not in VALID_EXPECTED:
            errors.append(f"{rel}: invalid expected value '{expected_value}' (valid: {VALID_EXPECTED})")
        # check that the source file exists
        source_name = entry.name[: -len(".desc")]
        source_path = solutions_dir / source_name
        if not source_path.exists():
            errors.append(f"{rel}: source file 'solutions/{source_name}' missing")
    return errors


def _warnings_completeness(root: Path) -> list[str]:
    """Warn about missing content that a finished problem should have."""
    warnings: list[str] = []

    # --- build.json completeness ---
    build_path = root / "config" / "build.json"
    if not build_path.exists():
        warnings.append("config/build.json: file missing â€?no components configured")
    else:
        try:
            build = json.loads(build_path.read_text(encoding="utf-8"))
        except Exception:
            build = {}
        if isinstance(build, dict):
            if not build.get("accepted_solution_source"):
                warnings.append("config/build.json: accepted_solution_source is empty â€?no accepted solution configured")
            if not build.get("validator_source"):
                warnings.append("config/build.json: validator_source is empty â€?no validator configured")

    # --- checker existence ---
    problem_path = root / "config" / "problem.json"
    mode = ""
    try:
        problem = json.loads(problem_path.read_text(encoding="utf-8"))
        mode = problem.get("mode", "")
    except Exception:
        pass
    checkers_dir = root / "checkers"
    has_checker = checkers_dir.is_dir() and any(
        f.is_file() and not f.name.startswith(".") for f in checkers_dir.iterdir()
    ) if checkers_dir.exists() else False
    if not has_checker and mode != "interactive":
        warnings.append("checkers/: no checker source found")

    # --- tests completeness ---
    spec_path = root / "tests" / "spec.json"
    if not spec_path.exists():
        warnings.append("tests/spec.json: file missing â€?no tests defined")
    else:
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            tests = spec.get("tests", [])
        except Exception:
            tests = []
        if isinstance(tests, list):
            if not tests:
                warnings.append("tests/spec.json: tests array is empty â€?no tests defined")
            else:
                # sample tests should come before non-sample tests
                last_sample_idx = -1
                first_nonsample_idx = -1
                for i, entry in enumerate(tests):
                    if not isinstance(entry, dict):
                        continue
                    is_sample = bool(entry.get("sample"))
                    if is_sample:
                        last_sample_idx = i
                    elif first_nonsample_idx == -1:
                        first_nonsample_idx = i
                if last_sample_idx > first_nonsample_idx >= 0:
                    warnings.append(
                        f"tests/spec.json: sample tests should come before non-sample tests "
                        f"(sample at index {last_sample_idx} follows non-sample at index {first_nonsample_idx})"
                    )
                # warn if no samples at all
                if last_sample_idx == -1 and len(tests) > 0:
                    warnings.append("tests/spec.json: no sample tests defined (no entry has \"sample\": true)")

    # --- statement sections ---
    sections_dir = root / "statement-sections"
    if not sections_dir.is_dir():
        warnings.append("statement-sections/: directory missing â€?no statement languages")
    else:
        languages = [d.name for d in sorted(sections_dir.iterdir()) if d.is_dir() and not d.is_symlink()]
        if not languages:
            warnings.append("statement-sections/: no language directories found")
        else:
            for lang in languages:
                lang_dir = sections_dir / lang
                required_sections = ["name.tex", "legend.tex", "input.tex", "output.tex"]
                for section in required_sections:
                    section_path = lang_dir / section
                    if not section_path.exists():
                        warnings.append(f"statement-sections/{lang}/{section}: file missing")
                    elif section_path.stat().st_size == 0 and section in ("name.tex", "legend.tex"):
                        warnings.append(f"statement-sections/{lang}/{section}: file is empty")
    return warnings


def validate(root: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    errors.extend(_errors_problem_json(root))
    errors.extend(_errors_build_json(root))
    errors.extend(_errors_spec_json(root))
    errors.extend(_errors_solution_descs(root))
    warnings: list[str] = []
    warnings.extend(_warnings_completeness(root))
    warnings.extend(_warnings_judging_time(root))
    return errors, warnings


def _warnings_judging_time(root: Path) -> list[str]:
    """Warn if max(1s, time_limit) * pass_limit * num_tests >= 300s."""
    problem_path = root / "config" / "problem.json"
    spec_path = root / "tests" / "spec.json"
    if not problem_path.exists() or not spec_path.exists():
        return []
    try:
        problem = json.loads(problem_path.read_text(encoding="utf-8"))
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    tl_ms = problem.get("time_limit_ms", 2000)
    pass_limit = problem.get("pass_limit", 1)
    tests = spec.get("tests", [])
    if not isinstance(tl_ms, int) or not isinstance(pass_limit, int) or not isinstance(tests, list):
        return []
    tl_sec = max(1.0, tl_ms / 1000.0)
    total = tl_sec * pass_limit * len(tests)
    if total >= 300:
        return [f"this problem may take a fairly long time to judge ({tl_sec:.0f}s Ã— {pass_limit} pass Ã— {len(tests)} tests = {total:.0f}s)"]
    return []


def main() -> int:
    root = Path(os.environ.get("PROBLEM_ROOT", ".")).resolve()
    if not (root / "config").is_dir():
        print(f"ERROR: {root} does not look like a problem repo (no config/ directory)", file=sys.stderr)
        return 1
    errors, warnings = validate(root)
    for warn in warnings:
        print(f"  WARNING: {warn}", file=sys.stderr)
    if not errors:
        print(f"OK â€?all schema checks passed ({root.name})")
        return 0
    for err in errors:
        print(f"  ERROR: {err}", file=sys.stderr)
    print(f"\n{len(errors)} error(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
