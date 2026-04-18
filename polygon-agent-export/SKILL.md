---
name: polygon-agent-export
description: "Export and download a problem zip file through the Polygon Agent token workflow. Use when exporting via /agent/v1/export/* with a bearer token."
---

# Polygon Agent -- Export

## When to Use This Skill

Use this skill when:
- you need to start an export job
- you need to wait for export completion
- you need to download the ZIP artifact

## Required Token Scope

**`readonly`** or higher.

## Primary Path

### Start export

Native:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-start \
  --problem "alice/aplusb" \
  --export-type "native"
```

ICPC:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-start \
  --problem "alice/aplusb" \
  --export-type "icpc"
```

Read `export_id` from the JSON result.

### Wait for completion

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-wait \
  --problem "alice/aplusb" \
  --export-id "exp-api-abc123"
```

### Download the ZIP

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-download \
  --problem "alice/aplusb" \
  --export-id "exp-api-abc123" \
  --output "./alice/aplusb/temp/aplusb.zip"
```

`--output` is required. The CLI does not guess a default download filename.

## Notes

- `native` export works from the current working tree
- `icpc` export requires a committed revision
- the CLI writes the ZIP directly to `--output` and returns only a small JSON summary
- if you store a remote problem locally, use `./<owner>/<problem>/` as the repo root

## Reference

- Shared CLI commands: `skills/polygon-agent-cli/references/cli.md`
- Endpoint reference: `skills/polygon-agent-init/references/agent-api.md`
