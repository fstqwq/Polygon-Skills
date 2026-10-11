---
name: polygon-agent-push
description: "Push a local Polygon problem mirror to the remote workspace through the agent CLI. Use when applying local clone changes atomically."
---

# Polygon Agent -- Push

## When to Use

Use this skill when a local mirror created by `polygon-agent-pull` should replace the remote workspace working tree.

Requires effective `workspace` scope or higher. If the identity has only
readonly access, use `polygon-agent-auth` to request a workspace grant or ask
the user to adjust general permission.

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

`push` sends the same full ZIP to compare and then apply; apply changes the workspace atomically.

## Interrupted Push

The CLI exits on failure without retries, backoff, or automatic file uploads.
Use its `stage`, `remote_outcome`, and `recovery` fields to decide the next step.
An interrupted apply may already have succeeded: inspect the remote state first.
`preflight_diff`, when present, describes the state before apply, not remaining work.

For transport failures, you may use existing `upload` and `delete` commands to
finish confirmed changes from the local track. Compare with current remote files;
local track does not prove the remote workspace is unchanged. Do not delete
unrelated remote files or bypass permission, version, or validation rejections.

Execute each selected operation once. If it fails, report remaining work instead
of entering a retry loop. File-by-file recovery can leave a partially updated
workspace and is not atomic. Verify contents with `list-files` and `read-file`
when needed, using LF normalization for text and exact bytes for binary files.
Matching `workspace-status` paths alone does not establish equal contents.
Report partial completion or an unconfirmed result until verified. Do not
manually update `polygon-agent.remote-head`, commit, or publish as recovery.

## Rules

- Push modifies only the remote workspace working tree.
- Push does not commit or start verification.
- Push ignores `.git/`, `temp/`, `draft/`, hidden paths, and invalid workspace roots.
- Use `polygon-agent-verification` after push when final verdicts matter.
- Use `polygon-agent-commit` only after the user explicitly asks to publish.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for upload/delete convenience commands.
