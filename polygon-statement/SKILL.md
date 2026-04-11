---
name: polygon-statement
description: "Write or edit the problem statement for a competitive programming problem. Use when the user wants to write, revise, or format the problem statement sections (legend, input, output, notes, interaction). Works through a Markdown draft first, then converts to LaTeX for all configured languages."
---

# Write Problem Statement

## Inputs

The user provides problem content in any form: rough notes, pseudocode, another problem's format, natural language, etc. The agent's job is to organize this into a clean statement WITHOUT adding or assuming any content.

## Procedure

### Phase 1: Draft in the user's language

1. **Read existing state**:
   - Check `draft/` for existing drafts (`draft/statement.*.md`)
   - Check `statement-sections/` for configured languages and existing `.tex` content

   If `.tex` files exist but no draft, this is an imported or hand-edited problem. Read the `.tex` content and reconstruct a draft in the standard format (step 3) before proceeding. Show it to the user as "I reconstructed this draft from the existing .tex files."

2. **Gather information from the user.** For a complete statement, you need:
   - **Legend**: The problem description / story
   - **Input format**: What the input looks like
   - **Output format**: What to output
   - **Notes** (optional): Explanation of sample cases
   - **Interaction protocol** (if interactive): How the interaction works

   If the user gives a partial description, work with what they provide and ask about missing pieces. Do NOT fill in gaps yourself.

   **Constraint checklist** -- confirm each applicable item with the user before drafting:

   | Topic | What to ask |
   |-------|-------------|
   | **Integer types** | Are all inputs integers? Specify explicitly (e.g., "integer", not just a variable name). |
   | **Value ranges** | Exact bounds for every variable: $1 \le n \le 10^5$, not just "n is large". |
   | **Multi-test sum** | If multi-test: is there a constraint on $\sum n$ across all test cases? What is it? |
   | **Graph validity** | Simple graph? No self-loops, no multi-edges? Connected? Directed or undirected? |
   | **Tree guarantee** | "It is guaranteed that the input forms a tree" -- explicit or implied? |
   | **Degenerate cases** | Can $n=1$? Can the answer be 0? Can the graph be disconnected? Can coordinates coincide? |
   | **Output uniqueness** | Is the answer unique, or can there be multiple valid outputs? If multiple, any preference? |
   | **Edge cases branch** | If the problem has "output -1 if impossible" -- is it guaranteed that such cases exist in any valid test suite? |
   | **Coordinate/weight range** | Integer or real? Positive only or can be negative/zero? |
   | **String constraints** | Alphabet (lowercase Latin?), length bounds. |

3. **Write a concise draft.** Organize the user's content into the standard sections. Keep the user's original framing  --  if they described the problem in terms of a known algorithm, a game, or a scenario, preserve that context. Do not strip motivation or add decoration.

   Save to `draft/statement.<lang>.md` using this exact format:

   ```markdown
   # Problem Title

   ## Legend

   (Problem description. Pure math/algorithm, no story.)

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
   - `# Problem Title` → maps to `name.tex`
   - `## Legend` → maps to `legend.tex`
   - `## Input` → maps to `input.tex`
   - `## Output` → maps to `output.tex`
   - `## Sample N` → for review only; not converted to `.tex` (samples are managed by `/polygon-generate-tests`)
   - `## Interaction` → maps to `interaction.tex` (omit if not interactive)
   - `## Notes` → maps to `notes.tex` (omit if not needed)
   - `## Constraints` → folded into `## Input` during LaTeX conversion (not a separate file)
   - Use LaTeX math (`$...$`) inline in the Markdown  --  it carries over directly to `.tex`

4. **Show the draft and ask about style.** Present the draft, then ask:

   > Here is the draft. Any style adjustments?
   > For example: add a themed setting, make it more formal/mathematical, adjust the tone, etc.

   - **If satisfied** → proceed to step 7.
   - **If wants a themed setting** → go to step 5.
   - **If wants other changes** → iterate on the draft directly.

5. **Gather theme details.** Do NOT invent a story. Ask the user these specific questions:
   - **Setting**: "What is the scenario?" (e.g. game, city planning, competition, cooking, ...)
   - **Characters** (if any): "Who are the actors?" (e.g. Alice and Bob, a traveler, a king, ...)
   - **Object mapping**: "What do the mathematical objects represent?" (e.g. vertices → cities, edges → roads, values → costs, ...)

   Then rewrite the draft with the theme applied. The mathematical content and constraints stay identical  --  only the framing changes.

