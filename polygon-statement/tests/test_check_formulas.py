import importlib.util
import tempfile
import unittest
from collections import Counter
from pathlib import Path


CHECKER_PATH = Path(__file__).resolve().parents[1] / "check_formulas.py"
SPEC = importlib.util.spec_from_file_location("polygon_check_formulas", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
check_formulas = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_formulas)


class FormulaConsistencyTests(unittest.TestCase):
    def test_extract_formulas_preserves_occurrences(self) -> None:
        formulas = check_formulas._extract_formulas("$i$ then $i$ and $j$")
        self.assertEqual(formulas, Counter({"i": 2, "j": 1}))

    def test_sections_report_formula_occurrence_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            english = root / "statement-sections" / "english"
            chinese = root / "statement-sections" / "chinese"
            english.mkdir(parents=True)
            chinese.mkdir(parents=True)
            (english / "input.tex").write_text(
                "Students $i$ and $j$.\n",
                encoding="utf-8",
            )
            (chinese / "input.tex").write_text(
                "第 $i$ 行描述学生 $i$ 和 $j$。\n",
                encoding="utf-8",
            )

            warnings = check_formulas._check_sections(root)

        self.assertEqual(
            warnings,
            [
                "statement-sections/english/input.tex: "
                "missing 1 occurrence of formula $i$ "
                "(counts: chinese=2, english=1)"
            ],
        )

    def test_sections_compare_language_with_no_formulas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            english = root / "statement-sections" / "english"
            chinese = root / "statement-sections" / "chinese"
            english.mkdir(parents=True)
            chinese.mkdir(parents=True)
            (english / "output.tex").write_text(
                "Output $x$.\n",
                encoding="utf-8",
            )
            (chinese / "output.tex").write_text(
                "输出答案。\n",
                encoding="utf-8",
            )

            warnings = check_formulas._check_sections(root)

        self.assertEqual(
            warnings,
            [
                "statement-sections/chinese/output.tex: "
                "missing 1 occurrence of formula $x$ "
                "(counts: chinese=0, english=1)"
            ],
        )

    def test_drafts_report_formula_occurrence_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            draft = root / "draft"
            draft.mkdir()
            (draft / "statement.english.md").write_text(
                "Use $i$.\n",
                encoding="utf-8",
            )
            (draft / "statement.chinese.md").write_text(
                "第 $i$ 行使用 $i$。\n",
                encoding="utf-8",
            )

            warnings = check_formulas._check_drafts(root)

        self.assertEqual(
            warnings,
            [
                "draft/statement.english.md: "
                "missing 1 occurrence of formula $i$ "
                "(counts: statement.chinese.md=2, statement.english.md=1)"
            ],
        )


if __name__ == "__main__":
    unittest.main()
