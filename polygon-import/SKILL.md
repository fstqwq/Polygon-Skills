---
name: polygon-import
description: "Import a native zip package into a local problem repository. Use when the user has a .zip exported from Polygon-Replica or /polygon-export and wants to set up or update a local working copy."
---

# Import Problem Package

## Procedure

1. **Locate the package file**. The user provides a path to a `.zip` file.

2. **Validate the package**. Check that `config/problem.json` exists inside the zip (it may be at the zip root or inside a single wrapper directory). If absent, report the error and stop.

3. **Read the problem slug** from `config/problem.json` -> `"name"` (or the zip filename as fallback).

4. **Decide the target directory**. Ask the user:

   - **If a local repo already exists for this problem** (e.g. the current working directory has `config/problem.json`):
     - Default: **overwrite** -- replace all files with the package contents, preserving `.git/`.
     - Confirm with the user: "This will overwrite the current working tree. Proceed?"

   - **If no repo exists**:
     - Create a new directory named `{slug}/` under the current directory.
     - Initialize git: `git init`

5. **Extract the package**:
   ```
   # Clear existing contents (except .git/, temp/, draft/)
   # Extract zip contents into the target directory
   ```
   - Preserve `.git/` if it exists (keeps history).
   - Preserve `temp/` and `draft/` if they exist (local work).
   - Overwrite everything else with package contents.

6. **Post-import setup**:
   ```
   git add -A
   git commit -m "import: {slug} from {package_filename}"
   ```

7. **Run the review**:
   ```
   python <skills>/polygon-spec/review.py
   ```
   Report the result so the user knows the imported state.

8. **Report to the user**:
   - Target directory path
   - Summary: number of tests, solutions, components present
   - Suggest next steps: `/polygon-solution` to add solutions, `/polygon-generate-tests` to add tests, etc.

## Rules

- Always confirm before overwriting an existing repo.
- Preserve `.git/`, `temp/`, and `draft/` on overwrite -- they are local-only.
- After import, all package contents must be committed.
- The package must contain `config/problem.json` to be recognized as native.
