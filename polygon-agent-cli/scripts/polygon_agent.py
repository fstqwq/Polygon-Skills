#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
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
from typing import Any, NamedTuple, Sequence
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
        details: JsonObject | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.http_status = http_status
        self.details = details or {}


class UsageError(CliError):
    def __init__(self, message: str) -> None:
        super().__init__(code="usage_error", message=message, exit_code=2)


class AgentCredentials(NamedTuple):
    credential: str


AGENT_CREDENTIAL_PATTERN = re.compile(r"polygon_agent_[A-Za-z0-9_-]{43}\Z")


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
    payload["error"].update(error.details)
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
        candidate = str(os.environ.get("COMPUTERNAME") or "").strip()
        if candidate:
            return candidate
    candidate = socket.gethostname().strip()
    if candidate:
        return candidate
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


def _state_pending_access(state: JsonObject) -> JsonObject:
    pending_access = state.get("pending_access")
    if isinstance(pending_access, dict):
        return pending_access
    pending_access = {}
    state["pending_access"] = pending_access
    return pending_access


def _state_credentials(state: JsonObject) -> AgentCredentials:
    raw = state.get("credential")
    if not isinstance(raw, str) or not AGENT_CREDENTIAL_PATTERN.fullmatch(raw):
        raise CliError(
            code="agent_reconnect_required",
            message=(
                "agent state has no valid credential; run init with a new "
                "registration URL to reconnect this session"
            ),
        )
    return AgentCredentials(credential=raw)


def _http_code_name(status: int) -> str:
    if status == 401:
        return "agent_credential_invalid"
    if status == 403:
        return "agent_permission_required"
    if status == 404:
        return "not_found"
    if status == 409:
        return "operation_conflict"
    if status == 410:
        return "registration_code_invalid"
    return "api_error"


def _api_error_from_response(status: int, body: bytes) -> CliError:
    message = f"http {status}"
    code = _http_code_name(status)
    details: JsonObject = {}
    if body:
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = None
        if isinstance(payload, dict):
            detail = payload.get("detail")
            error_payload = detail if isinstance(detail, dict) else payload
            error_text = error_payload.get("error")
            if isinstance(error_text, str) and error_text.strip():
                code = error_text.strip()
                message = code
            message_text = error_payload.get("message")
            if isinstance(message_text, str) and message_text.strip():
                message = message_text.strip()
            details = {
                key: value
                for key, value in error_payload.items()
                if key not in {"error", "message"}
            }
    return CliError(code=code, message=message, http_status=status, details=details)


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


def _auth_headers(
    credentials: AgentCredentials,
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {credentials.credential}",
    }
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


def _problem_url(
    base_url: str,
    path: str,
    problem: str,
    query: dict[str, str] | None = None,
) -> str:
    parameters = {"problem": problem}
    if query:
        parameters.update(query)
    return f"{base_url}{path}?{urlencode(parameters)}"


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
    request: JsonObject = {
        "agent_name": agent_name,
        "desktop_id": desktop_id,
        "init_ts": init_ts,
    }
    existing_session_id = existing_state.get("agent_session_id")
    if isinstance(existing_session_id, str) and existing_session_id.strip():
        request["existing_session_id"] = existing_session_id
    response = _http_json(
        url=register_url,
        method="POST",
        headers={"Content-Type": "application/json"},
        body=_json_body(request),
        verify_tls=bool(args.secure),
        warn_insecure=(not bool(args.secure)),
    )
    agent_session_id = str(response.get("agent_session_id") or "")
    credential = str(response.get("credential") or "")
    user = str(response.get("user") or "")
    server_name = str(response.get("server_name") or "")
    if (
        not agent_session_id
        or not AGENT_CREDENTIAL_PATTERN.fullmatch(credential)
        or not user
        or not server_name
    ):
        raise CliError(code="bad_response", message="registration response is missing required fields")
    state: JsonObject = {
        "base_url": base_url,
        "agent_session_id": agent_session_id,
        "credential": credential,
        "identity": {
            "agent_name": agent_name,
            "desktop_id": desktop_id,
            "init_ts": init_ts,
        },
        "user": user,
        "server_name": server_name,
        "pending_access": _state_pending_access(existing_state),
    }
    if isinstance(existing_state.get("tokens"), dict):
        state["tokens"] = existing_state["tokens"]
    _save_state(state_path, state)
    return {
        "base_url": base_url,
        "agent_session_id": agent_session_id,
        "user": user,
        "server_name": server_name,
        "state_file": _state_file_result(state_path),
    }


