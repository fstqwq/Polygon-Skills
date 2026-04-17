---
name: polygon-agent-connect
description: "Request access to a specific Polygon problem and obtain a bearer token. Use when the task is specifically about connecting an already-initialized agent to a problem through /agent/v1/*."
---

# Polygon Agent -- Connect

## When to Use This Skill

Use this skill when:
- you already have a session state from `polygon-agent-init`
- you need a token for a specific problem
- you need to upgrade or refresh access for that problem

## Primary Path

### Step 1: Request access

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py connect \
  --problem "alice/aplusb"
```

Or with an explicit state file:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py connect \
  --state-file "/path/to/polygon-agent-state.json" \
  --problem "alice/aplusb"
```

The result JSON includes:
- `request_id`
- `approve_url`
- `expires_in`
- `problem`

### Step 2: Show the approval URL to the user

**You MUST NOT approve the request yourself.**

Read `approve_url` from the command output and show it to the user.

You must not:
- POST to the approval endpoint
- fake a browser session or cookie
- skip the human approval step

### Step 3: Poll and save the token

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py poll \
  --request-id "ar-fedcba9876543210" \
  --wait
```

Or with an explicit state file:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py poll \
  --state-file "/path/to/polygon-agent-state.json" \
  --request-id "ar-fedcba9876543210" \
  --wait
```

On the first approved response, the CLI saves the token into the state file automatically.

## Token Lifecycle

- each problem has its own cached token
- if a later operation returns `401`, discard the token and reconnect for that problem
- when approval succeeds but the one-time token was already lost, request access again

## Reference

- Shared CLI commands: `skills/polygon-agent-cli/references/cli.md`
- State schema: `skills/polygon-agent-init/references/state-schema.md`
- Endpoint reference: `skills/polygon-agent-init/references/agent-api.md`
