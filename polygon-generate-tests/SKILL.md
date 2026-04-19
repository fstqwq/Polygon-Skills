---
name: polygon-generate-tests
description: "Design and create test cases -- samples, edge cases, stress tests, anti-hack tests."
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
- **Small exhaustive coverage opportunity**: can all valid instances up to some small bound be enumerated exactly, and if so, how many test files would that require under the repository constraints?

---

## Phase 2: Design the test plan

Write the test plan to `draft/tests.md` before implementing anything. The plan lists all tests grouped into 7 parts. IDs are assigned sequentially -- no gaps, no fixed ranges.

Example plan:

```markdown
# Test Plan

## Part 1: Samples (typically 1-3)
- sample 1 from statement
- sample 2 from statement

## Part 2: Edge cases (typically 6-12)
- n=1, minimum input
- n=N-1 and n=N for maximum-bound off-by-one coverage
- n=min+1 for minimum-bound off-by-one coverage
- all elements equal
- maximum values at minimum size
- already sorted
- reverse sorted

## Part 3: Small exhaustive coverage (typically 3-15)
- enumerate all valid instances up to the largest feasible small bound
- slice the boundary layer if one file would exceed the repository constraints
- keep the exhaustive block compact

## Part 4: Stress / random (typically 15-30)
- gen_random, small (n~10), x3 seeds
- gen_random, medium (n~1000), x3 seeds
- gen_random, near-max (n=N-1), x3 seeds
- gen_random, max (n=N), x3 seeds

## Part 5: Anti-hack (typically 4-10)
- gen_worstcase -- breaks greedy, x3 variants
- manual -- always-YES case, breaks dummy

## Part 6: Max-stress (typically 4-10)
- gen_maxstress -- adversarial structure at N-1 and N, x2 seeds each

## Part 7: Extra
(ask user for additional ideas)
```

IDs are assigned sequentially when implementing (001, 002, ...), no gaps.

### Category guidance

**Part 1 -- Samples**: extracted from the problem statement. `"sample": true`.

**Part 2 -- Edge cases**: walk the constraint boundaries systematically.

| Category | Examples |
|----------|----------|
| Minimum size | n=1, n=0, empty input |
| Minimum off-by-one | n=min, n=min+1 |
| Max values at min size | n=1 with a[i]=10^9 |
| Maximum off-by-one | n=N-1, n=N; m=M-1, m=M; value=max-1, value=max |
| All-same | all elements equal, all edges same weight |
| Sorted / reverse-sorted | already sorted, reverse order |
| Binary | all 0s, all 1s, alternating |
| Boundary values | a[i]=1, a[i]=max, coordinates at limits |
| Special graphs | star, chain, complete, disconnected |
| Trivial answers | guaranteed YES, guaranteed NO, answer=0, answer=max |

Pick the ones relevant to the problem.

**Part 3 -- Small exhaustive coverage**:
- Use this part when the full small state space is enumerable.
- Before generating it, estimate how many test files are needed after applying repository constraints such as `\sum n`.
- Keep the exhaustive block compact; by default, keep it within 20 test files.
- Choose the largest fully covered range that fits this budget.
- If needed, enumerate all cases up to `n = k`, then slice only the boundary layer `n = k + 1`.
- When a canonical encoding exists, enumerate each structure exactly once. For rooted forests given by parents, prefer canonical forms such as `p_i < i`.

**Part 4 -- Stress (random)**: random tests at varying sizes.
- Small (n ~ 5-10): fast, debuggable, good for stress vs brute force
- Medium (n ~ 100-1000): find off-by-one, overflow
- Near-boundary (n = N-1, m = M-1, values = max-1): catches strict-inequality and allocation off-by-one bugs
- Large (n = max): TLE / MLE detection
- For each random size/category, use several different seeds. Default to at least 3 seeds per category; use 5-8 when the generator distribution is broad or branch coverage is uncertain.
- Do not count one random file as coverage for a category. A random category is only covered after repeated seeds with the same parameter shape.

