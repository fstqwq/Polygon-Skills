---
name: polygon-agent-export
description: "Build and download DOMjudge or ICPC 2025-09 problem packages through the agent CLI."
---

# Polygon Agent -- Export

## When to Use

Use this skill to start an export job, wait for completion, and download the ZIP artifact. Requires `readonly` scope or higher.

## Export

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-start \
  --problem "alice/aplusb" \
  --format "domjudge"
```

Use `--format "icpc-2025-09"` for a strict ICPC Problem Package 2025-09.
Read `job_id` from the JSON result.

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-wait \
  --problem "alice/aplusb" \
  --job-id "exp-api-abc123"
```

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-download \
  --problem "alice/aplusb" \
  --job-id "exp-api-abc123" \
  --output "./alice/aplusb/temp/aplusb-domjudge.zip"
```

`--output` is required; the CLI does not guess a filename.

## Rules

- Both formats target the latest published revision captured when the export starts.
- If that revision has not been fully verified, the export job runs Verification before
  projecting the requested package.
- A Workspace snapshot is a separate working-copy operation; package export never reads
  the local or remote working tree.
- Store downloaded ZIPs under `temp/` unless the file is intentionally becoming tracked content.
- Use owner-qualified repo paths such as `./alice/aplusb/`.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for optional export flags.
