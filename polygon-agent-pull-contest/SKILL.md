---
name: polygon-agent-pull-contest
description: "Pull every problem in a remote Polygon Contest into label-named independent local Git repositories through the Polygon Agent CLI. Use when the user asks to pull, clone, download, or synchronize a whole Contest rather than one problem."
---

# Polygon Agent -- Pull Contest

Run from the workspace containing `.polygon-agent/state.json`, or pass an
explicit `--state-file`:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py pull-contest \
  --contest "summer-2026" \
  --target-dir "./summer-2026"
```

The connected Agent requires general `readonly` permission and the user must
have current read access to the Contest. Show permission errors to the user;
never approve or broaden access from the CLI.

The command obtains one roster generation, downloads every problem snapshot to
temporary staging, and only then changes the target directory. It creates one
independent Git repository per server-supplied label:

```text
summer-2026/
|-- A/
|-- B/
`-- C/
```

Each repository records its Problem and Contest mapping in local Git config and
continues to use the ordinary single-problem pull and push commands. The
Contest root has no manifest.

If the command returns `contest_layout_conflict`, report every structured
conflict and its expected path. Do not move, rename, overwrite, or delete local
directories without explicit user confirmation. After resolution, rerun the
whole command so it fetches a fresh roster generation.

If any snapshot download fails or the roster changes, do not partially apply
the Contest. Preserve existing local repositories and rerun after addressing
the reported error.

For command flags and response shapes, read
`../polygon-agent-cli/references/cli.md`.
