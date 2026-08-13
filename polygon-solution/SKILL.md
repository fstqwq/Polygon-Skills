---
name: polygon-solution
description: "Write solutions -- brute force, wrong-answer traps, main correct, and translations, optionally imitating user-provided code style."
---

# Write Solution

## Procedure

1. **Understand the problem**. Read `statement-sections/english/legend.tex`, `input.tex`, `output.tex`, and `config/problem.json`.

2. **Create the task plan before asking about style.** Before writing any code, scan `solutions/` for existing files and determine which steps are already done. Then write a checklist to `draft/solutions.md`:

   ```markdown
   # Solutions Plan

   ## Code Style Reference

   - Reference: pending
   - Applies to: pending
   - Overrides: none

   ## Tasks

   - [ ] A. Brute force -- `solutions/brute_force.cpp`
   - [ ] B. Wrong-answer trap -- `solutions/rej_greedy.cpp`
   - [ ] C. Dummy solution -- `solutions/rej_dummy.cpp` (skip if no branching)
   - [ ] D. Main correct -- `solutions/std.cpp`
   - [ ] E. Language translations -- `solutions/ac_java.java`, `solutions/ac_python.py`
   - [ ] F. Additional approaches (if requested)
   ```

   Mark already-completed items as `[x]`. Show the plan to the user. Update this file as you complete each step.

   Extend the checklist when the problem needs:
   - an independently implemented second correct solution,
   - a Java solution because C++ already uses more than one quarter of TL or about 50 MB,
   - a Python solution as an overflow-safe reference,
   - overflow-prone rejected variants,
   - casework variants that omit one important branch,
   - an optimized slow solution that should not pass.

3. **Resolve the code style reference once.** After creating and showing `draft/solutions.md`, ask one bundled question unless the user already supplied a reference or the draft records a resolved choice:

   > Do you want me to imitate code you provide? If yes, paste the reference code or give its repository path, and say which languages or solutions it applies to. If no, I will use the minimal defaults in this skill.

   Do not offer named style profiles and do not ask separate questions about formatting, templates, or I/O.

   - If the user declines, replace `pending` with `none` and record the applicable scope.
   - If the user provides code, save an exact snapshot as `draft/solution-style.cpp`, `draft/solution-style.py`, or `draft/solution-style.java`. Use one file per provided language.
   - Record each saved reference, its scope, and any explicit style overrides in `draft/solutions.md`.
   - On a resumed task, reuse the resolved choice in `draft/solutions.md`; do not ask again.
   - Explicit instructions in the current request override the saved reference. Correctness, required I/O, and compilation requirements override style.
   - Imitate formatting, naming, includes/imports, aliases, macros, function layout, container choices, and other recurring idioms. Do not copy problem-specific algorithms, constants, debug code, or unused helpers.
   - Do not silently clean up the user's style. If following it would cause a correctness, compilation, or portability problem, explain the conflict before deviating.

4. **Write auxiliary solutions first** (before the main correct solution). Go through each category below in order. For each one, propose the approach, write it, show to user, commit.

### Step A: Brute force

Suggest the most naive, direct approach -- exhaustive enumeration, full search, O(n!) permutation, etc. This solution should be **correct but slow**.

- Filename: `solutions/brute_force.cpp`
- Expected: `time_limit_exceeded` (or `accepted` if the problem is small enough)
- Purpose: serves as a reference oracle for stress-testing the main solution
- Implement exactly the direct process described by the statement. It should produce only correct results or time out; avoid undefined behavior and accidental wrong answers. If a finite direct implementation can terminate early for irrelevant reasons, use an explicit non-terminating fallback so the expected failure remains TLE.

### Step B: Greedy / simple heuristic

Suggest a plausible but wrong approach. Common patterns:

- **Greedy**: sort by some criterion, always pick the locally optimal choice
- **Multi-greedy**: try several greedy strategies, take the best (`min` / `max` of multiple wrong answers)
- **Random / shuffle**: randomly permute, check if it works, repeat -- give up and output "NO" or `-1` if no solution found after N tries
- **Local search**: start from any solution, repeatedly improve by swapping adjacent elements

Pick whichever is most natural for the problem. The solution should look plausible to a contestant but fail on well-designed tests.

- Filename: `solutions/rej_greedy.cpp` (or `rej_random.cpp`, `rej_heuristic.cpp`)
- Expected: `rejected`
- Purpose: ensures the test data rejects naive heuristics

### Step C: Dummy solution (if applicable)