**Part 5 -- Anti-hack**: tests designed to break specific wrong solutions. For each `rej_*` solution, analyze what input would expose it.

| Wrong approach | Anti-hack strategy |
|---------------|-------------------|
| Greedy by value | Construct where greedy ordering fails |
| Always output NO/-1 | Ensure positive cases exist |
| O(n^2) solution | Maximum n to trigger TLE |
| Overflow-prone | Values near 2^31 or 2^63 boundaries |
| Floating-point fragile | Near-degenerate geometry, cancellation, tolerance-boundary answers |

**Part 6 -- Max-stress**: maximum constraints with adversarial structure -- worst-case for the intended algorithm, maximum output size, degenerate structures.
- Include both exact maximum and near-maximum variants (`N-1`, `M-1`, `max_value-1`) unless the constraint makes that meaningless.
- Repeat adversarial generators with different seeds or perturbations so a hard-coded or shape-specific wrong solution cannot pass one instance by accident.

**Part 7 -- Extra**: ask the user: "Do you have any specific test scenarios you want to add?" Add whatever they suggest.

### Domain-specific checklists

Check which of these apply to the problem and incorporate into the plan:

**Multi-test (T test cases)**:
- **Increasing n**: T tests where n grows each case (1, 2, 4, 8, ..., max). Catches solutions that clear arrays to `n+1` but leave stale data from earlier larger cases.
- **Maximum T, minimum n**: T at maximum, each case has n=1 or minimum. Catches solutions that memset `MAXN` every test case (TLE on large T).
- Both patterns are mandatory when multi-test is present.

**Integer overflow / width bugs**:
- If input values can be large, include values around common type boundaries: `2^31-1`, `2^31`, `10^9`, `10^18`, and the stated maximum.
- Include cases where each individual value fits in 32-bit, but sums, prefix sums, products, squared distances, or pair counts exceed 32-bit.
- Include mixed-scale cases in the same test: very small values with very large values, zeros if allowed, and negative values if allowed.
- For binary search or midpoint-heavy problems, include ranges where `l + r` overflows 32-bit and where `r - l` is near the maximum.
- For shortest paths / DP / cost problems, include answers near and above common wrong `INF` sentinels such as `10^9`, `1e18`, and `LLONG_MAX / 4` when meaningful.
- For modular arithmetic, include operands near the modulus, products near `mod^2`, and repeated accumulation that overflows before taking modulo.

**Floating-point / precision bugs**:
- If outputs or computations use real numbers, add cases near the promised tolerance boundary, not only easy integer-looking answers.
- Include very small and very large magnitudes in the same test when the statement allows it; this catches cancellation and relative-error mistakes.
- For geometry, include near-collinear points, almost tangent/intersecting objects, coincident or duplicate points if allowed, and distances/areas close to zero.
- Include cases where the correct answer is exactly zero, very close to zero, and very close to a decision threshold.
- Include both absolute-error-sensitive and relative-error-sensitive cases if the checker allows either.
- Avoid relying only on random floating-point data; handcraft at least a few near-degenerate cases.

**Branching-output problems**:
- If the output has multiple branches such as `YES/NO`, `Alice/Bob`, `possible/impossible`, or `answer / -1`, do not assume random tests cover all branches well.
- If a trusted solution is available, run it on a small random sample before finalizing the plan and record the observed branch distribution.
- If random generation is strongly biased toward one branch, add explicit tests for the underrepresented branch.
- Include both small proof-style cases and at least one nontrivial larger case for the underrepresented branch.
- When reviewing the final tests, check that every intended output branch is represented.

**Trees**:
- Random parent tree (`rnd.next(0, i-1)`) has expected height O(log n) -- this is too shallow if tree depth matters.
- For problems where depth matters (e.g., heavy-light decomposition, centroid decomposition, Euler tour): use Prufer sequence or rejection sampling to generate trees with expected depth O(sqrt(n)).
- Include both deep (chain-like) and shallow (star-like) trees in the plan.

