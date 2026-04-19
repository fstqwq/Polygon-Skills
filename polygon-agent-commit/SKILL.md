---
name: polygon-agent-commit
description: "Commit and publish Polygon workspace changes through the agent CLI. HIGH RISK -- use only after explicit user approval."
---

# Polygon Agent -- Commit

## When to Use

Use this skill only when the user explicitly asks to commit/publish remote workspace changes.

Requires `commit` scope. If the cached token has lower scope, use `polygon-agent-auth` to request a commit token.

## Mandatory Approval

Before running commit, show the user:
- what will be committed
- the proposed commit message
- current verification status, if available

Run the command only after explicit affirmative approval. Do not commit as a side effect of push, verification, or export.

## Commit

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py commit \
  --problem "alice/aplusb" \
  --message "add brute force solution"
```

Use `--message-file` for quote-sensitive or multi-line messages.

Check publish status:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py commit-status \
  --problem "alice/aplusb" \
  --ref "abc123def456"
```

## Rules

- The server-side endpoint handles add, commit, push, and rollback on push failure.
- If there are no changes, the endpoint may succeed without creating a new commit.
- Approval discipline stays in this skill; the CLI only invokes the endpoint.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for message-file usage.
