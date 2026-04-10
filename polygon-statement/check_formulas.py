#!/usr/bin/env python3
"""Cross-language formula consistency checker for problem statements.

Run from the problem repo root:

    python <skills>/polygon-statement/check_formulas.py

Compares the set of LaTeX math expressions across all languages in
statement-sections/. Reports formulas that appear in one language but
not another, per section file.

Also checks draft/statement.*.md files if present.

Exit code 0 = consistent, 1 = discrepancies found.
"""
from __future__ import annotations

import os
import re
import sys
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


def _extract_formulas(text: str) -> set[str]:
    """Extract all math expressions from text, normalized."""
    formulas: set[str] = set()
    # Extract math environments (align*, equation*, gather*)
    for m in MATH_ENV_RE.finditer(text):
        body = m.group(2)
        # Split align rows by \\ and treat each as a formula
        for row in re.split(r"\\\\", body):
            row = row.strip()
            if row:
                formulas.add(_normalize(row))
    # Remove math environments to avoid double-matching
    cleaned = MATH_ENV_RE.sub("", text)
    # Extract display math (before inline, since $$ contains $)
    for m in DISPLAY_MATH_RE.finditer(cleaned):
        formulas.add(_normalize(m.group(1)))
    cleaned = DISPLAY_MATH_RE.sub("", cleaned)
    # Extract inline math
    for m in INLINE_MATH_RE.finditer(cleaned):
        formulas.add(_normalize(m.group(1)))
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
        lang_formulas: dict[str, set[str]] = {}
        for lang in languages:
            path = sections_dir / lang / section
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            formulas = _extract_formulas(text)
            if formulas:
                lang_formulas[lang] = formulas

        if len(lang_formulas) < 2:
            continue

        # Compute the union and find per-language differences
        all_formulas = set()
        for f in lang_formulas.values():
            all_formulas |= f

        for lang, formulas in lang_formulas.items():
            missing = all_formulas - formulas
            if missing:
                others = [l for l in lang_formulas if l != lang and missing & lang_formulas[l]]
                for formula in sorted(missing):
                    present_in = [l for l in others if formula in lang_formulas[l]]
                    warnings.append(
                        f"statement-sections/{lang}/{section}: "
                        f"missing formula ${formula}$ (present in {', '.join(present_in)})"
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
    draft_formulas: dict[str, set[str]] = {}
    for draft in drafts:
        text = draft.read_text(encoding="utf-8", errors="replace")
        formulas = _extract_formulas(text)
        if formulas:
            draft_formulas[draft.name] = formulas

    if len(draft_formulas) < 2:
        return []

    all_formulas = set()
    for f in draft_formulas.values():
        all_formulas |= f

    for name, formulas in draft_formulas.items():
        missing = all_formulas - formulas
        if missing:
            for formula in sorted(missing):
                present_in = [n for n, f in draft_formulas.items() if n != name and formula in f]
                warnings.append(
                    f"draft/{name}: missing formula ${formula}$ (present in {', '.join(present_in)})"
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
