---
name: polygon-agent-auth
description: "Initialize Polygon agent identity authentication and request scoped problem grants. Use for registration URLs, session status, connect/poll approval flow, or grant scope upgrades."
---

# Polygon Agent -- Auth

## When to Use

Use this skill when:
- the user provides an `/agent/v1/register/` URL
- no local agent session exists yet
- a problem grant is missing, expired, or has insufficient scope
- you need an independent `readonly`, `workspace`, or `commit` grant

## Registration URL

If no registration URL is available, ask the user with this exact text:

```text
Please open Polygon-Replica and click the top-right Settings -> Connected Agents -> Connect to Agent. Copy the generated Registration URL and send it here.
```

Do not invent alternate navigation wording for this step.

## Initialize Session

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py init \
  --register-url "http://polygon.example.com/agent/v1/register/reg-abc" \
  --agent-name "Codex"
```

If omitted, `--state-file` defaults to `./.polygon-agent/state.json` under the current working directory.

Check the cached session:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py status
```

## Request Problem Access

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py connect \
  --problem "alice/aplusb"
```

Show the returned `approve_url` to the user. Do not approve the browser request yourself.

After the user approves:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py poll \
  --request-id "ar-0123456789abcdef" \
  --wait
```

Approval creates a server-side grant. The CLI keeps using its connected
identity and never receives or saves a problem secret.

## Rules

- Agent identity name should be the product name: `Codex`, `Claude Code`, or similar.
- Do not store registration codes, passwords, browser cookies, or approval URLs after approval.
- The session may have a non-expiring general permission selected by the user
  in Connected Agents.
- Per-problem approvals retain independent scopes and expiries.
- A 401 means the connected credential is invalid; do not silently create a
  new session or discard diagnostic state. Ask the user for a new registration
  URL and run `init` to reconnect and rotate the credential.
- For `agent_permission_required`, request the indicated problem scope. For
  `agent_general_permission_required`, direct the user to Connected Agents;
  a problem grant cannot replace required general permission.
- The CLI never approves access by itself; human browser approval is mandatory.
- For internal HTTPS servers with self-signed certificates, the CLI already disables TLS verification by default and warns only during `init`.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for the full command catalog.
