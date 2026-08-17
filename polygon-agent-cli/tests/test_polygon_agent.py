import argparse
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "polygon_agent.py"
_SPEC = importlib.util.spec_from_file_location("polygon_agent_cli", _SCRIPT)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load Polygon Agent CLI")
cli = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cli)


class TestPolygonAgentCLI(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_file = self.root / "state.json"
        self.state = {
            "base_url": "https://polygon.example",
            "agent_session_id": "as-session",
            "credential": "polygon_agent_" + "a" * 43,
            "identity": {"agent_name": "Codex"},
            "pending_access": {},
        }
        self.state_file.write_text(json.dumps(self.state), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_cli_has_no_problem_secret_or_contest_manifest_protocol(self) -> None:
        source = _SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("poly_", source)
        self.assertNotIn("X-Polygon-Agent-Identity-Hash", source)
        self.assertNotIn("X-Polygon-Agent-Session-ID", source)
        self.assertNotIn("checkout.json", source)
        self.assertNotIn("state_version", source)
        self.assertNotIn("schema_version", source)

    def _args(self, **values):
        return argparse.Namespace(
            state_file=str(self.state_file),
            secure=False,
            **values,
        )

    def test_status_removes_legacy_token_map_only_after_authentication(self) -> None:
        state = dict(self.state)
        state["tokens"] = {"alice/a": {"token": "legacy-secret"}}
        self.state_file.write_text(json.dumps(state), encoding="utf-8")
        with patch.object(
            cli,
            "_http_json",
            return_value={
                "user": "alice",
                "server_name": "Polygon Replica",
                "last_seen_at": "now",
                "general_scope": "none",
                "problem_grants": [],
            },
        ):
            result = cli._command_status(self._args())
        self.assertEqual(result["general_scope"], "none")
        saved = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertNotIn("tokens", saved)

        state["tokens"] = {"alice/a": {"token": "keep-for-diagnosis"}}
        self.state_file.write_text(json.dumps(state), encoding="utf-8")
        with patch.object(
            cli,
            "_http_json",
            side_effect=cli.CliError(
                code="agent_credential_invalid",
                message="invalid",
                http_status=401,
            ),
        ):
            with self.assertRaises(cli.CliError):
                cli._command_status(self._args())
        preserved = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertIn("tokens", preserved)

    def test_auth_uses_only_bearer_credential(self) -> None:
        headers = cli._auth_headers(cli._state_credentials(self.state))
        self.assertEqual(
            headers,
            {"Authorization": "Bearer polygon_agent_" + "a" * 43},
        )

    def test_old_identity_state_requires_explicit_reconnect(self) -> None:
        old_state = dict(self.state)
        old_state.pop("credential")
        old_state["identity_hash"] = "predictable-metadata-hash"

        with self.assertRaises(cli.CliError) as raised:
            cli._state_credentials(old_state)

        self.assertEqual(raised.exception.code, "agent_reconnect_required")

    def test_init_reconnects_existing_session_and_never_prints_credential(self) -> None:
        response_credential = "polygon_agent_" + "b" * 43
        request_body = None

        def register(**kwargs):
            nonlocal request_body
            request_body = json.loads(kwargs["body"].decode("utf-8"))
            return {
                "agent_session_id": "as-session",
                "credential": response_credential,
                "user": "alice",
                "server_name": "Polygon Replica",
            }

        with patch.object(cli, "_http_json", side_effect=register):
            result = cli._command_init(
                self._args(
                    register_url="https://polygon.example/agent/v1/register/reg-code",
                    agent_name=None,
                    desktop_id="desktop",
                    init_ts="2026-08-17T00:00:00Z",
                )
            )

        self.assertEqual(request_body["existing_session_id"], "as-session")
        self.assertNotIn("credential", result)
        self.assertNotIn("identity_hash", result)
        saved = json.loads(self.state_file.read_text(encoding="utf-8"))
        self.assertEqual(saved["credential"], response_credential)
        self.assertNotIn("identity_hash", saved)

    def test_init_new_session_does_not_send_existing_session_id(self) -> None:
        self.state_file.unlink()
        request_body = None

        def register(**kwargs):
            nonlocal request_body
            request_body = json.loads(kwargs["body"].decode("utf-8"))
            return {
                "agent_session_id": "as-new",
                "credential": "polygon_agent_" + "c" * 43,
                "user": "alice",
                "server_name": "Polygon Replica",
            }

        with patch.object(cli, "_http_json", side_effect=register):
            cli._command_init(
                self._args(
                    register_url="https://polygon.example/agent/v1/register/reg-code",
                    agent_name="Codex",
                    desktop_id="desktop",
                    init_ts="2026-08-17T00:00:00Z",
                )
            )

        self.assertNotIn("existing_session_id", request_body)

    def test_init_does_not_reconnect_legacy_identity_state(self) -> None:
        legacy_state = dict(self.state)
        legacy_state.pop("credential")
        legacy_state["identity_hash"] = "legacy-metadata-hash"
        self.state_file.write_text(json.dumps(legacy_state), encoding="utf-8")
        request_body = None

        def register(**kwargs):
            nonlocal request_body
            request_body = json.loads(kwargs["body"].decode("utf-8"))
            return {
                "agent_session_id": "as-replaced",
                "credential": "polygon_agent_" + "d" * 43,
                "user": "alice",
                "server_name": "Polygon Replica",
            }

        with patch.object(cli, "_http_json", side_effect=register):
            cli._command_init(
                self._args(
                    register_url="https://polygon.example/agent/v1/register/reg-code",
                    agent_name=None,
                    desktop_id="desktop",
                    init_ts="2026-08-17T00:00:00Z",
                )
            )

        self.assertNotIn("existing_session_id", request_body)

    def test_contest_layout_detects_relabel_before_download(self) -> None:
        target = self.root / "contest"
        old_path = target / "A"
        old_path.mkdir(parents=True)
        cli._git_run(old_path, ["init"])
        cli._git_config_set(old_path, "polygon-agent.problem", "alice/a")
        cli._git_config_set(old_path, "polygon-agent.contest", "summer")
        cli._git_config_set(old_path, "polygon-agent.contest-problem-id", "101")
        cli._git_config_set(old_path, "polygon-agent.contest-label", "A")

        conflicts = cli._contest_layout_conflicts(
            target_dir=target,
            contest_slug="summer",
            roster_problems=[
                {
                    "contest_problem_id": 101,
                    "idx": "B",
                    "problem": "alice/a",
                }
            ],
        )

        self.assertIn("problem_relabelled", {item["kind"] for item in conflicts})
        self.assertTrue(old_path.is_dir())
        self.assertFalse((target / "B").exists())

    def test_contest_roster_uses_idx_without_position(self) -> None:
        response = {
            "contest_id": 1,
            "contest_slug": "summer",
            "contest_title": "Summer",
            "source_generation": 7,
            "problem_count": 2,
            "problems": [
                {
                    "contest_problem_id": 101,
                    "idx": "A",
                    "problem": "alice/a",
                },
                {
                    "contest_problem_id": 102,
                    "idx": "B",
                    "problem": "alice/b",
                },
            ],
        }

        with patch.object(cli, "_http_json", return_value=response):
            roster = cli._fetch_contest_roster(
                base_url="https://polygon.example",
                credentials=cli.AgentCredentials(
                    credential="polygon_agent_" + "a" * 43,
                ),
                contest_slug="summer",
                verify_tls=True,
            )

        self.assertEqual(roster["problems"], response["problems"])
        self.assertNotIn("position", roster["problems"][0])

    def test_pull_contest_downloads_every_snapshot_before_local_changes(self) -> None:
        target = self.root / "summer"
        roster = {
            "contest_id": 1,
            "contest_slug": "summer",
            "contest_title": "Summer",
            "source_generation": 7,
            "problem_count": 2,
            "problems": [
                {
                    "contest_problem_id": 101,
                    "idx": "A",
                    "problem": "alice/a",
                },
                {
                    "contest_problem_id": 102,
                    "idx": "B",
                    "problem": "alice/b",
                },
            ],
        }
        fetch_count = 0

        def fetch_snapshot(**kwargs):
            nonlocal fetch_count
            fetch_count += 1
            if fetch_count == 2:
                raise cli.CliError(
                    code="contest_roster_changed",
                    message="changed",
                    http_status=409,
                )
            stage = kwargs["staging_parent"] / "snapshot"
            (stage / "config").mkdir(parents=True)
            (stage / "config" / "problem.json").write_text("{}\n", encoding="utf-8")
            return stage, {"remote_head_commit": "head-a", "remote_dirty": False}

        with (
            patch.object(cli, "_fetch_contest_roster", return_value=roster),
            patch.object(cli, "_fetch_snapshot_url", side_effect=fetch_snapshot),
        ):
            with self.assertRaisesRegex(cli.CliError, "changed"):
                cli._command_pull_contest(
                    self._args(contest="summer", target_dir=str(target))
                )
        self.assertEqual(fetch_count, 2)
        self.assertFalse(target.exists())

    def test_contest_snapshot_creates_independent_repo_config_without_manifest(self) -> None:
        stage = self.root / "stage"
        (stage / "config").mkdir(parents=True)
        (stage / "config" / "problem.json").write_text("{}\n", encoding="utf-8")
        target = self.root / "contest" / "A"
        item = {
            "contest_problem_id": 101,
            "idx": "A",
            "problem": "alice/a",
        }

        result = cli._apply_contest_snapshot(
            state=self.state,
            contest_slug="summer",
            item=item,
            stage_root=stage,
            transport_metadata={
                "remote_head_commit": "abc123",
                "remote_dirty": False,
            },
            target_dir=target,
        )

        self.assertTrue(result["created_repo"])
        self.assertTrue((target / ".git").is_dir())
        self.assertEqual(
            cli._git_config_get(target, "polygon-agent.problem"),
            "alice/a",
        )
        self.assertEqual(
            cli._git_config_get(target, "polygon-agent.contest"),
            "summer",
        )
        self.assertEqual(
            cli._git_config_get(target, "polygon-agent.contest-problem-id"),
            "101",
        )
        self.assertEqual(
            cli._git_config_get(target, "polygon-agent.contest-label"),
            "A",
        )
        self.assertFalse((self.root / "contest" / ".polygon" / "checkout.json").exists())


if __name__ == "__main__":
    unittest.main()
