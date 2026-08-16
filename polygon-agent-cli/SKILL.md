---
name: polygon-agent-cli
description: "Shared CLI for Polygon agent workflows. Use when any polygon-agent-* skill needs to execute a real /agent/v1/* operation through a stable cross-platform script."
user-invocable: false
---

# Polygon Agent -- Shared CLI

## Purpose

This skill provides the shared command-line entrypoint used by:
- `polygon-agent-auth`
- `polygon-agent-pull`
- `polygon-agent-push`
- `polygon-agent-verification`
- `polygon-agent-export`
- `polygon-agent-commit`

It also creates canonical empty remote problems before those per-problem
workflows begin.

Use the CLI instead of writing ad hoc Python, curl, or shell code for `/agent/v1/*`.
For full local mirrors, prefer `clone` and `pull` over one-file-at-a-time reads.

## Entry Point

Run:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py <command> ...
```

The CLI is:
- cross-platform for Windows and Linux
- JSON-only on `stdout`
- flag-based for input
- state-file based for connected identity persistence
- insecure by default for HTTPS, with warnings on `stderr` during `init`

## Input Rules

- Do not pass JSON bodies on the command line.
- Use plain flags such as `--problem`, `--request-id`, `--workspace-path`, `--local-file`, and `--message`.
- Use `--message-file` for quote-sensitive commit messages.
- Use `--save-to` or `--output` for large or binary payloads.
- Save one-off downloads, diagnostics, and exported artifacts under the problem repo's `temp/` unless the file is intentionally becoming tracked workspace content.

## Output Rules

Every command prints exactly one JSON object to `stdout`.

Success:

```json
{"ok":true,"result":{...}}
```

Failure:

```json
{"ok":false,"error":{"code":"agent_credential_invalid","message":"agent credential is invalid","http_status":401}}
```

## State File

Every stateful command accepts `--state-file`.

If omitted, the CLI uses this default path:
`./.polygon-agent/state.json` under the current working directory.

The state file contains a `polygon_agent_...` bearer credential and must be
kept private. Running `init` again with a new registration URL rotates that
credential while preserving grants attached to the existing session.
State from the former identity-header protocol has no credential and starts a
new session instead; old sessions and grants are not migrated.

## Local Repo Naming

When you need to mirror a remote problem into a local repository, use:

`./<owner>/<problem>/`

Example:

`./fstqwq/a-plus-b/`

Do not collapse the owner name away into `./a-plus-b/`. The owner-qualified path matches the remote problem slug and avoids collisions.

## Clone / Pull Rules

- `clone --problem owner/problem` mirrors into `./owner/problem/` by default.
- Problem commands use the connected identity directly. When a per-problem
  grant is needed, they return `approve_url` and `required_scope`; show the URL
  to the user and rerun the command after approval.
- `pull` updates an existing clone through the same identity and grant rules.
- `push` uploads the full local mirror ZIP and applies it atomically on the server.
- both commands use local Git commits as recovery points.
- both commands preserve `.git/`, `temp/`, and `draft/`.
- agent-managed UTF-8 text files are LF-canonical; binary files are byte-preserving.

## Polygon Agent Pull Contest Rules

- `pull-contest --contest <slug>` requires general `readonly` permission.
- It creates one independent Git repository per server label under `A/`, `B/`,
  `C/`, and so on; the CLI does not renumber labels.
- It downloads every snapshot to temporary staging before changing the target.
- A removed or relabelled problem, occupied path, mismatched Git config,
  duplicate mapping, or case collision returns `contest_layout_conflict`.
- Never move, rename, or delete conflicting directories without showing the
  structured conflicts and receiving explicit user confirmation.
- No Contest root manifest is created. Each child repository remains usable by
  ordinary `pull` and `push` through its `polygon-agent.problem` Git config.

## TLS Rules

- For HTTPS endpoints, certificate verification is disabled by default.
- The CLI prints a warning to `stderr` only during `init` when insecure HTTPS is used.
- Pass `--secure` to enforce normal certificate verification.
- `--insecure` is accepted as an explicit form of the default.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for the command catalog.
