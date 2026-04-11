---
name: polygon-tests
description: "Create or manage test cases for a competitive programming problem. Use when the user wants to add, edit, or review test cases  -- both manual (hand-written) tests and generator-based test specifications."
---

# Manage Test Cases

## Adding Manual Tests

1. **Get the test data from the user**. They may provide:
   - Explicit input text (e.g., "input: `3\n1 2 3\n`, output: `6\n`")
   - A description (e.g., "a test with n=1, the minimum case")
   - Sample input/output from the statement

   If the user describes a test case rather than giving exact data, **ask for the exact input and expected output**. Do not generate test data without the user's confirmation.

2. **Determine the test ID**. IDs are exactly 3 decimal digits starting from `001`. Continue from the highest existing ID.

3. **Write the input file**: `tests/manual/{id}.in`
   - Ensure the input ends with a newline.
   - Strip trailing spaces from each line.

4. **Write the answer file** (if the user provides expected output): `tests/answers/{id}.ans`

5. **Update tests/spec.json**. Add an entry to the `tests` array (refer to polygon-spec for the full schema):
   ```json
   {
     "id": "001",
     "kind": "manual",
     "sample": true,
     "sample_input": "3\n1 2 3\n",
     "sample_output": "6\n"
   }
   ```

   - Set `"sample": true` for tests that should appear as examples in the statement. Usually the first 1-3 tests are samples.
   - Include `sample_input` and `sample_output` for sample tests  -- these are used by the statement renderer.
   - Non-sample tests omit `sample_input` and `sample_output`.

6. **Commit**:
   ```
   git add tests/
   git commit -m "tests: add manual test {id}"
   ```

## Adding Multiple Tests at Once

If the user provides multiple tests, add them all in one operation:
1. Write all `tests/manual/{id}.in` and `tests/answers/{id}.ans` files.
2. Update `tests/spec.json` with all entries.
3. Single commit: `"tests: add manual tests {first_id}-{last_id}"`.

## Reviewing Tests

If the user asks to see current tests:
1. Read `tests/spec.json` and list all tests with their IDs, kind, and sample flag.
2. For each test, show the contents of `tests/manual/{id}.in` and `tests/answers/{id}.ans`.

## Rules

- Test IDs must be unique and zero-padded to at least 3 digits.
- `tests/manual/{id}.in` must exist for every manual test entry.
- `tests/answers/{id}.ans` should exist when the expected output is known.
- Sample tests should come first in the ordering.
- Input files must end with exactly one trailing newline, no trailing spaces on lines.
