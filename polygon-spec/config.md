# config/problem.json  --  Full Schema

```json
{
  "mode": "pass-fail",
  "pass_limit": 1,
  "time_limit_ms": 2000,
  "memory_limit_mb": 1024
}
```

| Field | Type | Values | Note |
|-------|------|--------|------|
| `mode` | string | `"pass-fail"` or `"interactive"` | required |
| `pass_limit` | int | ≥ 1 | 1 for normal; ≥ 2 for multi-pass interactive |
| `time_limit_ms` | int | > 0 | milliseconds |
| `memory_limit_mb` | int | > 0 | megabytes |

---

# config/build.json  --  Full Schema

```json
{
  "accepted_solution_source": "solutions/std.cpp",
  "validator_source": "validators/validator.cpp",
  "checker_source": "checkers/checker.cpp",
  "interactor_source": "",
  "generator_sources": []
}
```

| Field | Type | Note |
|-------|------|------|
| `accepted_solution_source` | string | repo-relative path to the main AC solution |
| `validator_source` | string | repo-relative path to the validator; empty if none |
| `checker_source` | string | repo-relative path to checker source (standard or custom); empty for auto-discovery |
| `interactor_source` | string | repo-relative path to the interactor; empty for non-interactive |
| `generator_sources` | array | list of repo-relative paths to generator sources |

Rules:
- All paths are repo-relative (e.g., `"solutions/std.cpp"`).
- Referenced files must exist.
- Standard checkers are copied into `checkers/` and referenced via `checker_source` like any other checker.
- For interactive problems: set `interactor_source`, leave `checker_source` empty.
