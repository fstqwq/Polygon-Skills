---
name: polygon-agent-push
description: "Upload or delete workspace files in a Polygon problem through the agent token workflow. Use when pushing local changes to a Polygon workspace via /agent/v1/workspace/* write endpoints."
---

# Polygon Agent -- Push

## When to Use This Skill

Use this skill when:
- You need to upload files to a Polygon problem workspace via the agent API
- You need to delete files from a workspace via the agent API
- You have made local edits and want to push them to the cloud workspace

Do NOT use this skill for:
- Reading files (use `polygon-agent-fetch`)
- Committing / publishing changes (use `polygon-agent-commit`)
- Uploading through the web UI

## Required Token Scope

**`workspace`** (or higher)

If you only have a `readonly` token, upload and delete will return 403.
Request a new token with `workspace` scope using `polygon-agent-connect`.

## Endpoints

All requests require `Authorization: Bearer <token>`.

### Upload a file

```
POST {base_url}/agent/v1/workspace/upload
Content-Type: multipart/form-data

Fields:
  path: solutions/brute.py       (workspace-relative path)
  file: <file content>           (the file binary)
```

Response:
```json
{"ok": true, "path": "solutions/brute.py", "bytes": 256}
```

- The path is workspace-relative. Absolute paths and `..` traversal are rejected.
- If the file already exists, it is overwritten.
- Parent directories are created automatically.
- The target must be a file path, not a directory.

### Delete a file

```
DELETE {base_url}/agent/v1/workspace/files/solutions/brute.py
```

Response:
```json
{"ok": true, "path": "solutions/brute.py"}
```

## Typical Workflow

1. **Fetch** current files with `polygon-agent-fetch` to understand the workspace
2. Make your changes locally
3. **Push** changed files with `workspace/upload`
4. Optionally delete obsolete files with `workspace/files/{path}`
5. **Verify** with `polygon-agent-verification` to confirm correctness
6. **Commit** with `polygon-agent-commit` when ready to publish

## Important Notes

- Push only modifies the workspace working tree. Changes are NOT committed.
  Use `polygon-agent-commit` to commit and publish.
- After pushing, the workspace will show `"dirty": true` in status.
- Push does not trigger verification. Use `polygon-agent-verification` separately.

## Reference

For full endpoint details, read `skills/polygon-agent-init/references/agent-api.md`.
For curl examples, read `skills/polygon-agent-init/references/http-examples.md`.
