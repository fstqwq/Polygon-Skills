---
name: polygon-review
description: "Perform a comprehensive review of a competitive programming problem. Use when the user wants to audit the problem for completeness, consistency, and quality before export or contest use."
---

# Review Problem

## Procedure

Run all checks in order. Produce a report in `draft/review.md` with findings grouped by section.

### Step 1: Structural health

Run `python <skills>/polygon-spec/review.py` from the repo root. Include the output in the report.

### Step 2: Statement review

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

Read `config/build.json` for the checker type and `checkers/` for custom checkers.

Check:
- [ ] Checker type is appropriate for the problem (e.g., `wcmp` for exact match, `rcmp6` for floating point)
- [ ] If custom checker: reads jury answer first, then contestant answer (testlib convention)
- [ ] If multiple valid outputs: checker handles all valid forms
- [ ] If floating point: tolerance matches what the statement promises

### Step 5: Test suite review

Read `tests/spec.json` and count tests by category.

Check:
- [ ] At least 1 sample test exists
- [ ] Sample I/O matches what the statement shows
- [ ] Edge cases cover minimum and maximum constraints
- [ ] Stress tests exist at multiple sizes (small, medium, max)
- [ ] If `rej_*` solutions exist: anti-hack tests are designed to break them
- [ ] If multi-test: includes "increasing n" and "max T min n" patterns
- [ ] Total test count is reasonable (typically 15-50 for most problems)

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

### Step 8: Produce the report

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
