---
name: polygon-agent-verification
description: "Run and inspect verification results through the Polygon Agent token workflow. Use when starting or checking verification via /agent/v1/verification/* with a bearer token."
---

# Polygon Agent -- Verification

## When to Use This Skill

Use this skill when:
- you need to start a full verification
- you need to wait for the final verification status
- you need the detailed YAML verification report

## Required Token Scope

Starting verification from a local mirror requires **`workspace`** scope because the workflow must `push` first to confirm the remote workspace version.

Waiting for an already-started verification and fetching details only need **`readonly`** scope.

## Primary Path

### Confirm remote version, then start verification

Before `verify-start`, push the local mirror so the remote workspace being verified is exactly the version you intend to test:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py push \
  --problem "alice/aplusb"
```

If your current directory is inside the problem repo, pass explicit paths:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py push \
  --problem "alice/aplusb" \
  --state-file "../.polygon-agent/state.json" \
  --target-dir "."
```

If `push` fails, stop and report the error. Do not start verification against a stale remote workspace.

After `push` succeeds, start verification:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-start \
  --problem "alice/aplusb"
```

Read `verification_id` from the JSON result. This verification captures the remote workspace state after the successful push.

### Wait for completion

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-wait \
  --problem "alice/aplusb" \
  --verification-id "ver-0123456789ab"
```

The result is intentionally small: final status only.

### Fetch detail report

Inline:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-detail \
  --problem "alice/aplusb" \
  --verification-id "ver-0123456789ab"
```

Save to a local file:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-detail \
  --problem "alice/aplusb" \
  --verification-id "ver-0123456789ab" \
  --save-to "./alice/aplusb/temp/verification.yaml"
```

Zoom into a specific test:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-detail \
  --problem "alice/aplusb" \
  --verification-id "ver-0123456789ab" \
  --test-name "002.in"
```

Zoom into a specific source/test cell:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-detail \
  --problem "alice/aplusb" \
  --verification-id "ver-0123456789ab" \
  --test-name "002.in" \
  --source "solutions/ac_python.py"
```

## Notes

- only one verification can run at a time per workspace
- a running verification uses the workspace state captured at start time
- do not run `verify-start` directly after local edits; `push` first to confirm the remote version
- the CLI does not return verbose polling logs by default
- saved verification reports are diagnostics and must go under the local problem repo's `temp/`

## Reference

- Shared CLI commands: `skills/polygon-agent-cli/references/cli.md`
- Endpoint reference: `skills/polygon-agent-init/references/agent-api.md`
