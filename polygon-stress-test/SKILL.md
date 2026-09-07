---
name: polygon-stress-test
description: >-
  Stress-test competitive-programming solutions and improve test coverage
  for Polygon problems. Use when asked to "hack a solution" by finding
  and verifying a counterexample within the problem constraints, assess
  test coverage, check worst-case performance, or fix a specified
  implementation using a failing test.
---

# Stress-Test the Problem

## Purpose

In this competitive-programming workflow, "hack a solution" means finding a legal input that makes the supplied solution produce a wrong answer, a runtime error, or a time-limit failure. Inputs must satisfy the statement and validator constraints.

Use this skill in one of two modes:

- **Audit mode**: inspect the current problem data and solution set, discover weak coverage or plausible wrong solutions, and recommend targeted additions. Use this after the statement, checker, validator, and at least one intended solution direction exist.
- **Targeted mode**: test one supplied solution by finding a legal counterexample, or repair one specified implementation against a supplied failing test. This mode starts from a concrete artifact and should not expand into a general audit.

If the user supplies code to stress-test or a failing input to fix, choose targeted mode unless they explicitly request a broader audit. Add counterexamples to the formal test suite only when the user explicitly asks.

Audit mode combines three tracks:
- **Public-artifact coverage analysis**: assume a contestant sees the statement, checker, and generator source, but not tests, `std.cpp`, accepted solutions, or private reasoning.
- **Bugged-intended solution analysis**: start from the intended algorithm and introduce plausible contestant mistakes.
- **Independent subagent search**: split counterexample discovery across fresh subagents with no inherited context, so each worker explores a different failure mode instead of converging on the coordinator's assumptions.

## Targeted Workflow

Targeted work is hypothesis-driven: trace the supplied code or failing input, identify one concrete failure mechanism, and verify the result. Do not run the audit mode's broad candidate-discovery workflow.

1. **Fix the target and success condition.**
   - Use the exact code or input named by the user.
   - For a counterexample-search request, success means a validator-legal input on which the target demonstrably gets WA, RE, TLE, or another intended failing verdict.
   - For a data-to-repair request, success means the specified implementation handles that input for the general reason revealed by the failure and continues to pass relevant regressions.
   - If a failing input is supplied but several implementations could be "current," identify the configured or actively edited implementation only when unambiguous; otherwise ask which file to change.

2. **Read only the necessary context.**
   - Always read the target code or failing input in full.
   - Read the relevant statement semantics, limits, validator, and checker behavior needed to decide legality and correctness.
   - Use the configured accepted solution, a small brute-force oracle, or a directly proved expected answer as appropriate. Do not inventory unrelated rejected solutions or generator strategies unless they bear on the concrete target.

3. **Reproduce before changing anything.**
   - Compile the target using `/polygon-spec/compile.md` where applicable.
   - For a supplied test, validate it and reproduce the target's actual output, exit status, time behavior, and checker verdict.
   - If the input is invalid or the claimed failure cannot be reproduced, report that evidence instead of editing code speculatively.

4. **Assess difficulty before delegating.**
   - Make a short direct attempt first to understand the target and estimate the structural difficulty. Do not invoke the audit mode's mandatory five discovery passes.
   - If the problem structure or failure mechanism appears complex, try the targeted task from scratch with a fresh independent subagent that inherits no conversation context. If it appears straightforward, continue directly.
   - When two genuinely different fresh attempts would help, use at most **two subagents total**, which may run in parallel. Each must start without inherited context.
   - Pass the raw target and only the authoritative problem context needed to solve it. Do not prime the subagents with the coordinator's hypotheses, suspected bug, partial conclusions, or failed search path.
   - Ask each subagent to solve the same concrete target independently, not to enumerate unrelated failure modes, audit the whole repository, or modify files. The coordinator remains responsible for reproducing and verifying any result.

