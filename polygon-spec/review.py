#!/usr/bin/env python3
"""Problem repository review -- produces a structured report.

Run from the problem repo root:

    python <skills>/polygon-spec/review.py

Checks:
  - config/problem.json   (schema validation)
  - config/build.json     (schema + file references)
  - tests/spec.json       (schema + file existence)
  - solutions/*.desc      (expected behavior + source existence)
  - statement-sections/   (required files and interaction layout)
  - completeness warnings (missing components, no samples, etc.)

Outputs a report with sections: Status, Warnings, Errors.
Exit code 0 = no errors, 1 = errors found.
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
        return [f"config/problem.json: invalid JSON -- {exc}"]
    if not isinstance(data, dict):
        return ["config/problem.json: must be a JSON object"]
    errors: list[str] = []
    mode = data.get("mode")
    if mode is None:
        errors.append("config/problem.json: missing required field 'mode'")
    elif mode not in VALID_MODES:
        errors.append(f"config/problem.json: invalid mode '{mode}' (expected {VALID_MODES})")
    pass_limit = data.get("pass_limit")
    if pass_limit is None:
        errors.append("config/problem.json: missing required field 'pass_limit'")
    elif not isinstance(pass_limit, int) or pass_limit < 1:
        errors.append(f"config/problem.json: pass_limit must be int >= 1, got {pass_limit!r}")
    tl = data.get("time_limit_ms")
    if tl is not None and (not isinstance(tl, int) or tl <= 0):
        errors.append(f"config/problem.json: time_limit_ms must be int > 0, got {tl!r}")
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
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"config/build.json: invalid JSON -- {exc}"]
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
    mode = _read_valid_problem_mode(root)
    checker_source = data.get("checker_source", "")
    interactor_source = data.get("interactor_source", "")
    if mode == "pass-fail":
        if isinstance(checker_source, str) and checker_source != "" and not checker_source.startswith("checkers/"):
            errors.append("config/build.json: checker_source must be under checkers/ for pass-fail problems")
        if isinstance(interactor_source, str) and interactor_source != "":
            errors.append("config/build.json: interactor_source must be empty for pass-fail problems")
    elif mode == "interactive":
        if isinstance(checker_source, str) and checker_source != "":
            errors.append("config/build.json: checker_source must be empty for interactive problems")
    return errors


def _errors_spec_json(root: Path) -> list[str]:
    path = root / "tests" / "spec.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"tests/spec.json: invalid JSON -- {exc}"]
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
        tid = entry.get("id")
        if tid is None:
            errors.append(f"{prefix}: missing 'id'")
        elif not isinstance(tid, str) or not TEST_ID_RE.fullmatch(tid):
            errors.append(f"{prefix}: id must be 3-digit string, got {tid!r}")
        else:
            if tid in seen_ids:
                errors.append(f"{prefix}: duplicate id '{tid}'")
            seen_ids.add(tid)
        kind = entry.get("kind")
        if kind is None:
            errors.append(f"{prefix}: missing 'kind'")
        elif kind not in VALID_KINDS:
            errors.append(f"{prefix}: invalid kind '{kind}' (expected {VALID_KINDS})")
        sample = entry.get("sample")
        if sample is not None and not isinstance(sample, bool):
            errors.append(f"{prefix}: 'sample' must be a boolean")
        if kind == "manual" and isinstance(tid, str) and TEST_ID_RE.fullmatch(tid):
            manual_path = root / "tests" / "manual" / f"{tid}.in"
            if not manual_path.exists():
                errors.append(f"{prefix}: manual test file 'tests/manual/{tid}.in' missing")
        if kind == "gen" and isinstance(tid, str) and TEST_ID_RE.fullmatch(tid):
            gen_path = root / "tests" / "generator" / f"{tid}.in"
            if not gen_path.exists():
                errors.append(f"{prefix}: generator payload file 'tests/generator/{tid}.in' missing")
    id_list = sorted(seen_ids)
    for j, tid in enumerate(id_list):
        expected = f"{j + 1:03d}"
        if tid != expected:
            errors.append(f"tests/spec.json: ids not sequential -- expected '{expected}', got '{tid}'")
            break
    answers_dir = root / "tests" / "answers"
    if answers_dir.exists():
        errors.append("tests/answers/: committed answer files are not allowed")
    tests_dir = root / "tests"
    if tests_dir.is_dir():
        for ans_path in sorted(tests_dir.rglob("*.ans")):
            rel = ans_path.relative_to(root).as_posix()
            errors.append(f"{rel}: committed answer files are not allowed")
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
        source_name = entry.name[: -len(".desc")]
        source_path = solutions_dir / source_name
        if not source_path.exists():
            errors.append(f"{rel}: source file 'solutions/{source_name}' missing")
    return errors


def _read_valid_problem_mode(root: Path) -> str:
    path = root / "config" / "problem.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    if not isinstance(data, dict):
        return ""
    mode = data.get("mode")
    if mode == "pass-fail" or mode == "interactive":
        return mode
    return ""


def _errors_statement_interaction_layout(root: Path) -> list[str]:
    mode = _read_valid_problem_mode(root)
    if not mode:
        return []

    sections_dir = root / "statement-sections"
    if not sections_dir.is_dir():
        return []

    errors: list[str] = []
    for lang_dir in sorted(sections_dir.iterdir()):
        if not lang_dir.is_dir() or lang_dir.is_symlink():
            continue
        interaction_path = lang_dir / "interaction.tex"
        rel_path = f"statement-sections/{lang_dir.name}/interaction.tex"
        if mode == "interactive":
            if not interaction_path.exists():
                errors.append(f"{rel_path}: missing for interactive problem")
        elif interaction_path.exists():
            errors.append(f"{rel_path}: must not exist for pass-fail problem")
    return errors


def _warnings_completeness(root: Path) -> list[str]:
    """Warn about missing content that a finished problem should have."""
    warnings: list[str] = []
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        warnings.append(".gitignore: missing -- temp/ must be ignored")
    else:
        try:
            gitignore_lines = gitignore_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            gitignore_lines = []
        ignored_patterns = {line.strip() for line in gitignore_lines if line.strip() and not line.strip().startswith("#")}
        if "temp/" not in ignored_patterns and "/temp/" not in ignored_patterns:
            warnings.append(".gitignore: temp/ is not ignored")
    testlib_path = root / "third_party" / "testlib" / "testlib.h"
    if not testlib_path.exists():
        warnings.append("third_party/testlib/testlib.h: missing -- required for import")
    build_path = root / "config" / "build.json"
    build: dict[str, object] = {}
    if not build_path.exists():
        warnings.append("config/build.json: file missing -- no components configured")
    else:
        try:
            build_obj = json.loads(build_path.read_text(encoding="utf-8"))
        except Exception:
            build_obj = {}
        if isinstance(build_obj, dict):
            build = build_obj
            if not build.get("accepted_solution_source"):
                warnings.append("config/build.json: no accepted solution configured")
            if not build.get("validator_source"):
                warnings.append("config/build.json: no validator configured")

    mode = _read_valid_problem_mode(root)
    if build_path.exists() and mode == "pass-fail" and not build.get("checker_source"):
        warnings.append("config/build.json: no checker configured")
    spec_path = root / "tests" / "spec.json"
    if not spec_path.exists():
        warnings.append("tests/spec.json: no tests defined")
    else:
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            tests = spec.get("tests", [])
        except Exception:
            tests = []
        if isinstance(tests, list):
            if not tests:
                warnings.append("tests/spec.json: tests array is empty")
            else:
                last_sample_idx = -1
                first_nonsample_idx = -1
                for i, entry in enumerate(tests):
                    if not isinstance(entry, dict):
                        continue
                    if bool(entry.get("sample")):
                        last_sample_idx = i
                    elif first_nonsample_idx == -1:
                        first_nonsample_idx = i
                if last_sample_idx > first_nonsample_idx >= 0:
                    warnings.append(
                        f"tests/spec.json: sample at index {last_sample_idx} follows non-sample at {first_nonsample_idx}"
                    )
                if last_sample_idx == -1 and len(tests) > 0:
                    warnings.append("tests/spec.json: no sample tests defined")

    sections_dir = root / "statement-sections"
    if not sections_dir.is_dir():
        warnings.append("statement-sections/: directory missing")
    else:
        languages = [d.name for d in sorted(sections_dir.iterdir()) if d.is_dir() and not d.is_symlink()]
        if not languages:
            warnings.append("statement-sections/: no language directories found")
        else:
            for lang in languages:
                lang_dir = sections_dir / lang
                for section in ["name.tex", "legend.tex", "input.tex", "output.tex"]:
                    section_path = lang_dir / section
                    if not section_path.exists():
                        warnings.append(f"statement-sections/{lang}/{section}: missing")
                    elif section_path.stat().st_size == 0 and section in ("name.tex", "legend.tex"):
                        warnings.append(f"statement-sections/{lang}/{section}: empty")
    return warnings


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
        return [f"estimated judge time is high ({tl_sec:.0f}s x {pass_limit} pass x {len(tests)} tests = {total:.0f}s)"]
    return []


def _component_status(root: Path) -> dict[str, str]:
    """Return a dict mapping component name to status string."""
    status: dict[str, str] = {}

    build: dict[str, object] = {}
    build_path = root / "config" / "build.json"
    if build_path.exists():
        try:
            build = json.loads(build_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    problem: dict[str, object] = {}
    problem_path = root / "config" / "problem.json"
    if problem_path.exists():
        try:
            problem = json.loads(problem_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    mode = str(problem.get("mode", ""))
    pass_limit = problem.get("pass_limit", 1)
    mode_label = mode or "?"
    if isinstance(pass_limit, int) and pass_limit > 1:
        mode_label += f" (pass_limit={pass_limit})"
    status["mode"] = mode_label

    tl = problem.get("time_limit_ms")
    ml = problem.get("memory_limit_mb")
    status["time_limit"] = f"{tl}ms" if tl else "not set"
    status["memory_limit"] = f"{ml}MB" if ml else "not set"

    for key, label in [
        ("validator_source", "validator"),
        ("checker_source", "checker"),
        ("interactor_source", "interactor"),
        ("accepted_solution_source", "accepted_solution"),
    ]:
        val = build.get(key, "")
        if val and isinstance(val, str):
            exists = (root / val).exists()
            status[label] = f"{val}" + ("" if exists else " [MISSING]")
        else:
            status[label] = "not configured"

    gen_sources = build.get("generator_sources", [])
    if isinstance(gen_sources, list) and gen_sources:
        status["generators"] = ", ".join(str(g) for g in gen_sources)
    else:
        status["generators"] = "none"

    spec_path = root / "tests" / "spec.json"
    if spec_path.exists():
        try:
            spec = json.loads(spec_path.read_text(encoding="utf-8"))
            tests = spec.get("tests", [])
            if isinstance(tests, list):
                n_total = len(tests)
                n_sample = sum(1 for t in tests if isinstance(t, dict) and t.get("sample"))
                n_manual = sum(1 for t in tests if isinstance(t, dict) and t.get("kind") == "manual")
                n_gen = sum(1 for t in tests if isinstance(t, dict) and t.get("kind") == "gen")
                status["tests"] = f"{n_total} total ({n_sample} sample, {n_manual} manual, {n_gen} gen)"
            else:
                status["tests"] = "invalid"
        except Exception:
            status["tests"] = "spec.json unreadable"
    else:
        status["tests"] = "no spec.json"

    sections_dir = root / "statement-sections"
    if sections_dir.is_dir():
        languages = [d.name for d in sorted(sections_dir.iterdir()) if d.is_dir() and not d.is_symlink()]
        status["languages"] = ", ".join(languages) if languages else "none"
    else:
        status["languages"] = "none"

    attach_dir = root / "attachments"
    if attach_dir.is_dir():
        files = [f.name for f in sorted(attach_dir.iterdir()) if f.is_file() and not f.name.startswith(".")]
        status["attachments"] = ", ".join(files) if files else "empty"
    else:
        status["attachments"] = "none"

    solutions_dir = root / "solutions"
    if solutions_dir.is_dir():
        sol_files = [f.name for f in sorted(solutions_dir.iterdir())
                     if f.is_file() and not f.name.endswith(".desc") and not f.name.startswith(".")]
        status["solutions"] = f"{len(sol_files)} files" if sol_files else "none"
    else:
        status["solutions"] = "none"

    return status


def validate(root: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    errors.extend(_errors_problem_json(root))
    errors.extend(_errors_build_json(root))
    errors.extend(_errors_spec_json(root))
    errors.extend(_errors_solution_descs(root))
    errors.extend(_errors_statement_interaction_layout(root))
    warnings: list[str] = []
    warnings.extend(_warnings_completeness(root))
    warnings.extend(_warnings_judging_time(root))
    return errors, warnings


def main() -> int:
    root = Path(os.environ.get("PROBLEM_ROOT", ".")).resolve()
    if not (root / "config").is_dir():
        print(f"ERROR: {root} does not look like a problem repo (no config/ directory)", file=sys.stderr)
        return 1

    errors, warnings = validate(root)
    status = _component_status(root)

    print(f"=== Problem Review: {root.name} ===")
    print()

    print("## Status")
    max_key = max(len(k) for k in status)
    for key, val in status.items():
        print(f"  {key:<{max_key}}  {val}")
    print()

    if warnings:
        print(f"## Warnings ({len(warnings)})")
        for w in warnings:
            print(f"  [!] {w}")
        print()

    if errors:
        print(f"## Errors ({len(errors)})")
        for e in errors:
            print(f"  [X] {e}")
        print()
        print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    print(f"RESULT: OK -- {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
