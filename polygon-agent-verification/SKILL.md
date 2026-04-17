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

**`readonly`** or higher.

## Primary Path

### Start verification

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-start \
  --problem "alice/aplusb"
```

Read `verification_id` from the JSON result.

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
  --save-to "./verification.yaml"
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
- the CLI does not return verbose polling logs by default

## Reference

- Shared CLI commands: `skills/polygon-agent-cli/references/cli.md`
- Endpoint reference: `skills/polygon-agent-init/references/agent-api.md`