5. **When given code, find a counterexample for that code.**
   - Trace its assumptions, branches, numeric ranges, state transitions, and complexity against the specification.
   - Form a specific failure hypothesis before searching broadly. Prefer a minimal hand-derived witness; use exhaustive or differential search over small legal instances when it is more reliable.
   - Minimize the witness without removing the failure mechanism.
   - For randomized or heuristic targets, require a counterexample that remains effective across seed changes and reasonable parameter changes. Prefer a structural failure with guaranteed or consistently high failure probability; test multiple seeds and nearby parameter settings when they are controllable. Do not accept a witness that succeeds only for one unlucky seed or one narrowly tuned configuration.
   - Validate the input, establish the expected result with a trustworthy oracle, run the target, and confirm the predicted failure. A merely suspicious code path is not a verified counterexample.
   - Keep exploratory programs and inputs under `temp/`. Do not add the witness to the formal suite unless requested.

6. **When given data, repair the implementation.**
   - Trace the exact failing execution and state the root cause before patching.
   - Make the smallest general correction that restores the intended invariant. Do not hardcode the supplied input, add a one-case exception, or weaken the checker, validator, constraints, or tests.
   - Re-run the supplied input, samples, relevant existing tests, and nearby boundary cases aimed at the same bug class. Use a brute-force or differential check when the state space permits.
   - If the input instead exposes a statement, validator, checker, or oracle defect, report the actual faulty component rather than forcing the target implementation to accommodate it.

7. **Report evidence, not a candidate list.**
   - For a verified counterexample, provide the input, expected versus actual behavior, and exact failure mechanism.
   - For a successful repair, provide the root cause, the general fix, and the regression evidence.
   - Do not require `draft/stress-tests.md` or a separate plan-approval checkpoint for the targeted action already requested. Use them only if the user expands the task into audit mode or asks to preserve a broader plan.

## Audit Workflow

1. **Read the problem surface.**
   - Read `statement-sections/english/input.tex`, `output.tex`, and relevant statement text.
   - Read `config/problem.json` and `config/build.json`.
   - Read the configured checker and generator sources. If the user specified files, use exactly those files.
   - Read `validators/validator.cpp` for input bounds and format.
   - Read existing `solutions/` only for inventory. Do not use accepted solutions for the public-artifact coverage analysis track.

2. **Create or update `draft/stress-tests.md` before writing code.**
   Use this structure:

   ```markdown
   # Stress-Test Plan

   ## Coverage Analysis Model
   - Public artifacts visible to the reviewer:
   - Files intentionally hidden from the reviewer:

   ## Candidate Wrong Solutions
   | Name | Track | Idea | Expected failure | Counterexample shape |
   |------|-------|------|------------------|----------------------|

   ## Subagent Findings
   | Agent | Inputs | Search mode | Candidates | Best counterexample |
   |-------|--------|-------------|------------|---------------------|

   ## Planned Tests
   | Test idea | Kind | Targets | Notes |
   |-----------|------|---------|-------|

   ## Verification Notes
   - Local results are advisory.
   - Final verdicts require Polygon-Replica Verification.
   ```

3. **Run mandatory independent subagent passes.**
   This skill expects subagent support. Spawn each subagent with **no inherited context**; pass only the explicit prompt and listed file excerpts. If the runtime cannot spawn independent subagents, stop and tell the user that the full audit workflow cannot be performed.

   Required subagents:
   - **A. Standard worst-case designer**: give the statement, limits, validator bounds, and configured standard solution. Ask for legal cases that make the standard solution run slowest.
   - **B. Rejected-code brute-force mutator**: give the statement and existing rejected solution source(s). Ask for a plausible wrong solution based on them using brute force plus constant-factor optimization.
   - **C. Rejected-code randomized mutator**: give the statement and existing rejected solution source(s). Ask for a plausible wrong solution based on them using randomized or probabilistic heuristics.
   - **D. Tag-diverse wrong-algorithm designer**: give the statement and one assigned tag from `graphs`, `dp`, `greedy`, `hash`, `geometry`; the tag must differ from the standard solution's main technique.
   - **E. Second tag-diverse wrong-algorithm designer**: same as D, but with a different assigned tag.

   The coordinator chooses tags for D/E after reading the configured standard solution. Do not assign a tag that matches the standard solution's main technique, and do not assign the same tag twice.

   Record each subagent result in `draft/stress-tests.md` under `## Subagent Findings` before selecting candidates.

