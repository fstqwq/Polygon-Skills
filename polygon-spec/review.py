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
  - standard sentences   (high-confidence English/Chinese wording checks)
  - validator/checker     (lightweight testlib API sanity checks)
  - statement-assets/     (figure references and editable sources)
  - attachments/          (contestant-visible files)
  - completeness warnings (missing components, no samples, etc.)

Outputs a report with sections: Status, Warnings, Errors.
Exit code 0 = no errors, 1 = errors found.
No external dependencies required.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path, PurePosixPath

VALID_MODES = {"pass-fail", "interactive"}
VALID_KINDS = {"manual", "gen"}
VALID_EXPECTED = {
    "accepted",
    "wrong_answer",
    "tle_or_correct",
    "tle_or_re",
    "time_limit_exceeded",
    "run_time_error",
    "rejected",
    "unknown",
}
TEST_ID_RE = re.compile(r"^[0-9]{3,12}$")
SOLUTION_EXTENSIONS = {".cpp", ".cc", ".cxx", ".c++", ".py", ".java"}
CPP_EXTENSIONS = {".cpp", ".cc", ".cxx", ".c++"}
PROBLEM_KEYS = {
    "time_limit_ms",
    "memory_limit_mb",
    "mode",
    "pass_limit",
}
BUILD_SELECTIONS = {
    "accepted_solution_source": ("solutions", SOLUTION_EXTENSIONS, True),
    "validator_source": ("validators", CPP_EXTENSIONS, False),
    "checker_source": ("checkers", CPP_EXTENSIONS, False),
    "interactor_source": ("interactors", CPP_EXTENSIONS, False),
}
BUILD_REQUIRED_KEYS = {
    "generator_sources",
    "generator_runs",
    "generator_args",
    "validator_args",
    "checker_args",
    "compile_jobs",
    "validate_jobs",
    "solve_jobs",
    "run_jobs",
    "run_timeout_sec",
}
BUILD_KEYS = BUILD_REQUIRED_KEYS | set(BUILD_SELECTIONS)
SPEC_ENTRY_REQUIRED_KEYS = {"id", "kind", "sample"}
SPEC_ENTRY_KEYS = SPEC_ENTRY_REQUIRED_KEYS | {
    "sample_input",
    "sample_output",
    "sample_output_validate",
}
INCLUDEGRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
CPP_TOKEN_RE = re.compile(
    r'"(?:\\.|[^"\\])*"|'
    r"'(?:\\.|[^'\\])*'|"
    r"//[^\n]*|"
    r"/\*.*?\*/",
    re.DOTALL,
)
LONG_DECIMAL_RE = re.compile(r"(?<![A-Za-z0-9_'.])([1-9][0-9]{6,})(?:ULL|LLU|UL|LU|LL|L|U)?\b")


class _DuplicateJsonKey(ValueError):
    pass


def _json_object_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in pairs:
        if key in payload:
            raise _DuplicateJsonKey(key)
        payload[key] = value
    return payload


