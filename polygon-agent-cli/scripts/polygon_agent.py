#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Sequence
from urllib.parse import quote, urlencode, urlparse
from uuid import uuid4


JsonObject = dict[str, Any]
DEFAULT_HTTP_TIMEOUT_SEC = 30.0
DEFAULT_WAIT_INTERVAL_SEC = 3.0
DEFAULT_CLONE_SCOPE = "workspace"
PRESERVED_REPO_DIRS = {".git", "draft", "temp"}
ALLOWED_WORKSPACE_ROOT_NAMES = {
    "attachments",
    "checkers",
    "config",
    "generators",
    "interactors",
    "solutions",
    "statement",
    "statement-assets",
    "statement-sections",
    "tests",
    "third_party",
    "validators",
}
_INSECURE_WARNING_EMITTED: set[str] = set()


class CliError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        exit_code: int = 1,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.http_status = http_status


class UsageError(CliError):
    def __init__(self, message: str) -> None:
        super().__init__(code="usage_error", message=message, exit_code=2)


def _write_success(result: JsonObject) -> None:
    sys.stdout.write(json.dumps({"ok": True, "result": result}, ensure_ascii=False, separators=(",", ":")) + "\n")


def _write_error(error: CliError) -> None:
    payload: JsonObject = {
        "ok": False,
        "error": {
            "code": error.code,
            "message": error.message,
        },
    }
    if error.http_status is not None:
        payload["error"]["http_status"] = error.http_status
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def _without_none(payload: JsonObject) -> JsonObject:
    return {key: value for key, value in payload.items() if value is not None}


def _default_state_file() -> Path:
    return Path.cwd() / ".polygon-agent" / "state.json"


def _resolve_state_file(raw: str | None) -> Path:
    if raw:
        return Path(raw).expanduser().resolve()
    return _default_state_file().resolve()


