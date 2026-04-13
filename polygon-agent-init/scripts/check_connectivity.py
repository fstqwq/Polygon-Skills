#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _normalize_base_url(raw: str) -> str:
    value = raw.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"invalid base URL: {raw}")
    return f"{parsed.scheme}://{parsed.netloc}"


def _base_url_from_register_url(raw: str) -> str:
    value = raw.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"invalid registration URL: {raw}")
    if "/agent/v1/register/" not in parsed.path:
        raise ValueError("registration URL must contain /agent/v1/register/")
    return f"{parsed.scheme}://{parsed.netloc}"


def _load_state_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"state file {path} does not contain a JSON object")
    return data


def _base_url_from_state(data: dict[str, Any], path: Path) -> str:
    base_url = data.get("base_url")
    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError(f"state file {path} does not contain a usable base_url")
    return _normalize_base_url(base_url)


def _probe(url: str, method: str, timeout_sec: float) -> tuple[int | None, str]:
    opener = urllib.request.build_opener(_NoRedirectHandler)
    request = urllib.request.Request(url=url, method=method)
    try:
        with opener.open(request, timeout=timeout_sec) as response:
            return response.getcode(), "ok"
    except urllib.error.HTTPError as exc:
        return exc.code, f"http {exc.code}"
    except urllib.error.URLError as exc:
        return None, f"network error: {exc.reason}"


def _probe_json(url: str, method: str, timeout_sec: float) -> tuple[int | None, str, dict[str, Any] | None]:
    opener = urllib.request.build_opener(_NoRedirectHandler)
    request = urllib.request.Request(url=url, method=method)
    try:
        with opener.open(request, timeout=timeout_sec) as response:
            raw = response.read()
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            if not isinstance(payload, dict):
                payload = {}
            return response.getcode(), "ok", payload
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        payload: dict[str, Any] | None = None
        if raw:
            try:
                parsed = json.loads(raw.decode("utf-8"))
                if isinstance(parsed, dict):
                    payload = parsed
            except Exception:
                payload = None
        return exc.code, f"http {exc.code}", payload
    except urllib.error.URLError as exc:
        return None, f"network error: {exc.reason}", None


def _status_ok(code: int | None) -> bool:
    return code is not None


def _print_probe(name: str, url: str, method: str, timeout_sec: float) -> bool:
    code, detail = _probe(url, method, timeout_sec)
    ok = _status_ok(code)
    label = "OK" if ok else "FAIL"
    code_text = str(code) if code is not None else "-"
    print(f"[{label}] {name}: {method} {url} -> {code_text} ({detail})")
    return ok


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check basic Polygon Agent connectivity using the current base_url, "
            "registration URL, or saved state file."
        )
    )
    parser.add_argument("--base-url", help="Polygon base URL, for example http://localhost:8080")
    parser.add_argument(
        "--register-url",
        help="One-time registration URL. The script derives base_url from it but does not consume it.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        help="Path to a saved agent state JSON file containing base_url.",
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=5.0,
        help="HTTP probe timeout in seconds. Default: 5.0",
    )
    return parser


def _print_authorized_problems(payload: dict[str, Any]) -> None:
    items = payload.get("authorized_problems")
    if not isinstance(items, list) or not items:
        print("Authorized problems: none")
        return
    print("Authorized problems:")
    for item in items:
        if not isinstance(item, dict):
            continue
        problem = str(item.get("problem") or "")
        scope = str(item.get("scope") or "")
        expires_at = str(item.get("expires_at") or "")
        if expires_at:
            print(f"- {problem} [{scope}] expires {expires_at}")
        else:
            print(f"- {problem} [{scope}]")


def _check_session_status(base_url: str, state: dict[str, Any], timeout_sec: float) -> bool:
    session_id = str(state.get("agent_session_id") or "")
    identity_hash = str(state.get("identity_hash") or "")
    if not session_id or not identity_hash:
        return False
    query = urlencode({"agent_session_id": session_id, "identity_hash": identity_hash})
    url = f"{base_url}/agent/v1/auth/status?{query}"
    code, detail, payload = _probe_json(url, "GET", timeout_sec)
    ok = code == 200 and isinstance(payload, dict) and str(payload.get("status") or "") == "ok"
    label = "OK" if ok else "FAIL"
    code_text = str(code) if code is not None else "-"
    print(f"[{label}] session heartbeat: GET {url} -> {code_text} ({detail})")
    if isinstance(payload, dict):
        error_text = str(payload.get("error") or "")
        if error_text:
            print(f"Error: {error_text}")
        if ok:
            print(f"User: {payload.get('user')}")
            print(f"Server: {payload.get('server_name')}")
            print(f"Last seen: {payload.get('last_seen_at')}")
            _print_authorized_problems(payload)
    return ok


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    state: dict[str, Any] | None = None

    try:
        if args.base_url:
            base_url = _normalize_base_url(args.base_url)
        elif args.register_url:
            base_url = _base_url_from_register_url(args.register_url)
        elif args.state_file:
            state = _load_state_file(args.state_file)
            base_url = _base_url_from_state(state, args.state_file)
        else:
            parser.error("provide one of --base-url, --register-url, or --state-file")
            return 2
    except ValueError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2

    print(f"Base URL: {base_url}")
    if state is not None:
        print("State file provided. The script will use session heartbeat if session metadata is present.")
    else:
        print("This script only checks reachability. It does not consume the registration code.")
    print()

    if state is not None and _check_session_status(base_url, state, args.timeout_sec):
        print()
        print("[OK] Session heartbeat looks usable for polygon-agent-init.")
        return 0
    if state is not None:
        print()
        print("Session heartbeat was not available. Falling back to public reachability probes.")
        print()

    checks = [("login page", f"{base_url}/login", "GET"), ("agent sessions page", f"{base_url}/agent/sessions", "GET")]
    if args.register_url:
        print(f"Registration URL provided: {args.register_url}")
        print("The script will not send any request to the one-time registration endpoint.")
        print()

    results = [_print_probe(name, url, method, args.timeout_sec) for name, url, method in checks]
    if all(results):
        print()
        print("[OK] Connectivity looks usable for polygon-agent-init.")
        return 0

    print()
    print("[FAIL] At least one probe failed. Check base_url, network reachability, or TLS configuration.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
