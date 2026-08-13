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
  "generator_sources": ["generators/gen.cpp"]
}
```

| Field | Type | Note |
|-------|------|------|
| `accepted_solution_source` | string | optional path directly below `solutions/` to the main AC solution |
| `validator_source` | string | optional path below `validators/` |
| `checker_source` | string | optional path below `checkers/`; pass-fail only |
| `interactor_source` | string | optional path below `interactors/`; interactive only |
| `generator_sources` | string[] | optional allowlist of unique paths below `generators/`; absence means `[]` |

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
- `accepted_solution_source` is the only accepted-solution selection. It does
  not require or rewrite an adjacent descriptor.
- Runtime consumers never infer selections from component directories or
  filenames. Each generated test command names one unambiguous member of
  `generator_sources`; a source merely present below `generators/` is not
  executable until selected.