def _load_json_file(path: Path) -> JsonObject:
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise CliError(code="bad_state", message=f"state file not found: {path}") from exc
    except OSError as exc:
        raise CliError(code="bad_state", message=f"cannot read state file: {path}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CliError(code="bad_state", message=f"state file is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise CliError(code="bad_state", message=f"state file must contain a JSON object: {path}")
    return data


def _load_json_file_if_exists(path: Path) -> JsonObject:
    if not path.exists():
        return {}
    return _load_json_file(path)


def _normalize_text_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _normalize_text_bytes(content: bytes) -> bytes:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return content
    return _normalize_text_newlines(text).encode("utf-8")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(_normalize_text_newlines(content))
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def _save_state(path: Path, state: JsonObject) -> None:
    _atomic_write_text(path, json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _normalize_base_url(raw: str) -> str:
    value = str(raw or "").strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise UsageError(f"invalid base URL: {raw}")
    return f"{parsed.scheme}://{parsed.netloc}"


def _base_url_from_register_url(raw: str) -> str:
    value = str(raw or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise UsageError(f"invalid registration URL: {raw}")
    if "/agent/v1/register/" not in parsed.path:
        raise UsageError("registration URL must contain /agent/v1/register/")
    return f"{parsed.scheme}://{parsed.netloc}"


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _default_desktop_id() -> str:
    if os.name == "nt":
        token = str(os.environ.get("COMPUTERNAME") or "").strip()
        if token:
            return token
    token = socket.gethostname().strip()
    if token:
        return token
    return f"host-{uuid4()}"


def _state_string(state: JsonObject, key: str) -> str:
    value = state.get(key)
    if isinstance(value, str) and value.strip():
        return value
    raise CliError(code="bad_state", message=f"state file is missing {key}")


def _state_identity_defaults(state: JsonObject) -> JsonObject:
    identity = state.get("identity")
    if isinstance(identity, dict):
        return identity
    return {}


def _state_tokens(state: JsonObject) -> JsonObject:
    tokens = state.get("tokens")
    if isinstance(tokens, dict):
        return tokens
    tokens = {}
    state["tokens"] = tokens
    return tokens


def _state_pending_access(state: JsonObject) -> JsonObject:
    pending_access = state.get("pending_access")
    if isinstance(pending_access, dict):
        return pending_access
    pending_access = {}
    state["pending_access"] = pending_access
    return pending_access


def _token_entry(state: JsonObject, problem: str) -> JsonObject:
    entry = _state_tokens(state).get(problem)
    if isinstance(entry, dict):
        return entry
    raise CliError(code="missing_token", message=f"no cached token for problem {problem}")


def _token_for_problem(state: JsonObject, problem: str) -> str:
    entry = _token_entry(state, problem)
    token = entry.get("token")
    if isinstance(token, str) and token:
        return token
    raise CliError(code="missing_token", message=f"no cached token for problem {problem}")


def _scope_rank(scope: str) -> int:
    return {"readonly": 1, "workspace": 2, "commit": 3}.get(scope, 0)


def _token_scope_satisfies(entry: JsonObject, required_scope: str) -> bool:
    scope = entry.get("scope")
    if not isinstance(scope, str) or not scope:
        return True
    return _scope_rank(scope) >= _scope_rank(required_scope)


def _invalidate_problem_token(path: Path, state: JsonObject, problem: str) -> None:
    tokens = _state_tokens(state)
    if problem in tokens:
        del tokens[problem]
        _save_state(path, state)


def _http_code_name(status: int) -> str:
    if status == 401:
        return "token_invalid"
    if status == 403:
        return "scope_insufficient"
    if status == 404:
        return "not_found"
    if status == 409:
        return "operation_conflict"
    if status == 410:
        return "registration_code_invalid"
    return "api_error"


def _api_error_from_response(status: int, body: bytes) -> CliError:
    message = f"http {status}"
    if body:
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = None
        if isinstance(payload, dict):
            error_text = payload.get("error")
            if isinstance(error_text, str) and error_text.strip():
                message = error_text.strip()
    return CliError(code=_http_code_name(status), message=message, http_status=status)


def _tls_context(*, url: str, verify_tls: bool, warn_insecure: bool = False) -> ssl.SSLContext | None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return None
    if verify_tls:
        return ssl.create_default_context()
    if warn_insecure:
        host = parsed.netloc or parsed.path or url
        if host not in _INSECURE_WARNING_EMITTED:
            print(
                f"warning: TLS certificate verification is disabled by default for https://{host}; pass --secure to enforce verification",
                file=sys.stderr,
            )
            _INSECURE_WARNING_EMITTED.add(host)
    return ssl._create_unverified_context()


def _http_request(
    *,
    url: str,
    method: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout_sec: float = DEFAULT_HTTP_TIMEOUT_SEC,
    verify_tls: bool = False,
    warn_insecure: bool = False,
) -> tuple[int, bytes, dict[str, str]]:
    request = urllib.request.Request(url=url, method=method, headers=headers or {}, data=body)
    try:
        context = _tls_context(url=url, verify_tls=verify_tls, warn_insecure=warn_insecure)
        with urllib.request.urlopen(request, timeout=timeout_sec, context=context) as response:
            return (int(response.getcode()), response.read(), dict(response.headers.items()))
    except urllib.error.HTTPError as exc:
        raise _api_error_from_response(exc.code, exc.read()) from exc
    except urllib.error.URLError as exc:
        raise CliError(code="network_error", message=f"network error: {exc.reason}") from exc


def _http_json(
    *,
    url: str,
    method: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    verify_tls: bool = False,
    warn_insecure: bool = False,
) -> JsonObject:
    _status, payload, _headers = _http_request(
        url=url,
        method=method,
        headers=headers,
        body=body,
        verify_tls=verify_tls,
        warn_insecure=warn_insecure,
    )
    try:
        data = json.loads(payload.decode("utf-8")) if payload else {}
    except json.JSONDecodeError as exc:
        raise CliError(code="bad_response", message="server returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise CliError(code="bad_response", message="server returned a non-object JSON payload")
    return data


def _http_text(
    *,
    url: str,
    method: str,
    headers: dict[str, str] | None = None,
    verify_tls: bool = False,
    warn_insecure: bool = False,
) -> str:
    _status, payload, _headers = _http_request(
        url=url,
        method=method,
        headers=headers,
        verify_tls=verify_tls,
        warn_insecure=warn_insecure,
    )
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CliError(code="bad_response", message="server returned non-utf8 text") from exc


def _http_binary(
    *,
    url: str,
    method: str,
    headers: dict[str, str] | None = None,
    verify_tls: bool = False,
    warn_insecure: bool = False,
) -> bytes:
    _status, payload, _headers = _http_request(
        url=url,
        method=method,
        headers=headers,
        verify_tls=verify_tls,
        warn_insecure=warn_insecure,
    )
    return payload


def _json_body(payload: JsonObject) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _auth_headers(token: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if extra:
        headers.update(extra)
    return headers


def _multipart_upload_body(*, fields: dict[str, str], file_field_name: str, file_name: str, file_bytes: bytes) -> tuple[bytes, str]:
    boundary = f"polygon-agent-{uuid4().hex}"
    parts: list[bytes] = []
    for key, value in fields.items():
        parts.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    parts.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="{file_field_name}"; filename="{file_name}"\r\n'.encode("utf-8"),
            b"Content-Type: application/octet-stream\r\n\r\n",
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return (b"".join(parts), f"multipart/form-data; boundary={boundary}")


def _state_file_result(path: Path) -> str:
    return str(path)


def _problem_url(base_url: str, path: str) -> str:
    return f"{base_url}{path}"


def _command_init(args: argparse.Namespace) -> JsonObject:
    state_path = _resolve_state_file(args.state_file)
    existing_state = _load_json_file_if_exists(state_path)
    identity_defaults = _state_identity_defaults(existing_state)
    agent_name = str(args.agent_name or identity_defaults.get("agent_name") or "").strip()
    if not agent_name:
        raise UsageError("--agent-name is required when the state file has no cached identity")
    desktop_id = str(args.desktop_id or identity_defaults.get("desktop_id") or _default_desktop_id()).strip()
    init_ts = str(args.init_ts or identity_defaults.get("init_ts") or _utc_now_iso()).strip()
    register_url = str(args.register_url or "").strip()
    base_url = _base_url_from_register_url(register_url)
    response = _http_json(
        url=register_url,
        method="POST",
        headers={"Content-Type": "application/json"},
        body=_json_body(
            {
                "agent_name": agent_name,
                "desktop_id": desktop_id,
                "init_ts": init_ts,
            }
        ),
        verify_tls=bool(args.secure),
        warn_insecure=(not bool(args.secure)),
    )
    agent_session_id = str(response.get("agent_session_id") or "")
    identity_hash = str(response.get("identity_hash") or "")
    user = str(response.get("user") or "")
    server_name = str(response.get("server_name") or "")
    if not agent_session_id or not identity_hash or not user or not server_name:
        raise CliError(code="bad_response", message="registration response is missing required fields")
    tokens = _state_tokens(existing_state)
    state: JsonObject = {
        "base_url": base_url,
        "agent_session_id": agent_session_id,
        "identity_hash": identity_hash,
        "identity": {
            "agent_name": agent_name,
            "desktop_id": desktop_id,
            "init_ts": init_ts,
        },
        "user": user,
        "server_name": server_name,
        "tokens": tokens,
    }
    _save_state(state_path, state)
    return {
        "base_url": base_url,
        "agent_session_id": agent_session_id,
        "identity_hash": identity_hash,
        "user": user,
        "server_name": server_name,
        "state_file": _state_file_result(state_path),
    }


def _command_status(args: argparse.Namespace) -> JsonObject:
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    session_id = _state_string(state, "agent_session_id")
    identity_hash = _state_string(state, "identity_hash")
    query = urlencode({"agent_session_id": session_id, "identity_hash": identity_hash})
    response = _http_json(url=f"{base_url}/agent/v1/auth/status?{query}", method="GET", verify_tls=bool(args.secure))
    return {
        "user": response.get("user"),
        "server_name": response.get("server_name"),
        "last_seen_at": response.get("last_seen_at"),
        "authorized_problems": response.get("authorized_problems", []),
    }


def _request_access(
    *,
    state_path: Path,
    state: JsonObject,
    base_url: str,
    problem: str,
    verify_tls: bool,
    required_scope: str | None = None,
) -> JsonObject:
    session_id = _state_string(state, "agent_session_id")
    identity_hash = _state_string(state, "identity_hash")
    response = _http_json(
        url=f"{base_url}/agent/v1/auth/request-access",
        method="POST",
        headers={"Content-Type": "application/json"},
        body=_json_body(
            {
                "agent_session_id": session_id,
                "identity_hash": identity_hash,
                "problem": problem,
            }
        ),
        verify_tls=verify_tls,
    )
    approve_path = str(response.get("approve_path") or "")
    request_id = str(response.get("request_id") or "")
    expires_in = response.get("expires_in")
    if not approve_path or not request_id:
        raise CliError(code="bad_response", message="connect response is missing required fields")
    result: JsonObject = {
        "request_id": request_id,
        "approve_url": f"{base_url}{approve_path}",
        "expires_in": expires_in,
        "problem": problem,
    }
    if required_scope:
        result["required_scope"] = required_scope
    pending_entry = dict(result)
    _state_pending_access(state)[problem] = pending_entry
    _save_state(state_path, state)
    return result


def _poll_access_request(
    *,
    state_path: Path,
    state: JsonObject,
    base_url: str,
    request_id: str,
    verify_tls: bool,
    wait: bool,
    interval_sec: float,
    timeout_sec: float | None,
    expected_problem: str | None = None,
) -> JsonObject:
    session_id = _state_string(state, "agent_session_id")
    identity_hash = _state_string(state, "identity_hash")
    deadline = None if timeout_sec is None else time.monotonic() + timeout_sec
    while True:
        query = urlencode({"agent_session_id": session_id, "identity_hash": identity_hash})
        response = _http_json(
            url=f"{base_url}/agent/v1/auth/poll/{request_id}?{query}",
            method="GET",
            verify_tls=verify_tls,
        )
        status = str(response.get("status") or "")
        if status == "approved":
            problem = str(response.get("problem") or expected_problem or "")
            token = response.get("token")
            expires_at = response.get("expires_at")
            token_saved = False
            if isinstance(token, str) and token:
                entry = _state_tokens(state).setdefault(problem, {})
                entry["token"] = token
                if isinstance(expires_at, str) and expires_at:
                    entry["expires_at"] = expires_at
                _state_pending_access(state).pop(problem, None)
                _save_state(state_path, state)
                token_saved = True
            else:
                if not problem:
                    raise CliError(code="approval_token_missing", message="approval succeeded but response did not include the problem slug")
                existing_entry = _state_tokens(state).get(problem)
                if not isinstance(existing_entry, dict) or not isinstance(existing_entry.get("token"), str) or not existing_entry.get("token"):
                    raise CliError(
                        code="approval_token_missing",
                        message="approval succeeded but the one-time token was not available; request access again",
                    )
            return {
                "status": status,
                "problem": problem,
                "expires_at": expires_at,
                "token_saved": token_saved,
            }
        if status in {"denied", "expired"}:
            if expected_problem:
                _state_pending_access(state).pop(expected_problem, None)
                _save_state(state_path, state)
            return {
                "status": status,
                "problem": response.get("problem") or expected_problem,
                "expires_at": response.get("expires_at"),
                "token_saved": False,
            }
        if not wait:
            return {"status": status, "problem": expected_problem}
        if deadline is not None and time.monotonic() >= deadline:
            raise CliError(code="timeout", message="approval polling timed out")
        time.sleep(interval_sec)


def _command_connect(args: argparse.Namespace) -> JsonObject:
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    problem = str(args.problem or "").strip()
    return _request_access(
        state_path=state_path,
        state=state,
        base_url=base_url,
        problem=problem,
        verify_tls=bool(args.secure),
    )


def _command_poll(args: argparse.Namespace) -> JsonObject:
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    request_id = str(args.request_id or "").strip()
    expected_problem = None
    for problem, entry in _state_pending_access(state).items():
        if isinstance(entry, dict) and entry.get("request_id") == request_id:
            expected_problem = str(problem)
            break
    return _poll_access_request(
        state_path=state_path,
        state=state,
        base_url=base_url,
        request_id=request_id,
        verify_tls=bool(args.secure),
        wait=bool(args.wait),
        interval_sec=float(args.interval_sec),
        timeout_sec=args.timeout_sec,
        expected_problem=expected_problem,
    )


def _state_and_token(args: argparse.Namespace) -> tuple[Path, JsonObject, str, str]:
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    problem = str(args.problem or "").strip()
    token = _token_for_problem(state, problem)
    return (state_path, state, base_url, token)


def _run_token_command(args: argparse.Namespace, callback: Any) -> JsonObject:
    state_path, state, base_url, token = _state_and_token(args)
    problem = str(args.problem or "").strip()
    try:
        return callback(state_path, state, base_url, problem, token)
    except CliError as exc:
        if exc.http_status == 401:
            _invalidate_problem_token(state_path, state, problem)
        raise


def _command_workspace_status(args: argparse.Namespace) -> JsonObject:
    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        response = _http_json(
            url=f"{base_url}/agent/v1/workspace/status",
            method="GET",
            headers=_auth_headers(token),
            verify_tls=bool(args.secure),
        )
        return {
            "problem": response.get("problem"),
            "workspace_id": response.get("workspace_id"),
            "head_commit": response.get("head_commit"),
            "dirty": response.get("dirty"),
            "git": response.get("git"),
        }

    return _run_token_command(args, callback)


def _command_list_files(args: argparse.Namespace) -> JsonObject:
    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        query = ""
        if args.path:
            query = "?" + urlencode({"path": str(args.path)})
        response = _http_json(
            url=f"{base_url}/agent/v1/workspace/files{query}",
            method="GET",
            headers=_auth_headers(token),
            verify_tls=bool(args.secure),
        )
        return {
            "base_path": response.get("base_path"),
            "entries": response.get("entries", []),
            "truncated": bool(response.get("truncated")),
        }

    return _run_token_command(args, callback)


def _command_read_file(args: argparse.Namespace) -> JsonObject:
    save_to = Path(str(args.save_to)).expanduser().resolve() if args.save_to else None

    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        response = _http_json(
            url=f"{base_url}/agent/v1/workspace/file?{urlencode({'path': str(args.path)})}",
            method="GET",
            headers=_auth_headers(token),
            verify_tls=bool(args.secure),
        )
        if bool(response.get("is_dir")):
            raise CliError(code="path_is_directory", message=f"path is a directory: {args.path}")
        path = response.get("path")
        encoding = response.get("encoding")
        media_type = response.get("media_type")
        size_bytes = response.get("size_bytes")
        content = response.get("content")
        if not isinstance(content, str):
            raise CliError(code="bad_response", message="workspace file response is missing content")
        result: JsonObject = {
            "path": path,
            "encoding": encoding,
            "media_type": media_type,
            "size_bytes": size_bytes,
        }
        if save_to is None:
            result["content"] = content
            return result
        if encoding == "utf-8":
            _atomic_write_text(save_to, content)
        elif encoding == "base64":
            try:
                decoded = base64.b64decode(content)
            except Exception as exc:
                raise CliError(code="bad_response", message="workspace file response contains invalid base64") from exc
            _atomic_write_bytes(save_to, decoded)
        else:
            raise CliError(code="bad_response", message=f"unsupported file encoding: {encoding}")
        result["saved_to"] = str(save_to)
        return result

    return _run_token_command(args, callback)


def _command_upload(args: argparse.Namespace) -> JsonObject:
    local_file = Path(str(args.local_file or "")).expanduser().resolve()
    if not local_file.is_file():
        raise UsageError(f"--local-file is not a file: {local_file}")
    file_bytes = local_file.read_bytes()

    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        body, content_type = _multipart_upload_body(
            fields={"path": str(args.workspace_path)},
            file_field_name="file",
            file_name=local_file.name,
            file_bytes=file_bytes,
        )
        response = _http_json(
            url=f"{base_url}/agent/v1/workspace/upload",
            method="POST",
            headers=_auth_headers(token, {"Content-Type": content_type}),
            body=body,
            verify_tls=bool(args.secure),
        )
        return {
            "path": response.get("path"),
            "bytes": response.get("bytes"),
        }

    return _run_token_command(args, callback)


def _command_delete(args: argparse.Namespace) -> JsonObject:
    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        quoted = quote(str(args.workspace_path), safe="/")
        response = _http_json(
            url=f"{base_url}/agent/v1/workspace/files/{quoted}",
            method="DELETE",
            headers=_auth_headers(token),
            verify_tls=bool(args.secure),
        )
        return {"path": response.get("path")}

    return _run_token_command(args, callback)


def _command_verify_start(args: argparse.Namespace) -> JsonObject:
    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        response = _http_json(
            url=f"{base_url}/agent/v1/verification/start",
            method="POST",
            headers=_auth_headers(token, {"Content-Type": "application/json"}),
            body=_json_body({}),
            verify_tls=bool(args.secure),
        )
        return {
            "verification_id": response.get("verification_id"),
            "status": response.get("status"),
        }

    return _run_token_command(args, callback)


def _wait_for_status(
    *,
    fetcher: Any,
    done_statuses: set[str],
    interval_sec: float,
    timeout_sec: float | None,
) -> JsonObject:
    deadline = None if timeout_sec is None else time.monotonic() + timeout_sec
    while True:
        response = fetcher()
        status = str(response.get("status") or "")
        if status in done_statuses:
            return response
        if deadline is not None and time.monotonic() >= deadline:
            raise CliError(code="timeout", message="wait operation timed out")
        time.sleep(interval_sec)


def _command_verify_wait(args: argparse.Namespace) -> JsonObject:
    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        verification_id = str(args.verification_id or "").strip()

        def fetcher() -> JsonObject:
            return _http_json(
                url=f"{base_url}/agent/v1/verification/{verification_id}/status",
                method="GET",
                headers=_auth_headers(token),
                verify_tls=bool(args.secure),
            )

        response = _wait_for_status(
            fetcher=fetcher,
            done_statuses={"ok", "failed"},
            interval_sec=float(args.interval_sec),
            timeout_sec=args.timeout_sec,
        )
        return {
            "verification_id": response.get("verification_id"),
            "status": response.get("status"),
        }

    return _run_token_command(args, callback)


def _command_verify_detail(args: argparse.Namespace) -> JsonObject:
    save_to = Path(str(args.save_to)).expanduser().resolve() if args.save_to else None

    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        query_pairs: list[tuple[str, str]] = []
        if args.test_name:
            query_pairs.append(("test_name", str(args.test_name)))
        if args.source:
            query_pairs.append(("source", str(args.source)))
        query = ("?" + urlencode(query_pairs)) if query_pairs else ""
        verification_id = str(args.verification_id or "").strip()
        detail_text = _http_text(
            url=f"{base_url}/agent/v1/verification/{verification_id}/detail{query}",
            method="GET",
            headers=_auth_headers(token),
            verify_tls=bool(args.secure),
        )
        result: JsonObject = {"verification_id": verification_id}
        if save_to is None:
            result["detail_text"] = detail_text
            return result
        _atomic_write_text(save_to, detail_text)
        result["saved_to"] = str(save_to)
        return result

    return _run_token_command(args, callback)


def _command_export_start(args: argparse.Namespace) -> JsonObject:
    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        payload: JsonObject = {"export_type": str(args.export_type)}
        if args.verification_id:
            payload["verification_id"] = str(args.verification_id)
        response = _http_json(
            url=f"{base_url}/agent/v1/export/start",
            method="POST",
            headers=_auth_headers(token, {"Content-Type": "application/json"}),
            body=_json_body(payload),
            verify_tls=bool(args.secure),
        )
        return {
            "export_id": response.get("export_id"),
            "status": response.get("status"),
        }

    return _run_token_command(args, callback)


def _command_export_wait(args: argparse.Namespace) -> JsonObject:
    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        export_id = str(args.export_id or "").strip()

        def fetcher() -> JsonObject:
            return _http_json(
                url=f"{base_url}/agent/v1/export/{export_id}/status",
                method="GET",
                headers=_auth_headers(token),
                verify_tls=bool(args.secure),
            )

        response = _wait_for_status(
            fetcher=fetcher,
            done_statuses={"ok", "failed"},
            interval_sec=float(args.interval_sec),
            timeout_sec=args.timeout_sec,
        )
        result: JsonObject = {
            "export_id": response.get("export_id"),
            "status": response.get("status"),
        }
        filename = response.get("filename")
        if isinstance(filename, str) and filename:
            result["filename"] = filename
        return result

    return _run_token_command(args, callback)


def _command_export_download(args: argparse.Namespace) -> JsonObject:
    output = Path(str(args.output or "")).expanduser().resolve()

    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        export_id = str(args.export_id or "").strip()
        payload = _http_binary(
            url=f"{base_url}/agent/v1/export/{export_id}/download",
            method="GET",
            headers=_auth_headers(token),
            verify_tls=bool(args.secure),
        )
        _atomic_write_bytes(output, payload)
        return {
            "export_id": export_id,
            "output": str(output),
            "bytes_written": len(payload),
        }

    return _run_token_command(args, callback)


def _message_from_args(args: argparse.Namespace) -> str:
    if bool(args.message) == bool(args.message_file):
        raise UsageError("provide exactly one of --message or --message-file")
    if args.message:
        value = str(args.message).strip()
    else:
        path = Path(str(args.message_file)).expanduser().resolve()
        if not path.is_file():
            raise UsageError(f"--message-file is not a file: {path}")
        value = path.read_text(encoding="utf-8-sig").strip()
    if not value:
        raise UsageError("commit message must not be empty")
    return value


def _command_commit(args: argparse.Namespace) -> JsonObject:
    message = _message_from_args(args)

    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        response = _http_json(
            url=f"{base_url}/agent/v1/commit",
            method="POST",
            headers=_auth_headers(token, {"Content-Type": "application/json"}),
            body=_json_body({"message": message}),
            verify_tls=bool(args.secure),
        )
        return {
            "status": response.get("status"),
            "head": response.get("head"),
        }

    return _run_token_command(args, callback)


def _command_commit_status(args: argparse.Namespace) -> JsonObject:
    def callback(_state_path: Path, _state: JsonObject, base_url: str, _problem: str, token: str) -> JsonObject:
        ref = str(args.ref or "").strip()
        response = _http_json(
            url=f"{base_url}/agent/v1/commit/{quote(ref, safe='')}/status",
            method="GET",
            headers=_auth_headers(token),
            verify_tls=bool(args.secure),
        )
        return {
            "ref": response.get("ref"),
            "status": response.get("status"),
            "head": response.get("head"),
            "remote_head": response.get("remote_head"),
        }

    return _run_token_command(args, callback)


def _problem_path_parts(problem: str) -> list[str]:
    parts = problem.split("/")
    if len(parts) != 2:
        raise UsageError("--problem must use owner/problem form for clone and pull")
    for part in parts:
        if part in {"", ".", ".."} or "\\" in part:
            raise UsageError("--problem contains an unsafe path component")
    return parts


def _target_dir_for_problem(problem: str, raw_target_dir: str | None) -> Path:
    _problem_path_parts(problem)
    if raw_target_dir:
        return Path(raw_target_dir).expanduser().resolve()
    return Path.cwd().joinpath(*problem.split("/")).resolve()


def _ensure_not_filesystem_root(path: Path) -> None:
    if path.parent == path:
        raise UsageError("--target-dir must not be a filesystem root")


def _nearest_existing_parent(path: Path) -> Path:
    current = path
    while not current.exists():
        if current.parent == current:
            raise CliError(code="local_fs_error", message=f"no existing parent for target path: {path}")
        current = current.parent
    if not current.is_dir():
        return current.parent
    return current


def _assert_writable_directory(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(dir=str(path), prefix=".polygon-agent-write-test-", suffix=".tmp")
        os.close(fd)
        Path(temp_name).unlink(missing_ok=True)
    except OSError as exc:
        raise CliError(code="local_fs_error", message=f"directory is not writable: {path}") from exc


def _validate_clone_target(target_dir: Path) -> None:
    _ensure_not_filesystem_root(target_dir)
    if target_dir.exists():
        if not target_dir.is_dir():
            raise UsageError(f"--target-dir is not a directory: {target_dir}")
        if _git_is_repo(target_dir):
            raise UsageError(f"target already contains a git repo; use pull: {target_dir}")
        if any(target_dir.iterdir()):
            raise UsageError(f"target directory is not empty: {target_dir}")
        _assert_writable_directory(target_dir)
        return
    _assert_writable_directory(_nearest_existing_parent(target_dir.parent))


def _validate_pull_target(target_dir: Path, problem: str) -> None:
    _ensure_not_filesystem_root(target_dir)
    if not target_dir.is_dir():
        raise UsageError(f"pull target does not exist: {target_dir}")
    if not _git_is_repo(target_dir):
        raise UsageError(f"pull target is not a git repo created by clone: {target_dir}")
    stored_problem = _git_config_get(target_dir, "polygon-agent.problem")
    if not stored_problem:
        raise CliError(
            code="repo_problem_missing",
            message="target repo is missing polygon-agent.problem; re-clone before using pull",
        )
    if stored_problem != problem:
        raise CliError(
            code="repo_problem_mismatch",
            message=f"target repo is for {stored_problem}, not {problem}",
        )
    _assert_writable_directory(target_dir)


def _git_run(repo_dir: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_dir), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise CliError(code="git_unavailable", message="git executable not found") from exc
    if check and completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or f"git {' '.join(args)} failed"
        raise CliError(code="git_error", message=message)
    return completed


def _git_is_repo(repo_dir: Path) -> bool:
    completed = _git_run(repo_dir, ["rev-parse", "--show-toplevel"], check=False)
    if completed.returncode != 0:
        return False
    top_level = completed.stdout.strip()
    if not top_level:
        return False
    return Path(top_level).resolve() == repo_dir.resolve()


def _git_config_get(repo_dir: Path, key: str) -> str:
    completed = _git_run(repo_dir, ["config", "--get", key], check=False)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _git_config_set(repo_dir: Path, key: str, value: str) -> None:
    _git_run(repo_dir, ["config", key, value])


def _git_head(repo_dir: Path) -> str | None:
    completed = _git_run(repo_dir, ["rev-parse", "--verify", "HEAD"], check=False)
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def _git_is_dirty(repo_dir: Path) -> bool:
    completed = _git_run(repo_dir, ["status", "--porcelain=v1", "--untracked-files=all"])
    return bool(completed.stdout.strip())


def _ensure_git_identity(repo_dir: Path, state: JsonObject) -> None:
    if not _git_config_get(repo_dir, "user.name"):
        identity = _state_identity_defaults(state)
        agent_name = identity.get("agent_name")
        _git_config_set(repo_dir, "user.name", str(agent_name or "Polygon Agent"))
    if not _git_config_get(repo_dir, "user.email"):
        _git_config_set(repo_dir, "user.email", "polygon-agent@local")


def _git_commit_snapshot(repo_dir: Path, state: JsonObject, message: str, *, allow_empty: bool = False) -> str | None:
    dirty = _git_is_dirty(repo_dir)
    if not dirty and not allow_empty:
        return None
    _ensure_git_identity(repo_dir, state)
    _git_run(repo_dir, ["add", "-A"])
    commit_args = ["commit", "-m", message]
    if allow_empty and not dirty:
        commit_args = ["commit", "--allow-empty", "-m", message]
    _git_run(repo_dir, commit_args)
    return _git_head(repo_dir)


def _safe_workspace_relative_path(remote_path: str) -> Path:
    pure_path = PurePosixPath(str(remote_path or "").replace("\\", "/"))
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise CliError(code="bad_response", message=f"unsafe remote path: {remote_path}")
    parts = [part for part in pure_path.parts if part not in {"", "."}]
    if not parts:
        raise CliError(code="bad_response", message="empty remote file path")
    if parts[0] not in ALLOWED_WORKSPACE_ROOT_NAMES:
        raise CliError(code="bad_response", message=f"remote path root is not allowed: {remote_path}")
    if any(part.startswith(".") for part in parts):
        raise CliError(code="bad_response", message=f"hidden remote path is not allowed: {remote_path}")
    return Path(*parts)


def _safe_extract_workspace_zip(payload: bytes, extract_dir: Path) -> None:
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for info in archive.infolist():
            rel_path = _safe_workspace_relative_path(info.filename)
            target = extract_dir / rel_path
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write_bytes(target, _normalize_text_bytes(archive.read(info)))


def _remove_repo_child(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def _copy_repo_child(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise CliError(code="bad_response", message=f"remote mirror contains unsupported symlink: {source}")
    if source.is_dir():
        shutil.copytree(source, destination)
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _apply_remote_mirror(source_root: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for child in list(target_dir.iterdir()):
        if child.name in PRESERVED_REPO_DIRS:
            continue
        _remove_repo_child(child)
    for child in source_root.iterdir():
        if child.name in PRESERVED_REPO_DIRS:
            continue
        _copy_repo_child(child, target_dir / child.name)


def _fetch_workspace_status(base_url: str, token: str, verify_tls: bool) -> JsonObject:
    return _http_json(
        url=f"{base_url}/agent/v1/workspace/status",
        method="GET",
        headers=_auth_headers(token),
        verify_tls=verify_tls,
    )


def _fetch_snapshot_mirror(*, base_url: str, token: str, staging_parent: Path, verify_tls: bool) -> tuple[Path, JsonObject]:
    _status, payload, headers = _http_request(
        url=f"{base_url}/agent/v1/workspace/snapshot",
        method="GET",
        headers=_auth_headers(token),
        verify_tls=verify_tls,
    )
    stage_root = staging_parent / "snapshot"
    _safe_extract_workspace_zip(payload, stage_root)
    return (
        stage_root,
        {
            "transport": "snapshot",
            "remote_head_commit": headers.get("X-Head-Commit", ""),
            "remote_dirty": str(headers.get("X-Workspace-Dirty", "")).lower() == "true",
        },
    )


def _local_workspace_zip(repo_dir: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for child in sorted(repo_dir.iterdir(), key=lambda p: p.name):
            if child.name in PRESERVED_REPO_DIRS or child.name.startswith("."):
                continue
            if child.name not in ALLOWED_WORKSPACE_ROOT_NAMES:
                continue
            if child.is_symlink():
                continue
            if child.is_file():
                archive.writestr(child.name, _normalize_text_bytes(child.read_bytes()))
                continue
            if not child.is_dir():
                continue
            archive.writestr(child.name + "/", b"")
            for dirpath, dirnames, filenames in os.walk(child, topdown=True, followlinks=False):
                dir_root = Path(dirpath)
                keep_dirs: list[str] = []
                for dirname in sorted(dirnames):
                    nested = dir_root / dirname
                    if dirname.startswith(".") or nested.is_symlink():
                        continue
                    keep_dirs.append(dirname)
                    archive.writestr(nested.relative_to(repo_dir).as_posix() + "/", b"")
                dirnames[:] = keep_dirs
                for filename in sorted(filenames):
                    nested = dir_root / filename
                    if filename.startswith(".") or nested.is_symlink() or not nested.is_file():
                        continue
                    archive.writestr(nested.relative_to(repo_dir).as_posix(), _normalize_text_bytes(nested.read_bytes()))
    return buffer.getvalue()


def _workspace_compare_zip(base_url: str, token: str, zip_bytes: bytes, verify_tls: bool) -> JsonObject:
    body, content_type = _multipart_upload_body(
        fields={},
        file_field_name="archive",
        file_name="workspace.zip",
        file_bytes=zip_bytes,
    )
    return _http_json(
        url=f"{base_url}/agent/v1/workspace/compare",
        method="POST",
        headers=_auth_headers(token, {"Content-Type": content_type}),
        body=body,
        verify_tls=verify_tls,
    )


def _workspace_apply_zip(base_url: str, token: str, zip_bytes: bytes, base_head_commit: str, verify_tls: bool) -> JsonObject:
    body, content_type = _multipart_upload_body(
        fields={"base_head_commit": base_head_commit},
        file_field_name="archive",
        file_name="workspace.zip",
        file_bytes=zip_bytes,
    )
    return _http_json(
        url=f"{base_url}/agent/v1/workspace/apply",
        method="POST",
        headers=_auth_headers(token, {"Content-Type": content_type}),
        body=body,
        verify_tls=verify_tls,
    )


def _clone_auth_result(problem: str, target_dir: Path, request_info: JsonObject, status: str) -> JsonObject:
    result: JsonObject = {
        "problem": problem,
        "target_dir": str(target_dir),
        "changed": False,
        "created_repo": False,
        "auto_connected": True,
        "approval_status": status,
        "required_scope": DEFAULT_CLONE_SCOPE,
    }
    for key in ("request_id", "approve_url", "expires_in"):
        value = request_info.get(key)
        if value:
            result[key] = value
    return result


def _clone_token_or_auth_result(
    *,
    state_path: Path,
    state: JsonObject,
    base_url: str,
    problem: str,
    target_dir: Path,
    verify_tls: bool,
    force_new_request: bool = False,
) -> tuple[str | None, JsonObject | None]:
    if not force_new_request:
        try:
            entry = _token_entry(state, problem)
            if _token_scope_satisfies(entry, DEFAULT_CLONE_SCOPE):
                token = entry.get("token")
                if isinstance(token, str) and token:
                    return (token, None)
        except CliError as exc:
            if exc.code != "missing_token":
                raise
    pending_entry = _state_pending_access(state).get(problem)
    if force_new_request and problem in _state_pending_access(state):
        del _state_pending_access(state)[problem]
        _save_state(state_path, state)
        pending_entry = None
    if isinstance(pending_entry, dict):
        request_id = str(pending_entry.get("request_id") or "")
        if request_id:
            poll_result = _poll_access_request(
                state_path=state_path,
                state=state,
                base_url=base_url,
                request_id=request_id,
                verify_tls=verify_tls,
                wait=False,
                interval_sec=DEFAULT_WAIT_INTERVAL_SEC,
                timeout_sec=None,
                expected_problem=problem,
            )
            status = str(poll_result.get("status") or "")
            if status == "approved":
                return (_token_for_problem(state, problem), {"auto_connected": True, "approval_status": "approved"})
            return (None, _clone_auth_result(problem, target_dir, pending_entry, status))
    request_info = _request_access(
        state_path=state_path,
        state=state,
        base_url=base_url,
        problem=problem,
        verify_tls=verify_tls,
        required_scope=DEFAULT_CLONE_SCOPE,
    )
    return (None, _clone_auth_result(problem, target_dir, request_info, "pending"))


def _sync_remote_to_repo(
    *,
    state: JsonObject,
    base_url: str,
    token: str,
    problem: str,
    target_dir: Path,
    verify_tls: bool,
    mode: str,
    auth_result: JsonObject | None = None,
) -> JsonObject:
    with tempfile.TemporaryDirectory(prefix="polygon-agent-mirror-") as temp_name:
        staging_parent = Path(temp_name)
        stage_root, transport_metadata = _fetch_snapshot_mirror(
            base_url=base_url,
            token=token,
            verify_tls=verify_tls,
            staging_parent=staging_parent,
        )
        remote_head_commit = str(transport_metadata.get("remote_head_commit") or "")
        if mode == "clone":
            target_dir.mkdir(parents=True, exist_ok=True)
            _apply_remote_mirror(stage_root, target_dir)
            _git_run(target_dir, ["init"])
            _git_config_set(target_dir, "polygon-agent.problem", problem)
            _git_config_set(target_dir, "polygon-agent.remote-head", remote_head_commit)
            post_sync_commit = _git_commit_snapshot(
                target_dir,
                state,
                f"sync: clone remote workspace for {problem}",
                allow_empty=True,
            )
            return _without_none({
                "problem": problem,
                "target_dir": str(target_dir),
                "changed": True,
                "created_repo": True,
                "auto_connected": bool(auth_result and auth_result.get("auto_connected")),
                "approval_status": auth_result.get("approval_status") if auth_result else None,
                "post_sync_commit": post_sync_commit,
                **transport_metadata,
            })
        pre_sync_commit = None
        if _git_is_dirty(target_dir):
            pre_sync_commit = _git_commit_snapshot(
                target_dir,
                state,
                f"sync: save local state before pulling {problem}",
            )
        _apply_remote_mirror(stage_root, target_dir)
        _git_config_set(target_dir, "polygon-agent.problem", problem)
        _git_config_set(target_dir, "polygon-agent.remote-head", remote_head_commit)
        post_sync_commit = _git_commit_snapshot(
            target_dir,
            state,
            f"sync: pull remote workspace for {problem}",
        )
        return _without_none({
            "problem": problem,
            "target_dir": str(target_dir),
            "changed": bool(post_sync_commit),
            "created_repo": False,
            "pre_sync_commit": pre_sync_commit,
            "post_sync_commit": post_sync_commit,
            **transport_metadata,
        })


def _command_clone(args: argparse.Namespace) -> JsonObject:
    problem = str(args.problem or "").strip()
    target_dir = _target_dir_for_problem(problem, args.target_dir)
    _validate_clone_target(target_dir)
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    verify_tls = bool(args.secure)
    token, auth_result = _clone_token_or_auth_result(
        state_path=state_path,
        state=state,
        base_url=base_url,
        problem=problem,
        target_dir=target_dir,
        verify_tls=verify_tls,
    )
    if token is None:
        if auth_result is None:
            raise CliError(code="missing_token", message=f"no cached token for problem {problem}")
        return auth_result
    try:
        return _sync_remote_to_repo(
            state=state,
            base_url=base_url,
            token=token,
            problem=problem,
            target_dir=target_dir,
            verify_tls=verify_tls,
            mode="clone",
            auth_result=auth_result,
        )
    except CliError as exc:
        if exc.http_status not in {401, 403}:
            raise
        if exc.http_status == 401:
            _invalidate_problem_token(state_path, state, problem)
        token, auth_result = _clone_token_or_auth_result(
            state_path=state_path,
            state=state,
            base_url=base_url,
            problem=problem,
            target_dir=target_dir,
            verify_tls=verify_tls,
            force_new_request=True,
        )
        if token is None:
            if auth_result is None:
                raise
            return auth_result
        return _sync_remote_to_repo(
            state=state,
            base_url=base_url,
            token=token,
            problem=problem,
            target_dir=target_dir,
            verify_tls=verify_tls,
            mode="clone",
            auth_result=auth_result,
        )


def _command_pull(args: argparse.Namespace) -> JsonObject:
    problem = str(args.problem or "").strip()
    target_dir = _target_dir_for_problem(problem, args.target_dir)
    _validate_pull_target(target_dir, problem)
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    try:
        token = _token_for_problem(state, problem)
    except CliError as exc:
        if exc.code == "missing_token":
            raise CliError(code="missing_token", message=f"no cached token for {problem}; run clone or connect first") from exc
        raise
    try:
        return _sync_remote_to_repo(
            state=state,
            base_url=base_url,
            token=token,
            problem=problem,
            target_dir=target_dir,
            verify_tls=bool(args.secure),
            mode="pull",
        )
    except CliError as exc:
        if exc.http_status == 401:
            _invalidate_problem_token(state_path, state, problem)
            raise CliError(code="token_invalid", message=f"token invalid for {problem}; run clone or connect first", http_status=401) from exc
        if exc.http_status == 403:
            raise CliError(code="scope_insufficient", message=f"token scope insufficient for {problem}; run clone or connect first", http_status=403) from exc
        raise


def _command_push(args: argparse.Namespace) -> JsonObject:
    problem = str(args.problem or "").strip()
    target_dir = _target_dir_for_problem(problem, args.target_dir)
    _validate_pull_target(target_dir, problem)
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    try:
        token = _token_for_problem(state, problem)
    except CliError as exc:
        if exc.code == "missing_token":
            raise CliError(code="missing_token", message=f"no cached token for {problem}; run clone or connect first") from exc
        raise
    zip_bytes = _local_workspace_zip(target_dir)
    base_head_commit = _git_config_get(target_dir, "polygon-agent.remote-head")
    try:
        compare = _workspace_compare_zip(base_url, token, zip_bytes, bool(args.secure))
        apply = _workspace_apply_zip(base_url, token, zip_bytes, base_head_commit, bool(args.secure))
        remote_head_commit = str(apply.get("head_commit") or "")
        if remote_head_commit:
            _git_config_set(target_dir, "polygon-agent.remote-head", remote_head_commit)
        return {
            "problem": problem,
            "target_dir": str(target_dir),
            "changed": bool(apply.get("changed")),
            "applied": bool(apply.get("applied")),
            "uploads": apply.get("uploads", []),
            "deletes": apply.get("deletes", []),
            "same_count": len(apply.get("same") or []),
            "remote_head_commit": remote_head_commit,
            "remote_dirty": bool(apply.get("dirty")),
            "preflight_changed": bool(compare.get("changed")),
        }
    except CliError as exc:
        if exc.http_status == 401:
            _invalidate_problem_token(state_path, state, problem)
            raise CliError(code="token_invalid", message=f"token invalid for {problem}; run clone or connect first", http_status=401) from exc
        if exc.http_status == 403:
            raise CliError(code="scope_insufficient", message=f"token scope insufficient for {problem}; run clone or connect first", http_status=403) from exc
        raise


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


def _add_state_file(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--state-file")


def _add_problem(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--problem", required=True)


def _add_wait_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--interval-sec", type=float, default=DEFAULT_WAIT_INTERVAL_SEC)
    parser.add_argument("--timeout-sec", type=float)


def _add_tls_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--secure", action="store_true", help="Enable TLS certificate verification")
    group.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification (default)")


def _add_sync_flags(parser: argparse.ArgumentParser) -> None:
    _add_state_file(parser)
    _add_problem(parser)
    parser.add_argument("--target-dir")
    _add_tls_flags(parser)


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description="Polygon Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--register-url", required=True)
    init_parser.add_argument("--state-file")
    init_parser.add_argument("--agent-name")
    init_parser.add_argument("--desktop-id")
    init_parser.add_argument("--init-ts")
    _add_tls_flags(init_parser)
    init_parser.set_defaults(func=_command_init)

    status_parser = subparsers.add_parser("status")
    _add_state_file(status_parser)
    _add_tls_flags(status_parser)
    status_parser.set_defaults(func=_command_status)

    connect_parser = subparsers.add_parser("connect")
    _add_state_file(connect_parser)
    _add_problem(connect_parser)
    _add_tls_flags(connect_parser)
    connect_parser.set_defaults(func=_command_connect)

    poll_parser = subparsers.add_parser("poll")
    _add_state_file(poll_parser)
    poll_parser.add_argument("--request-id", required=True)
    poll_parser.add_argument("--wait", action="store_true")
    _add_wait_flags(poll_parser)
    _add_tls_flags(poll_parser)
    poll_parser.set_defaults(func=_command_poll)

    clone_parser = subparsers.add_parser("clone")
    _add_sync_flags(clone_parser)
    clone_parser.set_defaults(func=_command_clone)

    pull_parser = subparsers.add_parser("pull")
    _add_sync_flags(pull_parser)
    pull_parser.set_defaults(func=_command_pull)

    push_parser = subparsers.add_parser("push")
    _add_sync_flags(push_parser)
    push_parser.set_defaults(func=_command_push)

    workspace_status_parser = subparsers.add_parser("workspace-status")
    _add_state_file(workspace_status_parser)
    _add_problem(workspace_status_parser)
    _add_tls_flags(workspace_status_parser)
    workspace_status_parser.set_defaults(func=_command_workspace_status)

    list_files_parser = subparsers.add_parser("list-files")
    _add_state_file(list_files_parser)
    _add_problem(list_files_parser)
    list_files_parser.add_argument("--path")
    _add_tls_flags(list_files_parser)
    list_files_parser.set_defaults(func=_command_list_files)

    read_file_parser = subparsers.add_parser("read-file")
    _add_state_file(read_file_parser)
    _add_problem(read_file_parser)
    read_file_parser.add_argument("--path", required=True)
    read_file_parser.add_argument("--save-to")
    _add_tls_flags(read_file_parser)
    read_file_parser.set_defaults(func=_command_read_file)

    upload_parser = subparsers.add_parser("upload")
    _add_state_file(upload_parser)
    _add_problem(upload_parser)
    upload_parser.add_argument("--workspace-path", required=True)
    upload_parser.add_argument("--local-file", required=True)
    _add_tls_flags(upload_parser)
    upload_parser.set_defaults(func=_command_upload)

    delete_parser = subparsers.add_parser("delete")
    _add_state_file(delete_parser)
    _add_problem(delete_parser)
    delete_parser.add_argument("--workspace-path", required=True)
    _add_tls_flags(delete_parser)
    delete_parser.set_defaults(func=_command_delete)

    verify_start_parser = subparsers.add_parser("verify-start")
    _add_state_file(verify_start_parser)
    _add_problem(verify_start_parser)
    _add_tls_flags(verify_start_parser)
    verify_start_parser.set_defaults(func=_command_verify_start)

    verify_wait_parser = subparsers.add_parser("verify-wait")
    _add_state_file(verify_wait_parser)
    _add_problem(verify_wait_parser)
    verify_wait_parser.add_argument("--verification-id", required=True)
    _add_wait_flags(verify_wait_parser)
    _add_tls_flags(verify_wait_parser)
    verify_wait_parser.set_defaults(func=_command_verify_wait)

    verify_detail_parser = subparsers.add_parser("verify-detail")
    _add_state_file(verify_detail_parser)
    _add_problem(verify_detail_parser)
    verify_detail_parser.add_argument("--verification-id", required=True)
    verify_detail_parser.add_argument("--test-name")
    verify_detail_parser.add_argument("--source")
    verify_detail_parser.add_argument("--save-to")
    _add_tls_flags(verify_detail_parser)
    verify_detail_parser.set_defaults(func=_command_verify_detail)

    export_start_parser = subparsers.add_parser("export-start")
    _add_state_file(export_start_parser)
    _add_problem(export_start_parser)
    export_start_parser.add_argument("--export-type", required=True, choices=["native", "icpc"])
    export_start_parser.add_argument("--verification-id")
    _add_tls_flags(export_start_parser)
    export_start_parser.set_defaults(func=_command_export_start)

    export_wait_parser = subparsers.add_parser("export-wait")
    _add_state_file(export_wait_parser)
    _add_problem(export_wait_parser)
    export_wait_parser.add_argument("--export-id", required=True)
    _add_wait_flags(export_wait_parser)
    _add_tls_flags(export_wait_parser)
    export_wait_parser.set_defaults(func=_command_export_wait)

    export_download_parser = subparsers.add_parser("export-download")
    _add_state_file(export_download_parser)
    _add_problem(export_download_parser)
    export_download_parser.add_argument("--export-id", required=True)
    export_download_parser.add_argument("--output", required=True)
    _add_tls_flags(export_download_parser)
    export_download_parser.set_defaults(func=_command_export_download)

    commit_parser = subparsers.add_parser("commit")
    _add_state_file(commit_parser)
    _add_problem(commit_parser)
    commit_parser.add_argument("--message")
    commit_parser.add_argument("--message-file")
    _add_tls_flags(commit_parser)
    commit_parser.set_defaults(func=_command_commit)

    commit_status_parser = subparsers.add_parser("commit-status")
    _add_state_file(commit_status_parser)
    _add_problem(commit_status_parser)
    commit_status_parser.add_argument("--ref", required=True)
    _add_tls_flags(commit_status_parser)
    commit_status_parser.set_defaults(func=_command_commit_status)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        result = args.func(args)
    except CliError as exc:
        _write_error(exc)
        return exc.exit_code
    except Exception as exc:
        print(f"unexpected error: {exc}", file=sys.stderr)
        _write_error(CliError(code="unexpected_error", message="unexpected error"))
        return 1
    _write_success(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
