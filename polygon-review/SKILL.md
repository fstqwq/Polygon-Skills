---
name: polygon-review
description: "Audit the problem for completeness, consistency, and quality before local zip creation or agent export."
---

# Review Problem

## Review posture

Be skeptical. Local green runs are not final proof, especially for timing-sensitive Python or C++ behavior. Look for contestant failure modes and for tests that were shaped around existing solutions instead of the stated problem.

## Procedure

Run all checks in order. Produce a report in `draft/review.md` with findings grouped by section.

### Step 1: Structural health

Run `python <skills>/polygon-spec/review.py` from the repo root. Include the output in the report.

### Step 2: Statement review

Run `python <skills>/polygon-statement/check_formulas.py` on all `.tex` files. Include any warnings in the report.

Read `draft/statement.*.md` and all `statement-sections/<lang>/*.tex`.

Check:
- [ ] **Completeness**: legend, input, output sections all exist and are non-empty
- [ ] **English style**: English uses American spelling and an appropriately title-cased problem name
- [ ] **Legend prose**: when the problem has a meaningful natural-language setting, formulas in the Legend are limited to those that materially improve clarity; formal definitions, coordinates, limits, and input guarantees are deferred to Input where possible
- [ ] **Constraints block**: every variable in the input format has an explicit bound ($1 \le n \le \ldots$)
- [ ] **Integer types**: all input variables are explicitly stated as integers (or reals, strings, etc.)
- [ ] **Multi-test sum**: if multi-test, $\sum n$ constraint is stated
- [ ] **Graph guarantees**: if graph, explicitly states: simple/multi-edge, self-loops, connected/disconnected, directed/undirected
- [ ] **Tree guarantee**: if tree, "it is guaranteed that the input forms a tree"
- [ ] **Degenerate cases**: are edge cases like $n=1$, empty input, answer=0 explicitly allowed or excluded?
- [ ] **Output uniqueness**: if multiple valid outputs, "output any" is stated; if unique, checker matches
- [ ] **Variables and TeX**: symbols are not reused for different objects, ordinary variables are lowercase, multi-letter names are upright, and formulas are punctuated as sentence parts
- [ ] **Standard wording**: applicable Input, Output, guarantee, and definition text agrees with `/polygon-statement` references
- [ ] **Samples**: at least two distinct samples exist by default and cover every output form
- [ ] **Sample explanations**: at least two samples have useful notes by default, and every potentially confusing sample is explained; honor explicit problem-specific user decisions
- [ ] **Language consistency**: if multiple languages, content matches across all

Report: list each check as PASS / FAIL / N/A with a one-line note.

### Step 3: Validator vs statement

Read `validators/validator.cpp` and cross-check against the statement constraints.

Check:
- [ ] Every constraint in the statement is enforced by the validator
- [ ] The validator does not enforce constraints NOT stated in the statement (hidden constraints)
- [ ] Multi-test: validator checks $\sum n$ if stated
- [ ] Names passed to `read*` calls match the corresponding statement symbols
- [ ] Array-reading functions are used when they match the input line and improve clarity
- [ ] Cross-test sums are updated and checked immediately after each relevant test point
- [ ] Newline / whitespace format matches the input specification exactly
- [ ] `endf()` or `eof()` is called at the end

Report: list mismatches between statement and validator.

### Step 4: Checker review

Read `config/build.json` for `checker_source`. Judging uses that repository source directly; if it matches a standard checker by content, treat it as a standard checker copy.

Check:
- [ ] Checker type is appropriate for the problem; when applicable prefer `ncmp`, then `nyesno`, then `wcmp`, and use an `rcmp` variant for floating point
- [ ] If custom checker: reads jury answer first, then contestant answer through a function named `readAns`
- [ ] If custom checker: resets all per-answer global state at the beginning of `readAns`
- [ ] If multiple valid outputs: checker handles all valid forms
- [ ] If floating point: tolerance matches what the statement promises
- [ ] If custom checker: it does not enforce validator-style exact whitespace unless the output format explicitly requires whitespace-sensitive output
- [ ] If custom checker: prefers `readToken()` to `readLine()` and gives explicit bounds or bounded patterns for values read from `ouf` and `ans`
- [ ] Checker messages are clear and do not reveal hidden answers or solution ideas

### Step 5: Test suite review

Read `tests/spec.json` and count tests by category.

Check:
- [ ] At least 2 distinct sample tests exist by default; any deliberate exception follows an explicit problem-specific user instruction
- [ ] Sample I/O matches what the statement shows
- [ ] Edge cases cover minimum and maximum constraints
- [ ] Edge cases cover off-by-one boundaries (`min+1`, `N-1`, `N`, `max-1`, `max`)
- [ ] Integer-heavy tests cover overflow risks: large sums/products/squares, type boundaries, and wrong `INF` sentinels
- [ ] Floating-point tests cover precision risks: near-zero, tolerance-boundary, mixed-magnitude, and near-degenerate cases
- [ ] Stress tests exist at multiple sizes (small, medium, near-max, max)
- [ ] A large-random stress mode is suitable for comparing independently implemented correct solutions
- [ ] A small-random stress mode is suitable for comparison with the brute-force solution
- [ ] Random/stress categories repeat the same parameter shape with multiple seeds
- [ ] Generator modes collectively cover the full legal input space without accidental assumptions such as fixed sizes, distinct values, narrower ranges, connected graphs, or non-degenerate geometry
- [ ] Targeted anti-hack tests, when present, are mapped to the specific rejected solutions they are intended to break
- [ ] If multi-test: includes "increasing n" and "max T min n" patterns
- [ ] Total test count is reasonable (typically 20-70 for most problems; fewer than 20 requires an explicit reason)
- [ ] No tests appear weakened, deleted, or avoided only because a current solution failed them

