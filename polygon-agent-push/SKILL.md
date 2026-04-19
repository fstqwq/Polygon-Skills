---
name: polygon-agent-push
description: "Push a local Polygon problem mirror to the remote workspace through the agent token workflow. Use when applying local clone changes via /agent/v1/workspace/apply."
---

# Polygon Agent -- Push

## When to Use This Skill

Use this skill when:
- you have a local clone created by `polygon-agent-sync`
- you need to apply local file additions, edits, and deletions to the remote workspace
- you want one atomic remote workspace update

## Required Token Scope

**`workspace`** or higher.

If you only have `readonly`, request a higher-scope token through `polygon-agent-connect`.

## Primary Path

### Push Full Local Mirror

Run this from the workspace root that contains `./.polygon-agent/state.json`:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py push \
  --problem "alice/aplusb"
```

If your current directory is already inside the problem repo, pass both paths explicitly:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py push \
  --problem "alice/aplusb" \
  --state-file "../.polygon-agent/state.json" \
  --target-dir "."
```

`push` sends one full ZIP, the server compares it with the remote working tree, then applies it atomically.

### Single-File Convenience

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py upload \
  --problem "alice/aplusb" \
  --workspace-path "solutions/brute.py" \
  --local-file "./alice/aplusb/solutions/brute.py"
```

### Delete

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py delete \
  --problem "alice/aplusb" \
  --workspace-path "solutions/brute.py"
```

## Typical Workflow

1. fetch or inspect current workspace state
2. edit the local mirror
3. run `push`
4. run verification with `polygon-agent-verification`
5. commit only after the user explicitly asks for it

## Notes

- `push` ignores `.git/`, `temp/`, `draft/`, hidden paths, and invalid workspace roots
- UTF-8 text files are LF-normalized before upload
- push modifies only the workspace working tree
- push does not trigger verification automatically

## Reference

- Shared CLI commands: `skills/polygon-agent-cli/references/cli.md`
- Endpoint reference: `skills/polygon-agent-init/references/agent-api.md`
