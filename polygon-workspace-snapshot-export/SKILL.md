---
name: polygon-workspace-snapshot-export
description: "Create a Workspace snapshot ZIP from the current problem repository."
---

# Export a Workspace Snapshot

## Procedure

1. **Run the review** to show the current state of the repo:
   ```
   python <skills>/polygon-spec/review.py
   ```
   Report the output to the user. This is informational only -- it does not block local zip creation.

2. **Create the local zip file** from the current working tree:
   ```
   cd {repo_root}
   mkdir -p temp
   zip -r temp/{slug}.zip . -x ".git/*" -x "temp/*" -x "draft/*" -x ".*" -x "*/.*"
   ```
   - The zip root must directly contain `config/`, `tests/`, `solutions/`, etc. -- no wrapper directory.
   - `config/problem.json` at the zip root identifies an authored problem Workspace snapshot.
   - `.git/`, `temp/`, `draft/`, and hidden dot-paths are excluded.

3. **Report to the user**:
   - Path to the zip file
   - Summary from the review (number of tests, solutions, components present)
   - "You can restore this Workspace snapshot through Polygon-Replica's Import page."

## Rules

- Never block local zip creation. The review is informational; the user decides whether to proceed.
- The `.git/` directory must NOT be included in the zip.
- The `temp/` and `draft/` directories must NOT be included.
- Hidden dot-paths must NOT be included.
- The zip root must directly contain `config/`, `tests/`, `solutions/`, etc. -- no wrapper directory.
