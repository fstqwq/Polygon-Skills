---
name: polygon-solution
description: "Write solutions for a competitive programming problem -- brute force, wrong-answer traps, and main correct solution. Handles C++ competitive programming code style, .desc files, and build.json updates."
---

# Write Solution

## Procedure

1. **Understand the problem**. Read `statement-sections/english/legend.tex`, `input.tex`, `output.tex`, and `config/problem.json`.

2. **Write auxiliary solutions first** (before the main correct solution). Go through each category below in order. For each one, propose the approach, write it, show to user, commit.

### Step A: Brute force

Suggest the most naive, direct approach -- exhaustive enumeration, full search, O(n!) permutation, etc. This solution should be **correct but slow**.

- Filename: `solutions/brute_force.cpp`
- Expected: `time_limit_exceeded` (or `accepted` if the problem is small enough)
- Purpose: serves as a reference oracle for stress-testing the main solution

### Step B: Greedy / simple heuristic

Suggest a plausible but likely wrong greedy or randomized approach. Expect it to fail.

- Filename: `solutions/wa_greedy.cpp` (or `wa_random.cpp`)
- Expected: `wrong_answer`
- Purpose: ensures the test data catches naive greedy strategies

### Step C: Dummy solution (if applicable)

If the problem has multiple outcome branches (e.g. "output the answer or -1 if impossible", "YES/NO", "possible/impossible"), write a solution that always outputs the trivial branch.

- Example: always print `-1`, always print `NO`, always print `0`
- Filename: `solutions/wa_dummy.cpp`
- Expected: `wrong_answer`
- Purpose: ensures the test data contains cases for all branches, not just the trivial one
- Skip this step if the problem has no such branching.

### Step D: Main correct solution

After auxiliary solutions are committed, ask the user:

> "Do you want to write the main correct solution now?"

If yes:
- Ask the user for the intended algorithm / approach. Do NOT just implement your own idea silently.
- Filename: `solutions/std.cpp`
- Expected: `accepted`
- Update `config/build.json`: `"accepted_solution_source": "solutions/std.cpp"`

### Step E: Language translations

After the main correct solution is committed, translate it to Java and/or Python. These must be direct, faithful translations -- same algorithm, same logic.

- Filename: `solutions/ac_java.java`, `solutions/ac_python.py`
- Expected: `accepted`
- Purpose: verifies that time/memory limits are achievable in other languages

### Step F: Additional approaches

Ask the user: "Do you want to test any other approaches (e.g. a different algorithm that should also pass, or a specific wrong approach you want to make sure fails)?"

If yes, write the solution with the user's specified expected behavior and repeat the per-solution steps below.

---

## For each solution

3. **Write the code**. Use C++ by default. For Step E translations, use the target language.

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

   - Do NOT write comments. Code must be self-explanatory through clear variable names and structure.
   - Self-contained: single file, no external dependencies.
   - Match the input/output format from the statement exactly.

4. **Write the .desc file** alongside:
   ```
   expected: accepted
   ```
   Valid values: `accepted`, `wrong_answer`, `time_limit_exceeded`, `run_time_error`, `rejected`.

5. **Show the code to the user** and wait for feedback before committing.

6. **Commit**:
   ```
   git add solutions/{name}.cpp solutions/{name}.cpp.desc config/build.json
   git commit -m "solution: add {name} ({expected behavior})"
   ```

## Rules

- Always show code to the user before committing.
- Write auxiliary solutions (brute, wa, dummy) BEFORE asking about the main correct solution.
- If the statement is incomplete or ambiguous, ask for clarification rather than guessing.
- The agent CAN write the solution code (unlike statement content, where the agent must not invent).
