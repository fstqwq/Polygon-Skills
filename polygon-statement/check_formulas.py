#!/usr/bin/env python3
"""Cross-language formula consistency checker for problem statements.

Run from the problem repo root:

    python <skills>/polygon-statement/check_formulas.py

Compares LaTeX math expression occurrence counts across all languages
in statement-sections/. Reports missing occurrences per section file.

Also checks draft/statement.*.md files if present.

Exit code 0 = consistent, 1 = discrepancies found.
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter
from pathlib import Path

# Match $...$ (non-greedy, single-line) but skip \$ escapes
INLINE_MATH_RE = re.compile(r"(?<!\\)\$([^$]+?)\$")
# Match $$...$$ (display math)
DISPLAY_MATH_RE = re.compile(r"(?<!\\)\$\$(.+?)\$\$", re.DOTALL)
# Match \begin{env}...\end{env} for math environments
MATH_ENV_RE = re.compile(
    r"\\begin\{(align\*?|equation\*?|gather\*?)\}(.+?)\\end\{\1\}",
    re.DOTALL,
)


def _extract_formulas(text: str) -> Counter[str]:
    """Extract all normalized math expressions while preserving occurrences."""
    formulas: Counter[str] = Counter()
    # Extract math environments (align*, equation*, gather*)
    for m in MATH_ENV_RE.finditer(text):
        body = m.group(2)
        # Split align rows by \\ and treat each as a formula
        for row in re.split(r"\\\\", body):
            row = row.strip()
            if row:
                formulas[_normalize(row)] += 1
    # Remove math environments to avoid double-matching
    cleaned = MATH_ENV_RE.sub("", text)
    # Extract display math (before inline, since $$ contains $)
    for m in DISPLAY_MATH_RE.finditer(cleaned):
        formulas[_normalize(m.group(1))] += 1
    cleaned = DISPLAY_MATH_RE.sub("", cleaned)
    # Extract inline math
    for m in INLINE_MATH_RE.finditer(cleaned):
        formulas[_normalize(m.group(1))] += 1
    return formulas


def _normalize(formula: str) -> str:
    """Normalize whitespace in a formula for comparison."""
    return " ".join(formula.split())


def _check_sections(root: Path) -> list[str]:
    """Compare formulas across languages in statement-sections/."""
    sections_dir = root / "statement-sections"
    if not sections_dir.is_dir():
        return []

    languages = sorted(
        d.name for d in sections_dir.iterdir()
        if d.is_dir() and not d.is_symlink()
    )
    if len(languages) < 2:
        return []

    warnings: list[str] = []

    # Collect formulas per (language, section)
    section_names = {"legend.tex", "input.tex", "output.tex", "notes.tex", "interaction.tex"}
    for section in sorted(section_names):
        lang_formulas: dict[str, Counter[str]] = {}
        for lang in languages:
            path = sections_dir / lang / section
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            lang_formulas[lang] = _extract_formulas(text)

        if len(lang_formulas) < 2:
            continue

        # Compute the union and find per-language differences
        all_formulas: Counter[str] = Counter()
        for f in lang_formulas.values():
            all_formulas |= f

        for lang, formulas in lang_formulas.items():
            missing = all_formulas - formulas
            if missing:
                for formula, count in sorted(missing.items()):
                    counts = ", ".join(
                        f"{other}={lang_formulas[other][formula]}"
                        for other in languages
                        if other in lang_formulas
                    )
                    occurrence = "occurrence" if count == 1 else "occurrences"
                    warnings.append(
                        f"statement-sections/{lang}/{section}: "
                        f"missing {count} {occurrence} of formula ${formula}$ "
                        f"(counts: {counts})"
                    )
    return warnings


def _check_drafts(root: Path) -> list[str]:
    """Compare formulas across draft/statement.*.md files."""
    draft_dir = root / "draft"
    if not draft_dir.is_dir():
        return []

    drafts = sorted(
        f for f in draft_dir.iterdir()
        if f.name.startswith("statement.") and f.name.endswith(".md") and f.is_file()
    )
    if len(drafts) < 2:
        return []

    warnings: list[str] = []
    draft_formulas: dict[str, Counter[str]] = {}
    for draft in drafts:
        text = draft.read_text(encoding="utf-8", errors="replace")
        draft_formulas[draft.name] = _extract_formulas(text)

    if len(draft_formulas) < 2:
        return []

    all_formulas: Counter[str] = Counter()
    for f in draft_formulas.values():
        all_formulas |= f

    for name, formulas in draft_formulas.items():
        missing = all_formulas - formulas
        if missing:
            for formula, count in sorted(missing.items()):
                counts = ", ".join(
                    f"{draft_name}={draft_formulas[draft_name][formula]}"
                    for draft_name in sorted(draft_formulas)
                )
                occurrence = "occurrence" if count == 1 else "occurrences"
                warnings.append(
                    f"draft/{name}: missing {count} {occurrence} of formula "
                    f"${formula}$ (counts: {counts})"
                )
    return warnings


def main() -> int:
    root = Path(os.environ.get("PROBLEM_ROOT", ".")).resolve()
    warnings: list[str] = []
    warnings.extend(_check_sections(root))
    warnings.extend(_check_drafts(root))

    if not warnings:
        print("OK — formulas are consistent across all languages")
        return 0

    for w in warnings:
        print(f"  MISMATCH: {w}", file=sys.stderr)
    print(f"\n{len(warnings)} formula mismatch(es) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
