---
name: polygon-statement
description: "Write or edit the problem statement (Markdown draft, then LaTeX)."
---

# Write Problem Statement

## Inputs

The user provides problem content in any form: rough notes, pseudocode, another problem's format, natural language, etc. The agent's job is to organize this into a clean, complete statement.

## Solver Model

Write for contestants. Assume they know how to program, understand standard input/output, and know high-school mathematics. Do not assume they know any extra concept, term, model, or operation. If the statement uses anything beyond basic programming conventions and high-school coursework, define it before using it.

## Procedure

### Phase 1: Choose the primary language and draft

1. **Read existing state**:
   - Check `draft/` for existing drafts (`draft/statement.*.md`)
   - Check `statement-sections/` for configured languages and existing `.tex` content

   If `.tex` files exist but no draft, this is an imported or hand-edited problem. Read the `.tex` content and reconstruct a draft in the standard format (step 3) before proceeding. Show it to the user as "I reconstructed this draft from the existing .tex files."

2. **Identify what's missing and ask only the essential questions.**

   For a complete statement you need: legend, input format, output format, constraints, and samples. Prepare at least two distinct samples by default, unless the user gives a problem-specific reason to use fewer. Scan what the user provided and check the list below internally. Ask ONLY about items that are genuinely ambiguous or missing -- do NOT dump the entire checklist on the user.

   **Constraint checklist** (check internally, ask only gaps):

   | Topic | What the statement must specify |
   |-------|--------------------------------|
   | Integer types | Explicitly state "integer" for all numeric inputs |
   | Value ranges | Exact bounds for every variable |
   | Multi-test sum | $\sum n$ constraint if multi-test |
   | Graph guarantees | Simple/multi-edge, self-loops, connected, directed |
   | Tree guarantee | "It is guaranteed that the input forms a tree" |
   | Degenerate cases | Whether $n=1$, answer=0, etc. are possible |
   | Output uniqueness | "If multiple answers, output any" or unique |
   | Impossible branch | "output -1 if impossible" -- when applicable |
   | Value types | Integer/real, positive/negative/zero |
   | String format | Alphabet, length bounds |

   **How to ask**: bundle all missing items into ONE question. Do not ask one item at a time. If you can make a reasonable assumption, state it as a default ("I'll assume X unless you say otherwise") rather than blocking on it.

   **Samples**: if the user says "make one up" or doesn't provide a sample, construct a small, illustrative example yourself. A sample is a worked example of the problem, not creative content -- generating one is expected.

3. **Write the draft immediately.** Do not ask about style, tone, or theme before writing.

   **Choose the primary draft language before writing**:
   - If only Chinese is configured, write only the Chinese draft.
   - If English is configured, default to an English draft even if the user wrote the prompt in Chinese.
   - If the user explicitly says to write Chinese first, use Chinese as the primary draft language.
   - If the repository does not make the configured languages clear, default to English unless the user explicitly asks for Chinese first.

   **Choose the style before writing**:
   - Default to World Finals style. Read `<skills>/polygon-statement/styles/world_finals.md`.
   - If the user explicitly asks for a more direct statement, no story, or Codeforces style, read `<skills>/polygon-statement/styles/codeforces.md` instead.

   Save to `draft/statement.<lang>.md` using this exact format:

   ```markdown
   # Problem Title

   ## Legend

   (Problem description with scenario.)

   ## Input

   (Input format description.)

   ## Output

   (Output format description.)

   ## Sample 1

   **Input**
   ```
   3
   1 2 3
   ```

   **Output**
   ```
   6
   ```

   ## Interaction

   (Only for interactive problems. Delete this section otherwise.)

   ## Notes

   In the first sample, the answer is $1 + 2 + 3 = 6$.

   ## Constraints

   - $1 \le n \le 10^5$
   - $1 \le a_i \le 10^9$
   ```

   **Rules for the draft format:**
   - `# Problem Title` -> maps to `name.tex`
   - `## Legend` -> maps to `legend.tex`
   - `## Input` -> maps to `input.tex`
   - `## Output` -> maps to `output.tex`
   - `## Sample N` -> for review only; not converted to `.tex` (samples are managed by `/polygon-generate-tests`)
   - `## Interaction` -> maps to `interaction.tex` (omit if not interactive)
   - `## Notes` -> maps to `notes.tex`. By default, give useful explanations for at least two samples and for every sample likely to raise a question. Do not restate the problem or reveal the solution. A problem-specific user instruction may request fewer or no notes
   - `## Constraints` -> folded into `## Input` during LaTeX conversion (not a separate file)
   - Use LaTeX math (`$...$`) inline in the Markdown  --  it carries over directly to `.tex`

4. **Show the draft.** Present it and wait for feedback. Do not ask "any style adjustments?" -- the user will tell you if they want changes. If they approve (or say nothing specific to change), proceed to step 7.

5. **If the user requests a themed setting**, ask:
   - What is the scenario?
   - What do the mathematical objects represent? (e.g. vertices -> cities)

   Then rewrite the draft with the theme. Mathematical content stays identical.

