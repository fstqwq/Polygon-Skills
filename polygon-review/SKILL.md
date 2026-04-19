---
name: polygon-review
description: "Audit the problem for completeness, consistency, and quality before local zip creation or agent export."
---

# Review Problem

## Procedure

Run all checks in order. Produce a report in `draft/review.md` with findings grouped by section.

### Step 1: Structural health

Run `python <skills>/polygon-spec/review.py` from the repo root. Include the output in the report.

### Step 2: Statement review

Run `python <skills>/polygon-statement/check_formulas.py` on all `.tex` files. Include any warnings in the report.

Read `draft/statement.*.md` and all `statement-sections/<lang>/*.tex`.

Check:
- [ ] **Completeness**: legend, input, output sections all exist and are non-empty
- [ ] **Constraints block**: every variable in the input format has an explicit bound ($1 \le n \le \ldots$)
- [ ] **Integer types**: all input variables are explicitly stated as integers (or reals, strings, etc.)
- [ ] **Multi-test sum**: if multi-test, $\sum n$ constraint is stated
- [ ] **Graph guarantees**: if graph, explicitly states: simple/multi-edge, self-loops, connected/disconnected, directed/undirected
- [ ] **Tree guarantee**: if tree, "it is guaranteed that the input forms a tree"
- [ ] **Degenerate cases**: are edge cases like $n=1$, empty input, answer=0 explicitly allowed or excluded?
- [ ] **Output uniqueness**: if multiple valid outputs, "print any" is stated; if unique, checker matches
- [ ] **Sample explanations**: at least one sample has a note explaining it
- [ ] **Language consistency**: if multiple languages, content matches across all

Report: list each check as PASS / FAIL / N/A with a one-line note.

### Step 3: Validator vs statement

Read `validators/validator.cpp` and cross-check against the statement constraints.

Check:
- [ ] Every constraint in the statement is enforced by the validator
- [ ] The validator does not enforce constraints NOT stated in the statement (hidden constraints)
- [ ] Multi-test: validator checks $\sum n$ if stated
- [ ] Newline / whitespace format matches the input specification exactly
- [ ] `endf()` or `eof()` is called at the end

Report: list mismatches between statement and validator.

### Step 4: Checker review

Read `config/build.json` for `checker_source`. Judging uses that repository source directly; if it matches a standard checker by content, treat it as a standard checker copy.

Check:
- [ ] Checker type is appropriate for the problem (e.g., `wcmp` for exact match, `rcmp6` for floating point)
- [ ] If custom checker: reads jury answer first, then contestant answer (testlib convention)
- [ ] If multiple valid outputs: checker handles all valid forms
- [ ] If floating point: tolerance matches what the statement promises
- [ ] If custom checker: it does not enforce validator-style exact whitespace unless the output format explicitly requires whitespace-sensitive output

### Step 5: Test suite review

Read `tests/spec.json` and count tests by category.

Check:
- [ ] At least 1 sample test exists
- [ ] Sample I/O matches what the statement shows
- [ ] Edge cases cover minimum and maximum constraints
- [ ] Edge cases cover off-by-one boundaries (`min+1`, `N-1`, `N`, `max-1`, `max`)
- [ ] Stress tests exist at multiple sizes (small, medium, near-max, max)
- [ ] Random/stress categories repeat the same parameter shape with multiple seeds
- [ ] If `rej_*` solutions exist: anti-hack tests are designed to break them
- [ ] If multi-test: includes "increasing n" and "max T min n" patterns
- [ ] Total test count is reasonable (typically 35-70 for most problems; fewer than 30 requires an explicit reason)

Report: test count breakdown and coverage gaps.

### Step 6: Solution review

Read `solutions/` and their `.desc` files.

Check:
- [ ] At least one `accepted` solution exists (`std.cpp`)
- [ ] `build.json` `accepted_solution_source` points to an existing file
- [ ] Brute force solution exists (`brute_force.cpp`, expected TLE or accepted)
- [ ] At least one `rejected` solution exists (greedy, dummy, etc.)
- [ ] Solution code style follows `/polygon-solution` conventions (no comments, no return 0, etc.)
- [ ] If multi-language: Java and/or Python translations exist

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