def _read_json_object(path: Path, label: str) -> tuple[dict[str, object] | None, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None, [f"{label}: must be UTF-8"]
    except OSError as exc:
        return None, [f"{label}: cannot read file -- {exc}"]
    if not text.strip():
        return None, [f"{label}: file is empty"]
    try:
        payload = json.loads(text, object_pairs_hook=_json_object_pairs)
    except _DuplicateJsonKey as exc:
        return None, [f"{label}: duplicate key '{exc.args[0]}'"]
    except json.JSONDecodeError as exc:
        return None, [
            f"{label}: invalid JSON at line {exc.lineno} column {exc.colno}"
        ]
    if not isinstance(payload, dict):
        return None, [f"{label}: must be a JSON object"]
    return payload, []

STANDARD_SENTENCE_RULES = [
    {
        "languages": {"english"},
        "sections": {"input.tex"},
        "candidate": re.compile(
            r"\b(?:The\s+)?first\s+line\s+(?:contains|has|gives|consists\s+of)\b[^.!?。！？]*[.!?]"
        ),
        "accepted": re.compile(r"The first line contains .+\.$"),
        "expected": "The first line contains an integer $n$ ($1 \\le n \\le 10^5$).",
    },
    {
        "languages": {"english"},
        "sections": {"input.tex"},
        "candidate": re.compile(
            r"\b(?:The\s+)?first\s+line\s+of\s+(?:each|every)\s+test\s+case\s+"
            r"(?:contains|has|gives|consists\s+of)\b[^.!?。！？]*[.!?]"
        ),
        "accepted": re.compile(r"The first line of each test case contains .+\.$"),
        "expected": (
            "The first line of each test case contains an integer $n$ "
            "($1 \\le n \\le 10^5$)."
        ),
    },
    {
        "languages": {"english"},
        "sections": {"output.tex"},
        "candidate": re.compile(
            r"\b(?:For\s+(?:each|every)|In\s+each)\s+test\s+case\s*,?\s*"
            r"(?:output|print)\b[^.!?。！？]*[.!?]",
            re.IGNORECASE,
        ),
        "accepted": re.compile(r"For each test case, output .+\.$"),
        "expected": (
            "For each test case, output an integer ~--- the answer to the problem."
        ),
    },
    {
        "languages": {"english"},
        "sections": {"input.tex"},
        "candidate": re.compile(
            r"\b(?:It\s+is\s+guaranteed\s+that\s+the\s+sum|"
            r"The\s+sum\b[^.!?。！？]*\b(?:is\s+guaranteed|does\s+not\s+exceed))"
            r"[^.!?。！？]*[.!?]",
            re.IGNORECASE,
        ),
        "accepted": re.compile(
            r"It is guaranteed that the sum of .+ over all test cases does not exceed .+\.$"
        ),
        "expected": (
            "It is guaranteed that the sum of $n$ over all test cases "
            "does not exceed $10^5$."
        ),
    },
    {
        "languages": {"english"},
        "sections": {"input.tex", "legend.tex"},
        "candidate": re.compile(
            r"\b(?:It\s+is\s+guaranteed\s+that\s+)?(?:the\s+)?"
            r"(?:given|input)\s+edges\s+(?:form|constitute|are)\s+a\s+tree[.!?]",
            re.IGNORECASE,
        ),
        "accepted": re.compile(r"It is guaranteed that the given edges form a tree\.$"),
        "expected": "It is guaranteed that the given edges form a tree.",
    },
    {
        "languages": {"english"},
        "sections": {"output.tex"},
        "candidate": re.compile(
            r"\bIf\s+there\s+(?:are|is)\s+multiple\b[^.!?。！？]*"
            r"\b(?:output|print)\b[^.!?。！？]*[.!?]",
            re.IGNORECASE,
        ),
        "accepted": re.compile(r"If there are multiple solutions, output any of them\.$"),
        "expected": "If there are multiple solutions, output any of them.",
    },
    {
        "languages": {"english"},
        "sections": {"output.tex"},
        "candidate": re.compile(
            r"\bIf\s+there\s+(?:is|are)\s+no\b[^.!?。！？]*"
            r"\b(?:output|print)\b[^.!?。！？]*-1[^.!?。！？]*[.!?]",
            re.IGNORECASE,
        ),
        "accepted": re.compile(r"If there is no solution, output \$-1\$\.$"),
        "expected": "If there is no solution, output $-1$.",
    },
    {
        "languages": {"english"},
        "sections": {"legend.tex", "input.tex", "output.tex", "interaction.tex"},
        "candidate": re.compile(r"\bas\s+follows?\b", re.IGNORECASE),
        "accepted": re.compile(r"as follows$"),
        "expected": "as follows",
    },
    {
        "languages": {"chinese"},
        "sections": {"input.tex"},
        "candidate": re.compile(r"(?<!的)第一行(?:包含|给出|有|为)[^。！？]*[。！？]"),
        "accepted": re.compile(r"第一行包含.+。$"),
        "expected": "第一行包含……。",
    },
    {
        "languages": {"chinese"},
        "sections": {"input.tex"},
        "candidate": re.compile(r"每组测试数据的第一行(?:包含|给出|有|为)[^。！？]*[。！？]"),
        "accepted": re.compile(r"每组测试数据的第一行包含.+。$"),
        "expected": "每组测试数据的第一行包含……。",
    },
    {
        "languages": {"chinese"},
        "sections": {"output.tex"},
        "candidate": re.compile(
            r"(?:对于)?每组测试数据[，,]?[^。！？]*?(?:输出|打印)[^。！？]*[。！？]"
        ),
        "accepted": re.compile(r"对于每组测试数据，输出.+。$"),
        "expected": "对于每组测试数据，输出……。",
    },
    {
        "languages": {"chinese"},
        "sections": {"input.tex"},
        "candidate": re.compile(
            r"(?:保证所有测试数据中[^。！？]*总和|"
            r"所有测试数据中[^。！？]*总和[^。！？]*(?:保证|不超过))[^。！？]*[。！？]"
        ),
        "accepted": re.compile(r"保证所有测试数据中.+的总和不超过.+。$"),
        "expected": "保证所有测试数据中……的总和不超过……。",
    },
    {
        "languages": {"chinese"},
        "sections": {"output.tex"},
        "candidate": re.compile(r"如果有多个[^。！？]*，?(?:输出|打印)[^。！？]*[。！？]"),
        "accepted": re.compile(r"如果有多个解，输出任意一个即可。$"),
        "expected": "如果有多个解，输出任意一个即可。",
    },
    {
        "languages": {"chinese"},
        "sections": {"output.tex"},
        "candidate": re.compile(r"如果无解[^。！？]*(?:输出|打印)[^。！？]*-1[^。！？]*[。！？]"),
        "accepted": re.compile(r"如果无解，输出 \$-1\$。$"),
        "expected": "如果无解，输出 $-1$。",
    },
]


def _errors_problem_json(root: Path) -> list[str]:
    path = root / "config" / "problem.json"
    if not path.exists():
        return ["config/problem.json: file missing"]
    data, read_errors = _read_json_object(path, "config/problem.json")
    if data is None:
        return read_errors
    errors: list[str] = []
    unknown = sorted(set(data) - PROBLEM_KEYS)
    missing = sorted(PROBLEM_KEYS - set(data))
    for key in unknown:
        errors.append(f"config/problem.json: unsupported field '{key}'")
    for key in missing:
        errors.append(f"config/problem.json: missing required field '{key}'")
    mode = data.get("mode")
    if mode is not None and mode not in VALID_MODES:
        errors.append(f"config/problem.json: invalid mode '{mode}' (expected {VALID_MODES})")
    pass_limit = data.get("pass_limit")
    if pass_limit is not None and (
        isinstance(pass_limit, bool)
        or not isinstance(pass_limit, int)
        or not 1 <= pass_limit <= 64
    ):
        errors.append(f"config/problem.json: pass_limit must be int 1..64, got {pass_limit!r}")
    tl = data.get("time_limit_ms")
    if tl is not None and (
        isinstance(tl, bool) or not isinstance(tl, int) or not 100 <= tl <= 30000
    ):
        errors.append(f"config/problem.json: time_limit_ms must be int 100..30000, got {tl!r}")
    ml = data.get("memory_limit_mb")
    if ml is not None and (
        isinstance(ml, bool) or not isinstance(ml, int) or not 1 <= ml <= 2048
    ):
        errors.append(f"config/problem.json: memory_limit_mb must be int 1..2048, got {ml!r}")
    return errors


def _check_source_path(
    root: Path,
    path_value: str,
    field: str,
    config_file: str,
    *,
    expected_root: str,
    extensions: set[str],
    direct_child: bool = False,
) -> list[str]:
    """Validate a repo-relative source path: format + existence."""
    errors: list[str] = []
    if not path_value or path_value != path_value.strip() or "\\" in path_value:
        errors.append(f"{config_file}: {field} must be a non-empty normalized path")
        return errors
    parts = path_value.split("/")
    path = PurePosixPath(path_value)
    if (
        path.is_absolute()
        or path.as_posix() != path_value
        or any(part in {"", ".", ".."} for part in parts)
        or parts[0] != expected_root
        or len(parts) < 2
    ):
        errors.append(f"{config_file}: {field} must be below {expected_root}/")
        return errors
    if direct_child and len(parts) != 2:
        errors.append(f"{config_file}: {field} must be directly below {expected_root}/")
        return errors
    if path.suffix.lower() not in extensions:
        errors.append(f"{config_file}: {field} has unsupported source extension")
        return errors
    source = root / path_value
    if source.is_symlink() or not source.is_file():
        errors.append(f"{config_file}: {field} references missing file '{path_value}'")
    return errors


def _errors_build_json(root: Path) -> list[str]:
    path = root / "config" / "build.json"
    if not path.exists():
        return ["config/build.json: file missing"]
    data, read_errors = _read_json_object(path, "config/build.json")
    if data is None:
        return read_errors
    errors: list[str] = []
    for key in sorted(set(data) - BUILD_KEYS):
        errors.append(f"config/build.json: unsupported field '{key}'")
    for key in sorted(BUILD_REQUIRED_KEYS - set(data)):
        errors.append(f"config/build.json: missing required field '{key}'")
    for field, (expected_root, extensions, direct_child) in BUILD_SELECTIONS.items():
        if field not in data:
            continue
        value = data[field]
        if not isinstance(value, str):
            errors.append(f"config/build.json: {field} must be a string")
            continue
        errors.extend(
            _check_source_path(
                root,
                value,
                field,
                "config/build.json",
                expected_root=expected_root,
                extensions=extensions,
                direct_child=direct_child,
            )
        )
    gen = data.get("generator_sources")
    if gen is not None and not isinstance(gen, list):
        errors.append("config/build.json: generator_sources must be an array")
    elif isinstance(gen, list):
        seen_generators: set[str] = set()
        for i, item in enumerate(gen):
            if not isinstance(item, str):
                errors.append(f"config/build.json: generator_sources[{i}] must be a string")
                continue
            errors.extend(
                _check_source_path(
                    root,
                    item,
                    f"generator_sources[{i}]",
                    "config/build.json",
                    expected_root="generators",
                    extensions=SOLUTION_EXTENSIONS,
                )
            )
            if item in seen_generators:
                errors.append(f"config/build.json: duplicate generator source '{item}'")
            seen_generators.add(item)
    for field in ("generator_args", "validator_args", "checker_args"):
        value = data.get(field)
        if value is not None and (
            not isinstance(value, list)
            or any(not isinstance(item, str) for item in value)
        ):
            errors.append(f"config/build.json: {field} must be an array of strings")
    for field, minimum, maximum in (
        ("generator_runs", 0, 4096),
        ("compile_jobs", 0, 16),
        ("validate_jobs", 0, 16),
        ("solve_jobs", 0, 16),
        ("run_jobs", 0, 16),
        ("run_timeout_sec", 1, 300),
    ):
        value = data.get(field)
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not minimum <= value <= maximum
        ):
            errors.append(
                f"config/build.json: {field} must be int {minimum}..{maximum}"
            )
    mode = _read_valid_problem_mode(root)
    checker_source = data.get("checker_source")
    interactor_source = data.get("interactor_source")
    if mode == "pass-fail":
        if interactor_source is not None:
            errors.append("config/build.json: interactor_source is invalid for pass-fail problems")
    elif mode == "interactive":
        if checker_source is not None:
            errors.append("config/build.json: checker_source is invalid for interactive problems")
    return errors


