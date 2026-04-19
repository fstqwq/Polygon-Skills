---
name: polygon-agent-push
description: "Push a local Polygon problem mirror to the remote workspace through the agent CLI. Use when applying local clone changes atomically."
---

# Polygon Agent -- Push

## When to Use

Use this skill when a local mirror created by `polygon-agent-pull` should replace the remote workspace working tree.

Requires `workspace` scope or higher. If the cached token is `readonly`, use `polygon-agent-auth` to request a higher-scope token.

## Push Full Local Mirror

Run from the workspace root containing `./.polygon-agent/state.json`:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py push \
  --problem "alice/aplusb"
```

If the current directory is already inside the problem repo, pass paths explicitly:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py push \
  --problem "alice/aplusb" \
  --state-file "../.polygon-agent/state.json" \
  --target-dir "."
```

`push` uploads one full ZIP, asks the server to compare it, then applies it atomically.

## Rules

- Push modifies only the remote workspace working tree.
- Push does not commit or start verification.
- Push ignores `.git/`, `temp/`, `draft/`, hidden paths, and invalid workspace roots.
- Use `polygon-agent-verification` after push when final verdicts matter.
- Use `polygon-agent-commit` only after the user explicitly asks to publish.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for upload/delete convenience commands.
