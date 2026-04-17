---
name: polygon-agent-commit
description: "Commit and publish workspace changes through the Polygon Agent token workflow. Use when committing via /agent/v1/commit with a bearer token. HIGH RISK -- requires explicit user approval."
---

# Polygon Agent -- Commit

## When to Use This Skill

Use this skill when:
- the user explicitly asked you to commit and publish
- verification is already in a good state
- you already hold a `commit` scope token

## Required Token Scope

**`commit`**

If you only have `readonly` or `workspace`, request a new token through `polygon-agent-connect`.

## Mandatory Human Approval

Before running the commit command, you MUST:

1. show the user what will be committed
2. show the proposed commit message
3. get explicit affirmative text approval
4. only then run the command

You must not auto-commit as a side effect of another workflow.

## Primary Path

### Commit with inline message

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py commit \
  --problem "alice/aplusb" \
  --message "add brute force solution"
```

### Commit with message file

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py commit \
  --problem "alice/aplusb" \
  --message-file "./commit-message.txt"
```

The CLI requires exactly one of `--message` or `--message-file`.

### Check publish status

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py commit-status \
  --problem "alice/aplusb" \
  --ref "abc123def456"
```

## Notes

- the server-side commit endpoint handles add, commit, push, and rollback on push failure
- if there are no changes, the endpoint may still succeed without creating a new commit
- the CLI only invokes the endpoint; approval discipline stays in this skill

## Reference

- Shared CLI commands: `skills/polygon-agent-cli/references/cli.md`
- Endpoint reference: `skills/polygon-agent-init/references/agent-api.md`
