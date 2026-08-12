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

## Local execution caveat

Local compile/run results are sanity checks only. Timing-sensitive results depend on the machine, OS, interpreter, compiler, load, and input plumbing. Treat local Python AC/TLE and local C++ timing as relative diagnostics, not final verdicts.

Do not tune time limits, weaken tests, or modify the runtime environment based only on local timing. Final correctness and performance are determined by Polygon-Replica Verification on judgehost.

## Environment policy

Use only the execution environment the user selected. Do not silently switch
to WSL, another compiler, another interpreter, or another host. If the selected
environment lacks `g++`, report that local compilation was skipped; online
Polygon-Replica Verification remains authoritative.
