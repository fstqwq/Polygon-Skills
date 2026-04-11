---
name: polygon-generate-tests
description: "Design and create test cases for a competitive programming problem -- samples, edge cases, generator-based stress tests, and anti-hack tests. Guides test suite design methodology."
---

# Generate Tests

## Phase 1: Understand what needs testing

Before writing any test, read:
- `statement-sections/english/input.tex` and `output.tex` -- exact I/O format and constraints
- `validators/validator.cpp` (if it exists) -- exact bounds
- `solutions/` -- what correct and wrong solutions exist

Identify:
- **Constraint boundaries**: min/max values of n, m, coordinates, weights, etc.
- **Output branches**: does the problem have YES/NO, "output -1 if impossible", multiple valid answers?
- **Special structure**: trees, graphs, permutations, strings, geometry?

---

## Phase 2: Design the test plan

Propose a test plan to the user before writing anything. The plan should cover these categories:

### 2a. Samples (manual, IDs 001-009)

- Extracted from the problem statement.
- These are `"sample": true` in spec.json.
- Must be small, clear, and illustrate the problem.
- Typically 1-3 tests.

### 2b. Edge cases (manual, IDs 010-029)

Walk through the constraint boundaries systematically:

| Category | Examples |
|----------|----------|
| **Minimum size** | n=1, n=0, empty input |
| **Maximum values at minimum size** | n=1 with a[i]=10^9 |
| **All-same** | all elements equal, all edges same weight |
| **Sorted / reverse-sorted** | already sorted input, reverse order |
| **Binary** | all 0s, all 1s, alternating |
| **Boundary values** | a[i]=1, a[i]=max, coordinates at limits |
| **Special graph shapes** | star, chain, complete graph, self-loop, disconnected |
| **Trivial answers** | guaranteed YES, guaranteed NO, answer is 0, answer is max possible |

From these, pick the ones relevant to the problem. Propose them to the user as a checklist.

### 2c. Stress tests (generated, IDs 030-059)

Random tests at various sizes, designed to:
- Verify correctness against brute force (`brute_force.cpp` if it exists)
- Cover general cases that hand-written tests might miss

Plan the size distribution:
```
small:   n in [2, 10]      -- 5 tests (fast, debuggable)
medium:  n in [100, 1000]   -- 5 tests (find off-by-one, overflow)
large:   n = max constraint  -- 5 tests (TLE, MLE detection)
```

### 2d. Anti-hack tests (generated or manual, IDs 060-079)

Tests specifically designed to break wrong solutions. For each `rej_*` solution that exists:
- Analyze what inputs would make it fail
- Design a generator or hand-craft a test that exploits the weakness

Common anti-patterns to target:
| Wrong approach | Anti-hack strategy |
|---------------|-------------------|
| Greedy by value | Construct case where greedy ordering fails |
| Always output NO/-1 | Ensure positive cases exist |
| O(n^2) solution | Maximum n to trigger TLE |
| Overflow-prone | Values near 2^31 or 2^63 boundaries |
| Hash collision | Construct collision strings (anti-hash) |

### 2e. Max-stress tests (generated, IDs 080-099)

Maximum constraint tests with adversarial structure:
- Worst-case for the intended algorithm (e.g., worst-case merge sort input)
- Maximum output size
- Degenerate graphs (all edges same weight, long paths)

---

## Phase 3: Implement the tests

After the user approves the plan, implement in order:

### Step 1: Add sample tests (manual)

For each sample from the statement:

1. Write `tests/manual/{id}.in` (ends with newline, no trailing spaces)
2. Write `tests/answers/{id}.ans` if expected output is known
3. Add to `tests/spec.json`:
   ```json
   {
     "id": "001",
     "kind": "manual",
     "sample": true,
     "sample_input": "3\n1 2 3\n",
     "sample_output": "6\n"
   }
   ```

### Step 2: Add edge case tests (manual)

Same format, but `"sample": false` and no `sample_input`/`sample_output`.

### Step 3: Write generators and add stress tests

1. **Write the generator** using testlib.h:
   ```cpp
   #include "testlib.h"
   using namespace std;

   int main(int argc, char* argv[]) {
       registerGen(argc, argv, 1);
       int n = atoi(argv[1]);
       int maxVal = atoi(argv[2]);
       // ...
   }
   ```

   Code style (same as `/polygon-solution`):
   - No comments, no `return 0;`.
   - Use testlib's `print()` / `println()`, not `cout`.

2. **Register in config/build.json**:
   ```json
   "generator_sources": ["generators/gen_random.cpp"]
   ```

3. **Wire into spec.json**:
   ```json
   {
     "id": "030",
     "kind": "gen",
     "gen_command": "gen_random 10 100 1"
   }
   ```
   - Last argument is the seed -- vary it per test.
   - Plan the size progression: small, medium, max.

4. **Compile (best-effort**, see `polygon-spec/compile.md`):
   ```
   g++ -std=c++20 -O2 -o gen generators/{name}.cpp -I <skills>/polygon-spec
   ```

### Step 4: Add anti-hack tests

Either hand-write or write a specialized generator (e.g., `gen_antihash.cpp`, `gen_worstcase.cpp`).

### Step 5: Commit

```
git add tests/ generators/ config/build.json
git commit -m "tests: add {description}"
```

---

## Section D: Reviewing tests

If the user asks to see current tests:
1. Read `tests/spec.json` and list all tests with their IDs, kind, and sample flag.
2. For manual tests, show the contents of `tests/manual/{id}.in` and `tests/answers/{id}.ans`.
3. For gen tests, show the gen command.
4. Report coverage: how many samples, edge cases, stress tests, anti-hack tests.

---

## testlib generator API

- `registerGen(argc, argv, 1)` -- seeds RNG from command-line args. Deterministic for same args.
- `rnd.next(lo, hi)` -- random integer in [lo, hi]
- `rnd.next(0.0, 1.0)` -- random double
- `rnd.next("[a-z]{1,10}")` -- random string matching regex (testlib regex)
- `rnd.perm(n)` / `rnd.perm(n, 1)` -- random permutation (0-indexed / 1-indexed)
- `rnd.partition(size, sum)` -- partition `sum` into `size` non-negative parts
- `println(...)` / `print(...)` -- testlib output helpers (use these, not `cout`)

## Common generator patterns

**Random array**: `rnd.next(1, maxVal)` in a loop.

**Random permutation**:
```cpp
auto p = rnd.perm(n, 1);
```

**Random tree** (random parent):
```cpp
vector<pair<int,int>> edges;
for (int i = 1; i < n; i++)
    edges.push_back({rnd.next(0, i - 1) + 1, i + 1});
shuffle(edges.begin(), edges.end());
```

**Random connected graph** (spanning tree + extra edges):
```cpp
// generate spanning tree first, then add random edges
```

**Star / chain** (edge-case trees):
```cpp
// star: all connect to node 1
// chain: i connects to i+1
```

**Large values**: parameterize via `argv[]` so the same generator covers small through max constraints.

## Rules

- Test IDs must be unique and zero-padded to 3 digits.
- Sample tests come first (001-009).
- Input files must end with exactly one trailing newline, no trailing spaces on lines.
- Generator output must match the exact format the validator expects.
- Always propose the test plan to the user before implementing.
- Use testlib's `print()` / `println()`, not `cout`.
