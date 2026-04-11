---
name: polygon-generate-tests
description: "Design and create test cases for a competitive programming problem -- samples, edge cases, stress tests, anti-hack tests, and max-stress tests. Guides test suite design methodology."
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

Write the test plan to `draft/tests.md` before implementing anything. The plan lists all tests grouped into 6 parts. IDs are assigned sequentially -- no gaps, no fixed ranges.

Example plan:

```markdown
# Test Plan

## Part 1: Samples
- 001: sample 1 from statement (sample=true)
- 002: sample 2 from statement (sample=true)

## Part 2: Edge cases
- 003: n=1, minimum input
- 004: all elements equal
- 005: maximum values at minimum size
- 006: already sorted
- 007: reverse sorted

## Part 3: Stress (random)
- 008: gen_random 5 100 1 (small)
- 009: gen_random 50 1000 2 (medium)
- 010: gen_random 200000 1000000000 3 (max)
- 011: gen_random 200000 1000000000 4 (max)
- 012: gen_random 200000 1000000000 5 (max)

## Part 4: Anti-hack
- 013: gen_worstcase 200000 1 (breaks greedy)
- 014: manual -- always-YES case (breaks dummy)

## Part 5: Max-stress
- 015: gen_maxstress 200000 1 (adversarial structure)
- 016: gen_maxstress 200000 2

## Part 6: Extra
(ask user for additional ideas)
```

### Category guidance

**Part 1 -- Samples**: extracted from the problem statement. `"sample": true`.

**Part 2 -- Edge cases**: walk the constraint boundaries systematically.

| Category | Examples |
|----------|----------|
| Minimum size | n=1, n=0, empty input |
| Max values at min size | n=1 with a[i]=10^9 |
| All-same | all elements equal, all edges same weight |
| Sorted / reverse-sorted | already sorted, reverse order |
| Binary | all 0s, all 1s, alternating |
| Boundary values | a[i]=1, a[i]=max, coordinates at limits |
| Special graphs | star, chain, complete, disconnected |
| Trivial answers | guaranteed YES, guaranteed NO, answer=0, answer=max |

Pick the ones relevant to the problem.

**Part 3 -- Stress (random)**: random tests at varying sizes.
- Small (n ~ 5-10): fast, debuggable, good for stress vs brute force
- Medium (n ~ 100-1000): find off-by-one, overflow
- Large (n = max): TLE / MLE detection

**Part 4 -- Anti-hack**: tests designed to break specific wrong solutions. For each `rej_*` solution, analyze what input would expose it.

| Wrong approach | Anti-hack strategy |
|---------------|-------------------|
| Greedy by value | Construct where greedy ordering fails |
| Always output NO/-1 | Ensure positive cases exist |
| O(n^2) solution | Maximum n to trigger TLE |
| Overflow-prone | Values near 2^31 or 2^63 boundaries |

**Part 5 -- Max-stress**: maximum constraints with adversarial structure -- worst-case for the intended algorithm, maximum output size, degenerate structures.

**Part 6 -- Extra**: ask the user: "Do you have any specific test scenarios you want to add?" Add whatever they suggest.

Show the draft plan to the user and iterate before implementing.

---

## Phase 3: Implement the tests

After the user approves the plan, implement each part sequentially. IDs are continuous across all parts.

### Manual tests

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
   Non-sample manual tests: `"sample": false`, omit `sample_input`/`sample_output`.

### Generated tests

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
   Code style (same as `/polygon-solution`): no comments, no `return 0;`, use `print()`/`println()`.

2. **Register in config/build.json**:
   ```json
   "generator_sources": ["generators/gen_random.cpp"]
   ```

3. **Wire into spec.json**:
   ```json
   {
     "id": "008",
     "kind": "gen",
     "gen_command": "gen_random 5 100 1"
   }
   ```
   Last argument is the seed -- vary it per test.

4. **Compile (best-effort**, see `polygon-spec/compile.md`):
   ```
   g++ -std=c++20 -O2 -o gen generators/{name}.cpp -I <skills>/polygon-spec
   ```

### Commit

```
git add tests/ generators/ config/build.json draft/tests.md
git commit -m "tests: add {description}"
```

---

## Section D: Reviewing tests

If the user asks to see current tests:
1. Read `tests/spec.json` and list all tests with their IDs, kind, and sample flag.
2. For manual tests, show `tests/manual/{id}.in` and `tests/answers/{id}.ans`.
3. For gen tests, show the gen command.
4. Report coverage: how many samples, edge cases, stress, anti-hack, max-stress.

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
- IDs are sequential with no gaps across all parts.
- Sample tests must come first.
- Input files must end with exactly one trailing newline, no trailing spaces on lines.
- Generator output must match the exact format the validator expects.
- Always write the test plan to `draft/tests.md` and get user approval before implementing.
- Use testlib's `print()` / `println()`, not `cout`.
