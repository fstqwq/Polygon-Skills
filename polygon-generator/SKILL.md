---
name: polygon-generator
description: "Write a testlib test generator for a competitive programming problem. Use when the user wants to generate test data programmatically -- random tests, stress tests, edge cases, or anti-hack tests."
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
       int maxVal = atoi(argv[2]);

       println(n);
       for (int i = 0; i < n; i++) {
           if (i > 0) print(' ');
           print(rnd.next(1, maxVal));
       }
       println();
   }
   ```

   Code style (same as `/polygon-solution`):
   - No comments, no `return 0;`.
   - Prefer simplicity -- short, readable, self-contained.
   - Use `vector`, `auto`, structured bindings where natural.

4. **Choose a descriptive filename**: `generators/gen_random.cpp`, `generators/gen_tree.cpp`, `generators/gen_maxn.cpp`.

5. **Update config/build.json**:
   ```json
   "generator_sources": ["generators/gen_random.cpp"]
   ```
   Append to the existing list if other generators exist.

6. **Show the code to the user** and ask if they want to generate any tests now (suggest `/polygon-tests`).

7. **Compile** (best-effort, see `polygon-spec/compile.md`):
   ```
   g++ -std=c++20 -O2 -o gen generators/{name}.cpp -I <skills>/polygon-spec
   ```
   If no compiler is available locally (and no WSL on Windows), report to the user and skip.

8. **Commit**:
   ```
   git add generators/{name}.cpp config/build.json
   git commit -m "generator: add {name}"
   ```

---

## testlib generator API

- `registerGen(argc, argv, 1)` -- seeds RNG from command-line args. Output is deterministic for the same args.
- `rnd.next(lo, hi)` -- random integer in [lo, hi]
- `rnd.next(0.0, 1.0)` -- random double
- `rnd.next("[a-z]{1,10}")` -- random string matching regex (testlib regex, not PCRE)
- `rnd.perm(n)` / `rnd.perm(n, 1)` -- random permutation (0-indexed / 1-indexed)
- `rnd.partition(size, sum)` -- partition `sum` into `size` non-negative parts
- `println(...)` / `print(...)` -- testlib output helpers (use these, not `cout`)
- Arguments come from `argv[]` -- the gen command in spec.json provides them

## Common patterns

**Random array**: `rnd.next(1, maxVal)` in a loop.

**Random permutation**:
```cpp
auto p = rnd.perm(n, 1);
```

**Random tree** (random parent for each node):
```cpp
vector<pair<int,int>> edges;
for (int i = 1; i < n; i++)
    edges.push_back({rnd.next(0, i - 1) + 1, i + 1});
shuffle(edges.begin(), edges.end());
```

**Random connected graph** (tree + extra edges):
```cpp
// generate spanning tree first, then add random edges
```

**Star / chain / bamboo** (edge-case trees):
```cpp
// star: all connect to node 1
// chain: i connects to i+1
```

**Large values**: use `argv[]` to parameterize n, max values, etc., so the same generator produces small and large tests.

## Rules

- Generator output must match the exact format the validator expects (same whitespace, same newlines).
- Arguments should be configurable via `argv[]` so spec.json gen commands can vary parameters.
- The generator itself does NOT get wired into test generation automatically -- the user must add gen entries to spec.json via `/polygon-tests`.
- Use testlib's `print()` / `println()`, not `cout`. This ensures trailing whitespace is handled correctly.
