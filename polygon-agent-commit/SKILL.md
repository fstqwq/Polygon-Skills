---
name: polygon-agent-commit
description: "Commit and publish workspace changes through the Polygon Agent token workflow. Use when committing via /agent/v1/commit with a bearer token. HIGH RISK -- requires explicit user approval."
---

# Polygon Agent -- Commit

## When to Use This Skill

Use this skill when:
- You need to commit and publish workspace changes via the agent API
- The user has explicitly asked you to commit

Do NOT use this skill for:
- Committing through the web UI or git CLI
- Uploading files (use `polygon-agent-push`)
- Any operation that doesn't involve the `/agent/v1/commit` endpoint

## Required Token Scope

**`commit`**

This is the highest scope level. If you only have `readonly` or `workspace`, commit will return 403.
Request a new token with `commit` scope using `polygon-agent-connect`.

## MANDATORY: Human Approval Before Commit

**Before executing a commit, you MUST:**

1. Show the user a summary of what will be committed (list changed files, describe the changes)
2. Show the proposed commit message
3. Ask for explicit text confirmation (e.g., "yes", "go ahead", "commit it")
4. Only proceed after receiving clear affirmative text from the user

**You MUST NOT:**
- Commit without showing the user what will be committed
- Commit without explicit user approval
- Auto-commit as part of another workflow without asking

## Endpoints

All requests require `Authorization: Bearer <token>`.

### Commit

```
POST {base_url}/agent/v1/commit
Content-Type: application/json

{"message": "add brute force solution"}
```

Response:
```json
{"status": "ok", "head": "abc123def456..."}
```

The commit message is required. Empty messages return 400.

### Behavior

The commit endpoint does three things atomically:
1. `git add -A && git commit -m "<message>"`
2. `git push origin main`
3. If push fails, the commit is rolled back

If there are no changes to commit, the response is still 200 (the command succeeds with no new commit).

### Check commit status

```
GET {base_url}/agent/v1/commit/{ref}/status
```

Response:
```json
{
  "ref": "abc123def456...",
  "status": "published",
  "head": "abc123def456...",
  "remote_head": "abc123def456..."
}
```

Status values:
- `published` -- the ref is both the local HEAD and remote HEAD
- `local` -- the ref is the local HEAD but not pushed
- `missing` -- the ref is not the current HEAD

## Typical Workflow

1. **Push** changes with `polygon-agent-push`
2. **Verify** with `polygon-agent-verification`
3. Review results and confirm everything is correct
4. **Show the user** what will be committed
5. **Get user approval**
6. **Commit**: `POST /agent/v1/commit`
7. Confirm publish: `GET /agent/v1/commit/{head}/status`

## Reference

For full endpoint details, read `skills/polygon-agent-init/references/agent-api.md`.
For curl examples, read `skills/polygon-agent-init/references/http-examples.md`.
