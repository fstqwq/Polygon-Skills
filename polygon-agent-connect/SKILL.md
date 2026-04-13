---
name: polygon-agent-connect
description: "Request access to a specific Polygon problem and obtain a bearer token. Use when the task is specifically about connecting an already-initialized agent to a problem through /agent/v1/*."
---

# Polygon Agent -- Connect

## When to Use This Skill

Use this skill when:
- The user asks to connect an initialized agent to a specific Polygon problem
- You need a bearer token to call other `/agent/v1/*` endpoints for a problem
- You already have a cached session but do not yet have a token for this problem

## Prerequisites

You must have already completed `polygon-agent-init`.

Required cached state:
- `base_url`
- `agent_session_id`
- `identity_hash`

## Procedure

### Step 1: Request problem access

```
POST {base_url}/agent/v1/auth/request-access
Content-Type: application/json

{
  "agent_session_id": "<cached>",
  "identity_hash": "<cached>",
  "problem": "alice/aplusb"
}
```

### Step 2: Present approval URL to the user

**CRITICAL: You MUST NOT attempt to approve the access request yourself.**

Display the full approval URL to the user:
```
Please open this URL in your browser and click Approve:
{base_url}{approve_path}
```

You cannot and must not:
- POST to the approval endpoint
- Fake a browser session or cookie
- Skip the human approval step

### Step 3: Poll for approval

```
GET {base_url}/agent/v1/auth/poll/{request_id}?agent_session_id=...&identity_hash=...
```

Poll every 3 seconds until `status` is one of:
- `approved` -- cache the `token` from the first poll response
- `denied` -- inform the user, stop
- `expired` -- inform the user, offer to retry

The token is returned **only on the first successful poll**. If you lose it, you must request access again.

### Step 4: Store the token

Cache the token keyed by problem slug.

Read `skills/polygon-agent-init/references/state-schema.md` for the recommended state structure.

## Requesting Additional Problems

Repeat Steps 1-4 for each problem. Each problem requires a separate approval and has its own token.

## Token Lifecycle

- Tokens expire based on the TTL the user chose at approval (1h / 24h / 7d / 30d / forever).
- If a request returns 401, the token is invalid. Discard it and re-request access.
- When done working, simply discard the token from memory. There is no agent-side logout.
- Revocation and session disconnect are managed by the user in the Web UI -- not by the agent.

## Reference

For payload details, read `skills/polygon-agent-init/references/agent-api.md`.
For curl examples, read `skills/polygon-agent-init/references/http-examples.md`.
