# Polygon Agent CLI Reference

Entry point:

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py <command> ...
```

All commands print JSON to `stdout`.

## Commands

### Init

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
  --save-to "./logo.png"
```

### Upload

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py upload \
  --problem "alice/aplusb" \
  --workspace-path "solutions/brute.py" \
  --local-file "./brute.py"
```

### Delete

```bash
python skills/polygon-agent-cli/scripts/polygon_agent.py delete \
  --problem "alice/aplusb" \
  --workspace-path "solutions/brute.py"
```

### Verify Start

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
  --save-to "./verification.yaml"
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
  --output "./aplusb.zip"
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
- `export-download` always requires `--output`.
- Stateful commands use `--state-file` if provided; otherwise they use the default per-user state path.
