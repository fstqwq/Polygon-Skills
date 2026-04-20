---
name: polygon-hack
description: "Generate adversarial wrong solutions and tests that hack them. Use when Codex needs to test whether a problem can be passed by non-general solutions, public-artifact exploits, or common incorrect variants of the intended solution."
---

# Hack the Problem

## Purpose

Use this skill after the statement, checker, validator, and at least one intended solution direction exist. The goal is to find solutions that should not pass, then add tests that reject them.

This skill combines two tracks:
- **Public-artifact attacks**: assume a contestant sees the statement, checker, and generator source, but not tests, `std.cpp`, accepted solutions, or private reasoning.
- **Bugged-intended attacks**: start from the intended algorithm and introduce plausible contestant mistakes.
- **Independent subagent search**: split hack discovery across fresh subagents with no inherited context, so each worker explores a different failure mode instead of converging on the coordinator's assumptions.

## Procedure

1. **Read the problem surface.**
   - Read `statement-sections/english/input.tex`, `output.tex`, and relevant statement text.
   - Read `config/problem.json` and `config/build.json`.
   - Read the configured checker and generator sources. If the user specified files, use exactly those files.
   - Read `validators/validator.cpp` for input bounds and format.
   - Read existing `solutions/` only for inventory. Do not use accepted solutions for the public-artifact attack track.

2. **Create or update `draft/hacks.md` before writing code.**
   Use this structure:

   ```markdown
   # Hack Plan

   ## Attack Model
   - Public artifacts visible to attacker:
   - Files intentionally hidden from attacker:

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
   This skill expects subagent support. Spawn each subagent with **no inherited context**; pass only the explicit prompt and listed file excerpts. If the runtime cannot spawn independent subagents, stop and tell the user that the full hack workflow cannot be performed.

   Required subagents:
   - **A. Standard worst-case designer**: give the statement, limits, validator bounds, and configured standard solution. Ask for legal cases that make the standard solution run slowest.
   - **B. Rejected-code brute-force mutator**: give the statement and existing rejected solution source(s). Ask for a plausible wrong solution based on them using brute force plus constant-factor optimization.
   - **C. Rejected-code randomized mutator**: give the statement and existing rejected solution source(s). Ask for a plausible wrong solution based on them using randomized or probabilistic heuristics.
   - **D. Tag-diverse wrong-algorithm designer**: give the statement and one assigned tag from `graphs`, `dp`, `greedy`, `hash`, `geometry`; the tag must differ from the standard solution's main technique.
   - **E. Second tag-diverse wrong-algorithm designer**: same as D, but with a different assigned tag.

   The coordinator chooses tags for D/E after reading the configured standard solution. Do not assign a tag that matches the standard solution's main technique, and do not assign the same tag twice.

   Record each subagent result in `draft/hacks.md` under `## Subagent Findings` before selecting candidates.

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

5. **Show `draft/hacks.md` and get user approval before writing files.**
   Do not create wrong solutions or tests until the user approves the selected candidates.

6. **Implement approved wrong solutions.**
   - Name files `solutions/rej_hack_<slug>.cpp`.
   - Write matching `.desc` files, usually `expected: rejected`.
   - Follow `/polygon-solution` style rules.
   - Do not add these as accepted solutions in `config/build.json`.

7. **Implement hack tests.**
   - Use manual tests for minimal counterexamples.
   - Add or extend generators only when several related counterexamples or stress shapes are needed.
   - Follow `/polygon-generate-tests` rules for `tests/spec.json`, test IDs, generator payloads, and sample handling.
   - In `draft/hacks.md`, map each new test idea to the `rej_hack_*` solution(s) it should reject.

8. **Validate best-effort.**
   - Compile new C++ solutions and generators using `/polygon-spec/compile.md`.
   - Run local checks only as advisory diagnostics.
   - Use online Polygon-Replica Verification for final verdicts.

## Subagent Prompt Templates

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

Goal: propose solutions that interpret the problem through the assigned tag, even if that is not the intended technique. The result should be plausible enough to write as a rejected solution and useful for generating anti-hack tests.

Return 3-8 candidates. For each candidate, include:
- short name
- assigned-tag algorithm sketch
- why a contestant might believe it
- why it is wrong or incomplete
- counterexample shape
- whether C++ implementation is straightforward
```

### Public-Artifact Attacker

Pass only the public artifacts. Do not pass tests, accepted solutions, `std.cpp`, or private analysis.

```text
You are attacking a competitive programming problem as a contestant who can see the statement, checker source, and generator source. You cannot see hidden tests or accepted solutions.

Goal: propose C++ solutions that are not general but might pass weak tests because they exploit the public artifacts, likely generator distributions, checker behavior, constraints, or statement ambiguity.

Inputs provided:
- statement excerpts
- problem limits
- checker source
- generator source
- validator bounds if needed for legal input shape

Return 3-8 candidates. For each candidate, include:
- short name
- exploit idea
- why it might pass weak tests
- why it is wrong in general
- minimal counterexample or generator shape that should reject it
- whether full C++ code is straightforward

Do not use or assume hidden tests, std solution, accepted solutions, or private author intent.
```

## Rules

- Do not weaken tests, checker, constraints, or time limits to make a hack solution fail.
- If the checker accepts invalid contestant output, record a checker issue instead of hiding it with tests.
- If `std.cpp` fails a proposed hack test, investigate `std.cpp`, the validator, and the statement before weakening the test.
- Prefer a few high-value hacks with clear counterexamples over many vague wrong solutions.
- Keep all temporary files under `temp/`.
- Commit wrong solutions and tests only after showing the user the code/test plan.