4. **Derive bugged-intended candidates.**
   Look for realistic mistakes:
   - off-by-one boundaries
   - overflow or wrong numeric type
   - wrong tie handling
   - missing output branch
   - stale state across test cases
   - incorrect indexing or coordinate convention
   - precision or tolerance mistakes
   - algorithm that is correct on samples/randoms but not general
   - too-slow near-correct implementation

   For overflow candidates, identify the exact variable, array size, accumulator, product, square, index expression, or sentinel that fails. For casework candidates, identify the exact omitted branch.

5. **Show `draft/stress-tests.md` and get user approval before writing files.**
   Do not create wrong solutions or tests until the user approves the selected candidates.

6. **Implement approved wrong solutions.**
   - Name files `solutions/rej_stress_<slug>.cpp`.
   - Write matching `.desc` files, usually `expected: rejected`.
   - Follow `/polygon-solution` style rules. Read `draft/solutions.md` and any applicable
     `draft/solution-style.<ext>` first; imitate the saved reference for rejected solutions
     within its recorded scope.
   - Do not add these as accepted solutions in `config/build.json`.

7. **Implement and verify counterexamples.**
   - Prefer a minimal manual counterexample.
   - Keep exploratory counterexamples under `temp/`.
   - Validate every counterexample with `validators/validator.cpp`.
   - Run the configured accepted solution to establish the expected behavior.
   - Run the targeted rejected solution and confirm that it fails for the predicted reason.
   - In `draft/stress-tests.md`, map each counterexample to the targeted `rej_stress_*` solution and its failure mechanism.
   - If the user explicitly asks to add the counterexample to the formal suite, follow `/polygon-generate-tests` for `tests/spec.json`, IDs, payloads, and sample handling. Add or extend a generator only when several related counterexamples or stress shapes are needed.

8. **Validate best-effort.**
   - Compile new C++ solutions and generators using `/polygon-spec/compile.md`.
   - Run local checks only as advisory diagnostics.
   - Use online Polygon-Replica Verification for final verdicts.

## Audit-Mode Subagent Prompt Templates

General requirements for every subagent:

- Start with no inherited context.
- Do not assume files, decisions, or private reasoning not provided in the prompt.
- Return concrete wrong-solution ideas and legal counterexample shapes.
- Prefer executable C++ strategies and generator-friendly test shapes.
- Do not modify repository files directly; the coordinator decides what to implement.

### A. Standard Worst-Case Designer

Pass the statement, constraints, validator bounds, and configured standard solution source.

```text
You are stress-testing the intended solution of a competitive programming problem.

Inputs provided:
- statement excerpts
- constraints and limits
- validator bounds
- configured standard solution source

Goal: construct legal input cases that make the standard solution run as slowly as possible while still being valid tests.

Return 3-8 candidate test shapes. For each candidate, include:
- short name
- why it is legal
- why it stresses the standard solution
- expected asymptotic or implementation bottleneck
- concrete minimal example if possible
- generator strategy for large/max cases

Do not propose invalid inputs. Do not weaken constraints or time limits.
```

### B. Rejected-Code Brute-Force Mutator

Pass the statement and existing `solutions/rej_*` source excerpts.