6. **Show the themed draft** to the user and iterate until approved.

### Phase 2: Translate to other languages

7. **Check which other languages are configured** in `statement-sections/`. If there are other languages, translate the approved draft:
   - Save each translation as `draft/statement.<lang>.md`
   - Show translations to the user for review

   If only one language is configured, skip this phase.

8. **Double-check all drafts.** Before converting to LaTeX, confirm with the user:
   > All drafts are ready:
   > - draft/statement.english.md ✓
   > - draft/statement.chinese.md ✓
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

10. **Check formula consistency** across languages:
    ```
    python <skills>/polygon-statement/check_formulas.py
    ```
    Fix any mismatches  --  every formula in one language must appear in all others.

11. **Commit** all languages together:
    ```
    git add statement-sections/ draft/
    git commit -m "statement: {brief description of change}"
    ```

12. **Suggest next step**: "Now that the statement is ready, you can write the input validator with `/polygon-validator`."

---

## Writing Style

Problem statements follow a **terse, precise** style. Every sentence must carry information. The tone, however, varies. When the user requests style adjustments (step 4), present these three tones as options and imitate the chosen one.

### Tone A  --  Concise

Direct, algebraic framing. No story. Standard Codeforces house style.

> You are given an array $a$ of $n$ integers. In one operation, you choose an index $i$ ($1 \le i \le n$) and set $a_i := a_i + 1$ or $a_i := a_i - 1$.
>
> Find the minimum number of operations to make all elements equal.

Characteristics: "You are given...", "Find...", no characters, no motivation.

### Tone B  --  Narrative

A self-contained scenario that feels like describing a real situation. The reader should forget they are solving a math problem. Standard ICPC World Finals house style.

> A group of hikers must cross a canyon using a single rope bridge that holds at most $k$ people at a time. Each hiker has a walking speed; when multiple hikers cross together, they move at the speed of the slowest person in the group. A flashlight is needed for every crossing, and there is only one  --  so someone must carry it back after each trip.
>
> Determine the minimum total time for all hikers to cross the canyon.

Characteristics: physical scenario, natural language, no variable names in the opening, constraints introduced through the story rather than through math.

### Tone C  --  Technical

Opens by defining or referencing a known concept, then poses a question about it. Common in IOI and research-flavored contests.

> Recall that the *Euler tour* of a rooted tree visits each vertex exactly twice: once on entry and once on exit. Given a rooted tree with $n$ vertices, process $q$ queries of the form: "Is vertex $u$ an ancestor of vertex $v$?"
>
> Answer each query using the Euler tour representation.

Characteristics: "Recall that...", defines structure first, poses the task second.

**At step 4**, if the user wants a style change, show these three examples and ask which tone they prefer. Then rewrite the draft to match.

### Core principles (apply to all tones)

1. **No spoilers.** Do not hint at the solution approach. Do not encourage a particular method  --  unless the user explicitly defines it as part of the problem's story (e.g. "using the Euler tour representation" in Tone C).
2. **No hedging.** Never write "you might want to", "it could be the case that", "you should consider". State facts.
3. **Precise quantifiers.** "at most", "exactly", "at least"  --  never "around", "roughly", "about".
4. **No condescension.** Do not write "as you probably know", "it is easy to see that", "obviously". Trust the reader.

### What to avoid (any tone)

| ✗ Bad | Why | ✓ Fix |
|---|---|---|
| "The array has a length of $n$, where $n$ can be quite large." | Vague ("quite large" carries no information) | State constraints in the Constraints section. |
| "Please note that the answer always exists, so you don't need to worry about impossible cases." | Patronizing + filler | "The answer always exists." |
| "You need to find the answer and output it. The answer is the minimum number of operations needed." | Redundant (two sentences for one fact) | "Find the minimum number of operations." |
| "In this problem, you will be working with a tree. A tree is a connected graph with no cycles." | Only define well-known terms if needed for precision. | "You are given a tree with $n$ vertices." or omit definition. |
| "Now, let's talk about the input format." | Meta-commentary | *(just start the Input section)* |