Report: test count breakdown and coverage gaps.

### Step 6: Solution review

Read `solutions/` and their `.desc` files.

Check:
- [ ] At least one `accepted` solution exists (`std.cpp`)
- [ ] `build.json` `accepted_solution_source` points to an existing file
- [ ] An independently implemented second correct solution exists unless the user narrowed the requested solution set
- [ ] Accepted solutions are benchmarked against the target of half TL and half ML, with exceptions reported
- [ ] Brute force solution exists (`brute_force.cpp`, expected TLE or accepted)
- [ ] The brute force directly follows the statement and produces only correct results or TLE
- [ ] Correct-but-too-slow translations use `tle_or_correct`, not plain `time_limit_exceeded`
- [ ] At least one `rejected` solution exists (greedy, dummy, etc.)
- [ ] Important overflow risks have been audited and representative rejected variants exist where useful
- [ ] If the intended algorithm uses casework, the complete implementation and representative omitted-branch variants exist
- [ ] Optimized slow solutions remain unable to pass the configured limits
- [ ] Solution code style follows `/polygon-solution` conventions (no comments, no return 0, etc.)
- [ ] A Python reference exists when C++ arithmetic has meaningful overflow risk
- [ ] A Java correct solution exists when measured C++ time above one quarter of TL or memory above about 50 MB makes Java performance a concern
- [ ] Timing-sensitive accepted/TLE expectations are backed by online Verification or clearly marked as local-only uncertainty

Report: solution inventory with expected verdicts.

### Step 7: Cross-consistency

Check relationships between components:
- [ ] Validator input format matches generator output format
- [ ] Sample test files match sample I/O in spec.json
- [ ] If interactive: interactor exists, `problem.json` has `"mode": "interactive"`
- [ ] If multi-pass: `pass_limit` is set correctly
- [ ] `build.json` references only files that exist

**Generator determinism**: read every generator source file and flag non-deterministic patterns:

| Pattern | Risk | Fix |
|---------|------|-----|
| `rand()`, `srand()`, `random()` | Platform-dependent RNG | Use `rnd.next()` from testlib |
| `time()`, `clock()`, `chrono::` | Time-seeded randomness | Remove; testlib seeds from argv |
| `&var`, pointer arithmetic | Address-dependent output | Remove address-based logic |
| `unordered_map`, `unordered_set` iteration | Iteration order varies across platforms/runs | Use `map`/`set`, or sort before output |
| `std::shuffle` with `default_random_engine` | Platform-dependent engine | Use testlib's `shuffle()` with `rnd` |
| Missing `registerGen(argc, argv, 1)` | No deterministic seeding | Add as first line of main |

### Step 8: Compilation check (best-effort)

Attempt to compile all C++ sources (see `polygon-spec/compile.md` for flags):

```
g++ -std=c++20 -O2 -fsyntax-only <file>.cpp -I <skills>/polygon-spec
```

Check each component:
- [ ] Validator compiles
- [ ] Checker compiles (if custom)
- [ ] Interactor compiles (if interactive)
- [ ] All generators compile
- [ ] All C++ solutions compile

Use `-fsyntax-only` for speed -- no need to produce binaries. If no compiler is available, skip this step and note it in the report.

### Step 9: Produce the report

Write the full report to `draft/review.md`:

```markdown
# Problem Review: {slug}

## Summary
- Status: READY / NOT READY
- Blocking issues: N
- Warnings: N

## Structural Health
(review.py output)

## Statement: {PASS/FAIL}
(checklist results)

## Validator vs Statement: {PASS/FAIL}
(mismatches)

## Checker: {PASS/FAIL}
(findings)

## Test Suite: {PASS/FAIL}
(coverage breakdown)

## Solutions: {PASS/FAIL}
(inventory)

## Cross-consistency: {PASS/FAIL}
(findings)

## Action Items
1. (highest priority fix)
2. ...
```

Show the report to the user and suggest which `/polygon-*` skill to use for each action item.

## Rules

- This skill is read-only -- it does not modify any files (except writing `draft/review.md`).
- Report facts, not opinions. If something is ambiguous, flag it as a question for the user.
- Do not auto-fix issues. List them and point to the right skill.
- The agent CAN and SHOULD read all source files to perform semantic checks (not just structural).
- Do not recommend changing the local runtime environment, weakening tests, or lowering constraints just to make a local run pass.