If the problem has multiple outcome branches (e.g. "output the answer or -1 if impossible", "YES/NO", "possible/impossible"), write a solution that always outputs the trivial branch.

- Example: always print `-1`, always print `NO`, always print `0`
- Filename: `solutions/rej_dummy.cpp`
- Expected: `rejected`
- Purpose: ensures the test data contains cases for all branches, not just the trivial one
- Skip this step if the problem has no such branching.

### Step D: Main correct solution

After auxiliary solutions are committed, ask the user which mode they prefer:

> "Ready for the main correct solution. Two options:
> 1. **You describe the algorithm** -- I implement it faithfully.
> 2. **I solve it myself** -- I'll analyze the problem, propose an approach with complexity and difficulty assessment, and ask for your approval before implementing."

**Mode 1 (user-driven):** The user explains the approach. Implement it exactly as described. Do not second-guess or "improve" the algorithm.

**Mode 2 (agent-driven):** Analyze the problem independently. Present:
- Proposed algorithm and complexity
- Difficulty estimate (e.g. "div2 C", "ICPC medium", "WF hard")
- Any alternative approaches worth considering

Wait for the user to approve or redirect before writing code.

- Filename: `solutions/std.cpp`
- Expected: `accepted`, established by the build selection below
- Update `config/build.json`: `"accepted_solution_source": "solutions/std.cpp"`
- Do not create or rewrite `solutions/std.cpp.desc`; the explicit build
  selection is authoritative.
- Keep the main solution clear and asymptotically appropriate without relying on unusual constant-factor tricks. Target at most half of TL and half of ML under authoritative Verification.

### Step E: Language translations

After the main correct solution is committed, translate it to Python first, then optionally Java. These must be faithful translations: same algorithm, same proof assumptions, same corner-case behavior. Make small constant-factor optimizations when they do not change the algorithm, such as faster input parsing, iterative loops instead of avoidable helper calls, preallocated lists/arrays, or buffered output.

- Filename: `solutions/ac_python.py` (priority), `solutions/ac_java.java` (if requested)
- Expected: `accepted`, or `tle_or_correct` if the faithful translation is algorithmically correct but may time out under the configured limits even after reasonable constant-factor optimization
- Purpose: verifies that time/memory limits are achievable in other languages
- Always consider a Python reference when C++ arithmetic has meaningful overflow risk.
- Prepare a Java correct solution when C++ already uses more than one quarter of TL or about 50 MB and Java performance could therefore be marginal. Base the decision on measurements, not on a mechanical translation requirement.

### Step F: Additional approaches

Ask the user: "Do you want to test any other approaches (e.g. a different algorithm that should also pass, or a specific wrong approach you want to make sure fails)?"

If yes, write the solution with the user's specified expected behavior and repeat the per-solution steps below.

Unless the user narrows the requested solution set, include at least one independently implemented correct solution in addition to `std.cpp`. Keep the same asymptotic target and aim for half of TL and ML.

### Overflow and casework variants

- Audit every input type, array size, accumulator, product, squared value, index expression, and sentinel.
- For each important overflow risk, create a plausible rejected solution using the wrong type or intermediate expression.
- If the correct algorithm uses casework, keep one complete correct implementation and create rejected variants that omit representative branches.
- Store each variant as a separate source file with an appropriate `.desc`; do not hide alternatives as commented-out code.

### Optimized slow solutions

- Implement slow approaches that contestants might plausibly optimize with pruning, bitsets, precomputation, or compiler pragmas.
- Optimize them enough that their rejection demonstrates the intended complexity boundary.
- Confirm that they still do not pass the configured limits; do not weaken tests or tighten limits merely to force the verdict.

---

## Verification posture

- Treat local runs as advisory. Confirm final accepted/TLE behavior through online Polygon-Replica Verification.
- If a solution fails strong tests, suspect the solution, complexity, implementation, or expected verdict before suspecting the tests.
- Do not weaken tests, lower constraints, or change limits to make a solution pass.
- For Python translations, local timing only indicates relative risk. Use `tle_or_correct` when the algorithm is correct but performance is uncertain, and rely on Verification for the final verdict.
- Do not modify the local runtime environment to rescue a solution unless the user explicitly asks.
- Avoid unnecessarily tight limits. For harder problems, use at least 2 seconds unless measurements and the target environment justify another choice.
- Benchmark every accepted solution against the target of half TL and half ML, and report exceptions instead of concealing them.

## For each solution

5. **Write the code**. Use C++ by default. For Step E translations, use the target language. Before writing, read the saved style reference for that language when one applies.

