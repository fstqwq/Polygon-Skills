import importlib.util
import tempfile
import unittest
from pathlib import Path


REVIEW_PATH = Path(__file__).resolve().parents[1] / "review.py"
SPEC = importlib.util.spec_from_file_location("polygon_review", REVIEW_PATH)
assert SPEC is not None and SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class StandardSentenceTests(unittest.TestCase):
    def _warnings(self, language: str, section: str, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "statement-sections" / language / section
            target.parent.mkdir(parents=True)
            target.write_text(text, encoding="utf-8")
            return review._warnings_standard_sentences(root)

    def test_accepts_standard_english_with_problem_specific_values(self) -> None:
        warnings = self._warnings(
            "english",
            "input.tex",
            "The first line contains two integers $x$ and $y$ "
            "($-10^9 \\le x, y \\le 10^9$).\n"
            "It is guaranteed that the sum of $x$ over all test cases "
            "does not exceed $2 \\times 10^5$.\n",
        )
        self.assertEqual(warnings, [])

    def test_warns_for_nonstandard_english(self) -> None:
        warnings = self._warnings(
            "english",
            "output.tex",
            "For every test case, print the answer.\n"
            "If there are multiple answers, print any one of them.\n",
        )
        self.assertEqual(len(warnings), 2)
        self.assertIn("For each test case, output an integer ~---", warnings[0])
        self.assertIn("If there are multiple solutions, output any of them.", warnings[1])

    def test_checks_chinese_wording(self) -> None:
        warnings = self._warnings(
            "chinese",
            "output.tex",
            "对于每组测试数据，输出一个整数，表示答案。\n"
            "如果有多个答案，打印任意一个。\n",
        )
        self.assertEqual(len(warnings), 1)
        self.assertIn("如果有多个解，输出任意一个即可。", warnings[0])

    def test_ignores_unrelated_prose_and_comments(self) -> None:
        warnings = self._warnings(
            "english",
            "legend.tex",
            "Alice prints a map before the contest.\n"
            "% The rules are as follow.\n",
        )
        self.assertEqual(warnings, [])

    def test_standard_sentence_warnings_are_in_validate_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "config").mkdir()
            (root / "config" / "problem.json").write_text(
                '{"mode":"pass-fail","pass_limit":1}', encoding="utf-8"
            )
            target = root / "statement-sections" / "english" / "output.tex"
            target.parent.mkdir(parents=True)
            target.write_text("For every test case, print the answer.\n", encoding="utf-8")

            _, warnings = review.validate(root)

        self.assertTrue(any("non-standard sentence" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
