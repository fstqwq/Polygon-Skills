---
name: polygon-agent-pull
description: "Clone or pull a full remote Polygon problem workspace into a local Git repo through the agent CLI."
---

# Polygon Agent -- Pull

## When to Use

Use this skill when you need a full local mirror of one remote problem, need to
sync an existing clone, or need to pull an entire Contest into label-named
independent repositories. Prefer this over one-file `read-file` operations.

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

`pull` updates an existing clone. If it returns an approval URL, show that URL
to the user and rerun the command after approval.

Before applying remote changes, `pull` commits local dirty state. After applying remote changes, it commits the synchronized mirror if anything changed.

## Pull Contest

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py pull-contest \
  --contest "summer-2026" \
  --target-dir "./summer-2026"
```

This requires general `readonly` permission in Connected Agents. It creates
independent repositories such as `A/`, `B/`, and `C/` using the labels returned
by the server. Each repository stores its canonical Problem and Contest mapping
in local Git config and continues to work with ordinary single-problem pull and
push.

The command performs a complete local layout preflight and downloads every
remote snapshot to staging before changing the target directory. If it returns
`contest_layout_conflict`, explain every structured conflict and the expected
directory layout to the user. Do not move, rename, or delete a local directory
until the user explicitly confirms the desired resolution. After resolving the
layout, rerun `pull-contest` so it obtains a fresh roster. The CLI never creates
a Contest root manifest.

## Rules

- Problem operations request the required grant when the connected identity's
  effective scope is insufficient.
- The CLI never approves browser requests by itself.
- Preserve the owner-qualified path: `./alice/aplusb/`, not `./aplusb/`.
- Clone and pull preserve `.git/`, `temp/`, and `draft/`.
- Agent-managed UTF-8 text files are LF-canonical; binary files are byte-preserving.
- Never infer Contest labels or silently reconcile removed/relabelled entries.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for flags and one-file inspection commands.
