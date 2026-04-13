# Polygon Agent State Schema

## Recommended Structure

The agent should maintain the following state during a session.
Storage mechanism (memory, file, env) is agent-specific -- this only defines the shape.

```json
{
  "base_url": "http://polygon.example.com",
  "agent_session_id": "as-0123456789abcdef",
  "identity_hash": "sha256...",
  "identity": {
    "agent_name": "<your-agent-name>",
    "desktop_id": "<unique-machine-or-session-id>",
    "init_ts": "2026-04-13T10:00:00Z"
  },
  "user": "alice",
  "server_name": "Polygon Replica",
  "tokens": {
    "alice/aplusb": {
      "token": "poly_aBcDeFgHiJkLmN...",
      "scope": "workspace",
      "expires_at": "2026-04-14T10:00:00Z"
    }
  }
}
```

## Field Descriptions

| Field | Source | Lifetime |
|-------|--------|----------|
| `base_url` | User provides or agent infers from registration URL | Session |
| `agent_session_id` | Response from `/agent/v1/register/{code}` | Session |
| `identity_hash` | Response from `/agent/v1/register/{code}` | Session |
| `identity` | Agent's own metadata, sent at registration | Fixed |
| `user` | Response from `/agent/v1/register/{code}` | Session |
| `tokens[problem]` | Response from first `poll` after approval | Per-problem, time-limited |

## Rules

- `base_url` must include scheme and host, no trailing slash.
  Derive it from the registration URL the user gives you.
  Example: if registration URL is `http://localhost:8080/agent/v1/register/reg-abc`, then `base_url = "http://localhost:8080"`.

- `tokens` is keyed by problem slug (e.g., `"alice/aplusb"`).
  Each problem requires a separate approval and has its own token.

- If a token returns 401, discard it and re-request access for that problem.

- The agent does not need to store scope or expires_at explicitly.
  The server enforces scope per-request. But storing them helps the agent
  decide when to request a higher scope without a round trip.

## What NOT to Store

- Do not store the registration code -- it is one-time use.
- Do not store the user's password or session cookie.
- Do not store approval URLs -- they are only needed during the approval flow.
