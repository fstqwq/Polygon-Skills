# Polygon Agent API — Endpoint Reference

All endpoints below are real and implemented.
Do NOT invent endpoints not listed here.

## Web UI Endpoints (session cookie auth, same-origin protection)

These are for the human user in a browser. Agents do not call these directly.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/agent/sessions` | Agent management page |
| POST | `/agent/connect` | Generate one-time registration code |
| GET | `/agent/approve/{request_id}` | Approval page |
| POST | `/agent/approve/{request_id}` | Submit approval decision |
| POST | `/agent/revoke/{token_id}` | Revoke a single token |
| POST | `/agent/disconnect/{session_id}` | Disconnect agent session + revoke all tokens |

## Agent Bearer Token Endpoints (`/agent/v1/*`)

### Auth (no token needed)

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/agent/v1/register/{code}` | `{"agent_name", "desktop_id", "init_ts"}` | `{"agent_session_id", "identity_hash", "user", "server_name"}` |
| POST | `/agent/v1/auth/request-access` | `{"agent_session_id", "identity_hash", "problem"}` | `{"request_id", "approve_path", "expires_in"}` |
| GET | `/agent/v1/auth/poll/{request_id}` | query: `agent_session_id`, `identity_hash` | `{"status": "pending\|approved\|denied\|expired", "token"?, "problem"?, "expires_at"?}` |

### Verification (min_scope: `readonly`)

| Method | Path | Body / Query | Response |
|--------|------|-------------|----------|
| POST | `/agent/v1/verification/start` | `{}` | `{"verification_id", "status": "queued"}` |
| GET | `/agent/v1/verification/{id}/status` | — | `{"verification_id", "status", "runtime_summary"}` |
| GET | `/agent/v1/verification/{id}/detail` | — | `{"verification", "detail", "runtime_summary"}` |
| GET | `/agent/v1/verification/{id}/detail/text` | — | plain text JSON |

### Export (min_scope: `readonly`)

| Method | Path | Body / Query | Response |
|--------|------|-------------|----------|
| POST | `/agent/v1/export/start` | `{"export_type": "icpc"\|"native", "verification_id"?}` | `{"export_id", "status": "queued"}` |
| GET | `/agent/v1/export/{id}/status` | — | `{"export_id", "status", "download_path"?, ...}` |
| GET | `/agent/v1/export/{id}/download` | — | binary `application/zip` |

### Workspace Read (min_scope: `readonly`)

| Method | Path | Query | Response |
|--------|------|-------|----------|
| GET | `/agent/v1/workspace/status` | — | `{"problem", "user", "workspace_id", "head_commit", "dirty", "git"}` |
| GET | `/agent/v1/workspace/files` | `path?` | `{"base_path", "entries": [{"path", "is_dir", "is_file"}], "truncated"}` |
| GET | `/agent/v1/workspace/file` | `path` | `{"path", "is_dir", "size_bytes", "media_type", "encoding", "content"}` |

Note: `workspace/file` returns `content` as either UTF-8 text (`"encoding": "utf-8"`) or base64 (`"encoding": "base64"`).

### Workspace Write (min_scope: `workspace`)

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/agent/v1/workspace/upload` | multipart: `path` (form field) + `file` | `{"ok", "path", "bytes"}` |
| DELETE | `/agent/v1/workspace/files/{path}` | — | `{"ok", "path"}` |

### Commit (min_scope: `commit`)

| Method | Path | Body | Response |
|--------|------|------|----------|
| POST | `/agent/v1/commit` | `{"message"}` | `{"status": "ok", "head": "<sha>"}` |
| GET | `/agent/v1/commit/{ref}/status` | — | `{"ref", "status": "published\|local\|missing", "head", "remote_head"}` |

## Scope Hierarchy

Scopes are cumulative. A higher scope includes all capabilities of lower scopes.

```
readonly < workspace < commit
```

| Scope | Can do |
|-------|--------|
| `readonly` | verification, export, workspace read, commit status |
| `workspace` | above + workspace upload/delete |
| `commit` | above + commit |

Effective permission = `min(token_scope, user_ACL)`.
If user's repo ACL is downgraded (e.g., `write` → `read`), the token's effective scope is immediately reduced.

## Path Safety Rules

All workspace paths are workspace-relative. The server rejects:
- Absolute paths
- `..` traversal
- Symlink escape

## Error Responses

All error responses use: `{"error": "<message>"}` with appropriate HTTP status codes.

| Code | Meaning |
|------|---------|
| 400 | Invalid input |
| 401 | Token invalid / expired / revoked |
| 403 | Scope insufficient |
| 404 | Resource not found |
| 409 | Operation already running |
| 410 | Registration code already used |
| 422 | Validation error |
