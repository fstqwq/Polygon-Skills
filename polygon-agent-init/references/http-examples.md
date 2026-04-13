# Polygon Agent API -- HTTP Examples

All examples assume `BASE=http://localhost:8080`.

## 1. Register

```bash
curl -X POST "$BASE/agent/v1/register/reg-a8f3c2e1b9d04567" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "Codex",
    "desktop_id": "DESKTOP-7F3A9C2E",
    "init_ts": "2026-04-13T10:00:00Z"
  }'
```

Use the product name for `agent_name`, for example `Codex`, `Claude Code`, or `OpenCode`.
For `desktop_id`, prefer a stable machine identifier; hostname / computer name is an acceptable fallback.

```json
{
  "agent_session_id": "as-0123456789abcdef",
  "identity_hash": "abcdef0123456789...",
  "user": "alice",
  "server_name": "Polygon Replica"
}
```

## 2. Request Access

```bash
curl -X POST "$BASE/agent/v1/auth/request-access" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_session_id": "as-0123456789abcdef",
    "identity_hash": "abcdef0123456789...",
    "problem": "alice/aplusb"
  }'
```

```json
{
  "request_id": "ar-fedcba9876543210",
  "approve_path": "/agent/approve/ar-fedcba9876543210",
  "expires_in": 600
}
```

## 3. Session Heartbeat

```bash
curl "$BASE/agent/v1/auth/status?agent_session_id=as-0123456789abcdef&identity_hash=abcdef0123456789..."
```

```json
{
  "status": "ok",
  "agent_session_id": "as-0123456789abcdef",
  "identity_hash": "abcdef0123456789...",
  "user": "alice",
  "server_name": "Polygon Replica",
  "last_seen_at": "2026-04-13T10:05:00+00:00",
  "authorized_problems": [
    {
      "problem": "alice/aplusb",
      "scope": "workspace",
      "expires_at": "2026-04-14T10:00:00Z"
    }
  ]
}
```

Use this when you already have a saved state file and want to confirm the session is still live.

## 4. Poll

```bash
curl "$BASE/agent/v1/auth/poll/ar-fedcba9876543210?agent_session_id=as-0123456789abcdef&identity_hash=abcdef0123456789..."
```

Before approval:
```json
{"status": "pending"}
```

After approval (first poll only):
```json
{
  "status": "approved",
  "token": "poly_aBcDeFgHiJkLmN...",
  "problem": "alice/aplusb",
  "expires_at": "2026-04-14T10:00:00Z"
}
```

## 5. Workspace Status

```bash
curl "$BASE/agent/v1/workspace/status" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..."
```

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

## 6. List Files

```bash
curl "$BASE/agent/v1/workspace/files?path=solutions" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..."
```

```json
{
  "base_path": "solutions",
  "entries": [
    {"path": "solutions/main.cpp", "is_dir": false, "is_file": true},
    {"path": "solutions/brute.py", "is_dir": false, "is_file": true}
  ],
  "truncated": false
}
```

## 7. Read File

```bash
curl "$BASE/agent/v1/workspace/file?path=solutions/main.cpp" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..."
```

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

## 8. Upload File

```bash
curl -X POST "$BASE/agent/v1/workspace/upload" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..." \
  -F "path=solutions/brute.py" \
  -F "file=@brute.py"
```

```json
{"ok": true, "path": "solutions/brute.py", "bytes": 256}
```

## 9. Delete File

```bash
curl -X DELETE "$BASE/agent/v1/workspace/files/solutions/brute.py" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..."
```

```json
{"ok": true, "path": "solutions/brute.py"}
```

## 10. Start Verification

```bash
curl -X POST "$BASE/agent/v1/verification/start" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..." \
  -H "Content-Type: application/json" \
  -d '{}'
```

```json
{"verification_id": "ver-0123456789ab", "status": "queued"}
```

## 11. Verification Status

```bash
curl "$BASE/agent/v1/verification/ver-0123456789ab/status" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..."
```

```json
{
  "verification_id": "ver-0123456789ab",
  "status": "ok",
  "runtime_summary": {...}
}
```

## 12. Export

```bash
curl -X POST "$BASE/agent/v1/export/start" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..." \
  -H "Content-Type: application/json" \
  -d '{"export_type": "native"}'
```

```json
{"export_id": "exp-api-abc123", "status": "queued"}
```

## 13. Download Export

```bash
curl -o package.zip "$BASE/agent/v1/export/exp-api-abc123/download" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..."
```

Returns binary `application/zip`. Save to a file, do not parse as JSON.

## 14. Commit

```bash
curl -X POST "$BASE/agent/v1/commit" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..." \
  -H "Content-Type: application/json" \
  -d '{"message": "add brute force solution"}'
```

```json
{"status": "ok", "head": "abc123def456..."}
```

## 15. Commit Status

```bash
curl "$BASE/agent/v1/commit/abc123def456.../status" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..."
```

```json
{
  "ref": "abc123def456...",
  "status": "published",
  "head": "abc123def456...",
  "remote_head": "abc123def456..."
}
```
