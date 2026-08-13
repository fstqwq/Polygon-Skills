import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REVIEW_PATH = Path(__file__).resolve().parents[1] / "review.py"
SPEC = importlib.util.spec_from_file_location("polygon_review_canonical", REVIEW_PATH)
assert SPEC is not None and SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class CanonicalSourceTests(unittest.TestCase):
    def _root(self, directory: str) -> Path:
        root = Path(directory)
        for relative in (
            "config",
            "solutions",
            "tests/manual",
            "tests/generator",
        ):
            (root / relative).mkdir(parents=True, exist_ok=True)
        (root / "config/problem.json").write_text(
            json.dumps(
                {
                    "time_limit_ms": 2000,
                    "memory_limit_mb": 1024,
                    "mode": "pass-fail",
                    "pass_limit": 1,
                }
            ),
            encoding="utf-8",
        )
        (root / "config/build.json").write_text(
            "{}\n",
            encoding="utf-8",
        )
        (root / "tests/spec.json").write_text(
            '{"tests": []}\n',
            encoding="utf-8",
        )
        return root

    def test_complete_empty_canonical_source_has_no_schema_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)

            errors, _warnings = review.validate(root)

        self.assertEqual(errors, [])

    def test_missing_fields_are_not_filled_by_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "config/problem.json").write_text(
                '{"mode": "pass-fail", "pass_limit": 1}\n',
                encoding="utf-8",
            )
            (root / "tests/spec.json").unlink()

            errors, _warnings = review.validate(root)

        joined = "\n".join(errors)
        self.assertIn("missing required field 'time_limit_ms'", joined)
        self.assertIn("tests/spec.json: file missing", joined)

    def test_solution_selection_is_explicit_and_descriptor_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            solution = root / "solutions/std.cpp"
            solution.write_text("int main(){}\n", encoding="utf-8")

            self.assertEqual(review._errors_solution_descs(root), [])

            build = json.loads(
                (root / "config/build.json").read_text(encoding="utf-8")
            )
            build["accepted_solution_source"] = ""
            (root / "config/build.json").write_text(
                json.dumps(build),
                encoding="utf-8",
            )

            build_errors = review._errors_build_json(root)

        self.assertTrue(
            any("accepted_solution_source must be" in item for item in build_errors)
        )

    def test_generator_command_resolves_source_without_build_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "generators").mkdir()
            (root / "generators/gen.cpp").write_text(
                "int main(){}\n",
                encoding="utf-8",
            )
            (root / "tests/generator/001.in").write_text(
                "gen 1\n",
                encoding="utf-8",
            )
            (root / "tests/spec.json").write_text(
                '{"tests":[{"id":"001","kind":"gen"}]}\n',
                encoding="utf-8",
            )

            errors = review._errors_spec_json(root)

        self.assertEqual(errors, [])

    def test_test_entries_require_canonical_types_and_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "tests/spec.json").write_text(
                json.dumps(
                    {
                        "tests": [
                            {"id": "1", "kind": "manual", "sample": "yes"}
                        ]
                    }
                ),
                encoding="utf-8",
            )

            errors = review._errors_spec_json(root)

        joined = "\n".join(errors)
        self.assertIn("id must be a 3-12 digit string", joined)
        self.assertIn("'sample' must be a boolean", joined)


if __name__ == "__main__":
    unittest.main()
