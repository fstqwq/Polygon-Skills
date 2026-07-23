# Testlib Component Style

Apply these rules to checkers, validators, and interactors:

- Use `testlib.h`.
- Use testlib random facilities whenever randomness is needed. Do not use another random source.
- Do not use `#define`.
- Use names that express the role of each value.
- Prefer straightforward control flow over compact tricks.
- Use one indentation style consistently.
- Do not mix tabs and spaces.
