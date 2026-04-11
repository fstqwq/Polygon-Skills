# tests/spec.json  --  Full Schema

```json
{
  "tests": [
    {
      "id": "001",
      "kind": "manual",
      "sample": true,
      "sample_input": "3\n1 2 3\n",
      "sample_output": "6\n"
    }
  ]
}
```

| Field | Type | Note |
|-------|------|------|
| `id` | string | exactly 3 digits, `[0-9]{3}`, starting from `"001"` |
| `kind` | string | `"manual"` or `"gen"` |
| `sample` | bool | optional; default `false`. Only write `"sample": true` for tests that appear as samples in the statement |
| `sample_input` | string | optional; override sample input displayed in the statement. Use when: (1) the accepted solution produces ugly floating-point output and you want a cleaner fixed format, (2) showing the real output would spoil the problem idea, or (3) the judging system cannot produce correct sample I/O automatically (e.g., interactive problems). |
| `sample_output` | string | optional; override sample output displayed in the statement. Same rationale as `sample_input`. |
| `sample_output_validate` | bool | optional; default `true`. If `false`, the sample output is displayed in the statement but **not checked** during verification. Only written when `false`. |

File conventions:
- Each `kind: "manual"` test must have `tests/manual/{id}.in` containing the test input.
- Each `kind: "gen"` test must have `tests/generator/{id}.in` containing the generator command (e.g., `gen_random 5 100 1`).
- Each test with a known expected answer must have `tests/answers/{id}.ans`.
- Input files must end with exactly one newline and have no trailing spaces per line.

---

# solutions/*.desc

```
expected: accepted
```

Valid `expected` values: `accepted`, `wrong_answer`, `time_limit_exceeded`, `run_time_error`, `rejected`.

---

# draft/ Conventions

The `draft/` directory holds working documents used during problem authoring. It is **git-tracked** and **excluded from zip packages**.

## draft/statement.md

Write the problem statement in Markdown before converting to LaTeX.

**Do:**
- Use `$...$` for inline math and `$$...$$` for display math
- Use plain prose for constraint descriptions; list ranges in a table if helpful
- Use fenced code blocks for sample input/output
- Mark which samples should appear in the statement

**Don't:**
- Do not write LaTeX commands (`\texttt`, `\le`, `\begin{itemize}`, etc.)
- Do not invent constraints or examples the user hasn't confirmed
- Do not mix test data with the statement draft

## draft/solution.md

Write the algorithm sketch and solution analysis.

**Do:**
- State key observations clearly
- Write complexity analysis: `O(n log n) time, O(n) space`
- Note expected behavior of WA/TLE solutions (e.g., "greedy fails on star graphs")
- Reference which algorithm each solution file implements

**Don't:**
- Do not write complete compilable code (that goes in `solutions/`)
- Do not describe input format here (that belongs in the statement)

## draft/notes.md

Free-form working notes: open questions, references, discussion history, todo items. No structure required.
