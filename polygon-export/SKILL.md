---
name: polygon-export
description: "Export the current problem repository as a native zip package. Use when the user wants to back up, share, or upload the problem to Polygon-Replica."
---

# Export Problem Package

## Procedure

1. **Run the review** to show the current state of the repo:
   ```
   python <skills>/polygon-spec/review.py
   ```
   Report the output to the user. This is informational only -- it does not block export.

2. **Create the zip** from the current working tree:
   ```
   cd {repo_root}
   zip -r ../{slug}.zip . -x ".git/*" -x "temp/*" -x "draft/*" -x ".*" -x "*/.*"
   ```
   - The zip root must directly contain `config/`, `tests/`, `solutions/`, etc. -- no wrapper directory.
   - `config/problem.json` at the zip root is how the import system detects this as a native package.
   - `.git/`, `temp/`, `draft/`, and hidden dot-paths are excluded.

3. **Report to the user**:
   - Path to the zip file
   - Summary from the review (number of tests, solutions, components present)
   - "You can import this package into Polygon-Replica via the Import page, or use `/polygon-import` to import it locally."

## Rules

- Never block export. The review is informational; the user decides whether to proceed.
- The `.git/` directory must NOT be included in the zip.
- The `temp/` and `draft/` directories must NOT be included.
- Hidden dot-paths must NOT be included.
- The zip root must directly contain `config/`, `tests/`, `solutions/`, etc. -- no wrapper directory.