6. **Iterate** until the user approves.

### Phase 2: Translate to other languages

7. **Check which other languages are configured** in `statement-sections/`. Treat the approved primary draft as the canonical source. If there are other languages, translate that draft:
   - Save each translation as `draft/statement.<lang>.md`
   - Show translations to the user for review

   If only one language is configured, skip this phase.

8. **Double-check all drafts.** Before converting to LaTeX, confirm with the user:
   > All drafts are ready:
   > - draft/statement.<primary>.md ✓
   > - draft/statement.<other>.md ✓
   >
   > Shall I convert these to LaTeX?

### Phase 3: Convert to LaTeX

9. **Convert each draft to LaTeX section files**, following the formatting rules below. For each language, write:
   - `statement-sections/<lang>/name.tex`  --  problem title (single line, no LaTeX commands)
   - `statement-sections/<lang>/legend.tex`  --  the legend text
   - `statement-sections/<lang>/input.tex`  --  input format
   - `statement-sections/<lang>/output.tex`  --  output format
   - `statement-sections/<lang>/notes.tex`  --  sample notes (if any)
   - `statement-sections/<lang>/interaction.tex`  --  interaction protocol (if interactive)

   For pass-fail problems, do not create `interaction.tex`; delete any existing `statement-sections/<lang>/interaction.tex` files.

   Put every shared statement build asset under `statement-assets/`, not `draft/` or `attachments/`. For each TikZ/LaTeX-generated figure, commit both the editable source `statement-assets/<name>.tex` and the rendered `statement-assets/<name>.pdf`.

10. **Check formula consistency** across languages:
    ```
    python <skills>/polygon-statement/check_formulas.py
    ```
    Fix any mismatches  --  every formula in one language must appear in all others.

11. **Commit** all languages and changed statement assets together. Stage only the exact files changed; do not add whole directories that may contain unrelated drafts or assets:
    ```
    git add -- statement-sections/<lang>/<changed-file>.tex draft/statement.<lang>.md statement-assets/<figure>.tex statement-assets/<figure>.pdf
    git commit -m "statement: {brief description of change}"
    ```

12. **Suggest next step**: "Now that the statement is ready, you can write the input validator with `/polygon-validator`."

---

## Style Selection

Problem statements follow a **terse, precise** style. Every sentence must carry information.

- Default to World Finals style. See `<skills>/polygon-statement/styles/world_finals.md`.
- If the user explicitly asks for a more direct statement, no story, or Codeforces style, switch to `<skills>/polygon-statement/styles/codeforces.md`.
- Do not proactively present a menu of tones. Draft first; if the user wants a style change, rewrite in the requested style.

## Shared Writing Rules

1. **No spoilers.** Do not hint at the solution approach. Do not encourage a particular method  --  unless the user explicitly defines it as part of the problem's story or statement setup.
2. **No hedging.** Never write "you might want to", "it could be the case that", "you should consider". State facts.
3. **Precise quantifiers.** "at most", "exactly", "at least"  --  never "around", "roughly", "about".
4. **No condescension.** Do not write "as you probably know", "it is easy to see that", "obviously". Trust the reader.
5. **Input/Output sections are format-only.** Describe the format, don't re-explain the problem.
6. **Chinese follows the same principles.** Use spoken Chinese, not textbook-formal. Keep it natural and direct.
7. **Use American English.** Correct grammar and prefer established competitive-programming phrasing.
8. **Use title case for English titles** unless the title intentionally contains stylized text.
9. **Use common personal names.** Do not introduce usernames, handles, or obscure nicknames as character names.
10. **Do not reuse a variable name for a different object.** A symbol introduced in a definition must not later be repurposed for the input object.
11. **Prefer the standard bilingual wording.** Read `references/standard-sentences.md` when writing Input, Output, guarantees, versions, or interaction text.
12. **Use standard definitions when needed.** Read `references/standard-definitions.md` before defining common sequence, string, arithmetic, or tree concepts.

### What to avoid

| ✗ Bad | Why | ✓ Fix |
|---|---|---|
| "The array has a length of $n$, where $n$ can be quite large." | Vague ("quite large" carries no information) | State constraints in the Constraints section. |
| "Please note that the answer always exists, so you don't need to worry about impossible cases." | Patronizing + filler | "The answer always exists." |
| "You need to find the answer and output it. The answer is the minimum number of operations needed." | Redundant (two sentences for one fact) | "Find the minimum number of operations." |
| "In this problem, you will be working with a tree. A tree is a connected graph with no cycles." | Only define well-known terms if needed for precision. | "You are given a tree with $n$ vertices." or omit definition. |
| "Now, let's talk about the input format." | Meta-commentary | *(just start the Input section)* |

### Length guideline

- **Legend**: No hard limit. When the problem can be defined accurately in natural language, especially when it has a meaningful setting rather than a bare "given an array" formulation, minimize formulas in the Legend. Move formal definitions, coordinate conventions, limits, and input guarantees to Input whenever this preserves clarity and correctness.
- **Input/Output**: Mechanical descriptions only. Keep tight.
- **Notes**: Explain at least two samples by default and every non-obvious sample. Do not restate the problem or reveal the solution. Honor explicit problem-specific user instructions.


