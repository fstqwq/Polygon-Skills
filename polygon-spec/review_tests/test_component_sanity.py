import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REVIEW_PATH = Path(__file__).resolve().parents[1] / "review.py"
SPEC = importlib.util.spec_from_file_location("polygon_review_components", REVIEW_PATH)
assert SPEC is not None and SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class ComponentSanityTests(unittest.TestCase):
    def _component_warnings(self, component: str, source: str) -> list[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_dir = root / f"{component}s"
            source_dir.mkdir()
            source_path = source_dir / f"{component}.cpp"
            source_path.write_text(source, encoding="utf-8")
            (root / "config").mkdir()
            (root / "config" / "build.json").write_text(
                json.dumps({f"{component}_source": source_path.relative_to(root).as_posix()}),
                encoding="utf-8",
            )
            return review._warnings_testlib_components(root)

    def test_accepts_bounded_validator_reads(self) -> None:
        warnings = self._component_warnings(
            "validator",
            '#include "testlib.h"\n'
            "int main(int argc, char* argv[]) {\n"
            "  registerValidation(argc, argv);\n"
            '  inf.readToken("[a-z]{1,20}", "s");\n'
            '  inf.readLong(0LL, 1\'000\'000\'000LL, "x");\n'
            '  ensuref(true, "1000000000"); // 1000000000\n'
            "  inf.readEof();\n"
            "}\n",
        )
        self.assertEqual(warnings, [])

    def test_warns_for_unbounded_validator_reads_and_large_decimal(self) -> None:
        warnings = self._component_warnings(
            "validator",
            '#include "testlib.h"\n'
            "int main(int argc, char* argv[]) {\n"
            "  registerValidation(argc, argv);\n"
            "  auto s = inf.readString();\n"
            '  auto t = inf.readToken("[a-z]+", "t");\n'
            '  int x = inf.readInt(1, 1000000000, "x");\n'
            "}\n",
        )
        joined = "\n".join(warnings)
        self.assertIn("readString() is unbounded", joined)
        self.assertIn("uses unsupported '+'", joined)
        self.assertIn("does not call inf.readEof()", joined)
        self.assertIn("decimal literal 1000000000 is 1e9", joined)

    def test_warns_for_checker_format_reads_and_unbounded_tokens(self) -> None:
        warnings = self._component_warnings(
            "checker",
            '#include "testlib.h"\n'
            "int main(int argc, char* argv[]) {\n"
            "  registerTestlibCmd(argc, argv);\n"
            "  ouf.readEoln();\n"
            "  auto token = ouf.readToken();\n"
            '  quitf(_ok, "correct");\n'
            "}\n",
        )
        joined = "\n".join(warnings)
        self.assertIn("checker uses readEoln()", joined)
        self.assertIn("readToken() is unbounded", joined)
        self.assertIn("message should start with 'ok'", joined)

    def test_skips_standard_checker_copy(self) -> None:
        standard_path = REVIEW_PATH.parent.parent / "polygon-checker" / "standard" / "wcmp.cpp"
        warnings = self._component_warnings(
            "checker", standard_path.read_text(encoding="utf-8")
        )
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
