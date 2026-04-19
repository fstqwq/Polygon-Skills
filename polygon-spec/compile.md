# Compiling with testlib.h

All testlib programs (validator, checker, interactor, generator) are compiled the same way.

## Command

```
mkdir -p temp
g++ -std=c++20 -O2 -o temp/<output> <source.cpp> -I <path-to-testlib>
```

Where `<path-to-testlib>` is the directory containing `testlib.h`. In the worktree, `testlib.h` is resolved at build time by the judge  --  for local testing, use the copy in `<skills>/polygon-spec/testlib.h`:

```
mkdir -p temp
g++ -std=c++20 -O2 -o temp/validator validators/validator.cpp -I <skills>/polygon-spec
```

All local compile outputs, logs, diagnostics, and ad-hoc input/output files belong under `temp/`. Never place temporary binaries in the repository root or beside component sources.

## Best-effort policy

Compilation is best-effort:
- If `g++` is not found, try `wsl g++` (Windows with WSL)
- If neither is available, **report to the user that local compilation was skipped** and proceed with the commit. The server will compile it later.
- Do not block the workflow on compilation failure.
