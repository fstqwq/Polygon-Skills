---
name: polygon-agent-pull
description: "Clone or pull a full remote Polygon problem workspace into a local Git repo through the agent CLI."
---

# Polygon Agent -- Pull

## When to Use

Use this skill when you need a full local mirror of a remote problem or need to sync the latest remote workspace into an existing clone. Prefer this over one-file `read-file` operations.

## Clone

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py clone \
  --problem "alice/aplusb"
```

Default target directory is `./alice/aplusb/`. Run from the workspace root containing `./.polygon-agent/state.json`, or pass `--state-file` and `--target-dir` explicitly.

If `clone` returns `approval_status:"pending"`, show `approve_url` to the user, ask them to approve workspace access, then rerun the same command. `clone` initializes Git and creates an initial mirror commit.

## Pull

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py pull \
  --problem "alice/aplusb"
```

`pull` updates an existing clone. It does not auto-request access; if auth is missing, expired, or too weak, use `polygon-agent-auth` or rerun `clone`.

Before applying remote changes, `pull` commits local dirty state. After applying remote changes, it commits the synchronized mirror if anything changed.

## Rules

- `clone` auto-requests workspace access; `pull` does not.
- The CLI never approves browser requests by itself.
- Preserve the owner-qualified path: `./alice/aplusb/`, not `./aplusb/`.
- Clone and pull preserve `.git/`, `temp/`, and `draft/`.
- Agent-managed UTF-8 text files are LF-canonical; binary files are byte-preserving.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for flags and one-file inspection commands.