## LaTeX Formatting Rules

### Mathematical typesetting
- **Inline math** `$...$`: `$n$`, `$a_i$`, `$t$`
- **Display math** `$$...$$`: Use for standalone formulas that deserve their own line:
  ```latex
  $$\sum_{i=1}^{n} a_i \le 2 \times 10^5$$
  ```
- **Multi-line formulas**  --  use `align*` for aligned equations:
  ```latex
  \begin{align*}
  f(1) &= 1 \\
  f(n) &= f(n-1) + f(n-2)
  \end{align*}
  ```
- Ranges with `\le`: `$1 \le n \le 10^5$`
- Large numbers: `$2 \times 10^5$` not `2e5`; `998\,244\,353` for large integers
- Ordinals: `$i$-th` (hyphen outside math mode)
- Use lowercase letters for ordinary variables. Sets and graphs may use uppercase letters when conventional.
- Avoid multi-letter variables. When one is necessary, typeset it upright with `\mathrm` or as a function with `\operatorname`.
- Keep words, spaces, and punctuation outside math mode.
- Treat formulas as parts of sentences and punctuate them normally, including display formulas.
- Use `\cdot` for multiplication, `\bmod` for remainders, and `\equiv` with `\pmod` for congruences.
- Write string constants as `$\mathtt{abacaba}$` in formulas and `\texttt{abacaba}` in prose.
- Use square brackets for arrays and sequences, and braces for sets and unordered multisets.

### Text formatting
- Output strings in `\texttt{}`: `\texttt{YES}`, `\texttt{NO}`, `\texttt{U}`, `\texttt{D}`
- Use `\textit{}` sparingly for new concepts
- Use `\textbf{}` only for a word or a short phrase that is genuinely important. Rewrite instead of bolding a sentence or paragraph.
- Reduce emphasis overall  --  let the math and structure carry the meaning

### Figures
Store a shared figure and its editable source as:

```text
statement-assets/figure_sample.tex
statement-assets/figure_sample.pdf
```

The `.tex` file is the version-controlled source; the `.pdf` is the compiled asset consumed by the statement builder. Keep them together with the same basename and regenerate the PDF whenever the source changes. Do not leave the source only in `draft/`, and do not put either file in contestant `attachments/`.

Reference the asset by filename, without a `statement-assets/` prefix, using the Polygon-compatible figure format:
```latex
\begin{center}
  \def \htmlPixelsInCm {45}
\includegraphics[width=17cm]{figure_sample.pdf}
 \\ \small{caption text here}
\end{center}
```

Before committing, confirm that the PDF exists, the source exists, and every `\includegraphics` filename matches a file under `statement-assets/`.

### Input section
- No `itemize` or `enumerate`  --  except for multi-operation problems where listing operations is natural
- Make the prose structure match the input structure: normally use one paragraph for one input line or repeated block.
- List all values on a line before giving their constraints, and place the constraints immediately after that list.
- Keep the parentheses around constraints outside math mode.
- Do not write "space-separated" unless the separation itself needs emphasis.
- **Multiple test points are optional.** Do not introduce $t$ merely to fit a template. If the input already contains multiple test points, use the lowercase variable `$t$` and the applicable template from `references/standard-sentences.md`.
- State a sum over all test points only when it is an actual input guarantee.
- **Single test case**: start directly with "The first line contains..."
- Line descriptions: "The following $n$ lines describe..." or "The $i$-th line contains..."

### Output section
- **Multiple test points**: use the applicable bilingual template from `references/standard-sentences.md`.
- Use "separated by a space" not "space-separated"
- Use "Output" not "Print"

### Interactive / multi-pass problems
- **Interactive**: Use the mandatory introduction and flush block from `references/standard-sentences.md`.
- **Multi-pass**: Start legend with `\textit{This is a multi-pass problem.}`
- **Both**: Start legend with `\textit{This is a multi-pass, interactive problem.}`
- **Mandatory flush block**: always include the exact language-appropriate block from `references/standard-sentences.md`, even if it is not mentioned in the source.

---

## Standard Phrasing

Read `references/standard-sentences.md` whenever a standard Input, Output, guarantee, version, or interaction sentence applies. Use its English/Chinese pairs directly when the semantics match; do not introduce a condition merely to use a template.

Read `references/standard-definitions.md` when the statement needs a standard sequence, string, lexicographical, arithmetic, modular, or tree definition.

---

## Rules

- **Never invent problem content.** If the user says "a tree problem," do NOT decide what the problem asks. Ask: "What should the solver compute? (e.g., diameter, centroid, LCA, ...)"
- **Always show the draft** and wait for user confirmation before converting to LaTeX.
- **Preserve existing content** when editing  --  only modify the sections the user asks to change.
- **One commit for all languages**  --  do not commit one language at a time.
- If the user provides both statement text and sample I/O at the same time, handle the statement here and suggest `/polygon-generate-tests` for the test data.
