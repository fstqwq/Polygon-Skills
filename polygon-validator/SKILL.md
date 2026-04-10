---
name: polygon-validator
description: "Write a testlib input validator for a competitive programming problem. Use when the user wants to add or modify the input validator, or mentions input validation, constraint checking, or test data verification."
---

# Write Input Validator

## Procedure

1. **Read the input format** from `statement-sections/english/input.tex` and `config/problem.json`.

2. **Extract constraints**. Identify all variables and their ranges from the statement. If any constraint is ambiguous or missing, **stop and ask the user** before writing code.

3. **Write the validator** using testlib.h:

   ```cpp
   #include "testlib.h"
   using namespace std;

   int main(int argc, char* argv[]) {
       registerValidation(argc, argv);

       int n = inf.readInt(1, 100000, "n");
       inf.readEoln();

       for (int i = 0; i < n; i++) {
           if (i > 0) inf.readSpace();
           inf.readInt(1, 1000000000, format("a[%d]", i));
       }
       inf.readEoln();

       inf.readEof();
       return 0;
       }
   ```

   Key testlib validator patterns:
   - `inf.readInt(lo, hi, "name")` — read and validate integer range
   - `inf.readLong(lo, hi, "name")` — for 64-bit integers
   - `inf.readDouble(lo, hi, "name")` — for floating point
   - `inf.readWord("[a-z]+", "name")` — read word matching regex
   - `inf.readString("[a-z]+", "name")` — read full line matching regex
   - `inf.readEoln()` — expect end of line
   - `inf.readEof()` — expect end of file (must be last)
   - `inf.readSpace()` — expect single space
   - `format("a[%d]", i)` — format variable name for error messages

   Common validation patterns:
   - **Tree**: validate n-1 edges, check connectivity, check no self-loops
   - **Graph**: validate m edges, check vertex range [1,n]
   - **Permutation**: validate each element in [1,n], check all distinct
   - **Multiple test cases**: read T first, validate sum constraints

4. **Save as** `validators/validator.cpp`.

5. **Update config/build.json**:
   ```json
   "validator_source": "validators/validator.cpp"
   ```

6. **Show the code to the user** and explain what constraints are being validated. Wait for feedback.

7. **Commit**:
   ```
   git add validators/validator.cpp config/build.json
   git commit -m "validator: add input validator"
   ```

## Rules

- Validate EVERY constraint from the statement — ranges, sums, structure (tree/graph/permutation).
- Use descriptive variable names in readInt/readLong calls for clear error messages.
- The validator must enforce exact whitespace: spaces between numbers on a line, newlines between lines, EOF at the end.
- If the statement doesn't specify a constraint (e.g., "an array of integers" with no range), **ask the user** for the specific bounds.
- `testlib.h` is available at build time — just `#include "testlib.h"`.
