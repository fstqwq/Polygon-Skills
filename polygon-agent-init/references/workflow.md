# Polygon Agent Workflow

## Overview

The agent workflow has three stages:
1. **Initialize** -- establish an agent session
2. **Connect to a problem** -- obtain a per-problem token
3. **Operate** -- use the token to fetch, push, verify, export, or commit

```
user generates register URL -> agent registers -> agent requests problem access -> user approves in browser -> agent polls -> token -> operate
```

## Stage 1: Initialize

### Step 1: User generates a registration URL

The **human user** clicks "Connect to Agent" in the Web UI.
This calls `POST /agent/connect` (session cookie auth) and returns a one-time URL:

```
http://polygon.example.com/agent/v1/register/reg-a8f3c2e1b9d04567
```

The user copies this URL and provides it to the agent.

### Step 2: Agent registers

The agent POSTs its identity to the registration URL:

```json
POST /agent/v1/register/reg-a8f3c2e1b9d04567
{
  "agent_name": "Codex",
  "desktop_id": "DESKTOP-7F3A9C2E",
  "init_ts": "2026-04-13T10:00:00Z"
}
```

Identity guidance:
- `agent_name` should be the agent product name, for example `Codex`, `Claude Code`, or `OpenCode`
- `desktop_id` should be stable for the same host or installation
- A machine name / hostname is acceptable if that is the most stable identifier the agent can obtain
- If the runtime exposes no stable host identifier, generate a UUID once and persist it locally

Response:
```json
{
  "agent_session_id": "as-0123456789abcdef",
  "identity_hash": "sha256...",
  "user": "alice",
  "server_name": "Polygon Replica"
}
```

The agent must cache `agent_session_id` and `identity_hash` for subsequent requests.

If the agent already has a saved local state file, it should prefer:

```
GET /agent/v1/auth/status?agent_session_id=as-...&identity_hash=sha256...
```

before re-registering or requesting access again. This confirms the session is still live and returns the current authorized problem list.

The registration code is **one-time use** and expires after 5 minutes.
If the same identity re-registers, the existing session is reused.

## Stage 2: Connect to a problem

### Step 3: Agent requests problem access

```json
POST /agent/v1/auth/request-access
{
  "agent_session_id": "as-0123456789abcdef",
  "identity_hash": "sha256...",
  "problem": "alice/aplusb"
}
```

Response:
```json
{
  "request_id": "ar-fedcba9876543210",
  "approve_path": "/agent/approve/ar-fedcba9876543210",
  "expires_in": 600
}
```

### Step 4: Human approves

The agent MUST display the full approval URL to the user:

```
Please open this URL in your browser to approve access:
http://polygon.example.com/agent/approve/ar-fedcba9876543210
```

The agent MUST NOT attempt to POST to the approval endpoint.
The agent MUST NOT try to fake a browser session.
Only the human can approve, choosing scope and TTL.

### Step 5: Agent polls for approval

```
GET /agent/v1/auth/poll/ar-fedcba9876543210?agent_session_id=as-...&identity_hash=sha256...
```

Poll until `status` is `approved`, `denied`, or `expired`.
Recommended poll interval: 2-3 seconds.

On `approved`, the response includes a token (first poll only):
```json
{
  "status": "approved",
  "token": "poly_aBcDeFgHiJkLmN...",
  "problem": "alice/aplusb",
  "expires_at": "2026-04-14T10:00:00Z"
}
```

The token is returned **exactly once**. Subsequent polls return `{"status": "approved"}` without the token.

## Stage 3: Operate

Use the token as a Bearer header on all `/agent/v1/*` endpoints:

```
Authorization: Bearer poly_aBcDeFgHiJkLmN...
```

The token is scoped to a specific problem. All operations implicitly target that problem's workspace.

## Token Lifecycle

- Tokens have a TTL set at approval time (1h / 24h / 7d / 30d / forever).
- The user can revoke individual tokens or disconnect the entire agent session via the Web UI.
- If the user's repo ACL is downgraded, the token's effective scope is immediately reduced.
- When an agent is done working, it can simply discard the token from memory. There is no agent-side logout endpoint.