**Graphs / shortest paths**:
- If SPFA or Bellman-Ford might be used as wrong solutions, add anti-SPFA tests:
  - Grid graphs (n x m grid, edges to adjacent cells)
  - Constructed graphs that force exponential relaxations under SLF optimization
  - Large cycles with perturbation
  - Binary tree shaped graphs
- Add random noise/edge shuffling to all constructed graphs to prevent special-case detection.

**Geometry**:
- Convex hull point count matters -- ensure generated point sets have large convex hulls (many points on the hull), not just random points in a square (which gives O(log n) hull points).
- For simple polygon problems: ask the user to reference ICPC 2017 "Airport Construction" test data for high-quality polygon generation patterns.
- Include degenerate cases: collinear points, coincident points, very small/large coordinates.

Show the draft plan to the user and iterate before implementing. If small exhaustive coverage is planned, include the estimated file count and chosen cutoff.

---

## Phase 3: Implement the tests

After the user approves the plan, implement each part sequentially. IDs are continuous across all parts.

### Manual tests

1. Write `tests/manual/{id}.in` (ends with newline, no trailing spaces)
2. Do **not** write `tests/answers/{id}.ans`; committed answer files are not part of the source repository or package
3. Add to `tests/spec.json`:
   ```json
   {
     "id": "001",
     "kind": "manual",
     "sample": true
   }
   ```
   Ordinary non-interactive sample tests: `"sample": true`, omit `sample_input`/`sample_output`. The statement uses the real `tests/manual/{id}.in`, and displayed output comes from generated official answers.
   Only add `sample_input`/`sample_output` when the statement must override the displayed sample text, such as interactive problems, spoiler-sensitive samples, or cleaner fixed-format presentation.
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
   Code style (same as `/polygon-solution`): no comments, no `return 0;`.

2. **Register in config/build.json**:
   ```json
   "generator_sources": ["generators/gen_random.cpp"]
   ```

3. **Wire into spec.json** and **create the generator payload file**:

   Add the entry to `tests/spec.json`:
   ```json
   {
     "id": "008",
     "kind": "gen"
   }
   ```

   Write the generator command to `tests/generator/008.in`:
   ```
   gen_random 5 100 1
   ```
   Last argument is the seed -- vary it per test. The payload file contains the full command line (generator name + arguments).

   For random/stress generators, write multiple payload files with the same parameter shape and different seeds. For boundary-sensitive dimensions, include both exact and off-by-one values such as `N-1`, `N`, `M-1`, `M`, `max_value-1`, and `max_value`.

4. **Compile (best-effort**, see `polygon-spec/compile.md`):
   ```
   mkdir -p temp
   g++ -std=c++20 -O2 -o temp/gen generators/{name}.cpp -I <skills>/polygon-spec
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
2. For manual tests, show `tests/manual/{id}.in` and any `sample_output` override from `tests/spec.json`.
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

## Common generator patterns

**Random array**: `rnd.next(1, maxVal)` in a loop.

**Random permutation**:
```cpp
auto p = rnd.perm(n, 1);
```

**Random tree** (random parent + shuffle labels):
```cpp
auto label = rnd.perm(n, 1);
vector<pair<int,int>> edges;
for (int i = 1; i < n; i++)
    edges.push_back({label[rnd.next(0, i - 1)], label[i]});
shuffle(edges.begin(), edges.end());
```
Always shuffle node labels -- otherwise node 1 is always the root and low-numbered nodes are always near the top.

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
- If you plan small exhaustive coverage, estimate the required number of files first and keep that block within 20 files by default.
- Most finished problems should have roughly 20-70 tests. Fewer than 20 tests needs an explicit reason, such as tiny exhaustive coverage, very expensive tests, or an interactive format with limited meaningful cases.
- If `tests/spec.json` is reduced or reorganized, remove unreferenced files from the test directories.
