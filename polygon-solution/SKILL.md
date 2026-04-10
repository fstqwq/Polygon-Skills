---
name: polygon-solution
description: "Write a solution for a competitive programming problem. Use when the user wants to add or modify a solution — accepted, wrong answer, TLE, or runtime error. Handles C++ competitive programming code style, .desc files, and build.json updates."
---

# Write Solution

## Procedure

1. **Understand the problem**. Read `statement-sections/english/legend.tex`, `input.tex`, `output.tex`, and `config/problem.json` to understand what the solution must do.

2. **Ask the user** what kind of solution to write:
   - **Accepted (std)**: The main correct solution. If none exists yet, default to this.
   - **Accepted (alternative)**: Another correct approach (e.g., different algorithm).
   - **Wrong answer**: A plausible but incorrect solution.
   - **Time limit exceeded**: A brute-force or slow correct solution.
   - **Runtime error**: A solution that crashes on some inputs.

   If the user doesn't specify, write an accepted solution.

3. **Ask about approach** (for accepted solutions):
   - If the user has a specific algorithm in mind, implement that.
   - If not, propose an approach and ask for confirmation. Do NOT just implement your own idea silently.

4. **Write the solution** in C++:

   ```cpp
   #include <bits/stdc++.h>
   using namespace std;

   int main() {
       ios::sync_with_stdio(false);
       cin.tie(nullptr);
       // ...
       return 0;
   }
   ```

   Code style:
   - Use `bits/stdc++.h` for competitive programming convenience.
   - Use `ios::sync_with_stdio(false); cin.tie(nullptr);` for fast I/O.
   - Clean, readable code with comments for non-obvious logic.
   - Match the input/output format from the statement exactly.
   - For interactive problems: flush after each output line.

5. **Choose the filename**:
   - Main accepted solution: `solutions/std.cpp`
   - Alternative accepted: `solutions/ac_alt.cpp` or descriptive name
   - Wrong answer: `solutions/wa.cpp` or `solutions/wa_greedy.cpp`
   - TLE: `solutions/tle_brute.cpp`

6. **Write the .desc file** alongside:
   ```
   expected: accepted
   ```
   Valid values: `accepted`, `wrong_answer`, `time_limit_exceeded`, `run_time_error`, `rejected`.

7. **Update config/build.json**: If this is the first accepted solution, set `"accepted_solution_source": "solutions/std.cpp"`.

8. **Show the code to the user** and wait for feedback before committing.

9. **Commit**:
   ```
   git add solutions/{name}.cpp solutions/{name}.cpp.desc config/build.json
   git commit -m "solution: add {name} ({expected behavior})"
   ```

## Rules

- Always show code to the user before committing.
- For accepted solutions, ensure correctness matches the problem statement.
- If the statement is incomplete or ambiguous, ask for clarification rather than guessing.
- The agent CAN write the solution code (unlike statement content, where the agent must not invent).