```text
You are designing a plausible rejected C++ solution for a competitive programming problem.

Inputs provided:
- statement excerpts
- existing rejected solution source(s)

Goal: build on these rejected ideas and propose a wrong solution that uses brute force with constant-factor optimization, pruning, bitsets, precomputation, or other speed tricks. The solution should be tempting and might pass weak tests, but must be wrong or too slow on strong tests.

Return 3-8 candidates. For each candidate, include:
- short name
- algorithm sketch
- why it might pass weak tests
- why it is wrong or too slow in general
- counterexample shape
- whether C++ implementation is straightforward
```

### C. Rejected-Code Randomized Mutator

Pass the statement and existing `solutions/rej_*` source excerpts.

```text
You are designing a plausible rejected C++ solution for a competitive programming problem.

Inputs provided:
- statement excerpts
- existing rejected solution source(s)

Goal: build on these rejected ideas and propose a wrong solution that uses randomization, sampling, shuffling, hashing, local search, Monte Carlo checks, or probabilistic heuristics. The solution should be tempting and might pass weak tests, but must be wrong or flaky on strong tests.

Return 3-8 candidates. For each candidate, include:
- short name
- randomized algorithm sketch
- why it might pass weak tests
- why it is wrong or flaky in general
- deterministic or high-probability counterexample shape
- whether C++ implementation is straightforward
```

### D/E. Tag-Diverse Wrong-Algorithm Designer

Pass the statement and exactly one assigned tag. Candidate tags are `graphs`, `dp`, `greedy`, `hash`, `geometry`. The coordinator must choose tags that differ from the standard solution's main technique and from each other.

```text
You are designing a plausible wrong C++ solution for a competitive programming problem.

Inputs provided:
- statement excerpts
- assigned algorithm tag: <TAG>

Goal: propose solutions that interpret the problem through the assigned tag, even if that is not the intended technique. The result should be plausible enough to write as a rejected solution and useful for generating targeted counterexample tests.

Return 3-8 candidates. For each candidate, include:
- short name
- assigned-tag algorithm sketch
- why a contestant might believe it
- why it is wrong or incomplete
- counterexample shape
- whether C++ implementation is straightforward
```

### Public-Artifact Coverage Analyst

Pass only the public artifacts. Do not pass tests, accepted solutions, `std.cpp`, or private analysis.

```text
You are assessing test coverage for a competitive programming problem from the perspective of a contestant who can see the statement, checker source, and generator source. You cannot see hidden tests or accepted solutions.

Goal: propose C++ solutions that are not general but might pass weak tests by relying on likely generator distributions, permissive checker behavior, special cases within the constraints, or statement ambiguity revealed by the public artifacts.

Inputs provided:
- statement excerpts
- problem limits
- checker source
- generator source
- validator bounds if needed for legal input shape

Return 3-8 candidates. For each candidate, include:
- short name
- coverage gap or incorrect assumption
- why it might pass weak tests
- why it is wrong in general
- minimal counterexample or generator shape that should reject it
- whether full C++ code is straightforward

Do not use or assume hidden tests, std solution, accepted solutions, or private author intent.
```

## Rules

- Do not weaken tests, checker, constraints, or time limits to make a rejected solution fail.
- If the checker accepts invalid contestant output, record a checker issue instead of hiding it with tests.
- If `std.cpp` fails a proposed counterexample test, investigate `std.cpp`, the validator, and the statement before weakening the test.
- Prefer a few high-value findings with clear counterexamples over many vague wrong solutions.
- A counterexample-search request needs to demonstrate a failure in the selected target, not every rejected solution in repository history.
- In targeted mode, do not turn one supplied code or test artifact into an unsolicited full-problem audit.
- Do not claim a verified counterexample or repair from reasoning alone; reproduce and verify the observed behavior whenever the local artifacts permit it.
- Do not add exploratory counterexamples to the formal test suite without explicit user direction.
- Keep all temporary files under `temp/`.
- Add approved wrong solutions only after showing the user the code/test plan. Add counterexamples to the formal test suite only when the user explicitly requests it.
