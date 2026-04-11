---
name: polygon-pack
description: "Package a problem repository into a native zip package for import into Polygon-Replica. Use when the user wants to export, package, or zip the current problem for import into the judging system."
---

# Package for Import

## Prerequisites Check

Before packaging, verify the repo is in a valid state. Report any issues to the user:

### Required
- [ ] `config/problem.json` exists and has valid `mode` and `pass_limit`
- [ ] `config/build.json` exists
- [ ] `tests/spec.json` exists with at least one test
- [ ] Every test in spec.json with `kind: "manual"` has a corresponding `tests/manual/{id}.in`
- [ ] At least one accepted solution exists in `solutions/`
- [ ] `config/build.json` `accepted_solution_source` points to an existing file
- [ ] Statement template files exist: `statement/statements.ftl`, `statement/problem.tex`, `statement/olymp.sty`
- [ ] `statement-sections/english/name.tex` is non-empty

### Required for Interactive Problems
- [ ] `config/problem.json` has `"mode": "interactive"`
- [ ] `config/build.json` has `interactor_source` pointing to an existing file

### Recommended (warn but don't block)
- [ ] Validator exists and is referenced in `build.json`
- [ ] At least one sample test (`"sample": true`) exists
- [ ] `statement-sections/english/legend.tex` is non-empty
- [ ] `statement-sections/english/input.tex` is non-empty
- [ ] `statement-sections/english/output.tex` is non-empty

## Procedure

1. **Run the prerequisites check**. Report results to the user.

2. **If there are blocking issues**, list them and suggest which `/polygon-*` skill to use to fix each one. Do not proceed.

3. **If there are only warnings**, show them and ask the user if they want to proceed anyway.

4. **Commit any uncommitted changes**:
   ```
   git add -A
   git status --short
   ```
   If there are changes, commit them: `"pre-package commit"`.

5. **Create the zip**:
   ```
   cd {repo_root}
   zip -r ../{slug}.zip . -x ".git/*" -x "draft/*"
   ```
   The zip should contain the repo contents directly at the root (no wrapper directory, no marker file). `config/problem.json` at the zip root is how the import system detects this as a native package. The `draft/` directory is excluded  --  it is authoring history, not part of the package.

6. **Report to the user**:
   - Path to the zip file
   - Summary: number of tests, number of solutions, whether checker/validator/interactor are present
   - "You can import this package into Polygon-Replica via the Import page"

## Rules

- Never package a repo with blocking issues unless the user explicitly overrides.
- The `.git/` directory must NOT be included in the zip.
- The zip root must directly contain `config/`, `tests/`, `solutions/`, etc.  --  no wrapper directory.
