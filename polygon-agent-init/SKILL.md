---
name: polygon-agent-init
description: "Initialize a Polygon agent identity and register it with the server. Use when the task is specifically about starting the /agent/v1/* token workflow and obtaining an agent session."
---

# Polygon Agent -- Init

## When to Use This Skill

Use this skill when:
- The user provides a registration URL (contains `/agent/v1/register/`)
- The user asks to initialize an agent against Polygon
- You do not yet have a cached `agent_session_id` / `identity_hash`

Do NOT use this skill for:
- Requesting access to a specific problem token (use `polygon-agent-connect`)
- Normal file editing, exporting, or committing through the web UI or git
- Tasks that don't involve the `/agent/v1/*` API

## Goal

Initialize the agent's identity and establish a reusable Polygon agent session.

At the end of this skill you should have cached:
- `base_url`
- `agent_session_id`
- `identity_hash`
- `identity`
- `user`
- `server_name`

Use `polygon-agent-connect` after this to request access to a specific problem and obtain a token.

## Procedure

### Step 1: Extract base URL from the registration URL

Given:
```
http://polygon.example.com/agent/v1/register/reg-a8f3c2e1b9d04567
```

Cache:
```
base_url = http://polygon.example.com
```

### Step 2: Prepare identity metadata

Prepare:
```json
{
  "agent_name": "<your-agent-name>",
  "desktop_id": "<unique-machine-or-session-id>",
  "init_ts": "<ISO-8601 timestamp>"
}
```

Rules:
- `agent_name` is chosen by the current agent implementation
- `desktop_id` should be stable enough to identify this agent instance or host
- `init_ts` should be generated once for this initialized identity

### Step 3: Register with the server

```
POST {base_url}/agent/v1/register/reg-a8f3c2e1b9d04567
Content-Type: application/json

{
  "agent_name": "<your-agent-name>",
  "desktop_id": "<unique-machine-or-session-id>",
  "init_ts": "<ISO-8601 timestamp>"
}
```

Cache the response:
- `agent_session_id`
- `identity_hash`
- `user`
- `server_name`

If the registration code is expired or already used, the server returns `404` or `410`.
In that case, ask the user to generate a new registration URL in the Web UI.

## Model Overview

The Polygon Agent API lets external agents (Claude Code, Codex, OpenCode, etc.) operate on problems through a bearer token workflow, without needing browser access.

### Key Concepts

1. **Session** -- Established by registering with a one-time code. Uniquely identified by `(user, identity_hash)`. Persists across re-registrations.

2. **Token** -- Scoped to a single `(user, problem)` pair. Has three levels:
   - `readonly` -- read workspace, run verification, export
   - `workspace` -- above + upload/delete files
   - `commit` -- above + git commit and push

3. **Human-in-the-loop** -- The user must approve each problem access request in their browser. The agent cannot approve itself.

4. **Effective scope** -- Always `min(token_scope, user_ACL)`. If the user's access is downgraded, the token's capabilities are immediately reduced.

### Workflow

```
init/register -> connect/request-access -> [user approves in browser] -> poll -> token -> operate
```

### Available Skills

| Skill | Purpose | Min Scope |
|-------|---------|-----------|
| `polygon-agent-connect` | Request access to a specific problem and obtain a token | -- |
| `polygon-agent-fetch` | Read workspace files | `readonly` |
| `polygon-agent-push` | Upload/delete workspace files | `workspace` |
| `polygon-agent-verification` | Run and check verification | `readonly` |
| `polygon-agent-export` | Export problem packages | `readonly` |
| `polygon-agent-commit` | Commit and publish | `commit` |

### Reference Documents

For detailed information, read these files using your file reading tool:

- `skills/polygon-agent-init/references/agent-api.md` -- Complete endpoint catalog with methods, scopes, and payloads
- `skills/polygon-agent-init/references/workflow.md` -- Step-by-step workflow from init to operate
- `skills/polygon-agent-init/references/state-schema.md` -- Recommended state structure
- `skills/polygon-agent-init/references/http-examples.md` -- curl/JSON examples for every endpoint

## Rules

- These skills are agent-agnostic. They work with Claude Code, Codex, OpenCode, or any agent that can make HTTP requests.
- There is no `/agent/v1/import/*` endpoint. File operations use the workspace API (`fetch` + `push`).
- Token revocation and session disconnect are managed by the user in the Web UI, not by the agent.
