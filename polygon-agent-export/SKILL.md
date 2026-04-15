---
name: polygon-agent-export
description: "Export and download a problem zip file through the Polygon Agent token workflow. Use when exporting via /agent/v1/export/* with a bearer token."
---

# Polygon Agent -- Export

## When to Use This Skill

Use this skill when:
- You need to export and download a problem zip file (ICPC or native format) via the agent API
- You need to check export status or download the result

Do NOT use this skill for:
- Exporting through the web UI
- Importing packages (use `polygon-agent-push` + `polygon-agent-fetch`)

## Required Token Scope

**`readonly`** (or higher)

Export does NOT require `workspace` or `commit` scope.

## Endpoints

All requests require `Authorization: Bearer <token>`.

### Start export

```
POST {base_url}/agent/v1/export/start
Content-Type: application/json

{"export_type": "native"}
```

Or:

```json
{"export_type": "icpc", "verification_id": "ver-0123456789ab"}
```

Response:
```json
{"export_id": "exp-api-abc123", "status": "queued"}
```

### Export types

| Type | Source | Requires committed revision? |
|------|--------|------------------------------|
| `native` | Current working tree | No |
| `icpc` | Last committed revision | Yes -- the workspace must have commits |

### Check status

```
GET {base_url}/agent/v1/export/{export_id}/status
```

Response when complete:
```json
{
  "export_id": "exp-api-abc123",
  "status": "ok",
  "download_path": "/agent/v1/export/exp-api-abc123/download",
  "filename": "aplusb-v3.zip"
}
```

Status values: `queued`, `running`, `ok`, `failed`

### Download

```
GET {base_url}/agent/v1/export/{export_id}/download
```

Returns binary `application/zip`.

**Important**: This returns a raw ZIP file, not JSON. Save the response body to a file:
```bash
curl -o package.zip "{base_url}/agent/v1/export/{export_id}/download" \
  -H "Authorization: Bearer <token>"
```

## Typical Workflow

1. Optionally run verification first (`polygon-agent-verification`)
2. Start export: `POST /agent/v1/export/start`
3. Poll status every 3-5 seconds: `GET /agent/v1/export/{id}/status`
4. When `status` is `ok`, download: `GET /agent/v1/export/{id}/download`
5. Save the ZIP to a local file

## Important Notes

- `icpc` export requires a committed revision. If the workspace has uncommitted changes, commit first with `polygon-agent-commit`.
- `native` export works from the current working tree, including uncommitted changes.
- Only one export of the same type/source can run at a time. Starting a duplicate returns 409.

## Reference

For full endpoint details, read `skills/polygon-agent-init/references/agent-api.md`.
For curl examples, read `skills/polygon-agent-init/references/http-examples.md`.