def _errors_spec_json(root: Path) -> list[str]:
    path = root / "tests" / "spec.json"
    if not path.exists():
        return ["tests/spec.json: file missing"]
    data, read_errors = _read_json_object(path, "tests/spec.json")
    if data is None:
        return read_errors
    errors: list[str] = []
    for key in sorted(set(data) - {"tests"}):
        errors.append(f"tests/spec.json: unsupported field '{key}'")
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
        for key in sorted(set(entry) - SPEC_ENTRY_KEYS):
            errors.append(f"{prefix}: unsupported field '{key}'")
        for key in sorted(SPEC_ENTRY_REQUIRED_KEYS - set(entry)):
            errors.append(f"{prefix}: missing '{key}'")
        tid = entry.get("id")
        if tid is not None and (
            not isinstance(tid, str) or not TEST_ID_RE.fullmatch(tid)
        ):
            errors.append(f"{prefix}: id must be a 3-12 digit string, got {tid!r}")
        elif isinstance(tid, str):
            if tid in seen_ids:
                errors.append(f"{prefix}: duplicate id '{tid}'")
            seen_ids.add(tid)
        kind = entry.get("kind")
        if kind is not None and kind not in VALID_KINDS:
            errors.append(f"{prefix}: invalid kind '{kind}' (expected {VALID_KINDS})")
        sample = entry.get("sample")
        if "sample" in entry and not isinstance(sample, bool):
            errors.append(f"{prefix}: 'sample' must be a boolean")
        for field in ("sample_input", "sample_output"):
            if field in entry and not isinstance(entry[field], str):
                errors.append(f"{prefix}: '{field}' must be a string")
        if "sample_output_validate" in entry and not isinstance(
            entry["sample_output_validate"], bool
        ):
            errors.append(f"{prefix}: 'sample_output_validate' must be a boolean")
        if kind == "manual" and isinstance(tid, str) and TEST_ID_RE.fullmatch(tid):
            manual_path = root / "tests" / "manual" / f"{tid}.in"
            if manual_path.is_symlink() or not manual_path.is_file():
                errors.append(f"{prefix}: manual test file 'tests/manual/{tid}.in' missing")
            else:
                try:
                    manual_text = manual_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    errors.append(f"{prefix}: manual test input must be UTF-8")
                except OSError as exc:
                    errors.append(f"{prefix}: cannot read manual test input -- {exc}")
                else:
                    if "\r" in manual_text:
                        errors.append(f"{prefix}: manual test input must use LF newlines")
                    if not manual_text.endswith("\n") or manual_text.endswith("\n\n"):
                        errors.append(
                            f"{prefix}: manual test input must end with exactly one newline"
                        )
                    if any(line.endswith((" ", "\t")) for line in manual_text.splitlines()):
                        errors.append(
                            f"{prefix}: manual test input lines must not have trailing whitespace"
                        )
        if kind == "gen" and isinstance(tid, str) and TEST_ID_RE.fullmatch(tid):
            gen_path = root / "tests" / "generator" / f"{tid}.in"
            if gen_path.is_symlink() or not gen_path.is_file():
                errors.append(f"{prefix}: generator payload file 'tests/generator/{tid}.in' missing")
            else:
                try:
                    command = gen_path.read_text(encoding="utf-8").strip()
                    tokens = shlex.split(command, posix=True)
                except UnicodeDecodeError:
                    errors.append(f"{prefix}: generator payload must be UTF-8")
                    tokens = []
                except (OSError, ValueError) as exc:
                    errors.append(f"{prefix}: invalid generator command -- {exc}")
                    tokens = []
                if not tokens:
                    errors.append(f"{prefix}: generator command is required")
                else:
                    build_path = root / "config" / "build.json"
                    try:
                        build = json.loads(build_path.read_text(encoding="utf-8"))
                    except (json.JSONDecodeError, OSError):
                        build = {}
                    configured = (
                        build.get("generator_sources", [])
                        if isinstance(build, dict)
                        else []
                    )
                    if isinstance(configured, list):
                        matches = _generator_source_matches(
                            tokens[0],
                            [item for item in configured if isinstance(item, str)],
                        )
                        if not matches:
                            errors.append(
                                f"{prefix}: generator source is not selected: {tokens[0]}"
                            )
                        elif len(matches) > 1:
                            errors.append(
                                f"{prefix}: generator source is ambiguous: {tokens[0]}"
                            )
    answers_dir = root / "tests" / "answers"
    if answers_dir.exists():
        errors.append("tests/answers/: committed answer files are not allowed")
    tests_dir = root / "tests"
    if tests_dir.is_dir():
        for ans_path in sorted(tests_dir.rglob("*.ans")):
            rel = ans_path.relative_to(root).as_posix()
            errors.append(f"{rel}: committed answer files are not allowed")
    return errors


