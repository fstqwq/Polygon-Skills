---
name: polygon-checker
description: "Write or configure a checker for a competitive programming problem. Use when the problem has special output requirements (multiple valid answers, floating point tolerance, property-based checking) or when the user wants to set a standard checker like std::wcmp."
---

# Write or Configure Checker

## Procedure

### Option A: Standard Checker (preferred when applicable)

1. **Determine which standard checker fits**. Refer to `polygon-spec/checkers.md` for the full catalog. Common choices:
   - `wcmp`  -- token-by-token comparison (default, most problems)
   - `ncmp`  -- ordered sequence of integers
   - `yesno` / `nyesno`  -- YES/NO (single or multi-test)
   - `rcmp4` / `rcmp6` / `rcmp9`  -- floating point with tolerance
   - `uncmp`  -- unordered sequence of integers

2. **Copy the standard checker into the repo** and update `config/build.json`:
   ```bash
   cp third_party/upstream/testlib/checkers/wcmp.cpp checkers/wcmp.cpp
   ```
   ```json
   "checker_source": "checkers/wcmp.cpp"
   ```

3. **Commit**:
   ```
   git add checkers/wcmp.cpp config/build.json
   git commit -m "checker: use standard checker std::wcmp"
   ```

### Option B: Custom Checker

1. **Understand what to check**. Read the output format from the statement. Identify what makes an answer valid.

2. **Write the checker.** When the problem has multiple valid answers or the checker validates answers independently (not comparing two files), use the `readAndCheckAnswer` pattern:

   ```cpp
   #include "testlib.h"
   using namespace std;

   // Returns true if the answer is valid. Quits with _wa/_fail on invalid.
   bool readAndCheckAnswer(/* input data */ int n, InStream& in) {
       // Read and validate the answer from `in`
       // Use in.readInt(), in.readToken(), etc.
       // Use in.quitf(_wa, ...) for invalid answers
       return true;
   }

   int main(int argc, char* argv[]) {
       registerTestlibCmd(argc, argv);

       // Read input
       int n = inf.readInt();

       // Validate jury answer first  -- catch judge bugs
       bool jury_ok = readAndCheckAnswer(n, ans);

       // Then validate contestant answer
       bool contestant_ok = readAndCheckAnswer(n, ouf);

       if (contestant_ok && !jury_ok)
           quitf(_fail, "contestant has valid answer but jury doesn't");
       if (!contestant_ok)
           quitf(_wa, "invalid answer");

       quitf(_ok, "correct");
   }
   ```

   **Why this pattern matters:** If the main correct solution has a bug, a naive checker that only compares `ouf` against `ans` will accept wrong answers. The `readAndCheckAnswer` pattern catches this by validating `ans` independently  -- an invalid jury answer triggers `_fail`, which is immediately visible in testing.

   Key points:
   - `readAndCheckAnswer(input_data, in)` reads from `in` (either `ouf` or `ans`)
   - `in.quitf(_wa, ...)` on invalid answers  -- testlib maps this to `_fail` automatically when called on `ans`
   - Three streams: `inf` (input), `ouf` (contestant output), `ans` (jury answer)
   - Verdicts: `_ok`, `_wa`, `_fail` only. Do not use `_pe`
   - **Multi-test**: call `setTestCase(t)` (1-indexed) at the top of each test case loop iteration  -- mandatory for proper per-testcase error messages

3. **Save as** `checkers/checker.cpp`.

4. **Update config/build.json**:
   ```json
   "checker_source": "checkers/checker.cpp"
   ```

5. **Show the code to the user** and wait for feedback.

6. **Compile** (best-effort, see `polygon-spec/compile.md`):
   ```
   g++ -std=c++20 -O2 -o checker checkers/checker.cpp -I <skills>/polygon-spec
   ```
   If no compiler is available locally (and no WSL on Windows), report to the user and skip.

7. **Commit**:
   ```
   git add checkers/checker.cpp config/build.json
   git commit -m "checker: add custom checker"
   ```

### Option C: Multi-pass Checker (non-interactive)

For non-interactive multi-pass problems (`pass_limit  -- 2`, mode `pass-fail`). The checker produces `nextpass.in` for subsequent passes.

The evaluation model is the same as multi-pass interactive (see `/polygon-interactor` Section B), except:
- The judge uses `checker <test.in> <contestant_output> <feedback_dir>` instead of an interactor
- There is no stdin/stdout interaction  -- the checker reads `ouf` (contestant output) after the solution finishes
- The checker writes `nextpass.in` via `tout` for the next pass

1. **Write the checker** with `start_next_pass()` lambda (see `/polygon-interactor` Section B):

   ```cpp
   #include "testlib.h"
   using namespace std;

   int main(int argc, char* argv[]) {
       registerTestlibCmd(argc, argv);

       auto start_next_pass = [&]() {
   #ifdef DOMJUDGE
           tout.open(make_new_file_in_a_dir(argv[3], "nextpass.in"),
                     ios_base::out);
   #endif
       };

       int op = inf.readInt();  // e.g., pass number

       if (op == 1) {
           // Check pass 1 output
           // ...

           // Prepare next pass
           start_next_pass();
           tout << 2 << "\n";
           // ... write whatever pass 2 needs ...

           quitf(_ok, "First pass OK");

       } else if (op == 2) {
           // Check pass 2 output
           int expected = inf.readInt();
           int got = ouf.readInt();
           if (got == expected)
               quitf(_ok, "correct");
           else
               quitf(_wa, "expected %d, got %d", expected, got);
       }
   }
   ```

2. **Save, update build.json, commit**  -- same as Option B.

**When to use which:**

| Situation | Use |
|-----------|-----|
| Interactive multi-pass (solution talks to judge) | Interactor (`/polygon-interactor` Section B) |
| Non-interactive multi-pass (solution just reads/writes) | Checker (Option C above) |

## Rules

- **Prefer standard checkers** unless the problem genuinely needs a custom one.
- Ask the user: "Does this problem have a unique answer, or can there be multiple valid answers?" This determines whether a standard checker suffices.
- Custom checkers must handle malformed contestant output gracefully (use `ouf.readInt()` etc., which auto-quit with WA on parse failure).
- Verdicts: use only `_ok` (accepted), `_wa` (wrong answer), `_fail` (judge error). Do not use `_pe`.
- **Multi-pass checkers**: always use the `start_next_pass()` lambda. Set `pass_limit` in `config/problem.json`.

## Examples

- `examples/constructive_checker.cpp`  -- constructive problem checker: validates contestant's matrix construction against constraints, uses `readAndCheckAnswer(n, in)` pattern to share logic between `ouf` and `ans`