### C++

   ```cpp
   #include <bits/stdc++.h>
   using namespace std;

   int main() {
       int n;
       cin >> n;
       // ...
       cout << ans << "\n";
   }
   ```

   - Without a saved reference, use `bits/stdc++.h`.
   - Use plain `cin` / `cout`.
   - By default, write no I/O setup at all. Do NOT add `ios::sync_with_stdio(false)`, `cin.tie(nullptr)`, a custom scanner, or other I/O boilerplate unless the user explicitly requests it or the saved style reference contains it.
   - Without a saved reference, do NOT write `return 0;` in `main`.
   - The judge runs with unlimited stack. Deep recursion (DFS, divide-and-conquer) is safe -- do not avoid it or rewrite as iterative out of stack concerns.
   - For interactive problems: `cout << endl` or `cout.flush()` after each output.

### Python

   ```python
   def main():
       n = int(input())
       # ...
       print(ans)

   main()
   ```

   - Use `input()` and `print()` by default; switch to `sys.stdin.buffer` and buffered output when needed for constant-factor performance.
   - Wrap logic in `main()` -- avoid top-level code beyond the `main()` call.
   - No imports beyond standard library. Prefer `sys`, `collections`, `heapq`, `bisect`, `math`.
   - No type hints, no docstrings, no classes unless necessary.
   - For recursive solutions: add `sys.setrecursionlimit(...)` at the top. The judge runs with unlimited stack, but Python's default limit is ~1000.
   - If performance is tight, reduce the number of `print()` calls -- collect output in a list and `print('\n'.join(results))` once at the end.
   - For interactive problems: `print(..., flush=True)` after each output.

### Java

   ```java
   import java.util.*;
   import java.io.*;

   public class Main {
       public static void main(String[] args) {
           Scanner sc = new Scanner(System.in);
           int n = sc.nextInt();
           // ...
           System.out.println(ans);
       }
   }
   ```

   - Class name: `Main`.
   - Use `Scanner` for input, `System.out.println` for output by default.
   - For performance-critical code, use `BufferedInputStream` or `BufferedReader` and `PrintWriter` for constant-factor performance.
   - For interactive problems: `System.out.flush()` after each output.

### Common rules (all languages)

   There is no named default style or built-in style menu. When no saved reference applies, use only the minimal language defaults in this section.

   **Prefer simplicity and readability.** Code should be short, clear, and direct.

   - Without a saved reference, do NOT write comments. Structure and naming carry all meaning.
   - Self-contained: single file, no external dependencies.
   - Match the input/output format from the statement exactly.
   - Short variable names are fine when conventional (`n`, `m`, `u`, `v`, `ans`, `dp`, `adj`).
   - Trust the input format. Do not write defensive I/O checks (e.g. `if (!(cin >> n))` is unnecessary -- just `cin >> n`).

6. **Record expected behavior.** For every non-main solution whose expected
   behavior is known, write the adjacent `.desc` file:
   ```
   expected: accepted
   ```
   Valid values:
   - `accepted` -- must pass all tests
   - `wrong_answer` -- expected to fail with WA
   - `tle_or_correct` -- correct algorithm, but either AC or TL is acceptable
   - `tle_or_re` -- either TL or RE is acceptable
   - `time_limit_exceeded` -- expected to fail with TL
   - `run_time_error` -- expected to fail with RE
   - `rejected` -- generic negative solution; any non-AC failure is acceptable

   Do not write a descriptor for an explicitly unclassified solution. Missing
   means `unknown`. For the selected main correct solution, do not write a
   descriptor: `accepted_solution_source` is the sole authority.

7. **Show the code to the user** and wait for feedback before committing.

8. **Update `draft/solutions.md`** (mark the step as `[x]`) and **commit**:
   ```
   git add solutions/{name}.cpp config/build.json draft/solutions.md
   git commit -m "solution: add {name} ({expected behavior})"
   ```

   Add `solutions/{name}.cpp.desc` to the staging command when this procedure
   created one.

   When a saved style reference was added or changed, stage its exact
   `draft/solution-style.<ext>` path in the same commit.

## Rules

- Always show code to the user before committing.
- Create `draft/solutions.md` before asking the one-time code style question.
- Ask about a user-provided style reference only once per solution task; persist and reuse the answer.
- Write auxiliary solutions (brute, wa, dummy) BEFORE asking about the main correct solution.
- If the statement is incomplete or ambiguous, ask for clarification rather than guessing.
- The agent CAN write the solution code (unlike statement content, where the agent must not invent).
