---
name: polygon-agent-push
description: "Upload or delete workspace files in a Polygon problem through the agent token workflow. Use when pushing local changes to a Polygon workspace via /agent/v1/workspace/* write endpoints."
---

# Polygon Agent -- Push

## When to Use This Skill

Use this skill when:
- you need to upload a local file into the remote workspace
- you need to delete a remote workspace file
- you already know what should change and want to update the cloud workspace state

## Required Token Scope

**`workspace`** or higher.

If you only have `readonly`, request a higher-scope token through `polygon-agent-connect`.

## Primary Path

### Upload

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py upload \
  --problem "alice/aplusb" \
  --workspace-path "solutions/brute.py" \
  --local-file "./brute.py"
```

### Delete

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py delete \
  --problem "alice/aplusb" \
  --workspace-path "solutions/brute.py"
```

## Typical Workflow

1. fetch or inspect current workspace state
2. update remote files with `upload` and `delete`
3. run verification with `polygon-agent-verification`
4. commit only after the user explicitly asks for it

## Notes

- upload always reads content from `--local-file`; do not construct file content inline in shell
- push modifies only the workspace working tree
- push does not trigger verification automatically

## Reference

- Shared CLI commands: `skills/polygon-agent-cli/references/cli.md`
- Endpoint reference: `skills/polygon-agent-init/references/agent-api.md`
