---
name: polygon-agent-sync
description: "Clone or pull a full remote Polygon problem workspace into a local Git repo through the agent CLI."
---

# Polygon Agent -- Sync

## When to Use This Skill

Use this skill when:
- you need a full local mirror of a remote problem
- you need to pull the latest remote workspace into an existing local clone
- one-file `read-file` / `upload` operations are too slow or too fragile

## Required Token Scope

Pulling a mirror only needs `readonly`, but `clone` asks the user to approve `workspace` scope by default so the resulting workflow can push edits later without a second approval.

## Primary Path

### Clone

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py clone \
  --problem "alice/aplusb"
```

Default target directory:

```text
./alice/aplusb/
```

Run this from the workspace root that contains `./.polygon-agent/state.json`. If your current directory is already inside the problem repo, pass both `--state-file` and `--target-dir` explicitly.

If the command returns `approval_status:"pending"`, read `approve_url` from the JSON, show it to the user, and ask them to approve **workspace** scope. Then rerun the same `clone` command.

`clone` initializes Git and creates an initial mirror commit.

### Pull

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py pull \
  --problem "alice/aplusb"
```

`pull` updates an existing clone. It does not auto-connect; if auth is missing or invalid, run `clone` again or use `polygon-agent-connect`.

Before applying remote changes, `pull` commits local dirty state. After applying remote changes, it commits the synchronized mirror if anything changed.

Run `pull` from the same workspace root used for `clone`, or provide explicit paths:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py pull \
  --problem "alice/aplusb" \
  --state-file "./.polygon-agent/state.json" \
  --target-dir "./alice/aplusb"
```

## Options

Use an explicit target directory only when the default owner-qualified path is not suitable:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py clone \
  --problem "alice/aplusb" \
  --target-dir "./work/alice/aplusb"
```

Sync always uses `/agent/v1/workspace/snapshot`. Native export is only for package export, not workspace sync.

## Rules

- `clone` auto-requests access; `pull` does not.
- The CLI never approves browser requests by itself.
- The user must approve workspace scope when `clone` returns an approval URL.
- Both commands preserve `.git/`, `temp/`, and `draft/`.
- UTF-8 text files are written with LF newlines locally.
- All other files are remote-owned after sync.
- Do not flatten remote problems into `./aplusb/`; use `./alice/aplusb/`.

## Reference

- Shared CLI commands: `skills/polygon-agent-cli/references/cli.md`
- State schema: `skills/polygon-agent-init/references/state-schema.md`
