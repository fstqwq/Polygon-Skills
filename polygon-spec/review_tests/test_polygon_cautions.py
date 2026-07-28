import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REVIEW_PATH = Path(__file__).resolve().parents[1] / "review.py"
SPEC = importlib.util.spec_from_file_location("polygon_review_cautions", REVIEW_PATH)
assert SPEC is not None and SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class PolygonCautionTests(unittest.TestCase):
    def test_warns_for_multiple_random_calls_in_one_output_expression(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generator = root / "generators" / "gen_random.cpp"
            generator.parent.mkdir()
            generator.write_text(
                '#include "testlib.h"\n'
                "int main() {\n"
                '  cout << rnd.next(1, 10) << " " << rnd.next(1, 10) << "\\n";\n'
                "}\n",
                encoding="utf-8",
            )
            (root / "config").mkdir()
            (root / "config" / "build.json").write_text(
                json.dumps({"generator_sources": ["generators/gen_random.cpp"]}),
                encoding="utf-8",
            )

            warnings = review._warnings_generator_sources(root)

        self.assertEqual(len(warnings), 1)
        self.assertIn("unspecified evaluation order", warnings[0])

    def test_accepts_random_calls_stored_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            generator = root / "generators" / "gen_random.cpp"
            generator.parent.mkdir()
            generator.write_text(
                '#include "testlib.h"\n'
                "int main() {\n"
                "  int x = rnd.next(1, 10);\n"
                "  int y = rnd.next(1, 10);\n"
                '  cout << x << " " << y << "\\n";\n'
                "}\n",
                encoding="utf-8",
            )
            (root / "config").mkdir()
            (root / "config" / "build.json").write_text(
                json.dumps({"generator_sources": ["generators/gen_random.cpp"]}),
                encoding="utf-8",
            )

            warnings = review._warnings_generator_sources(root)

        self.assertEqual(warnings, [])

    def test_warns_for_missing_statement_font_substrings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            english = root / "statement-sections" / "english"
            chinese = root / "statement-sections" / "chinese"
            english.mkdir(parents=True)
            chinese.mkdir(parents=True)
            (english / "input.tex").write_text(
                "The first line contains a string.\n",
                encoding="utf-8",
            )
            (chinese / "legend.tex").write_text(
                "这是题目描述。\n",
                encoding="utf-8",
            )

            warnings = review._warnings_statement_typography(root)

        joined = "\n".join(warnings)
        self.assertIn("lack monospaced font substrings", joined)
        self.assertIn("lack bold font substrings", joined)

    def test_accepts_statement_font_substrings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            english = root / "statement-sections" / "english"
            chinese = root / "statement-sections" / "chinese"
            english.mkdir(parents=True)
            chinese.mkdir(parents=True)
            (english / "input.tex").write_text(
                r"The token is \texttt{YES}." "\n",
                encoding="utf-8",
            )
            (chinese / "legend.tex").write_text(
                r"答案必须是 \textbf{最小值}。" "\n",
                encoding="utf-8",
            )

            warnings = review._warnings_statement_typography(root)

        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
