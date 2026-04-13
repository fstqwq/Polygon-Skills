---
name: polygon-agent-fetch
description: "Read workspace files from a Polygon problem through the agent token workflow. Use when operating Polygon through /agent/v1/workspace/* read endpoints with a bearer token."
---

# Polygon Agent -- Fetch

## When to Use This Skill

Use this skill when:
- You need to read files from a Polygon problem workspace via the agent API
- You need to check workspace status (head commit, dirty state)
- You need to list or enumerate workspace contents

Do NOT use this skill for:
- Reading local files on disk (use normal file tools)
- Uploading or deleting files (use `polygon-agent-push`)
- Operations through the web UI

## Required Token Scope

**`readonly`** (or higher)

All fetch operations only need a `readonly` token.

## Endpoints

All requests require `Authorization: Bearer <token>`.

### Check workspace status

```
GET {base_url}/agent/v1/workspace/status
```

Response:
```json
{
  "problem": "alice/aplusb",
  "user": "alice",
  "workspace_id": 42,
  "head_commit": "abc123...",
  "dirty": false,
  "git": {"branch": "main", "status": "clean"}
}
```

### List files

```
GET {base_url}/agent/v1/workspace/files
GET {base_url}/agent/v1/workspace/files?path=solutions
```

Response:
```json
{
  "base_path": "solutions",
  "entries": [
    {"path": "solutions/main.cpp", "is_dir": false, "is_file": true}
  ],
  "truncated": false
}
```

If `truncated` is true, list subdirectories individually to get complete results.

### Read a file

```
GET {base_url}/agent/v1/workspace/file?path=solutions/main.cpp
```

Response:
```json
{
  "path": "solutions/main.cpp",
  "is_dir": false,
  "size_bytes": 142,
  "media_type": "text/plain; charset=utf-8",
  "encoding": "utf-8",
  "content": "#include <bits/stdc++.h>\nint main(){...}\n"
}
```

For binary files, `encoding` will be `"base64"` and `content` will be base64-encoded.

If `is_dir` is true, the path is a directory -- use `files?path=...` to list its contents.

## Typical Workflow

1. Check `workspace/status` to see the current state
2. List `workspace/files` to discover what exists
3. Read specific files you need with `workspace/file?path=...`

## Reference

For full endpoint details, read `skills/polygon-agent-init/references/agent-api.md`.
For curl examples, read `skills/polygon-agent-init/references/http-examples.md`.
