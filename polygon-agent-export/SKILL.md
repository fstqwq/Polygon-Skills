---
name: polygon-agent-export
description: "Start, monitor, and download Polygon-Replica external package exports through the agent CLI. Use when the user requests a DOMjudge, ICPC 2025-09, QOJ, or Nowcoder problem package."
---

# Polygon Agent -- Export

## Export

Starting an export requires `workspace` scope. Waiting for or downloading an
existing export requires `readonly` scope.

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-start \
  --problem "alice/aplusb" \
  --format "domjudge"
```

Current external formats are:

- `domjudge`
- `icpc-2025-09`
- `qoj`
- `nowcoder`

The server's adapter registry is authoritative; the CLI forwards `--format`
without maintaining a separate allowlist.
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

- Every external format targets the latest published revision captured when the export starts.
- If that revision has not been fully verified, the export job runs Verification before
  preparing the Native Package and running the requested adapter.
- The Agent Package Export API does not expose direct Native Package creation or download.
- A Workspace snapshot is a separate working-copy operation; package export never reads
  the local or remote working tree.
- Store downloaded ZIPs under `temp/` unless the file is intentionally becoming tracked content.
- Use owner-qualified repo paths such as `./alice/aplusb/`.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for optional export flags.
