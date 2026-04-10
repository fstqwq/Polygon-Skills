---
name: polygon-checker
description: "Write or configure a checker for a competitive programming problem. Use when the problem has special output requirements (multiple valid answers, floating point tolerance, property-based checking) or when the user wants to set a standard checker like std::wcmp."
---

# Write or Configure Checker

## Procedure

### Option A: Standard Checker (preferred when applicable)

1. **Determine which standard checker fits**. Refer to `polygon-schemas/checkers.md` for the full catalog. Common choices:
   - `wcmp` — token-by-token comparison (default, most problems)
   - `ncmp` — ordered sequence of integers
   - `yesno` / `nyesno` — YES/NO (single or multi-test)
   - `rcmp4` / `rcmp6` / `rcmp9` — floating point with tolerance
   - `uncmp` — unordered sequence of integers

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

2. **Write the checker** using testlib.h:

   ```cpp
   #include "testlib.h"
   using namespace std;

   int main(int argc, char* argv[]) {
       registerTestlibCmd(argc, argv);

       // inf = input file, ouf = contestant output, ans = jury answer
       // Read from these streams and compare

       int jury_answer = ans.readInt();
       int contestant_answer = ouf.readInt();

       if (contestant_answer == jury_answer) {
           quitf(_ok, "correct answer %d", contestant_answer);
       } else {
           quitf(_wa, "expected %d, got %d", jury_answer, contestant_answer);
       }
   }
   ```

   Key testlib checker patterns:
   - Three streams: `inf` (input), `ouf` (contestant output), `ans` (jury answer)
   - Exit with `quitf(_ok, ...)`, `quitf(_wa, ...)`, or `quitf(_pe, ...)`
   - For "output any valid answer" problems: validate the contestant's answer against the input directly, use jury answer only as a sanity reference

3. **Save as** `checkers/checker.cpp`.

4. **Update config/build.json**:
   ```json
   "checker_source": "checkers/checker.cpp"
   ```

5. **Show the code to the user** and wait for feedback.

6. **Commit**:
   ```
   git add checkers/checker.cpp config/build.json
   git commit -m "checker: add custom checker"
   ```

## Rules

- **Prefer standard checkers** unless the problem genuinely needs a custom one.
- Ask the user: "Does this problem have a unique answer, or can there be multiple valid answers?" This determines whether a standard checker suffices.
- Custom checkers must handle malformed contestant output gracefully (use `ouf.readInt()` etc., which auto-report PE on parse failure).
