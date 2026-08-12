# config/problem.json  --  Full Schema

```json
{
  "time_limit_ms": 2000,
  "memory_limit_mb": 1024,
  "mode": "pass-fail",
  "pass_limit": 1
}
```

| Field | Type | Values | Note |
|-------|------|--------|------|
| `time_limit_ms` | int | 100..30000 | milliseconds; required |
| `memory_limit_mb` | int | 1..2048 | megabytes; required |
| `mode` | string | `"pass-fail"` or `"interactive"` | required |
| `pass_limit` | int | 1..64 | 1 for normal; at least 2 for multi-pass; required |

Unknown fields, missing fields, booleans in integer fields, stringified
numbers, and out-of-range values are invalid. Defaults are written only when a
new problem is created; readers never manufacture them.

---

# config/build.json  --  Full Schema

```json
{
  "accepted_solution_source": "solutions/std.cpp",
  "validator_source": "validators/validator.cpp",
  "checker_source": "checkers/wcmp.cpp",
  "generator_sources": ["generators/gen.cpp"],
  "generator_runs": 3,
  "generator_args": [],
  "validator_args": [],
  "checker_args": [],
  "compile_jobs": 0,
  "validate_jobs": 0,
  "solve_jobs": 0,
  "run_jobs": 0,
  "run_timeout_sec": 30
}
```

| Field | Type | Note |
|-------|------|------|
| `accepted_solution_source` | string | optional path directly below `solutions/` to the main AC solution |
| `validator_source` | string | optional path below `validators/` |
| `checker_source` | string | optional path below `checkers/`; pass-fail only |
| `interactor_source` | string | optional path below `interactors/`; interactive only |
| `generator_sources` | array | required ordered paths below `generators/`; duplicates invalid |
| `generator_runs` | int | required, 0..4096 |
| `generator_args` | string array | required common generator arguments |
| `validator_args` | string array | required validator arguments |
| `checker_args` | string array | required checker arguments |
| `compile_jobs` | int | required, 0..16; 0 selects the service default |
| `validate_jobs` | int | required, 0..16; 0 selects the service default |
| `solve_jobs` | int | required, 0..16; 0 selects the service default |
| `run_jobs` | int | required, 0..16; 0 selects the service default |
| `run_timeout_sec` | int | required, 1..300 |

Rules:
- All paths are repo-relative (e.g., `"solutions/std.cpp"`).
- Referenced files must exist.
- Keep `build.json` keys in the schema order shown above. Omit unused optional
  selection keys; an empty string is invalid.
- Write JSON and source files with LF line endings.
- Standard checkers are copied into `checkers/` and referenced via `checker_source` like any other checker. There is no separate active standard-checker setting.
- For pass-fail problems: omit `checker_source` until the user chooses a
  checker, and always omit `interactor_source`.
- For interactive problems: set `interactor_source` and omit
  `checker_source`.
- `accepted_solution_source` is the only accepted-solution selection. Its
  adjacent descriptor must contain `expected: accepted`.
- Runtime consumers never scan component directories or infer selections from
  filenames. Importers may infer external intent once, then must write the
  selected paths here.
