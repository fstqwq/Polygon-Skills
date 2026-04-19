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
- state-file based for session and token persistence
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
{"ok":false,"error":{"code":"token_invalid","message":"token invalid","http_status":401}}
```

## State File

Every stateful command accepts `--state-file`.

If omitted, the CLI uses this default path:
`./.polygon-agent/state.json` under the current working directory.

## Local Repo Naming

When you need to mirror a remote problem into a local repository, use:

`./<owner>/<problem>/`

Example:

`./fstqwq/a-plus-b/`

Do not collapse the owner name away into `./a-plus-b/`. The owner-qualified path matches the remote problem slug and avoids collisions.

## Clone / Pull Rules

- `clone --problem owner/problem` mirrors into `./owner/problem/` by default.
- `clone` auto-requests access when no usable token exists. It returns `approve_url` and `required_scope:"workspace"`; show that URL to the user and rerun `clone` after approval.
- `pull` updates an existing clone and never auto-requests access.
- `push` uploads the full local mirror ZIP and applies it atomically on the server.
- both commands use local Git commits as recovery points.
- both commands preserve `.git/`, `temp/`, and `draft/`.
- agent-managed UTF-8 text files are LF-canonical; binary files are byte-preserving.

## TLS Rules

- For HTTPS endpoints, certificate verification is disabled by default.
- The CLI prints a warning to `stderr` only during `init` when insecure HTTPS is used.
- Pass `--secure` to enforce normal certificate verification.
- `--insecure` is accepted as an explicit form of the default.

## Reference

Read `skills/polygon-agent-cli/references/cli.md` for the command catalog.
