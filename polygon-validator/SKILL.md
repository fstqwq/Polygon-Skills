---
name: polygon-validator
description: "Write a testlib input validator for a competitive programming problem. Use when the user wants to add or modify the input validator, or mentions input validation, constraint checking, or test data verification."
---

# Write Input Validator

## Inputs

This skill reads from the statement draft produced by `/polygon-statement`. The draft's `## Input` and `## Constraints` sections define what the validator must enforce.

## Procedure

1. **Read the problem's input spec.** Look for sources in this order:
   1. `draft/statement.*.md` — preferred (has `## Input` and `## Constraints` sections)
   2. `statement-sections/<lang>/input.tex` + `statement-sections/<lang>/legend.tex` — fallback if no draft exists (e.g. imported problems)

   Also read `config/problem.json` for `mode` (interactive or pass-fail).

   **If neither draft nor .tex files exist, STOP.** Tell the user: "No statement found. Please run `/polygon-statement` first." Do not proceed.

2. **Present what will be validated** and ask the user to confirm:

   > From the statement, the validator will enforce:
   >
   > **Constraints:**
   > - $1 \le T \le 10^5$ (test cases)
   > - $1 \le n \le 2 \times 10^5$ (array length)
   > - $1 \le a_i \le 10^9$ (elements)
   > - Sum of $n$ over all test cases $\le 2 \times 10^5$
   >
   > **Input structure:**
   > - Line 1: $T$
   > - For each test case:
   >   - Line 1: $n$
   >   - Line 2: $a_1, a_2, \ldots, a_n$ (space-separated)
   >
   > Anything missing or wrong?

   Fix any issues before proceeding.

3. **Write the validator** using testlib.h. Save as `validators/validator.cpp`.

   Template:
   ```cpp
   #include "testlib.h"
   using namespace std;

   int main(int argc, char* argv[]) {
       registerValidation(argc, argv);

       // read and validate...

       inf.readEof();
       return 0;
   }
   ```

   ### testlib validator API

   | Function | Purpose |
   |----------|---------|
   | `inf.readInt(lo, hi, "name")` | Read int in [lo, hi] |
   | `inf.readLong(lo, hi, "name")` | Read long long in [lo, hi]. **Always use `LL` suffix**: `readLong(0LL, 1000000000000000LL, "x")`. Unsuffixed literals cause CE. |
   | `inf.readDouble(lo, hi, "name")` | Read double in [lo, hi] |
   | `inf.readWord("[a-z]{1,}", "name")` | Read whitespace-delimited token matching regex |
   | `inf.readString("[a-z]{1,}", "name")` | Read full line matching regex |
   | `inf.readEoln()` | Expect newline |
   | `inf.readEof()` | Expect end of file (must be last) |
   | `inf.readSpace()` | Expect single space |
   | `format("a[%d]", i)` | Format variable name for error messages |
   | `ensuref(cond, "msg", ...)` | Assert a condition with printf-style message |

   ### Polygon conventions

   **Boundary value naming (`~`):** Codeforces Polygon checks that every named variable hits both its min and max values across the entire test suite. Use `~` to suppress this check when a boundary can't or shouldn't be reached:

   | Name | Meaning |
   |------|---------|
   | `"n"` | Must hit both min and max of n across tests |
   | `"~T"` | T doesn't need to hit its boundary values (boundary coverage skipped) |
   | `"u~"` | u won't hit its upper bound (e.g. $u < v$ constrains $u < n$) |
   | `"~x~"` | x doesn't need to hit either bound |

   **Regex limitations:** Testlib has its own pattern engine (not POSIX/PCRE). Key differences from standard regex:

   | Behavior | Detail |
   |----------|--------|
   | **Greedy, no backtracking** | `[0-9]?1` does NOT match `"1"` — the `?` greedily consumes `1`, then fails on the literal `1`. |
   | **Spaces are ignored** | `readWord("NO SOLUTION")` matches `"NOSOLUTION"`. Escape spaces with `\\ `: `readWord("NO\\\\ SOLUTION")`. |
   | **`|` is brute-force** | Alternations are tried one by one. Do not use many alternatives in one expression — performance degrades. |
   | **`[^...]` can't generate** | `[^0-9]*` works for matching but cannot be used with `rnd.next()` for generation. |
   | **No lookahead/lookbehind** | `(?=...)`, `(?!...)`, etc. do not exist. |
   | **No `+`** | Use `{1,}` instead of `+`. Only `*`, `?`, and `{n,m}` are supported as quantifiers. |
   | **Supported syntax** | `[a-z]`, `[^a-z]` (match only), `*`, `?`, `{n}`, `{n,m}`, `(...)`, `\|` |

   ### Common validation patterns

   **Multiple test cases with sum constraint:**
   ```cpp
   int T = inf.readInt(1, 100000, "~T");
   inf.readEoln();
   int sum_n = 0;
   for (int t = 0; t < T; t++) {
       int n = inf.readInt(1, 200000, "n");
       inf.readEoln();
       sum_n += n;
       ensuref(sum_n <= 200000, "sum of n exceeds 200000");
       for (int i = 0; i < n; i++) {
           if (i > 0) inf.readSpace();
           inf.readInt(1, 1000000000, format("a[%d]", i));
       }
       inf.readEoln();
   }
   ```

   **Tree (n vertices, n-1 edges):**
   ```cpp
   int n = inf.readInt(2, 200000, "n");
   inf.readEoln();
   vector<vector<int>> adj(n + 1);
   for (int i = 0; i < n - 1; i++) {
       int u = inf.readInt(1, n, format("u[%d]", i));
       inf.readSpace();
       int v = inf.readInt(1, n, format("v[%d]", i));
       inf.readEoln();
       ensuref(u != v, "self-loop at edge %d", i);
       adj[u].push_back(v);
       adj[v].push_back(u);
   }
   // check connectivity (BFS/DFS)
   ```

   **Permutation:**
   ```cpp
   vector<bool> seen(n + 1, false);
   for (int i = 0; i < n; i++) {
       if (i > 0) inf.readSpace();
       int p = inf.readInt(1, n, format("p[%d]", i));
       ensuref(!seen[p], "duplicate value %d at position %d", p, i);
       seen[p] = true;
   }
   ```

   **String with character constraint:**
   ```cpp
   string s = inf.readWord("[a-z]{1,200000}", "s");
   ensuref((int)s.size() == n, "string length %d != n=%d", (int)s.size(), n);
   ```

4. **Show the code to the user.** Explain which constraints are validated. Wait for feedback.

5. **Update config/build.json:**
   ```json
   "validator_source": "validators/validator.cpp"
   ```

6. **Validate** — run the schema checker:
   ```
   python <skills>/polygon-schemas/test_schema.py
   ```

7. **Commit:**
   ```
   git add validators/validator.cpp config/build.json
   git commit -m "validator: add input validator"
   ```

8. **Suggest next step**: "You can now write tests with `/polygon-tests`, or add a solution with `/polygon-solution`."

## Rules

- Validate **every** constraint from the statement — ranges, sums, structure (tree/graph/permutation), string lengths, character sets.
- Use descriptive variable names in `readInt`/`readLong` calls for clear error messages.
- The validator must enforce **exact whitespace**: spaces between numbers on a line, newlines between lines, EOF at the end.
- If a constraint is ambiguous or missing, **stop and ask** — do not guess.
- `testlib.h` is available at build time — just `#include "testlib.h"`.
- For graphs: validate vertex range, check for self-loops, check for multi-edges if the statement forbids them.
- For trees: validate n-1 edges AND check connectivity.
