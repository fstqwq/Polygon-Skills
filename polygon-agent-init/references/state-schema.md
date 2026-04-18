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
    "agent_name": "Codex",
    "desktop_id": "DESKTOP-7F3A9C2E",
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

- Recommended default state file location:
  - `./.polygon-agent/state.json` under the current working directory
  This keeps the default state local to the workspace where the agent is running.

- `identity.agent_name` should be the agent product or implementation name.
  Good examples: `Codex`, `Claude Code`, `OpenCode`.
  Do not use a repo name, task description, or problem slug here.

- `identity.desktop_id` should be stable across runs on the same host or installation.
  Preferred order:
  1. a stable machine identifier exposed by the runtime or OS
  2. the machine hostname / computer name
  3. a generated UUID that the agent stores locally and reuses
  If only a hostname is available, using the machine name is acceptable.

- Recommended hostname lookup by platform:
  - Windows:
    - PowerShell: `$env:COMPUTERNAME`
    - fallback: `hostname`
  - Linux:
    - `hostname`
    - fallback: `cat /etc/hostname`

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
