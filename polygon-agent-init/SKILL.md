---
name: polygon-agent-init
description: "Initialize a Polygon agent identity and register it with the server. Use when the task is specifically about starting the /agent/v1/* token workflow and obtaining an agent session."
---

# Polygon Agent -- Init

## When to Use This Skill

Use this skill when:
- the user provides a registration URL containing `/agent/v1/register/`
- you need to initialize a new local agent session state
- you do not yet have a usable `agent_session_id` / `identity_hash`

Do NOT use this skill for:
- requesting a problem token after the session already exists
- workspace read/write operations
- export, verification, or commit operations

## Primary Path

Use the shared CLI:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py init \
  --register-url "http://polygon.example.com/agent/v1/register/reg-a8f3c2e1b9d04567" \
  --agent-name "Codex"
```

The command prints JSON to `stdout` and persists the session state.

If you want to store the state somewhere explicit, add:

```bash
--state-file "/path/to/polygon-agent-state.json"
```

## Identity Rules

- `agent_name` should be the product or agent implementation name
- good examples: `Codex`, `Claude Code`, `OpenCode`
- do not use a repo name or task name
- if you do not pass `--desktop-id`, the CLI chooses a stable local hostname-style default
- if you do not pass `--init-ts`, the CLI creates one and persists it with the state

## Session Check

Once initialized, reuse the same state file and check it with:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py status
```

Or:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py status \
  --state-file "/path/to/polygon-agent-state.json"
```

## Result

At the end of this skill you should have cached:
- `base_url`
- `agent_session_id`
- `identity_hash`
- `identity`
- `user`
- `server_name`

Use `polygon-agent-connect` after this to request access to a specific problem token.

## Notes

- the registration URL is one-time use
- if the code is expired or already consumed, ask the user to generate a fresh registration URL in the Web UI
- the CLI is the primary path; raw HTTP docs remain only as reference
- for local or internal HTTPS servers with self-signed certificates, the CLI already skips certificate verification by default and prints a warning to `stderr`
- pass `--secure` only when you want normal TLS verification enabled

## Reference

- Shared CLI commands: `skills/polygon-agent-cli/references/cli.md`
- State schema: `skills/polygon-agent-init/references/state-schema.md`
- Endpoint reference: `skills/polygon-agent-init/references/agent-api.md`
- Raw HTTP examples: `skills/polygon-agent-init/references/http-examples.md`
