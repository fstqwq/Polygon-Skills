---
name: polygon-interactor
description: "Write the interactor and local testing tool for an interactive problem."
---

# Write Interactor

## Prerequisites

The problem must have `"mode": "interactive"` in `config/problem.json`. If multi-pass, `"pass_limit"` must be ≥ 2.

Before writing code, read `../polygon-spec/references/codeforces-testlib-style.md` and apply its shared component rules. Read the interactive templates in `../polygon-statement/references/standard-sentences.md` when checking statement wording.

**If no interaction protocol exists, STOP.** Check `statement-sections/<lang>/interaction.tex` or `draft/statement.*.md` (`## Interaction` section). If empty, tell the user: "No interaction protocol found. Please define one with `/polygon-statement` first."

## Procedure

1. **Read the interaction protocol** from the draft (`## Interaction`) or `interaction.tex`. Check that it specifies query and response formats, ranges, query limits, required flushing, and immediate termination after reading $-1$.

2. **Determine the interactor type**:
   - **Single-pass interactive** -> section A
   - **Multi-pass** -> section B

   Ask the user if unclear.

3. **Write the interactor**, show it to the user, iterate until approved.

4. **Save as** `interactors/interactor.cpp`.

5. **Update config/build.json:**
   ```json
   "interactor_source": "interactors/interactor.cpp"
   ```

6. **Compile** (best-effort, see `polygon-spec/compile.md`):
   ```
   mkdir -p temp
   g++ -std=c++20 -O2 -o temp/interactor interactors/interactor.cpp -I <skills>/polygon-spec
   ```
   If no compiler is available locally (and no WSL on Windows), report to the user and skip.

7. **Commit:**
   ```
   git add interactors/interactor.cpp config/build.json
   git commit -m "interactor: add interactor"
   ```

7. **Ask the user**: "Do you need a local testing tool for contestants? (see `testing_tool.md`)" If yes, follow `testing_tool.md`.

8. **Update the statement.** After the testing tool is committed, append this line to the Interaction section of the statement (`statement-sections/<lang>/interaction.tex`):

   ```
   A testing tool is provided to help you develop and test your solution.
   ```

9. **Suggest next step**: "You can now write tests with `/polygon-generate-tests`, or add a solution with `/polygon-solution`."

---

## Section A: Single-pass interactive

```cpp
#include "testlib.h"
using namespace std;

int main(int argc, char* argv[]) {
    registerInteraction(argc, argv);

    int n = inf.readInt(1, 100000, "n");
    cout << n << endl;

    for (int i = 0; i < n; i++) {
        string query = ouf.readToken("[?!]", "query");
        // ... process query, send response ...
        cout << response << endl;
    }

    string answer = ouf.readToken("[0-9]{1,10}", "answer");
    if (/* correct */)
        quitf(_ok, "ok, correct");
    else
        quitf(_wa, "wrong answer");
}
```

Key API:
- `registerInteraction(argc, argv)`  --  must be first call
- `cout << ... << endl;`  --  send to contestant (`endl` flushes)
- `ouf.readToken("[a-z]{1,100}", "name")` / `ouf.readInt(lo, hi, "name")`  --  read from contestant's stdout. Always pass a pattern and a variable name.
- `inf`  --  read the pre-generated test input

---

## Section B: Multi-pass

The solution is executed multiple times. Between passes, the interactor (or checker) produces `nextpass.in` which becomes the input for the next pass.

### Evaluation model

The judge runs the next pass only if ALL of:
1. Current pass exited `_ok`
2. `nextpass.in` was written to the feedback directory
3. Pass count < `pass_limit` (from `config/problem.json`)

Each pass is a fresh solution process  --  no memory between passes. `inf` is the original test on pass 1, `nextpass.in` on subsequent passes.

The interactor can be **stateful** (encode a pass number in `nextpass.in`, dispatch on it) or **stateless** (same logic every pass, e.g. round-robin multi-party: Alice -> Bob -> Carl).

### Template (stateful example)

```cpp
#include <bits/stdc++.h>
#include "testlib.h"
using namespace std;

int main(int argc, char* argv[]) {
    registerInteraction(argc, argv);

    auto start_next_pass = [&]() {
#ifdef DOMJUDGE
        tout.open(make_new_file_in_a_dir(argv[3], "nextpass.in"),
                  ios_base::out);
#endif
    };

    int op = inf.readInt();

    if (op == 1) {
        int T = inf.readInt();
        cout << T << endl;
        // Interact with contestant...

        start_next_pass();
        tout << 2 << " " << T << "\n";
        quitf(_ok, "ok, first pass done");

    } else if (op == 2) {
        int T = inf.readInt();
        // Interact with contestant...
        quitf(_ok, "ok, second pass done");  // or _wa
    } else {
        quitf(_fail, "Invalid op %d", op);
    }
}
```

`start_next_pass()` must be defined as a lambda after `registerInteraction` (or `registerTestlibCmd` for checkers). Never inline the `#ifdef DOMJUDGE` block.

---

## Rules

- **Always flush** after every output (`endl`, not `\n`).
- Handle contestant protocol violations gracefully  --  quit with `_wa`.
- Verdicts: only `_ok`, `_wa`, `_fail`. Do not use `_pe`.
- **`quitf(_ok, ...)` message must start with `"ok"`** (e.g. `quitf(_ok, "ok, correct")`, `quitf(_ok, "ok, pass %d done", pass)`). This makes logs immediately scannable.
- The interactor reads test data from `inf`, contestant output from `ouf`.
- Make every query, response, range, and query-count rule match the statement exactly.
- Use only testlib random facilities when the interactor needs randomness.
- Do not reveal hidden data, answers, or solution ideas in verdict messages.
- Keep the local testing tool protocol identical to the official interactor protocol.

## Examples

- `examples/multipass_interactor.cpp`  --  real 2-pass interactor