### Length guideline

- **Legend**: No hard limit  --  Tone B naturally runs longer than Tone A. But every sentence must earn its place.
- **Input/Output**: Mechanical descriptions only. Keep tight.
- **Notes**: Only include if sample cases are non-obvious. Do not restate the problem.


## LaTeX Formatting Rules

### Mathematical typesetting
- **Inline math** `$...$`: `$n$`, `$a_i$`, `$T$`
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

### Text formatting
- Output strings in `\texttt{}`: `\texttt{YES}`, `\texttt{NO}`, `\texttt{U}`, `\texttt{D}`
- Use `\textit{}` sparingly for new concepts
- Use `\textbf{}` at most once per statement for key conditions
- Reduce emphasis overall  --  let the math and structure carry the meaning

### Figures
Use the Polygon-compatible figure format:
```latex
\begin{center}
  \def \htmlPixelsInCm {45}
\includegraphics[width=17cm]{figure_sample.pdf}
 \\ \small{caption text here}
\end{center}
```

### Input section
- No `itemize` or `enumerate`  --  except for multi-operation problems where listing operations is natural
- **Multiple test cases**: "The first line of the input contains an integer $T$ ($1 \le T \le \dots$) indicating the number of test cases. For each test case:" (always capital `$T$`)
- End with: "It is guaranteed that the sum of $n$ over all test cases does not exceed $\dots$"
- **Single test case**: start directly with "The first line contains..."
- Line descriptions: "The following $n$ lines describe..." or "The $i$-th line contains..."

### Output section
- **Multiple test cases**: "For each test case, output ..."
- Use "separated by a space" not "space-separated"
- Use "Output" not "Print"

### Interactive / multi-pass problems
- **Interactive**: Start legend with `\textit{This is an interactive problem.}`
- **Multi-pass**: Start legend with `\textit{This is a multi-pass problem.}`
- **Both**: Start legend with `\textit{This is a multi-pass, interactive problem.}`
- **Mandatory flush block**  --  always include, even if not mentioned in the source:
  ```latex
  To flush your output, you can use:
  \begin{itemize}
      \item \texttt{fflush(stdout)} or \texttt{cout.flush()} in C/C++;
      \item \texttt{System.out.flush()} in Java;
      \item \texttt{sys.stdout.flush()} in Python.
  \end{itemize}
  ```

---

## Standard Phrasing

Always correct awkward phrasing to the standard form:

| ✗ Avoid | ✓ Use |
|---------|-------|
| "The input starts with T." | "The first line of the input contains an integer $T$..." |
| "n lines follow." | "The following $n$ lines..." |
| "Print 'YES' if..." | "Output \texttt{YES} if..." |
| "Output space separated integers." | "Output $n$ integers separated by a space." |
| "The sum of N is < 2e5." | "The sum of $n$ over all test cases does not exceed $2 \times 10^5$." |
| "You can ask 10 queries." | "You can ask at most 10 queries." |
| "10^9" (in running text) | "$10^9$" |
| "Wait for the judge." (multi-pass) | "The program should exit immediately..." |

### Chinese phrasing conventions

When writing the Chinese version, use standard competitive programming Chinese:

| English | Chinese |
|---------|---------|
| "The first line contains an integer $T$..." | "第一行包含一个整数 $T$..." |
| "For each test case, output..." | "对于每组测试数据，输出..." |
| "It is guaranteed that..." | "保证..." |
| "separated by a space" | "用空格隔开" |
| "$i$-th" | "第 $i$ 个" |
| "Output \texttt{YES} if..." | "如果...，输出 \texttt{YES}..." |
| "at most" | "至多" |
| "does not exceed" | "不超过" |

---

## Rules

- **Never invent problem content.** If the user says "a tree problem," do NOT decide what the problem asks. Ask: "What should the solver compute? (e.g., diameter, centroid, LCA, ...)"
- **Always show the draft** and wait for user confirmation before converting to LaTeX.
- **Preserve existing content** when editing  --  only modify the sections the user asks to change.
- **One commit for all languages**  --  do not commit one language at a time.
- If the user provides both statement text and sample I/O at the same time, handle the statement here and suggest `/polygon-generate-tests` for the test data.
