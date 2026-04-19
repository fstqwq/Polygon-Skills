---
name: polygon-agent-verification
description: "Run and inspect Polygon verification through the agent CLI. Use when starting verification, waiting for completion, or fetching detailed reports."
---

# Polygon Agent -- Verification

## When to Use

Use this skill when final verdicts, limits, or performance matter. Local runs are advisory; online Verification is authoritative.

Starting verification from local edits requires `workspace` scope because the local mirror must be pushed first. Waiting for an existing verification or fetching detail only needs `readonly`.

## Start

Push first so verification captures the intended remote workspace:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py push \
  --problem "alice/aplusb"
```

If push fails, stop. Do not start verification against a stale remote workspace.

Then start verification:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-start \
  --problem "alice/aplusb"
```

Read `verification_id` from the JSON result.

## Wait and Inspect

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-wait \
  --problem "alice/aplusb" \
  --verification-id "ver-0123456789ab"
```

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-detail \
  --problem "alice/aplusb" \
  --verification-id "ver-0123456789ab" \
  --save-to "./alice/aplusb/temp/verification.yaml"
```

## Rules

- Only one verification can run at a time per workspace.
- Saved reports are diagnostics and belong under the local repo's `temp/`.
- Use `verify-detail --test-name ... --source ...` for focused failure inspection.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for inline detail and zoom-in flags.
