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

    def test_generator_command_requires_build_selection(self) -> None:
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

            unselected_errors = review._errors_spec_json(root)
            build_path = root / "config/build.json"
            build_path.write_text(
                '{"generator_sources":["generators/gen.cpp"]}\n',
                encoding="utf-8",
            )
            selected_errors = review._errors_spec_json(root)

        self.assertTrue(
            any("generator source is not selected" in item for item in unselected_errors)
        )
        self.assertEqual(selected_errors, [])

    def test_generator_sources_is_optional_and_strict_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            self.assertEqual(review._errors_build_json(root), [])
            (root / "config/build.json").write_text(
                '{"generator_sources":"generators/gen.cpp"}\n',
                encoding="utf-8",
            )

            errors = review._errors_build_json(root)

        self.assertIn(
            "config/build.json: generator_sources must be an array",
            errors,
        )

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

    def test_structured_samples_follow_the_application_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            for test_id in ("001", "002"):
                (root / "tests/manual" / f"{test_id}.in").write_text(
                    f"judge input {test_id}\n",
                    encoding="utf-8",
                )
            (root / "tests/spec.json").write_text(
                json.dumps(
                    {
                        "tests": [
                            {
                                "id": "001",
                                "kind": "manual",
                                "sample": True,
                                "sample_json": {
                                    "presentation": "pair",
                                    "passes": [
                                        {"input": "first\n", "output": "one\n"},
                                        {
                                            "number": 2,
                                            "input": "second\n",
                                            "output": "two\n",
                                        },
                                    ],
                                },
                            },
                            {
                                "id": "002",
                                "kind": "manual",
                                "sample": True,
                                "sample_json": {
                                    "presentation": "interaction",
                                    "passes": [
                                        {
                                            "events": [
                                                {
                                                    "source": "interactor",
                                                    "content": "问题\n",
                                                },
                                                {
                                                    "source": "solution",
                                                    "content": "answer\n",
                                                },
                                            ]
                                        },
                                        {"number": 2, "events": []},
                                    ],
                                },
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            errors = review._errors_spec_json(root)

        self.assertEqual(errors, [])

    def test_structured_samples_reject_invalid_shapes_and_legacy_mix(self) -> None:
        valid_pair = {
            "presentation": "pair",
            "passes": [{"number": 1, "input": "in\n", "output": "out\n"}],
        }
        cases = (
            (
                {"sample": False, "sample_json": valid_pair},
                "requires sample=true",
            ),
            (
                {
                    "sample": True,
                    "sample_input": "legacy\n",
                    "sample_json": valid_pair,
                },
                "cannot be combined",
            ),
            (
                {
                    "sample": True,
                    "sample_json": {"presentation": "pairs", "passes": [{}]},
                },
                "must be 'pair' or 'interaction'",
            ),
            (
                {
                    "sample": True,
                    "sample_json": {"presentation": "pair", "passes": []},
                },
                "must be a non-empty array",
            ),
            (
                {
                    "sample": True,
                    "sample_json": {
                        "presentation": "pair",
                        "passes": [{"number": True, "input": "", "output": ""}],
                    },
                },
                ".number: must be 1",
            ),
            (
                {
                    "sample": True,
                    "sample_json": {
                        "presentation": "pair",
                        "passes": [{"input": "in\n"}],
                    },
                },
                "output is required",
            ),
            (
                {
                    "sample": True,
                    "sample_json": {
                        "presentation": "interaction",
                        "passes": [
                            {
                                "events": [
                                    {"source": "solution", "content": 3}
                                ]
                            }
                        ],
                    },
                },
                ".content: must be a string",
            ),
            (
                {
                    "sample": True,
                    "sample_json": {
                        "presentation": "interaction",
                        "passes": [{"events": [], "input": "unexpected"}],
                    },
                },
                "unsupported field 'input'",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "tests/manual/001.in").write_text(
                "judge input\n",
                encoding="utf-8",
            )
            for sample_fields, expected in cases:
                with self.subTest(expected=expected):
                    entry = {"id": "001", "kind": "manual", **sample_fields}
                    (root / "tests/spec.json").write_text(
                        json.dumps({"tests": [entry]}),
                        encoding="utf-8",
                    )

                    errors = review._errors_spec_json(root)

                    self.assertIn(expected, "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
