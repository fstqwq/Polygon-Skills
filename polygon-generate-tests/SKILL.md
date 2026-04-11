---
name: polygon-generate-tests
description: "Create test cases for a competitive programming problem -- manual tests, generator-based tests, and test specification management. Covers writing testlib generators, wiring them into spec.json, and hand-written test cases."
---

# Generate Tests

## Section A: Manual tests

### Adding a manual test

1. **Get the test data from the user**. They may provide:
   - Explicit input text (e.g., "input: `3\n1 2 3\n`, output: `6\n`")
   - A description (e.g., "a test with n=1, the minimum case")
   - Sample input/output from the statement

   If the user describes a test case rather than giving exact data, **ask for the exact input and expected output**. Do not generate test data without the user's confirmation.

2. **Determine the test ID**. IDs are exactly 3 decimal digits starting from `001`. Continue from the highest existing ID.

3. **Write the input file**: `tests/manual/{id}.in`
   - Ensure the input ends with a newline.
   - Strip trailing spaces from each line.

4. **Write the answer file** (if the user provides expected output): `tests/answers/{id}.ans`

5. **Update tests/spec.json**. Add an entry to the `tests` array (refer to polygon-spec for the full schema):
   ```json
   {
     "id": "001",
     "kind": "manual",
     "sample": true,
     "sample_input": "3\n1 2 3\n",
     "sample_output": "6\n"
   }
   ```

   - Set `"sample": true` for tests that should appear as examples in the statement. Usually the first 1-3 tests are samples.
   - Include `sample_input` and `sample_output` for sample tests -- these are used by the statement renderer.
   - Non-sample tests omit `sample_input` and `sample_output`.

6. **Commit**:
   ```
   git add tests/
   git commit -m "tests: add manual test {id}"
   ```

### Adding multiple tests at once

If the user provides multiple tests, add them all in one operation:
1. Write all `tests/manual/{id}.in` and `tests/answers/{id}.ans` files.
2. Update `tests/spec.json` with all entries.
3. Single commit: `"tests: add manual tests {first_id}-{last_id}"`.

---

## Section B: Generated tests

When tests need to be generated programmatically (random, stress, edge-case, anti-hack):

### 1. Write the generator

Use testlib.h:

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
- Use testlib's `print()` / `println()`, not `cout`.

Choose a descriptive filename: `generators/gen_random.cpp`, `generators/gen_tree.cpp`, `generators/gen_maxn.cpp`.

### 2. Update config/build.json

```json
"generator_sources": ["generators/gen_random.cpp"]
```
Append to the existing list if other generators exist.

### 3. Compile (best-effort)

See `polygon-spec/compile.md`:
```
g++ -std=c++20 -O2 -o gen generators/{name}.cpp -I <skills>/polygon-spec
```
If no compiler is available locally (and no WSL on Windows), report to the user and skip.

### 4. Wire into spec.json

Add gen entries to `tests/spec.json`:
```json
{
  "id": "010",
  "kind": "gen",
  "gen_command": "gen_random 100 1000000 1"
}
```

- `gen_command` is the generator name (without path/extension) followed by its arguments.
- The last argument is typically a seed -- vary it across tests for different outputs.
- Plan a mix of test sizes: small (for debugging), medium, and maximum constraints.

### 5. Commit

```
git add generators/{name}.cpp config/build.json tests/spec.json
git commit -m "tests: add generator {name} and test entries"
```

---

## Section C: Reviewing tests

If the user asks to see current tests:
1. Read `tests/spec.json` and list all tests with their IDs, kind, and sample flag.
2. For manual tests, show the contents of `tests/manual/{id}.in` and `tests/answers/{id}.ans`.
3. For gen tests, show the gen command.

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

## Common generator patterns

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

**Large values**: use `argv[]` to parameterize n, max values, so the same generator produces small and large tests.

## Rules

- Test IDs must be unique and zero-padded to at least 3 digits.
- Sample tests should come first in the ordering.
- Input files must end with exactly one trailing newline, no trailing spaces on lines.
- Generator output must match the exact format the validator expects.
- Arguments should be configurable via `argv[]` so spec.json gen commands can vary parameters.
- Use testlib's `print()` / `println()`, not `cout`.