def _generator_source_matches(token: str, configured: list[str]) -> list[str]:
    raw = token.replace("\\", "/")
    while raw.startswith("./"):
        raw = raw[2:]
    if not raw or any(part in {"", ".", ".."} for part in raw.split("/")):
        return []
    token_path = PurePosixPath(raw)
    matches: list[str] = []
    for source in configured:
        source_path = PurePosixPath(source)
        without_root = source.removeprefix("generators/")
        suffix_length = len(source_path.suffix)
        source_without_suffix = source[:-suffix_length] if suffix_length else source
        without_root_suffix = (
            without_root[:-suffix_length] if suffix_length else without_root
        )
        if raw in {source, without_root, source_without_suffix, without_root_suffix}:
            matches.append(source)
        elif "/" not in raw and (
            token_path.name == source_path.name
            or (not token_path.suffix and token_path.name == source_path.stem)
        ):
            matches.append(source)
    return list(dict.fromkeys(matches))


def _errors_solution_descs(root: Path) -> list[str]:
    solutions_dir = root / "solutions"
    if not solutions_dir.is_dir():
        return []
    errors: list[str] = []
    source_names = {
        entry.name
        for entry in solutions_dir.iterdir()
        if entry.is_file() and not entry.is_symlink()
        and entry.suffix.lower() in SOLUTION_EXTENSIONS
    }
    for source_name in sorted(source_names):
        descriptor = solutions_dir / f"{source_name}.desc"
        if not descriptor.is_file() or descriptor.is_symlink():
            errors.append(f"solutions/{source_name}.desc: required descriptor is missing")
    for entry in sorted(solutions_dir.iterdir()):
        if not entry.name.endswith(".desc") or not entry.is_file() or entry.is_symlink():
            continue
        rel = f"solutions/{entry.name}"
        try:
            text = entry.read_text(encoding="utf-8")
        except OSError:
            errors.append(f"{rel}: unreadable")
            continue
        expected_value: str | None = None
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line:
                continue
            if ":" not in line:
                errors.append(f"{rel}:{line_number}: expected 'key: value'")
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key == "expected":
                if expected_value is not None:
                    errors.append(f"{rel}:{line_number}: duplicate expected field")
                elif value not in VALID_EXPECTED:
                    errors.append(f"{rel}: invalid expected value '{value}' (valid: {VALID_EXPECTED})")
                else:
                    expected_value = value
            elif key == "note":
                if not value:
                    errors.append(f"{rel}:{line_number}: note must not be empty")
            else:
                errors.append(f"{rel}:{line_number}: unsupported key '{key}'")
        if expected_value is None:
            errors.append(f"{rel}: missing 'expected:' line")
        source_name = entry.name[: -len(".desc")]
        source_path = solutions_dir / source_name
        if not source_path.exists():
            errors.append(f"{rel}: source file 'solutions/{source_name}' missing")
    build_path = root / "config" / "build.json"
    try:
        build = json.loads(build_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        build = {}
    accepted = build.get("accepted_solution_source") if isinstance(build, dict) else None
    if isinstance(accepted, str):
        descriptor = solutions_dir / f"{Path(accepted).name}.desc"
        try:
            descriptor_text = descriptor.read_text(encoding="utf-8")
        except OSError:
            descriptor_text = ""
        if not any(
            line.strip() == "expected: accepted"
            for line in descriptor_text.splitlines()
        ):
            errors.append(
                "config/build.json: accepted_solution_source descriptor must use expected: accepted"
            )
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


def _warnings_package_assets(root: Path) -> list[str]:
    """Warn about misplaced or incomplete statement and contestant assets."""
    warnings: list[str] = []
    assets_dir = root / "statement-assets"

    if assets_dir.is_dir():
        for pdf_path in sorted(assets_dir.rglob("*.pdf")):
            source_path = pdf_path.with_suffix(".tex")
            if not source_path.exists():
                rel_pdf = pdf_path.relative_to(root).as_posix()
                rel_source = source_path.relative_to(root).as_posix()
                warnings.append(f"{rel_pdf}: missing editable source '{rel_source}'")

        for source_path in sorted(assets_dir.rglob("*.tex")):
            pdf_path = source_path.with_suffix(".pdf")
            if not pdf_path.exists():
                rel_source = source_path.relative_to(root).as_posix()
                rel_pdf = pdf_path.relative_to(root).as_posix()
                warnings.append(f"{rel_source}: missing rendered asset '{rel_pdf}'")

    sections_dir = root / "statement-sections"
    if sections_dir.is_dir():
        for section_path in sorted(sections_dir.rglob("*.tex")):
            try:
                text = section_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for match in INCLUDEGRAPHICS_RE.finditer(text):
                asset_name = match.group(1).strip().replace("\\", "/")
                if asset_name.startswith("statement-assets/"):
                    rel_section = section_path.relative_to(root).as_posix()
                    warnings.append(
                        f"{rel_section}: reference '{asset_name}' should omit the statement-assets/ prefix"
                    )
                    asset_name = asset_name[len("statement-assets/"):]
                asset_path = assets_dir / asset_name
                candidates = [asset_path] if asset_path.suffix else [
                    asset_path.with_suffix(ext) for ext in (".pdf", ".png", ".jpg", ".jpeg")
                ]
                if not any(candidate.exists() for candidate in candidates):
                    rel_section = section_path.relative_to(root).as_posix()
                    warnings.append(
                        f"{rel_section}: statement asset '{match.group(1)}' is missing from statement-assets/"
                    )

    draft_dir = root / "draft"
    if draft_dir.is_dir():
        for source_path in sorted(draft_dir.rglob("*.tex")):
            try:
                text = source_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "\\begin{tikzpicture}" in text:
                rel_source = source_path.relative_to(root).as_posix()
                warnings.append(
                    f"{rel_source}: TikZ figure source belongs under statement-assets/ beside its rendered PDF"
                )

    if _read_valid_problem_mode(root) == "interactive":
        testing_tool = root / "attachments" / "testing_tool.py"
        if not testing_tool.exists():
            warnings.append(
                "attachments/testing_tool.py: missing contestant testing tool for interactive problem"
            )

    return warnings


def _collapse_statement_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _warnings_standard_sentences(root: Path) -> list[str]:
    """Warn about high-confidence deviations from the standard sentence templates."""
    sections_dir = root / "statement-sections"
    if not sections_dir.is_dir():
        return []

    warnings: list[str] = []
    for language_dir in sorted(sections_dir.iterdir()):
        if not language_dir.is_dir() or language_dir.is_symlink():
            continue
        language = language_dir.name.lower()
        for section_path in sorted(language_dir.glob("*.tex")):
            applicable_rules = [
                rule
                for rule in STANDARD_SENTENCE_RULES
                if language in rule["languages"] and section_path.name in rule["sections"]
            ]
            if not applicable_rules:
                continue
            try:
                raw_text = section_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            text = re.sub(r"(?<!\\)%[^\n]*", "", raw_text)
            rel_path = section_path.relative_to(root).as_posix()
            seen: set[tuple[int, str]] = set()
            for rule in applicable_rules:
                for match in rule["candidate"].finditer(text):
                    candidate = _collapse_statement_whitespace(match.group(0))
                    if rule["accepted"].fullmatch(candidate):
                        continue
                    line = text.count("\n", 0, match.start()) + 1
                    key = (line, rule["expected"])
                    if key in seen:
                        continue
                    seen.add(key)
                    display = candidate if len(candidate) <= 100 else candidate[:97] + "..."
                    warnings.append(
                        f"{rel_path}:{line}: non-standard sentence {display!r}; "
                        f"use '{rule['expected']}'"
                    )
    return warnings


def _mask_cpp_comments(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.startswith("//") or token.startswith("/*"):
            return "".join("\n" if char == "\n" else " " for char in token)
        return token

    return CPP_TOKEN_RE.sub(replace, text)


def _mask_cpp_strings(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.startswith('"') or token.startswith("'"):
            return "".join("\n" if char == "\n" else " " for char in token)
        return token

    return CPP_TOKEN_RE.sub(replace, text)


def _configured_component_sources(root: Path) -> list[tuple[str, Path]]:
    build_path = root / "config" / "build.json"
    try:
        build = json.loads(build_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(build, dict):
        return []

    sources: list[tuple[str, Path]] = []
    for component, field in [
        ("validator", "validator_source"),
        ("checker", "checker_source"),
    ]:
        value = build.get(field)
        if not isinstance(value, str) or not value:
            continue
        source_path = root / value
        if source_path.is_file():
            sources.append((component, source_path))
    return sources


def _is_standard_checker_copy(source_text: str) -> bool:
    standard_dir = Path(__file__).resolve().parent.parent / "polygon-checker" / "standard"
    normalized_source = source_text.replace("\r\n", "\n").strip()
    if not standard_dir.is_dir():
        return False
    for standard_path in standard_dir.glob("*.cpp"):
        try:
            standard_text = standard_path.read_text(encoding="utf-8")
        except OSError:
            continue
        if normalized_source == standard_text.replace("\r\n", "\n").strip():
            return True
    return False


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _scientific_notation(digits: str) -> str:
    tail = digits[1:].rstrip("0")
    coefficient = digits[0] + (f".{tail}" if tail else "")
    return f"{coefficient}e{len(digits) - 1}"


def _warnings_long_decimal_literals(root: Path, source_path: Path, text: str) -> list[str]:
    code = _mask_cpp_strings(_mask_cpp_comments(text))
    rel_path = source_path.relative_to(root).as_posix()
    warnings: list[str] = []
    seen: set[tuple[int, str]] = set()
    for match in LONG_DECIMAL_RE.finditer(code):
        digits = match.group(1)
        if not re.search(r"0{5,}$", digits):
            continue
        line = _line_number(code, match.start())
        key = (line, digits)
        if key in seen:
            continue
        seen.add(key)
        notation = _scientific_notation(digits)
        warnings.append(
            f"{rel_path}:{line}: decimal literal {digits} is {notation}; "
            "consider a named constant or digit separators"
        )
    return warnings


def _warnings_testlib_patterns(root: Path, source_path: Path, text: str) -> list[str]:
    code = _mask_cpp_comments(text)
    rel_path = source_path.relative_to(root).as_posix()
    warnings: list[str] = []
    call_re = re.compile(
        r"\b(?:inf|ouf|ans|in)\s*\.\s*(readToken|readWord|readString)\s*"
        r'\(\s*"((?:\\.|[^"\\])*)"'
    )
    for match in call_re.finditer(code):
        method = match.group(1)
        pattern = match.group(2)
        line = _line_number(code, match.start())
        if re.search(r"(?<!\\)\+", pattern):
            warnings.append(
                f"{rel_path}:{line}: {method}() pattern {pattern!r} uses unsupported '+'; "
                "use a testlib quantifier such as {1,}"
            )
        if any(token in pattern for token in ("(?=", "(?!", "(?<=", "(?<!")):
            warnings.append(
                f"{rel_path}:{line}: {method}() pattern {pattern!r} uses unsupported lookaround"
            )
        if re.search(r"(?<!\\) ", pattern):
            warnings.append(
                f"{rel_path}:{line}: {method}() pattern {pattern!r} contains an unescaped "
                r"space, which testlib ignores; use \\ "
            )
    return warnings


def _warnings_validator_source(root: Path, source_path: Path, text: str) -> list[str]:
    code = _mask_cpp_comments(text)
    rel_path = source_path.relative_to(root).as_posix()
    warnings: list[str] = []

    if not re.search(r'#\s*include\s*[<"]testlib\.h[>"]', code):
        warnings.append(f"{rel_path}: validator does not include testlib.h")
    if not re.search(r"\bregisterValidation\s*\(", code):
        warnings.append(f"{rel_path}: validator does not call registerValidation(argc, argv)")
    if not re.search(r"\binf\s*\.\s*readEof\s*\(\s*\)", code):
        warnings.append(f"{rel_path}: validator does not call inf.readEof()")

    for match in re.finditer(
        r"\binf\s*\.\s*(readToken|readWord|readString)\s*\(\s*\)", code
    ):
        line = _line_number(code, match.start())
        warnings.append(
            f"{rel_path}:{line}: {match.group(1)}() is unbounded in a validator; "
            "pass a lightweight testlib pattern and a stable variable name"
        )

    for match in re.finditer(
        r"\binf\s*\.\s*(readInt|readLong|readDouble|readReal)\s*\(\s*\)", code
    ):
        line = _line_number(code, match.start())
        warnings.append(
            f"{rel_path}:{line}: {match.group(1)}() is unbounded in a validator; "
            "pass explicit minimum and maximum values"
        )

    for match in re.finditer(
        r"\binf\s*\.\s*read(?:Int|Long|Double|Real|Token|Word|String)s?\s*"
        r"\([^;]*?\bformat\s*\(",
        code,
    ):
        line = _line_number(code, match.start())
        warnings.append(
            f"{rel_path}:{line}: generated read variable name fragments boundary logs; "
            "use a stable literal name"
        )

    for match in re.finditer(
        r"\binf\s*\.\s*readLong\s*\(\s*(-?[0-9]+)\s*,\s*(-?[0-9]+)", code
    ):
        line = _line_number(code, match.start())
        warnings.append(
            f"{rel_path}:{line}: readLong bounds should use the LL suffix"
        )

    return warnings


def _warnings_checker_source(root: Path, source_path: Path, text: str) -> list[str]:
    if _is_standard_checker_copy(text):
        return []

    code = _mask_cpp_comments(text)
    rel_path = source_path.relative_to(root).as_posix()
    warnings: list[str] = []

    if not re.search(r'#\s*include\s*[<"]testlib\.h[>"]', code):
        warnings.append(f"{rel_path}: checker does not include testlib.h")
    if not re.search(r"\bregisterTestlibCmd\s*\(", code):
        warnings.append(f"{rel_path}: checker does not call registerTestlibCmd(argc, argv)")

    for match in re.finditer(
        r"\b(?:ouf|ans|in)\s*\.\s*(readSpace|readEoln|readEof)\s*\(", code
    ):
        line = _line_number(code, match.start())
        warnings.append(
            f"{rel_path}:{line}: checker uses {match.group(1)}(); "
            "validate answer semantics with token-based reads instead of exact whitespace"
        )

    for match in re.finditer(r"\b(?:ouf|ans|in)\s*\.\s*(readLine|readString)\s*\(", code):
        line = _line_number(code, match.start())
        warnings.append(
            f"{rel_path}:{line}: checker uses {match.group(1)}(); prefer readToken() "
            "unless line boundaries are part of the answer semantics; if intentional, "
            "pass a bounded testlib pattern"
        )

    for match in re.finditer(
        r"\b(?:ouf|ans|in)\s*\.\s*"
        r"(readToken|readWord|readInt|readLong|readDouble|readReal)\s*\(\s*\)",
        code,
    ):
        line = _line_number(code, match.start())
        warnings.append(
            f"{rel_path}:{line}: {match.group(1)}() is unbounded for an answer stream; "
            "pass explicit bounds or a lightweight testlib pattern"
        )

    for match in re.finditer(r"\bquitf\s*\(\s*_pe\b", code):
        line = _line_number(code, match.start())
        warnings.append(f"{rel_path}:{line}: checker must not use the _pe verdict")

    for match in re.finditer(
        r'\bquitf\s*\(\s*_ok\s*,\s*"((?:\\.|[^"\\])*)"', code
    ):
        if match.group(1).lower().startswith("ok"):
            continue
        line = _line_number(code, match.start())
        warnings.append(
            f"{rel_path}:{line}: quitf(_ok, ...) message should start with 'ok'"
        )

    return warnings


def _warnings_testlib_components(root: Path) -> list[str]:
    warnings: list[str] = []
    for component, source_path in _configured_component_sources(root):
        try:
            text = source_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if component == "validator":
            warnings.extend(_warnings_validator_source(root, source_path, text))
        else:
            warnings.extend(_warnings_checker_source(root, source_path, text))
        if component != "checker" or not _is_standard_checker_copy(text):
            warnings.extend(_warnings_testlib_patterns(root, source_path, text))
            warnings.extend(_warnings_long_decimal_literals(root, source_path, text))
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
    statement_assets_dir = root / "statement-assets"
    if statement_assets_dir.is_dir():
        files = [
            f.relative_to(statement_assets_dir).as_posix()
            for f in sorted(statement_assets_dir.rglob("*"))
            if f.is_file() and not f.name.startswith(".")
        ]
        status["statement_assets"] = ", ".join(files) if files else "empty"
    else:
        status["statement_assets"] = "none"

    if attach_dir.is_dir():
        files = [
            f.relative_to(attach_dir).as_posix()
            for f in sorted(attach_dir.rglob("*"))
            if f.is_file() and not f.name.startswith(".")
        ]
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
    warnings.extend(_warnings_package_assets(root))
    warnings.extend(_warnings_standard_sentences(root))
    warnings.extend(_warnings_testlib_components(root))
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
