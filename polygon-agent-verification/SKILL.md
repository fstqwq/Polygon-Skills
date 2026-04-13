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

### Get full detail (JSON)

```
GET {base_url}/agent/v1/verification/{verification_id}/detail
```

Returns the complete verification result including per-test, per-solution results.

### Get full detail (text)

```
GET {base_url}/agent/v1/verification/{verification_id}/detail/text
```

Returns the same data as `/detail` but as `text/plain` (pretty-printed JSON).
Useful when you want human-readable output.

## Typical Workflow

1. Start verification: `POST /agent/v1/verification/start`
2. Poll status every 3-5 seconds: `GET /agent/v1/verification/{id}/status`
3. When `status` is `ok` or `failed`, get the full detail: `GET /agent/v1/verification/{id}/detail`
4. Analyze results:
   - Check if all expected-AC solutions passed
   - Check if expected-WA/TLE solutions got the expected verdict
   - Review any compilation errors or runtime failures

## Important Notes

- Only one verification can run at a time per workspace. Starting a new one while another is running returns 409.
- Verification results are tied to the workspace state at the time of starting -- pushing new files doesn't affect a running verification.

## Reference

For full endpoint details, read `skills/polygon-agent-init/references/agent-api.md`.
For curl examples, read `skills/polygon-agent-init/references/http-examples.md`.
