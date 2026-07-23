---
name: polygon-checker
description: "Write or select a checker (wcmp, ncmp, rcmp, or custom)."
---

# Write or Configure Checker

The only runtime checker is the repository source named by `config/build.json` `checker_source`. Standard checker selection means copying a standard source into `checkers/` and pointing `checker_source` at that copy; do not store `std::...` as configuration.

Before writing code, read `../polygon-spec/references/codeforces-testlib-style.md` and apply its shared component rules.

## Procedure

### Option A: Standard Checker (preferred when applicable)

1. **Determine which standard checker fits**. Refer to `polygon-spec/checkers.md` for the full catalog. When applicable, prefer `ncmp`, then `nyesno`, then `wcmp`; otherwise choose the standard checker that matches the output semantics:
   - `ncmp`  -- ordered sequence of integers
   - `nyesno`  -- case-insensitive YES/NO
   - `wcmp`  -- token-by-token comparison
   - `rcmp4` / `rcmp6` / `rcmp9`  -- floating point with tolerance; prefer the matching `rcmp` variant when `dcmp` would also fit a single value
   - `uncmp`  -- unordered sequence of integers

2. **Copy the standard checker into the repo** and update `config/build.json`:
   ```bash
   cp <skills>/polygon-checker/standard/wcmp.cpp checkers/wcmp.cpp
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

2. **Write the checker.** When the problem has multiple valid answers or the checker validates answers independently (not comparing two files), use the `readAns` pattern:

   ```cpp
   #include "testlib.h"
   using namespace std;

   // Returns true if the answer is valid. Quits with _wa/_fail on invalid.
   bool readAns(/* input data */ int n, InStream& in) {
       // Initialize any global state used while reading one answer here.
       // Read and validate the answer from `in`
       // Use in.readInt(), in.readToken(), etc.
       // Use in.quitf(_wa, ...) for invalid answers
       // Keep lexical checks that define the answer token itself,
       // e.g. in.readToken("[A-Za-z]{2,3}", "verdict") for YES/NO.
       // Do not check input/output format here; validate semantic answer only.
       return true;
   }

   int main(int argc, char* argv[]) {
       registerTestlibCmd(argc, argv);

       // Read input
       int n = inf.readInt();

       // Validate jury answer first  -- catch judge bugs
       bool jury_ok = readAns(n, ans);

       // Then validate contestant answer
       bool contestant_ok = readAns(n, ouf);

       if (contestant_ok && !jury_ok)
           quitf(_fail, "contestant has valid answer but jury doesn't");
       if (!contestant_ok)
           quitf(_wa, "invalid answer");

       quitf(_ok, "ok, correct");
   }
   ```

   **Why this pattern matters:** If the main correct solution has a bug, a naive checker that only compares `ouf` against `ans` will accept wrong answers. The `readAns` pattern catches this by validating `ans` independently  -- an invalid jury answer triggers `_fail`, which is immediately visible in testing.

   Key points:
   - The function must be named `readAns`.
   - Initialize every global variable used for one answer at the beginning of `readAns`.
   - `readAns(input_data, in)` reads from `in` (either `ouf` or `ans`)
   - `in.quitf(_wa, ...)` on invalid answers  -- testlib maps this to `_fail` automatically when called on `ans`
   - Three streams: `inf` (input), `ouf` (contestant output), `ans` (jury answer)
   - Checkers should validate answer semantics, not validator-style whitespace. Prefer token-based reads like `readInt()`, `readToken()`, and `readWord()`.
   - Use `readToken()` instead of `readLine()` unless line boundaries are part of the answer semantics.
   - Lexical restrictions for a semantic token are still part of answer validation. Keep bounded reads like `readToken("[A-Za-z]{2,3}", "verdict")`, `readInt(l, r, "x")`, or explicit enum checks for `YES`/`NO`; do not replace them with unconstrained `readToken("verdict")`.
   - Always give explicit bounds or a bounded pattern when reading values from `ouf` and `ans`.
   - **Do not check input or output format in a checker.** Do not use `readSpace()`, `readEoln()`, or `readEof()`.
   - `testlib.h` itself will take care of extra dirt in participant's output.
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
   mkdir -p temp
   g++ -std=c++20 -O2 -o temp/checker checkers/checker.cpp -I <skills>/polygon-spec
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

           quitf(_ok, "ok, first pass done");

       } else if (op == 2) {
           // Check pass 2 output
           int expected = inf.readInt();
           int got = ouf.readInt();
           if (got == expected)
               quitf(_ok, "ok, correct");
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
- When applicable, prefer `ncmp`, then `nyesno`, then `wcmp`. Otherwise use the matching standard checker, such as an `rcmp` variant for floating-point output.
- Ask the user: "Does this problem have a unique answer, or can there be multiple valid answers?" This determines whether a standard checker suffices.
- Custom checkers must handle malformed contestant output gracefully (use `ouf.readInt()` etc., which auto-quit with WA on parse failure).
- Lexical restrictions for answer tokens are semantic validation. Keep regex/range/enum checks that define valid tokens, for example `readToken("[A-Za-z]{2,3}", "verdict")` followed by a `YES`/`NO` check.
- Custom answer readers must be named `readAns`; reset all per-answer global state at the beginning of that function.
- Prefer `readToken()` over `readLine()`.
- Always bound values read from `ouf` and `ans`.
- **Do not check input or output format in a checker.** Do not use `readSpace()`, `readEoln()`, or `readEof()`.
- `testlib.h` itself will take care of extra dirt in participant's output.
- Exact whitespace belongs to validators. A checker should validate answer semantics only.
- Do not re-validate `inf` formatting in a checker. If input whitespace/line structure must be enforced, that belongs in `validators/validator.cpp`.
- Verdicts: use only `_ok` (accepted), `_wa` (wrong answer), `_fail` (judge error). Do not use `_pe`.
- **`quitf(_ok, ...)` message must start with `"ok"`** (e.g. `quitf(_ok, "ok, correct")`, `quitf(_ok, "ok, n=%d", n)`). This makes logs immediately scannable.
- Treat checker messages as contestant-visible: keep them clear and do not reveal hidden answers or solution ideas.
- **Multi-pass checkers**: always use the `start_next_pass()` lambda. Set `pass_limit` in `config/problem.json`.

## Examples

- `examples/constructive_checker.cpp`  -- constructive problem checker: validates contestant's matrix construction against constraints and shares `readAns(n, in)` logic between `ouf` and `ans`
