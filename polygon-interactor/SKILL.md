---
name: polygon-interactor
description: "Write a testlib interactor for an interactive competitive programming problem. Use when the problem mode is interactive and needs a judge-side interactor program that communicates with the contestant's solution via stdin/stdout."
---

# Write Interactor

## Prerequisites

The problem must have `"mode": "interactive"` in `config/problem.json`. The system will not accept an interactive problem without an interactor.

## Procedure

1. **Read the interaction protocol** from `statement-sections/english/interaction.tex`. If it doesn't exist or is empty, ask the user to describe the interaction protocol first (suggest `/polygon-statement`).

2. **Understand the protocol**: What does the judge send? What does the contestant send? How many rounds? What determines success/failure?

3. **Write the interactor** using testlib.h:

   ```cpp
   #include "testlib.h"
   using namespace std;

   int main(int argc, char* argv[]) {
       registerInteraction(argc, argv);

       // inf = test input (pre-generated)
       // Read the test data
       int n = inf.readInt();

       // Send initial data to contestant
       cout << n << endl;

       // Interaction loop
       for (int i = 0; i < n; i++) {
           // Read contestant's query
           int query = readInt();  // reads from contestant's stdout

           // Process and respond
           int response = /* compute based on test data */;
           cout << response << endl;
       }

       // Read contestant's final answer
       int answer = readInt();

       if (answer == /* expected */) {
           quitf(_ok, "correct");
       } else {
           quitf(_wa, "wrong answer");
       }
   }
   ```

   Key patterns:
   - `registerInteraction(argc, argv)` — must be first
   - `cout << ... << endl;` — send to contestant (endl flushes)
   - `readInt()` / `readWord()` — read from contestant's output
   - `quitf(_ok, ...)` / `quitf(_wa, ...)` — terminate with verdict
   - `inf` — read the pre-generated test input

4. **Save as** `interactors/interactor.cpp`.

5. **Update config/build.json**:
   ```json
   "interactor_source": "interactors/interactor.cpp"
   ```

6. **Show the code to the user** and wait for feedback.

7. **Commit**:
   ```
   git add interactors/interactor.cpp config/build.json
   git commit -m "interactor: add interactor"
   ```

## Rules

- Interactors must flush after every output (use `endl` not `\n`).
- Handle contestant protocol violations gracefully — if the contestant sends invalid data, quit with `_pe` or `_wa`.
- The interactor reads test data from `inf`, not from the contestant.
