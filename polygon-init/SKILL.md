---
name: polygon-init
description: "Initialize a new competitive programming problem repository from scratch. Use when the user wants to start creating a new problem and no repository exists yet. Creates the full directory skeleton, config files, statement templates, and initial git commit."
---

# Initialize Problem Repository

## Procedure

1. **Extract what the user already told you.** The user may provide just a title, or a full problem idea, partial statement, constraints, etc. From whatever they give you, infer as much as possible:
   - Problem name / title
   - Slug (derive from title)
   - Language(s) (if they write in Chinese  -- `english chinese`; otherwise `english`)
   - Interactive or not
   - Multipass or not
   - Time / memory limits (look for explicit mentions)

2. **Confirm with one bundled question.** Present your inferred settings and ask a single yes/no:

   > I'll initialize **{title}** (`{slug}`) with these settings:
   > - Languages: english
   > - Mode: pass-fail, single pass
   > - Limits: 2s, 512 MB
   >
   > Does this look right?

   If the user says no, ask which part to change. If yes, proceed.

   **Only ask individual follow-ups** for things you genuinely could not infer (e.g., "You mentioned queries  -- is this an interactive problem?").

3. **Create the working directory** and initialize git:
   ```
   mkdir {slug}
   cd {slug}
   git init
   ```

4. **Create the directory skeleton** (refer to polygon-spec skill for the canonical layout):
   ```
   config/
   checkers/
   validators/
   interactors/
   generators/
   solutions/
   statement/
   statement-sections/<language>/   # one per chosen language
   tests/manual/
   tests/answers/
   ```

5. **Write config/problem.json** with the confirmed parameters. Refer to polygon-spec for the schema.

6. **Write config/build.json** with empty defaults:
   ```json
   {
     "accepted_solution_source": "",
     "validator_source": "",
     "generator_sources": []
   }
   ```

7. **Write statement template files** (these are fixed boilerplate  -- do not customize):
   - `statement/statements.ftl`  -- use the system default FTL template.
   - `statement/problem.tex`  -- use the system default problem template.
   - `statement/olymp.sty`  -- use the system default style.

   To obtain the correct default content, read the defaults from `app/service/statement/constant.py` in the Polygon-Replica codebase. These must match exactly.

8. **Write statement section stubs** (for each chosen language, create `statement-sections/<language>/`):
   - `name.tex`  -- the problem title
   - `legend.tex`  -- empty
   - `input.tex`  -- empty
   - `output.tex`  -- empty
   - `notes.tex`  -- empty
   - `interaction.tex`  -- empty (if interactive)

   Additional languages can be added later via the UI or by creating new `statement-sections/<language>/` directories.

9. **Write empty tests/spec.json**:
   ```json
   {
     "tests": []
   }
   ```

10. **Validate**  -- run the schema checker before committing:
    ```
    python <skills>/polygon-spec/review.py
    ```
    Fix any errors. Warnings are expected for a fresh repo (no tests, no solution, etc.) and can be ignored.

11. **Commit**:
    ```
    git add -A
    git commit -m "init: {problem title}"
    ```

12. **Suggest next steps** based on what the user provided:
    - If they gave problem content  -- "I'll write the statement now with `/polygon-statement`" and proceed directly.
    - If they gave only a title  -- "You can write the statement with `/polygon-statement`, or describe your idea and I'll help you structure it."
    - If they gave test cases or constraints  -- mention `/polygon-tests` as a follow-up.

## Important

- Do NOT invent any problem content. The skeleton is empty placeholders only.
- If the user provided problem content at init time, **do not inline it into the skeleton**. Complete the init commit first, then invoke `/polygon-statement` as a separate step.