def _command_status(args: argparse.Namespace) -> JsonObject:
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    credentials = _state_credentials(state)
    response = _http_json(
        url=f"{base_url}/agent/v1/auth/status",
        method="GET",
        headers=_auth_headers(credentials),
        verify_tls=bool(args.secure),
    )
    if "tokens" in state:
        del state["tokens"]
        _save_state(state_path, state)
    return {
        "user": response.get("user"),
        "server_name": response.get("server_name"),
        "last_seen_at": response.get("last_seen_at"),
        "general_scope": response.get("general_scope"),
        "problem_grants": response.get("problem_grants", []),
    }


def _command_create(args: argparse.Namespace) -> JsonObject:
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    credentials = _state_credentials(state)
    problem = str(args.problem or "").strip()
    response = _http_json(
        url=f"{base_url}/agent/v1/problems",
        method="POST",
        headers=_auth_headers(
            credentials,
            {"Content-Type": "application/json"},
        ),
        body=_json_body({"problem": problem}),
        verify_tls=bool(args.secure),
    )
    return {"problem": response.get("problem")}


def _request_access(
    *,
    state_path: Path,
    state: JsonObject,
    base_url: str,
    problem: str,
    verify_tls: bool,
    required_scope: str | None = None,
) -> JsonObject:
    credentials = _state_credentials(state)
    scope = required_scope or "readonly"
    response = _http_json(
        url=f"{base_url}/agent/v1/auth/request-access",
        method="POST",
        headers=_auth_headers(
            credentials,
            {"Content-Type": "application/json"},
        ),
        body=_json_body(
            {
                "problem": problem,
                "scope": scope,
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
        "requested_scope": str(response.get("requested_scope") or scope),
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
    credentials = _state_credentials(state)
    deadline = None if timeout_sec is None else time.monotonic() + timeout_sec
    while True:
        response = _http_json(
            url=f"{base_url}/agent/v1/auth/poll/{request_id}",
            method="GET",
            headers=_auth_headers(credentials),
            verify_tls=verify_tls,
        )
        status = str(response.get("status") or "")
        if status == "approved":
            problem = str(response.get("problem") or expected_problem or "")
            expires_at = response.get("expires_at")
            if not problem:
                raise CliError(
                    code="bad_response",
                    message="approval response did not include the problem slug",
                )
            _state_pending_access(state).pop(problem, None)
            _save_state(state_path, state)
            return {
                "status": status,
                "problem": problem,
                "grant_id": response.get("grant_id"),
                "granted_scope": response.get("granted_scope"),
                "expires_at": expires_at,
            }
        if status in {"denied", "expired"}:
            if expected_problem:
                _state_pending_access(state).pop(expected_problem, None)
                _save_state(state_path, state)
            return {
                "status": status,
                "problem": response.get("problem") or expected_problem,
                "expires_at": response.get("expires_at"),
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
        required_scope=str(args.scope or "readonly"),
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


def _state_and_credentials(
    args: argparse.Namespace,
) -> tuple[Path, JsonObject, str, AgentCredentials]:
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    return (state_path, state, base_url, _state_credentials(state))


def _run_problem_command(
    args: argparse.Namespace,
    *,
    required_scope: str,
    callback: Any,
) -> JsonObject:
    state_path, state, base_url, credentials = _state_and_credentials(args)
    problem = str(args.problem or "").strip()
    try:
        return callback(state_path, state, base_url, problem, credentials)
    except CliError as exc:
        if exc.http_status == 403 and exc.code == "agent_permission_required":
            request_info = _request_access(
                state_path=state_path,
                state=state,
                base_url=base_url,
                problem=problem,
                verify_tls=bool(args.secure),
                required_scope=required_scope,
            )
            return {
                **request_info,
                "approval_status": "pending",
                "required_scope": required_scope,
            }
        raise


def _command_workspace_status(args: argparse.Namespace) -> JsonObject:
    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        response = _http_json(
            url=_problem_url(base_url, "/agent/v1/workspace/status", problem),
            method="GET",
            headers=_auth_headers(credentials),
            verify_tls=bool(args.secure),
        )
        return {
            "problem": response.get("problem"),
            "workspace_id": response.get("workspace_id"),
            "head_commit": response.get("head_commit"),
            "dirty": response.get("dirty"),
            "git": response.get("git"),
        }

    return _run_problem_command(
        args,
        required_scope="readonly",
        callback=callback,
    )


def _command_list_files(args: argparse.Namespace) -> JsonObject:
    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        query = {"path": str(args.path)} if args.path else None
        response = _http_json(
            url=_problem_url(
                base_url,
                "/agent/v1/workspace/files",
                problem,
                query,
            ),
            method="GET",
            headers=_auth_headers(credentials),
            verify_tls=bool(args.secure),
        )
        return {
            "base_path": response.get("base_path"),
            "entries": response.get("entries", []),
            "truncated": bool(response.get("truncated")),
        }

    return _run_problem_command(
        args,
        required_scope="readonly",
        callback=callback,
    )


def _command_read_file(args: argparse.Namespace) -> JsonObject:
    save_to = Path(str(args.save_to)).expanduser().resolve() if args.save_to else None

    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        response = _http_json(
            url=_problem_url(
                base_url,
                "/agent/v1/workspace/file",
                problem,
                {"path": str(args.path)},
            ),
            method="GET",
            headers=_auth_headers(credentials),
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

    return _run_problem_command(
        args,
        required_scope="readonly",
        callback=callback,
    )


def _command_upload(args: argparse.Namespace) -> JsonObject:
    local_file = Path(str(args.local_file or "")).expanduser().resolve()
    if not local_file.is_file():
        raise UsageError(f"--local-file is not a file: {local_file}")
    file_bytes = local_file.read_bytes()

    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        body, content_type = _multipart_upload_body(
            fields={"path": str(args.workspace_path)},
            file_field_name="file",
            file_name=local_file.name,
            file_bytes=file_bytes,
        )
        response = _http_json(
            url=_problem_url(base_url, "/agent/v1/workspace/upload", problem),
            method="POST",
            headers=_auth_headers(
                credentials,
                {"Content-Type": content_type},
            ),
            body=body,
            verify_tls=bool(args.secure),
        )
        return {
            "path": response.get("path"),
            "bytes": response.get("bytes"),
        }

    return _run_problem_command(
        args,
        required_scope="workspace",
        callback=callback,
    )


def _command_delete(args: argparse.Namespace) -> JsonObject:
    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        quoted = quote(str(args.workspace_path), safe="/")
        response = _http_json(
            url=_problem_url(
                base_url,
                f"/agent/v1/workspace/files/{quoted}",
                problem,
            ),
            method="DELETE",
            headers=_auth_headers(credentials),
            verify_tls=bool(args.secure),
        )
        return {"path": response.get("path")}

    return _run_problem_command(
        args,
        required_scope="workspace",
        callback=callback,
    )


def _command_verify_start(args: argparse.Namespace) -> JsonObject:
    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        response = _http_json(
            url=_problem_url(base_url, "/agent/v1/verification/start", problem),
            method="POST",
            headers=_auth_headers(
                credentials,
                {"Content-Type": "application/json"},
            ),
            body=_json_body({}),
            verify_tls=bool(args.secure),
        )
        return {
            "verification_id": response.get("verification_id"),
            "status": response.get("status"),
        }

    return _run_problem_command(
        args,
        required_scope="readonly",
        callback=callback,
    )


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
            last_response = json.dumps(
                response,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            raise CliError(
                code="timeout",
                message=(
                    "wait operation timed out; "
                    f"last response: {last_response}"
                ),
            )
        time.sleep(interval_sec)


def _command_verify_wait(args: argparse.Namespace) -> JsonObject:
    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        verification_id = str(args.verification_id or "").strip()

        def fetcher() -> JsonObject:
            return _http_json(
                url=_problem_url(
                    base_url,
                    f"/agent/v1/verification/{verification_id}/status",
                    problem,
                ),
                method="GET",
                headers=_auth_headers(credentials),
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

    return _run_problem_command(
        args,
        required_scope="readonly",
        callback=callback,
    )


def _command_verify_detail(args: argparse.Namespace) -> JsonObject:
    save_to = Path(str(args.save_to)).expanduser().resolve() if args.save_to else None

    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        query: dict[str, str] = {}
        if args.test_name:
            query["test_name"] = str(args.test_name)
        if args.source:
            query["source"] = str(args.source)
        verification_id = str(args.verification_id or "").strip()
        detail_text = _http_text(
            url=_problem_url(
                base_url,
                f"/agent/v1/verification/{verification_id}/detail",
                problem,
                query,
            ),
            method="GET",
            headers=_auth_headers(credentials),
            verify_tls=bool(args.secure),
        )
        result: JsonObject = {"verification_id": verification_id}
        if save_to is None:
            result["detail_text"] = detail_text
            return result
        _atomic_write_text(save_to, detail_text)
        result["saved_to"] = str(save_to)
        return result

    return _run_problem_command(
        args,
        required_scope="readonly",
        callback=callback,
    )


def _command_export_start(args: argparse.Namespace) -> JsonObject:
    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        payload: JsonObject = {"format": str(args.format)}
        response = _http_json(
            url=_problem_url(base_url, "/agent/v1/export/start", problem),
            method="POST",
            headers=_auth_headers(
                credentials,
                {"Content-Type": "application/json"},
            ),
            body=_json_body(payload),
            verify_tls=bool(args.secure),
        )
        job_id = str(response.get("job_id") or "")
        if not job_id:
            raise CliError(code="bad_response", message="export response is missing job_id")
        return _without_none({
            "job_id": job_id,
            "status": response.get("status"),
            "phase": response.get("phase"),
            "format": response.get("format"),
            "source_commit": response.get("source_commit"),
            "verified_revision_id": response.get("verified_revision_id"),
        })

    return _run_problem_command(
        args,
        required_scope="workspace",
        callback=callback,
    )


def _command_export_wait(args: argparse.Namespace) -> JsonObject:
    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        job_id = str(args.job_id or "").strip()

        def fetcher() -> JsonObject:
            return _http_json(
                url=_problem_url(
                    base_url,
                    f"/agent/v1/export/{job_id}/status",
                    problem,
                ),
                method="GET",
                headers=_auth_headers(credentials),
                verify_tls=bool(args.secure),
            )

        response = _wait_for_status(
            fetcher=fetcher,
            done_statuses={"succeeded", "failed"},
            interval_sec=float(args.interval_sec),
            timeout_sec=args.timeout_sec,
        )
        response_job_id = str(response.get("job_id") or "")
        if response_job_id != job_id:
            raise CliError(code="bad_response", message="export status response has an invalid job_id")
        status = str(response.get("status") or "")
        result: JsonObject = _without_none({
            "job_id": response_job_id,
            "status": status,
            "phase": response.get("phase"),
            "format": response.get("format"),
            "source_commit": response.get("source_commit"),
            "verified_revision_id": response.get("verified_revision_id"),
        })
        message = response.get("error")
        if isinstance(message, str) and message:
            result["warning" if status == "succeeded" else "error"] = message
        filename = response.get("filename")
        if isinstance(filename, str) and filename:
            result["filename"] = filename
        return result

    return _run_problem_command(
        args,
        required_scope="readonly",
        callback=callback,
    )


def _command_export_download(args: argparse.Namespace) -> JsonObject:
    output = Path(str(args.output or "")).expanduser().resolve()

    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        job_id = str(args.job_id or "").strip()
        payload = _http_binary(
            url=_problem_url(
                base_url,
                f"/agent/v1/export/{job_id}/download",
                problem,
            ),
            method="GET",
            headers=_auth_headers(credentials),
            verify_tls=bool(args.secure),
        )
        _atomic_write_bytes(output, payload)
        return {
            "job_id": job_id,
            "output": str(output),
            "bytes_written": len(payload),
        }

    return _run_problem_command(
        args,
        required_scope="readonly",
        callback=callback,
    )


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

    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        response = _http_json(
            url=_problem_url(base_url, "/agent/v1/commit", problem),
            method="POST",
            headers=_auth_headers(
                credentials,
                {"Content-Type": "application/json"},
            ),
            body=_json_body({"message": message}),
            verify_tls=bool(args.secure),
        )
        return {
            "status": response.get("status"),
            "head": response.get("head"),
        }

    return _run_problem_command(
        args,
        required_scope="commit",
        callback=callback,
    )


def _command_commit_status(args: argparse.Namespace) -> JsonObject:
    def callback(
        _state_path: Path,
        _state: JsonObject,
        base_url: str,
        problem: str,
        credentials: AgentCredentials,
    ) -> JsonObject:
        ref = str(args.ref or "").strip()
        response = _http_json(
            url=_problem_url(
                base_url,
                f"/agent/v1/commit/{quote(ref, safe='')}/status",
                problem,
            ),
            method="GET",
            headers=_auth_headers(credentials),
            verify_tls=bool(args.secure),
        )
        return {
            "ref": response.get("ref"),
            "status": response.get("status"),
            "head": response.get("head"),
            "remote_head": response.get("remote_head"),
        }

    return _run_problem_command(
        args,
        required_scope="readonly",
        callback=callback,
    )


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


def _fetch_snapshot_url(
    *,
    url: str,
    credentials: AgentCredentials,
    staging_parent: Path,
    verify_tls: bool,
) -> tuple[Path, JsonObject]:
    _status, payload, headers = _http_request(
        url=url,
        method="GET",
        headers=_auth_headers(credentials),
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


def _fetch_snapshot_mirror(
    *,
    base_url: str,
    credentials: AgentCredentials,
    problem: str,
    staging_parent: Path,
    verify_tls: bool,
) -> tuple[Path, JsonObject]:
    return _fetch_snapshot_url(
        url=_problem_url(base_url, "/agent/v1/workspace/snapshot", problem),
        credentials=credentials,
        staging_parent=staging_parent,
        verify_tls=verify_tls,
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


def _workspace_compare_zip(
    base_url: str,
    credentials: AgentCredentials,
    problem: str,
    zip_bytes: bytes,
    verify_tls: bool,
) -> JsonObject:
    body, content_type = _multipart_upload_body(
        fields={},
        file_field_name="archive",
        file_name="workspace.zip",
        file_bytes=zip_bytes,
    )
    return _http_json(
        url=_problem_url(base_url, "/agent/v1/workspace/compare", problem),
        method="POST",
        headers=_auth_headers(credentials, {"Content-Type": content_type}),
        body=body,
        verify_tls=verify_tls,
    )


def _workspace_apply_zip(
    base_url: str,
    credentials: AgentCredentials,
    problem: str,
    zip_bytes: bytes,
    base_head_commit: str,
    verify_tls: bool,
) -> JsonObject:
    body, content_type = _multipart_upload_body(
        fields={"base_head_commit": base_head_commit},
        file_field_name="archive",
        file_name="workspace.zip",
        file_bytes=zip_bytes,
    )
    return _http_json(
        url=_problem_url(base_url, "/agent/v1/workspace/apply", problem),
        method="POST",
        headers=_auth_headers(credentials, {"Content-Type": content_type}),
        body=body,
        verify_tls=verify_tls,
    )


def _clone_auth_result(problem: str, target_dir: Path, request_info: JsonObject, status: str) -> JsonObject:
    result: JsonObject = {
        "problem": problem,
        "target_dir": str(target_dir),
        "changed": False,
        "created_repo": False,
        "approval_status": status,
        "required_scope": DEFAULT_CLONE_SCOPE,
    }
    for key in ("request_id", "approve_url", "expires_in"):
        value = request_info.get(key)
        if value:
            result[key] = value
    return result


def _problem_approval_result(
    *,
    state_path: Path,
    state: JsonObject,
    base_url: str,
    problem: str,
    verify_tls: bool,
    required_scope: str,
) -> JsonObject:
    request_info = _request_access(
        state_path=state_path,
        state=state,
        base_url=base_url,
        problem=problem,
        verify_tls=verify_tls,
        required_scope=required_scope,
    )
    return {
        **request_info,
        "approval_status": "pending",
        "required_scope": required_scope,
    }


def _sync_remote_to_repo(
    *,
    state: JsonObject,
    base_url: str,
    credentials: AgentCredentials,
    problem: str,
    target_dir: Path,
    verify_tls: bool,
    mode: str,
) -> JsonObject:
    with tempfile.TemporaryDirectory(prefix="polygon-agent-mirror-") as temp_name:
        staging_parent = Path(temp_name)
        stage_root, transport_metadata = _fetch_snapshot_mirror(
            base_url=base_url,
            credentials=credentials,
            problem=problem,
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
    credentials = _state_credentials(state)
    try:
        return _sync_remote_to_repo(
            state=state,
            base_url=base_url,
            credentials=credentials,
            problem=problem,
            target_dir=target_dir,
            verify_tls=bool(args.secure),
            mode="clone",
        )
    except CliError as exc:
        if exc.http_status != 403 or exc.code != "agent_permission_required":
            raise
        result = _problem_approval_result(
            state_path=state_path,
            state=state,
            base_url=base_url,
            problem=problem,
            verify_tls=bool(args.secure),
            required_scope=DEFAULT_CLONE_SCOPE,
        )
        return _clone_auth_result(problem, target_dir, result, "pending")


def _command_pull(args: argparse.Namespace) -> JsonObject:
    problem = str(args.problem or "").strip()
    target_dir = _target_dir_for_problem(problem, args.target_dir)
    _validate_pull_target(target_dir, problem)
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    credentials = _state_credentials(state)
    try:
        return _sync_remote_to_repo(
            state=state,
            base_url=base_url,
            credentials=credentials,
            problem=problem,
            target_dir=target_dir,
            verify_tls=bool(args.secure),
            mode="pull",
        )
    except CliError as exc:
        if exc.http_status == 403 and exc.code == "agent_permission_required":
            return _problem_approval_result(
                state_path=state_path,
                state=state,
                base_url=base_url,
                problem=problem,
                verify_tls=bool(args.secure),
                required_scope=DEFAULT_CLONE_SCOPE,
            )
        raise


def _command_push(args: argparse.Namespace) -> JsonObject:
    problem = str(args.problem or "").strip()
    target_dir = _target_dir_for_problem(problem, args.target_dir)
    _validate_pull_target(target_dir, problem)
    state_path = _resolve_state_file(args.state_file)
    state = _load_json_file(state_path)
    base_url = _state_string(state, "base_url")
    credentials = _state_credentials(state)
    zip_bytes = _local_workspace_zip(target_dir)
    base_head_commit = _git_config_get(target_dir, "polygon-agent.remote-head")
    try:
        compare = _workspace_compare_zip(
            base_url,
            credentials,
            problem,
            zip_bytes,
            bool(args.secure),
        )
        apply = _workspace_apply_zip(
            base_url,
            credentials,
            problem,
            zip_bytes,
            base_head_commit,
            bool(args.secure),
        )
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
        if exc.http_status == 403 and exc.code == "agent_permission_required":
            return _problem_approval_result(
                state_path=state_path,
                state=state,
                base_url=base_url,
                problem=problem,
                verify_tls=bool(args.secure),
                required_scope="workspace",
            )
        raise


def _safe_contest_component(raw: str, *, field: str) -> str:
    value = str(raw or "")
    invalid_characters = set('<>:"/\\|?*')
    if (
        not value
        or value in {".", ".."}
        or value[-1] in {" ", "."}
        or any(character in invalid_characters or ord(character) < 32 for character in value)
    ):
        raise CliError(code="bad_response", message=f"unsafe Contest {field}: {value!r}")
    reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
    if value.split(".", 1)[0].upper() in reserved:
        raise CliError(code="bad_response", message=f"reserved Contest {field}: {value!r}")
    return value


def _contest_target_dir(contest_slug: str, raw_target_dir: str | None) -> Path:
    safe_slug = _safe_contest_component(contest_slug, field="slug")
    if raw_target_dir:
        return Path(raw_target_dir).expanduser().resolve()
    return (Path.cwd() / safe_slug).resolve()


def _fetch_contest_roster(
    *,
    base_url: str,
    credentials: AgentCredentials,
    contest_slug: str,
    verify_tls: bool,
) -> JsonObject:
    response = _http_json(
        url=f"{base_url}/agent/v1/contests/{quote(contest_slug, safe='')}/problems",
        method="GET",
        headers=_auth_headers(credentials),
        verify_tls=verify_tls,
    )
    generation = response.get("source_generation")
    raw_problems = response.get("problems")
    if isinstance(generation, bool) or not isinstance(generation, int):
        raise CliError(
            code="bad_response",
            message="Contest roster has an invalid source_generation",
        )
    if not isinstance(raw_problems, list):
        raise CliError(code="bad_response", message="Contest roster has an invalid problems list")
    problems: list[JsonObject] = []
    seen_ids: set[int] = set()
    seen_problems: set[str] = set()
    seen_labels: set[str] = set()
    for raw_problem in raw_problems:
        if not isinstance(raw_problem, dict):
            raise CliError(
                code="bad_response",
                message="Contest roster contains a non-object problem",
            )
        contest_problem_id = raw_problem.get("contest_problem_id")
        position = raw_problem.get("position")
        if (
            isinstance(contest_problem_id, bool)
            or not isinstance(contest_problem_id, int)
            or contest_problem_id <= 0
            or isinstance(position, bool)
            or not isinstance(position, int)
            or position < 0
        ):
            raise CliError(
                code="bad_response",
                message="Contest roster contains an invalid problem identity",
            )
        label = _safe_contest_component(str(raw_problem.get("idx") or ""), field="label")
        problem = str(raw_problem.get("problem") or "")
        try:
            _problem_path_parts(problem)
        except UsageError as exc:
            raise CliError(
                code="bad_response",
                message=f"Contest roster has an invalid problem: {problem!r}",
            ) from exc
        label_key = label.casefold()
        if (
            contest_problem_id in seen_ids
            or problem in seen_problems
            or label_key in seen_labels
        ):
            raise CliError(
                code="bad_response",
                message="Contest roster contains duplicate identities",
            )
        seen_ids.add(contest_problem_id)
        seen_problems.add(problem)
        seen_labels.add(label_key)
        problems.append(
            {
                "contest_problem_id": contest_problem_id,
                "position": position,
                "idx": label,
                "problem": problem,
            }
        )
    if response.get("problem_count") != len(problems):
        raise CliError(
            code="bad_response",
            message="Contest roster problem_count does not match problems",
        )
    returned_slug = str(response.get("contest_slug") or "")
    if returned_slug != contest_slug:
        raise CliError(code="bad_response", message="Contest roster slug does not match request")
    return {
        "contest_id": response.get("contest_id"),
        "contest_slug": returned_slug,
        "contest_title": str(response.get("contest_title") or ""),
        "source_generation": generation,
        "problem_count": len(problems),
        "problems": problems,
    }


def _contest_repo_config(repo_dir: Path) -> JsonObject:
    return {
        "problem": _git_config_get(repo_dir, "polygon-agent.problem"),
        "contest": _git_config_get(repo_dir, "polygon-agent.contest"),
        "contest_problem_id": _git_config_get(repo_dir, "polygon-agent.contest-problem-id"),
        "contest_label": _git_config_get(repo_dir, "polygon-agent.contest-label"),
    }


def _contest_layout_conflicts(
    *,
    target_dir: Path,
    contest_slug: str,
    roster_problems: list[JsonObject],
) -> list[JsonObject]:
    conflicts: list[JsonObject] = []
    if target_dir.exists() and not target_dir.is_dir():
        return [{"kind": "target_occupied", "current_path": str(target_dir)}]
    children = list(target_dir.iterdir()) if target_dir.is_dir() else []
    children_by_case: dict[str, list[Path]] = {}
    contest_repos: list[tuple[Path, JsonObject]] = []
    for child in children:
        children_by_case.setdefault(child.name.casefold(), []).append(child)
        if child.is_dir() and _git_is_repo(child):
            config = _contest_repo_config(child)
            if config["contest"] == contest_slug:
                contest_repos.append((child, config))
    for paths in children_by_case.values():
        if len(paths) > 1:
            conflicts.append(
                {
                    "kind": "label_case_conflict",
                    "paths": sorted(path.name for path in paths),
                }
            )

    by_id = {str(item["contest_problem_id"]): item for item in roster_problems}
    local_ids: dict[str, list[Path]] = {}
    local_problems: dict[str, list[Path]] = {}
    for path, config in contest_repos:
        local_id = str(config["contest_problem_id"] or "")
        local_problem = str(config["problem"] or "")
        if local_id:
            local_ids.setdefault(local_id, []).append(path)
        if local_problem:
            local_problems.setdefault(local_problem, []).append(path)
        expected = by_id.get(local_id)
        if expected is None:
            conflicts.append(
                {
                    "kind": "problem_removed",
                    "problem": local_problem,
                    "current_path": path.name,
                    "contest_problem_id": local_id,
                }
            )
            continue
        expected_label = str(expected["idx"])
        if path.name != expected_label:
            conflicts.append(
                {
                    "kind": "problem_relabelled",
                    "problem": expected["problem"],
                    "current_path": path.name,
                    "expected_path": expected_label,
                }
            )
        if local_problem != expected["problem"] or config["contest_label"] != expected_label:
            conflicts.append(
                {
                    "kind": "repo_config_mismatch",
                    "problem": expected["problem"],
                    "current_path": path.name,
                }
            )
    for local_id, paths in local_ids.items():
        if len(paths) > 1:
            conflicts.append(
                {
                    "kind": "duplicate_contest_problem_id",
                    "contest_problem_id": local_id,
                    "paths": sorted(path.name for path in paths),
                }
            )
    for problem, paths in local_problems.items():
        if len(paths) > 1:
            conflicts.append(
                {
                    "kind": "duplicate_problem",
                    "problem": problem,
                    "paths": sorted(path.name for path in paths),
                }
            )

    for item in roster_problems:
        label = str(item["idx"])
        matching_paths = children_by_case.get(label.casefold(), [])
        if not matching_paths:
            continue
        exact_path = next((path for path in matching_paths if path.name == label), None)
        if exact_path is None:
            conflicts.append(
                {
                    "kind": "label_case_conflict",
                    "expected_path": label,
                    "current_path": matching_paths[0].name,
                }
            )
            continue
        if not exact_path.is_dir() or not _git_is_repo(exact_path):
            conflicts.append(
                {
                    "kind": "label_path_occupied",
                    "problem": item["problem"],
                    "expected_path": label,
                }
            )
            continue
        config = _contest_repo_config(exact_path)
        expected_id = str(item["contest_problem_id"])
        if (
            config["contest"] != contest_slug
            or config["contest_problem_id"] != expected_id
            or config["problem"] != item["problem"]
            or config["contest_label"] != label
        ):
            conflicts.append(
                {
                    "kind": "repo_config_mismatch",
                    "problem": item["problem"],
                    "current_path": label,
                }
            )
    return conflicts


def _set_contest_repo_config(
    repo_dir: Path,
    *,
    contest_slug: str,
    item: JsonObject,
    remote_head_commit: str,
) -> None:
    _git_config_set(repo_dir, "polygon-agent.problem", str(item["problem"]))
    _git_config_set(repo_dir, "polygon-agent.remote-head", remote_head_commit)
    _git_config_set(repo_dir, "polygon-agent.contest", contest_slug)
    _git_config_set(
        repo_dir,
        "polygon-agent.contest-problem-id",
        str(item["contest_problem_id"]),
    )
    _git_config_set(repo_dir, "polygon-agent.contest-label", str(item["idx"]))


def _apply_contest_snapshot(
    *,
    state: JsonObject,
    contest_slug: str,
    item: JsonObject,
    stage_root: Path,
    transport_metadata: JsonObject,
    target_dir: Path,
) -> JsonObject:
    created_repo = not target_dir.exists()
    pre_sync_commit = None
    if created_repo:
        target_dir.mkdir(parents=True)
        _apply_remote_mirror(stage_root, target_dir)
        _git_run(target_dir, ["init"])
    else:
        if _git_is_dirty(target_dir):
            pre_sync_commit = _git_commit_snapshot(
                target_dir,
                state,
                f"sync: save local state before pulling {item['problem']}",
            )
        _apply_remote_mirror(stage_root, target_dir)
    remote_head_commit = str(transport_metadata.get("remote_head_commit") or "")
    _set_contest_repo_config(
        target_dir,
        contest_slug=contest_slug,
        item=item,
        remote_head_commit=remote_head_commit,
    )
    post_sync_commit = _git_commit_snapshot(
        target_dir,
        state,
        f"sync: pull Contest {contest_slug} problem {item['idx']}",
        allow_empty=created_repo,
    )
    return _without_none(
        {
            "contest_problem_id": item["contest_problem_id"],
            "idx": item["idx"],
            "problem": item["problem"],
            "target_dir": str(target_dir),
            "created_repo": created_repo,
            "changed": bool(post_sync_commit),
            "pre_sync_commit": pre_sync_commit,
            "post_sync_commit": post_sync_commit,
            **transport_metadata,
        }
    )


def _command_pull_contest(args: argparse.Namespace) -> JsonObject:
    contest_slug = str(args.contest or "").strip()
    target_dir = _contest_target_dir(contest_slug, args.target_dir)
    _ensure_not_filesystem_root(target_dir)
    state_path, state, base_url, credentials = _state_and_credentials(args)
    del state_path
    roster = _fetch_contest_roster(
        base_url=base_url,
        credentials=credentials,
        contest_slug=contest_slug,
        verify_tls=bool(args.secure),
    )
    roster_problems = roster["problems"]
    if not isinstance(roster_problems, list):
        raise CliError(code="bad_response", message="Contest roster problems are invalid")
    conflicts = _contest_layout_conflicts(
        target_dir=target_dir,
        contest_slug=contest_slug,
        roster_problems=roster_problems,
    )
    if conflicts:
        raise CliError(
            code="contest_layout_conflict",
            message="local Contest layout conflicts with the current roster",
            details={"contest": contest_slug, "conflicts": conflicts},
        )
    writable_parent = (
        target_dir
        if target_dir.is_dir()
        else _nearest_existing_parent(target_dir.parent)
    )
    _assert_writable_directory(writable_parent)
    generation = int(roster["source_generation"])
    staged: list[tuple[JsonObject, Path, JsonObject]] = []
    with tempfile.TemporaryDirectory(prefix="polygon-agent-contest-") as temp_name:
        staging_root = Path(temp_name)
        for offset, item in enumerate(roster_problems):
            item_staging = staging_root / str(offset)
            item_staging.mkdir()
            snapshot_path = (
                f"/agent/v1/contests/{quote(contest_slug, safe='')}/problems/"
                f"{item['contest_problem_id']}/workspace/snapshot"
            )
            stage_root, metadata = _fetch_snapshot_url(
                url=f"{base_url}{snapshot_path}?{urlencode({'source_generation': generation})}",
                credentials=credentials,
                staging_parent=item_staging,
                verify_tls=bool(args.secure),
            )
            staged.append((item, stage_root, metadata))
        target_dir.mkdir(parents=True, exist_ok=True)
        results = [
            _apply_contest_snapshot(
                state=state,
                contest_slug=contest_slug,
                item=item,
                stage_root=stage_root,
                transport_metadata=metadata,
                target_dir=target_dir / str(item["idx"]),
            )
            for item, stage_root, metadata in staged
        ]
    return {
        "contest": contest_slug,
        "contest_title": roster["contest_title"],
        "source_generation": generation,
        "problem_count": len(results),
        "target_dir": str(target_dir),
        "problems": results,
    }


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

    create_parser = subparsers.add_parser("create")
    _add_state_file(create_parser)
    _add_problem(create_parser)
    _add_tls_flags(create_parser)
    create_parser.set_defaults(func=_command_create)

    connect_parser = subparsers.add_parser("connect")
    _add_state_file(connect_parser)
    _add_problem(connect_parser)
    connect_parser.add_argument(
        "--scope",
        choices=["readonly", "workspace", "commit"],
        default="readonly",
    )
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

    pull_contest_parser = subparsers.add_parser("pull-contest")
    _add_state_file(pull_contest_parser)
    pull_contest_parser.add_argument("--contest", required=True)
    pull_contest_parser.add_argument("--target-dir")
    _add_tls_flags(pull_contest_parser)
    pull_contest_parser.set_defaults(func=_command_pull_contest)

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
    export_start_parser.add_argument("--format", required=True, choices=["domjudge", "icpc-2025-09"])
    _add_tls_flags(export_start_parser)
    export_start_parser.set_defaults(func=_command_export_start)

    export_wait_parser = subparsers.add_parser("export-wait")
    _add_state_file(export_wait_parser)
    _add_problem(export_wait_parser)
    export_wait_parser.add_argument("--job-id", required=True)
    _add_wait_flags(export_wait_parser)
    _add_tls_flags(export_wait_parser)
    export_wait_parser.set_defaults(func=_command_export_wait)

    export_download_parser = subparsers.add_parser("export-download")
    _add_state_file(export_download_parser)
    _add_problem(export_download_parser)
    export_download_parser.add_argument("--job-id", required=True)
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
