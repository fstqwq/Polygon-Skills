---
name: polygon-solution
description: "Write solutions -- brute force, wrong-answer traps, main correct, and translations."
---

# Write Solution

## Procedure

1. **Understand the problem**. Read `statement-sections/english/legend.tex`, `input.tex`, `output.tex`, and `config/problem.json`.

2. **Plan the task list upfront.** Before writing any code, scan `solutions/` for existing files and determine which steps are already done. Then write a checklist to `draft/solutions.md`:

   ```markdown
   # Solutions Plan

   - [ ] A. Brute force -- `solutions/brute_force.cpp`
   - [ ] B. Wrong-answer trap -- `solutions/rej_greedy.cpp`
   - [ ] C. Dummy solution -- `solutions/rej_dummy.cpp` (skip if no branching)
   - [ ] D. Main correct -- `solutions/std.cpp`
   - [ ] E. Language translations -- `solutions/ac_java.java`, `solutions/ac_python.py`
   - [ ] F. Additional approaches (if requested)
   ```

   Mark already-completed items as `[x]`. Show the plan to the user. Update this file as you complete each step.

3. **Write auxiliary solutions first** (before the main correct solution). Go through each category below in order. For each one, propose the approach, write it, show to user, commit.

### Step A: Brute force

Suggest the most naive, direct approach -- exhaustive enumeration, full search, O(n!) permutation, etc. This solution should be **correct but slow**.

- Filename: `solutions/brute_force.cpp`
- Expected: `time_limit_exceeded` (or `accepted` if the problem is small enough)
- Purpose: serves as a reference oracle for stress-testing the main solution

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
- Expected: `accepted`
- Update `config/build.json`: `"accepted_solution_source": "solutions/std.cpp"`

### Step E: Language translations

After the main correct solution is committed, translate it to Python first, then optionally Java. These must be direct, faithful translations -- same algorithm, same logic.

- Filename: `solutions/ac_python.py` (priority), `solutions/ac_java.java` (if requested)
- Expected: `accepted`, or `tle_or_correct` if the translation is algorithmically correct but may time out under the configured limits
- Purpose: verifies that time/memory limits are achievable in other languages

### Step F: Additional approaches

Ask the user: "Do you want to test any other approaches (e.g. a different algorithm that should also pass, or a specific wrong approach you want to make sure fails)?"

If yes, write the solution with the user's specified expected behavior and repeat the per-solution steps below.

---

## For each solution

4. **Write the code**. Use C++ by default. For Step E translations, use the target language.

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

   - Use `bits/stdc++.h`.
   - Use plain `cin` / `cout`. Do NOT use `ios::sync_with_stdio(false)` or `cin.tie(nullptr)`.
   - Do NOT write `return 0;` in `main`.
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

   - Use `input()` and `print()`.
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
   - Use `Scanner` for input, `System.out.println` for output.
   - For performance-critical code: use `BufferedReader` / `PrintWriter` instead.
   - For interactive problems: `System.out.flush()` after each output.

### Common rules (all languages)

   **Prefer simplicity and readability.** Code should be short, clear, and direct.

   - Do NOT write comments. Structure and naming carry all meaning.
   - Self-contained: single file, no external dependencies.
   - Match the input/output format from the statement exactly.
   - Short variable names are fine when conventional (`n`, `m`, `u`, `v`, `ans`, `dp`, `adj`).
   - Trust the input format. Do not write defensive I/O checks (e.g. `if (!(cin >> n))` is unnecessary -- just `cin >> n`).

   **C++ specific:**
   - Prefer `vector` over C arrays. Pass and return `vector` by value.
   - Globals are fine when many functions share context and passing arguments would add clutter (e.g. graph adjacency list, network flow). Otherwise prefer local variables and function arguments.
   - Use `auto` when the type is obvious from context (e.g. `auto it = mp.find(x)`).
   - Structured bindings are encouraged (e.g. `auto [u, v, w] = edges[i]`).

5. **Write the .desc file** alongside:
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

6. **Show the code to the user** and wait for feedback before committing.

7. **Update `draft/solutions.md`** (mark the step as `[x]`) and **commit**:
   ```
   git add solutions/{name}.cpp solutions/{name}.cpp.desc config/build.json
   git commit -m "solution: add {name} ({expected behavior})"
   ```

## Rules

- Always show code to the user before committing.
- Write auxiliary solutions (brute, wa, dummy) BEFORE asking about the main correct solution.
- If the statement is incomplete or ambiguous, ask for clarification rather than guessing.
- The agent CAN write the solution code (unlike statement content, where the agent must not invent).
