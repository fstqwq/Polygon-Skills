---
name: polygon-pack
description: "Package a problem repository into a native zip for backup or import into Polygon-Replica. Use when the user wants to export, package, or zip the current problem."
---

# Package for Import

## Procedure

1. **Run the review** to show the current state of the repo:
   ```
   python <skills>/polygon-spec/review.py
   ```
   Report the output to the user. This is informational only -- it does not block packaging.

2. **Commit any uncommitted changes** (if there are any):
   ```
   git add -A
   git status --short
   ```
   If there are changes, commit them: `"pre-package commit"`.

3. **Create the zip**:
   ```
   cd {repo_root}
   zip -r ../{slug}.zip . -x ".git/*" -x "temp/*"
   ```
   - The zip root must directly contain `config/`, `tests/`, `solutions/`, etc. -- no wrapper directory.
   - `config/problem.json` at the zip root is how the import system detects this as a native package.
   - `.git/` and `temp/` are excluded.

4. **Report to the user**:
   - Path to the zip file
   - Summary from the review (number of tests, solutions, components present)
   - "You can import this package into Polygon-Replica via the Import page"

## Rules

- Never block packaging. The review is informational; the user decides whether to proceed.
- The `.git/` directory must NOT be included in the zip.
- The `temp/` directory must NOT be included (local scratch files).
- The zip root must directly contain `config/`, `tests/`, `solutions/`, etc. -- no wrapper directory.
