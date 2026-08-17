# Testlib Component Style

Apply these rules to checkers, validators, interactors, and generators:

- Use `testlib.h`.
- Write code that compiles with the documented `g++ -std=c++14` command, even when the normal judging runtime uses C++20.
- Include every standard-library dependency directly. Never rely on `testlib.h` or another header to include it transitively. For example, this may compile as C++20 but fails as C++14 because `testlib.h` does not provide `<array>` in that mode:

  ```cpp
  #include "testlib.h"

  std::array<int, 2> values{{1, 2}};
  ```

  Add `#include <array>` explicitly.
- Prefer the specific standard headers used by the source when the list is short. Use `#include <bits/stdc++.h>` when the component has many standard-library dependencies and listing them individually would obscure the source.
- Use testlib random facilities whenever randomness is needed. Do not use another random source.
- Do not use `#define`.
- Use names that express the role of each value.
- Prefer straightforward control flow over compact tricks.
- Use one indentation style consistently.
- Do not mix tabs and spaces.
