---
name: polygon-agent-fetch
description: "Read workspace files from a Polygon problem through the agent token workflow. Use when operating Polygon through /agent/v1/workspace/* read endpoints with a bearer token."
---

# Polygon Agent -- Fetch

## When to Use This Skill

Use this skill when:
- you need workspace status
- you need to enumerate files
- you need to read one file from a problem workspace

Use `polygon-agent-pull` instead when you need a full local clone or pull of the remote workspace.

## Required Token Scope

**`readonly`** or higher.

## Primary Path

### Workspace status

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py workspace-status \
  --problem "alice/aplusb"
```

### List files

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py list-files \
  --problem "alice/aplusb" \
  --path "solutions"
```

### Read a file inline

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py read-file \
  --problem "alice/aplusb" \
  --path "solutions/main.cpp"
```

### Save a file locally

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py read-file \
  --problem "alice/aplusb" \
  --path "attachments/logo.png" \
  --save-to "./alice/aplusb/attachments/logo.png"
```

Use `--save-to` for binary files or large content when you do not want inline JSON content.

## Notes

- the CLI chooses the cached token from the state file by `--problem`
- file content is returned as UTF-8 text or base64, matching the server response
- if the remote path is a directory, the CLI returns an error instead of pretending it is a file
- if you mirror remote files into a local repo, use `./<owner>/<problem>/` as the repo root

## Reference

- Shared CLI commands: `skills/polygon-agent-cli/references/cli.md`
- Endpoint reference: `skills/polygon-agent-init/references/agent-api.md`
