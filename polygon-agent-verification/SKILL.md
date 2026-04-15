---
name: polygon-agent-verification
description: "Run and inspect verification results through the Polygon Agent token workflow. Use when starting or checking verification via /agent/v1/verification/* with a bearer token."
---

# Polygon Agent -- Verification

## When to Use This Skill

Use this skill when:
- You need to run a full verification of a problem's test suite
- You need to check the status or results of a verification run
- You want a machine-readable verification report

Do NOT use this skill for:
- Running verification through the web UI
- Writing or modifying solution files (use `polygon-agent-push`)

## Required Token Scope

**`readonly`** (or higher)

Verification does NOT require `workspace` scope.
Starting a verification is a read-only operation -- it runs against the current workspace state without modifying it.

## Endpoints

All requests require `Authorization: Bearer <token>`.

### Start verification

```
POST {base_url}/agent/v1/verification/start
Content-Type: application/json

{}
```

Response:
```json
{"verification_id": "ver-0123456789ab", "status": "queued"}
```

This starts a full verification:
- Generates test inputs (for generator-based tests)
- Validates inputs
- Runs all solutions (main correct + others)
- Checks outputs

There are no parameters -- it always runs the full verification against the current workspace.

### Check status

```
GET {base_url}/agent/v1/verification/{verification_id}/status
```

Response:
```json
{
  "verification_id": "ver-0123456789ab",
  "status": "running",
  "runtime_summary": {...}
}
```

Status values: `queued`, `running`, `ok`, `failed`

### Get verification detail

```
GET {base_url}/agent/v1/verification/{verification_id}/detail
```

Returns a readable YAML report as `text/plain`.

The default report contains the full source-first verification table:

```
verification: ver-0123456789ab
status: failed
reason: ac_python.py required AC got TL

tasks:
  pending: 0
  queued: 0
  running: 0
  done: 120
  failed: 1
  cancelled: 0

columns:
  ac_python.py:
    source: solutions/ac_python.py
    role: solution
    expected: AC
    result: TL 2000ms 64MB
    tests:
      001.in: AC 300ms 20MB
      002.in: TL 2000ms 64MB
```

Zoom in to one test:

```
GET {base_url}/agent/v1/verification/{verification_id}/detail?test_name=002.in
```

Zoom in to one source/test cell:

```
GET {base_url}/agent/v1/verification/{verification_id}/detail?test_name=002.in&source=solutions/ac_python.py
```

## Typical Workflow

1. Start verification: `POST /agent/v1/verification/start`
2. Poll status every 3-5 seconds: `GET /agent/v1/verification/{id}/status`
3. When `status` is `ok` or `failed`, get the YAML detail report: `GET /agent/v1/verification/{id}/detail`
4. Analyze results:
   - Check if all expected-AC solutions passed
   - Check if expected-WA/TLE solutions got the expected verdict
   - Review any compilation errors or runtime failures
5. If a specific test needs inspection, use `?test_name=...`; if a single solution cell needs inspection, also pass `source=...`

## Important Notes

- Only one verification can run at a time per workspace. Starting a new one while another is running returns 409.
- Verification results are tied to the workspace state at the time of starting -- pushing new files doesn't affect a running verification.

## Reference

For full endpoint details, read `skills/polygon-agent-init/references/agent-api.md`.
For curl examples, read `skills/polygon-agent-init/references/http-examples.md`.
