# Local Testing Tool

> **Important**: The judge system cannot verify testing tools. This artifact ships to contestants unvalidated. You MUST test it manually before committing.

A Python script in `attachments/` that simulates the interactor locally, letting contestants debug without submitting.

## When to create

Every interactive problem should have a testing tool. It is the only way contestants can test locally.

## Structure

Study `examples/testing_tool.py` for a production reference. A testing tool has these parts:

### 1. Docstring (mandatory)

```python
"""
Local testing tool for <problem name>

Disclaimer: This is NOT the same code used to test your solution
when it is submitted. This tool is provided as-is. ...

Usage:
    python3 tool.py [--quiet] <data_file> <program> [args...]
    python3 tool.py 1.in ./solution
    python3 tool.py 1.in java -cp . Solution
    python3 tool.py 1.in python3 solution.py

The behavior is controlled by an input data file.
<describe the format of the data file, with an example>
"""
```

The docstring must explain usage, data file format, and include the disclaimer. Contestants will read this directly.

### 2. I/O helpers

```python
def vprint(*args, **kwargs):
    """Send a line to the contestant, log it as '< ...'."""
    if verbose:
        print("< ", end=""); print(*args, **kwargs); sys.stdout.flush()
    print(*args, file=process.stdin, flush=True, **kwargs)

def vreadline():
    """Read a line from the contestant, log it as '> ...'."""
    line = process.stdout.readline()
    if verbose and line:
        print("> " + line.rstrip("\n"))
    if not line:
        raise EndOfFile()
    return line
```

All I/O goes through these two functions, so `--quiet` mode works and every message is logged.

### 3. Data file parser

Parse the test input file  --  the same format as `tests/manual/*.in`. Validate field ranges and give clear errors if the file is malformed.

### 4. Interaction logic

Replicate the interactor's protocol exactly. This means:
- Read the interactor source and match it line-by-line
- Same token order, same delimiters, same range checks
- For multi-pass: launch the solution process multiple times (one per pass)
- Validate contestant output and print clear error messages (e.g. "expected 42, got 7")

### 5. Entry point

```python
if __name__ == "__main__":
    try:
        sys.exit(main())
    except (WrongAnswer, ValueError, EndOfFile) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
```

Exit 0 on success, 1 on any error.

## Rules

- **Python stdlib only**  --  no external dependencies. Contestants may not have pip.
- **Match the interactor exactly**  --  the testing tool must accept the same inputs and produce the same outputs as the real interactor. Differences cause confused contestants.
- **Log everything**  --  verbose mode shows `< ` (judge→solution) and `> ` (solution→judge). This is the primary debugging aid.
- **Do not enforce resource limits**  --  the tool cannot measure time/memory. Say so in the disclaimer.
- **`argparse`-based CLI**  --  `tool.py [--quiet] <data_file> <program> [args...]`.

## Testing (mandatory)

The judge system will never run or validate this file. You must test it manually before committing.

1. **Explain the tool's design to the user.** Before testing, tell them:
   - Does the tool check correctness, or only replay the protocol and print output?
   - What does success/failure output look like?
   - What data file format does it expect?

2. **Write two small test programs** in `temp/` (not real solutions  --  just enough to exercise the tool):
   - `temp/test_ok.cpp` (or `.py`)  --  follows the protocol correctly and should pass
   - `temp/test_bad.cpp` (or `.py`)  --  violates the protocol (e.g. wrong format, out-of-range value) and should trigger an error

   Also write a small test input file `temp/sample.in` matching the expected data file format.

3. **Compile and run** the tool against both programs:
   ```
   python3 attachments/<tool>.py temp/sample.in ./temp/test_ok
   python3 attachments/<tool>.py temp/sample.in ./temp/test_bad
   ```

4. **Verify the behavior matches step 1.** Check that:
   - `test_ok` produces the expected success output
   - `test_bad` triggers a clear, descriptive error
   - The interaction log (`< ` / `> ` lines) is readable and correct

5. **Leakage review**  --  show the code to the user with this warning:

   > ⚠️ This file will be **distributed to contestants**. Please check whether it leaks the intended solution approach. Common leaks and fixes:
   > - **The tool computes the correct answer internally** → change to print the judge's output and let the contestant verify by eye, instead of computing and checking the answer
   > - **Variable names or comments hint at the solution strategy** → only implement the protocol described in the problem statement; remove any logic not visible to contestants
   > - **Range checks or validation logic expose key observations** → remove checks that go beyond the statement's constraints

6. **Summarize testing**  --  tell the user what you tested and the results (which programs, which inputs, observed output, any issues found). This is the only record that the tool was verified.

7. **Clean up `temp/`** and commit after user approval:
   ```
   rm -rf temp/
   git add attachments/
   git commit -m "attachment: add local testing tool"
   ```

## Example

- `examples/testing_tool.py`  --  245-line production tool for a 2-pass guessing game (read its source to understand the patterns above)
