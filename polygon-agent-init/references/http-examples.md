# Polygon Agent API -- HTTP Examples

All examples assume `BASE=http://localhost:8080`.

## 1. Register

```bash
curl -X POST "$BASE/agent/v1/register/reg-a8f3c2e1b9d04567" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "<your-agent-name>",
    "desktop_id": "<unique-machine-or-session-id>",
    "init_ts": "2026-04-13T10:00:00Z"
  }'
```

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

## 3. Poll

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

## 4. Workspace Status

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

## 5. List Files

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

## 6. Read File

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

## 7. Upload File

```bash
curl -X POST "$BASE/agent/v1/workspace/upload" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..." \
  -F "path=solutions/brute.py" \
  -F "file=@brute.py"
```

```json
{"ok": true, "path": "solutions/brute.py", "bytes": 256}
```

## 8. Delete File

```bash
curl -X DELETE "$BASE/agent/v1/workspace/files/solutions/brute.py" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..."
```

```json
{"ok": true, "path": "solutions/brute.py"}
```

## 9. Start Verification

```bash
curl -X POST "$BASE/agent/v1/verification/start" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..." \
  -H "Content-Type: application/json" \
  -d '{}'
```

```json
{"verification_id": "ver-0123456789ab", "status": "queued"}
```

## 10. Verification Status

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

## 11. Export

```bash
curl -X POST "$BASE/agent/v1/export/start" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..." \
  -H "Content-Type: application/json" \
  -d '{"export_type": "native"}'
```

```json
{"export_id": "exp-api-abc123", "status": "queued"}
```

## 12. Download Export

```bash
curl -o package.zip "$BASE/agent/v1/export/exp-api-abc123/download" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..."
```

Returns binary `application/zip`. Save to a file, do not parse as JSON.

## 13. Commit

```bash
curl -X POST "$BASE/agent/v1/commit" \
  -H "Authorization: Bearer poly_aBcDeFgHiJkLmN..." \
  -H "Content-Type: application/json" \
  -d '{"message": "add brute force solution"}'
```

```json
{"status": "ok", "head": "abc123def456..."}
```

## 14. Commit Status

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
