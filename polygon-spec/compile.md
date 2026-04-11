# Compiling with testlib.h

All testlib programs (validator, checker, interactor, generator) are compiled the same way.

## Command

```
g++ -std=c++20 -O2 -o <output> <source.cpp> -I <path-to-testlib>
```

Where `<path-to-testlib>` is the directory containing `testlib.h`. In the worktree, `testlib.h` is resolved at build time by the judge  --  for local testing, use the copy in `<skills>/polygon-spec/testlib.h`:

```
g++ -std=c++20 -O2 -o validator validators/validator.cpp -I <skills>/polygon-spec
```

## Best-effort policy

Compilation is best-effort:
- If `g++` is not found, try `wsl g++` (Windows with WSL)
- If neither is available, **report to the user that local compilation was skipped** and proceed with the commit. The server will compile it later.
- Do not block the workflow on compilation failure.
