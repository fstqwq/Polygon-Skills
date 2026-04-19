---
name: polygon-agent-auth
description: "Initialize Polygon agent authentication and request problem access tokens. Use for registration URLs, session status, connect/poll approval flow, or token scope upgrades."
---

# Polygon Agent -- Auth

## When to Use

Use this skill when:
- the user provides an `/agent/v1/register/` URL
- no local agent session exists yet
- a problem token is missing, expired, or has insufficient scope
- you need to upgrade from `readonly` to `workspace` or `commit`

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

The CLI saves the approved token into the state file.

## Rules

- Agent identity name should be the product name: `Codex`, `Claude Code`, or similar.
- Do not store registration codes, passwords, browser cookies, or approval URLs after approval.
- Each problem has its own token and scope.
- If an operation returns 401, request access again.
- If an operation returns 403, request a higher-scope token.
- The CLI never approves access by itself; human browser approval is mandatory.
- For internal HTTPS servers with self-signed certificates, the CLI already disables TLS verification by default and warns only during `init`.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for the full command catalog.
