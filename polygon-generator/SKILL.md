---
name: polygon-generator
description: "Write a testlib test generator for a competitive programming problem. Use when the user wants to generate test data programmatically — random tests, stress tests, edge cases, or anti-hack tests."
---

# Write Test Generator

## Procedure

1. **Read the input format** from `statement-sections/english/input.tex` and the validator from `validators/validator.cpp` (if it exists) to understand exact constraints and format.

2. **Ask the user** what kind of tests to generate:
   - Random tests within constraints?
   - Specific edge cases? (e.g., all elements equal, maximum n, star graph, chain graph)
   - Anti-hack tests targeting a specific wrong approach?
   - Stress test pairs with a brute-force solution?

3. **Write the generator** using testlib.h:

   ```cpp
   #include "testlib.h"
   using namespace std;

   int main(int argc, char* argv[]) {
       registerGen(argc, argv, 1);

       int n = atoi(argv[1]);
       int max_val = atoi(argv[2]);

       println(n);
       for (int i = 0; i < n; i++) {
           if (i > 0) print(' ');
           print(rnd.next(1, max_val));
       }
       println();

       return 0;
   }
   ```

   Key testlib generator patterns:
   - `registerGen(argc, argv, 1)` — seeds RNG from command-line args
   - `rnd.next(lo, hi)` — random integer in [lo, hi]
   - `rnd.next(0.0, 1.0)` — random double
   - `rnd.next("[a-z]{1,10}")` — random string matching regex
   - `rnd.perm(n)` / `rnd.perm(n, 1)` — random permutation (0-indexed / 1-indexed)
   - `println(...)` / `print(...)` — testlib output helpers
   - Arguments come from `argv[]` — the gen command in spec.json provides them

   Common generator patterns:
   - **Tree**: use `rnd.next()` to pick parents, or Prüfer sequence
   - **Graph**: generate random edges, check for duplicates
   - **Permutation**: `auto p = rnd.perm(n, 1);`

4. **Choose a descriptive filename**: `generators/gen_random.cpp`, `generators/gen_tree.cpp`, `generators/gen_maxn.cpp`.

5. **Update config/build.json**:
   ```json
   "generator_sources": ["generators/gen_random.cpp"]
   ```
   Append to the existing list if other generators exist.

6. **Show the code to the user** and ask if they want to generate any tests now (suggest `/polygon-tests`).

7. **Commit**:
   ```
   git add generators/{name}.cpp config/build.json
   git commit -m "generator: add {name}"
   ```

## Rules

- Generator output must match the exact format the validator expects (same whitespace, same newlines).
- Arguments should be configurable via `argv[]` so spec.json gen commands can vary parameters.
- The generator itself does NOT get wired into test generation automatically — the user must add gen entries to spec.json via `/polygon-tests`.
