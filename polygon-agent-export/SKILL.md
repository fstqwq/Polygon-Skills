---
name: polygon-agent-export
description: "Export and download Polygon problem packages through the agent CLI. Use for native or ICPC export jobs."
---

# Polygon Agent -- Export

## When to Use

Use this skill to start an export job, wait for completion, and download the ZIP artifact. Requires `readonly` scope or higher.

## Export

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-start \
  --problem "alice/aplusb" \
  --export-type "native"
```

Use `--export-type "icpc"` for ICPC packages. Read `export_id` from the JSON result.

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-wait \
  --problem "alice/aplusb" \
  --export-id "exp-api-abc123"
```

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-download \
  --problem "alice/aplusb" \
  --export-id "exp-api-abc123" \
  --output "./alice/aplusb/temp/aplusb.zip"
```

`--output` is required; the CLI does not guess a filename.

## Rules

- `native` export works from the current working tree.
- `icpc` export requires a committed revision.
- Store downloaded ZIPs under `temp/` unless the file is intentionally becoming tracked content.
- Use owner-qualified repo paths such as `./alice/aplusb/`.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for optional export flags.
