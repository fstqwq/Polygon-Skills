# Polygon Agent CLI Reference

Entry point:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py <command> ...
```

All commands print JSON to `stdout`.

TLS behavior:
- HTTPS certificate verification is disabled by default
- the CLI prints a warning to `stderr` only during `init` when it uses insecure HTTPS
- pass `--secure` to enforce normal certificate verification
- `--insecure` is accepted for explicitness, but it is already the default

## Commands

### Init

If no registration URL is available, ask the user with this exact text:

```text
Please open Polygon-Replica and click the top-right Settings -> Connected Agents -> Connect to Agent. Copy the generated Registration URL and send it here.
```

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py init \
  --register-url "http://polygon.example.com/agent/v1/register/reg-abc" \
  --agent-name "Codex"
```

Initializes or refreshes the local agent session state.

### Status

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py status
```

Checks the cached session with `/agent/v1/auth/status`.

### Connect

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py connect \
  --problem "alice/aplusb"
```

Requests problem access and returns `approve_url`.

### Poll

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py poll \
  --request-id "ar-0123456789abcdef" \
  --wait
```

Polls approval status and saves the token on the first approved response.

### Clone

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py clone \
  --problem "alice/aplusb"
```

Mirrors the full remote workspace into `./alice/aplusb/`, initializes Git, and creates an initial local commit.

Run from the workspace root that contains `./.polygon-agent/state.json`, or pass `--state-file` and `--target-dir` explicitly.

If no usable token exists, `clone` automatically requests access and returns `approval_status`, `approve_url`, and `required_scope:"workspace"`. Show the URL to the user, ask them to approve workspace access, then rerun `clone`.

Optional flags:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py clone \
  --problem "alice/aplusb" \
  --target-dir "./work/alice/aplusb"
```

`clone` downloads `/agent/v1/workspace/snapshot`. It does not use package export.

### Pull

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py pull \
  --problem "alice/aplusb"
```

Updates an existing clone at `./alice/aplusb/`.

Run from the same workspace root used for `clone`, or pass `--state-file` and `--target-dir` explicitly.

`pull` does not auto-connect. If the token is missing, invalid, or insufficient, run `clone` again or use explicit `connect` / `poll`.

Before applying remote changes, `pull` commits local dirty state. After applying remote changes, it commits the synchronized mirror if anything changed.

### Push

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py push \
  --problem "alice/aplusb"
```

Uploads the full local mirror as one ZIP, asks the server to compare it, then atomically applies it to the remote working tree.

`push` requires `workspace` scope or higher. It does not commit the remote workspace; run `commit` only after the user asks for it.

### Workspace Status

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py workspace-status \
  --problem "alice/aplusb"
```

### List Files

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py list-files \
  --problem "alice/aplusb" \
  --path "solutions"
```

### Read File

Inline content:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py read-file \
  --problem "alice/aplusb" \
  --path "solutions/main.cpp"
```

Save to disk:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py read-file \
  --problem "alice/aplusb" \
  --path "attachments/logo.png" \
  --save-to "./alice/aplusb/temp/logo.png"
```

### Upload

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

### Verify Start

From a local mirror, run `push` first so verification captures the intended remote workspace version:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py push \
  --problem "alice/aplusb"
```

Then start verification:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-start \
  --problem "alice/aplusb"
```

### Verify Wait

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-wait \
  --problem "alice/aplusb" \
  --verification-id "ver-0123456789ab"
```

### Verify Detail

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py verify-detail \
  --problem "alice/aplusb" \
  --verification-id "ver-0123456789ab" \
  --save-to "./alice/aplusb/temp/verification.yaml"
```

### Export Start

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-start \
  --problem "alice/aplusb" \
  --export-type "native"
```

### Export Wait

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-wait \
  --problem "alice/aplusb" \
  --export-id "exp-api-abc123"
```

### Export Download

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py export-download \
  --problem "alice/aplusb" \
  --export-id "exp-api-abc123" \
  --output "./alice/aplusb/temp/aplusb.zip"
```

### Commit

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py commit \
  --problem "alice/aplusb" \
  --message "add brute force solution"
```

Or:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py commit \
  --problem "alice/aplusb" \
  --message-file "./commit-message.txt"
```

### Commit Status

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py commit-status \
  --problem "alice/aplusb" \
  --ref "abc123def456"
```

## Exit Codes

- `0`: success
- `1`: operational failure
- `2`: usage failure

## Notes

- The CLI never approves browser requests on its own.
- The CLI never requires inline JSON bodies.
- `clone` auto-requests access when needed, but the user must still approve the browser request.
- `pull` never auto-requests access.
- `clone` and `pull` manage local Git commits as recovery boundaries.
- `push` sends one full ZIP and uses server-side atomic apply.
- Agent-managed UTF-8 text files are LF-canonical; binary files are preserved byte-for-byte.
- `export-download` always requires `--output`.
- Save one-off downloads, verification details, and exported ZIPs under the problem repo's `temp/` unless the file is intentionally becoming tracked workspace content.
- Stateful commands use `--state-file` if provided; otherwise they use `./.polygon-agent/state.json` under the current working directory.
- When saving a remote problem locally, use `./<owner>/<problem>/` as the default repo path.
- Keep downloaded or mirrored files under that repo root instead of flattening them into `./<problem>/`.
- For internal HTTPS servers with self-signed certificates, no extra flag is needed; pass `--secure` only when you want certificate verification enabled.
- The insecure HTTPS warning is intentionally limited to `init`, not normal follow-up commands like `status`, `connect`, or `poll`.
