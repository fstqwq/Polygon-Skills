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

   ## Planned Tests
   | Test idea | Kind | Targets | Notes |
   |-----------|------|---------|-------|

   ## Verification Notes
   - Local results are advisory.
   - Final verdicts require Polygon-Replica Verification.
   ```

3. **Run an independent attacker pass when available.**
   If subagents are available and allowed by the current agent policy, run a fresh subagent with the prompt template below. If not, use the same prompt as a local checklist and record that no independent subagent pass was run.

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

## Subagent Prompt Template

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
