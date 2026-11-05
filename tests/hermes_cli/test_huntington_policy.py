"""HUNTINGTON-AGENT fork policy: what each gate in hermes_cli/huntington.py lets through.

Behaviour contracts against the real modules and a temp HERMES_HOME (the autouse fixture), so an
upstream merge that bypasses a gate fails here instead of silently widening the product.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_provider_picker_offers_only_the_supported_vendors():
    from hermes_cli.main_provider_setup import _build_provider_picker_rows

    rows, _ = _build_provider_picker_rows({}, "", {}, {})
    keys = [key for key, _label, _members in rows]
    members = {m for _key, _label, group in rows for m in group}
    offered = {k for k in keys if not k.startswith("group:")} | members
    assert offered - {"custom", "reasoning", "aux-config", "cancel"} == {
        "anthropic", "openai-api", "openai-codex", "minimax", "minimax-oauth", "kimi-coding",
        "ollama-cloud"}
    assert "llamacpp" not in keys and "openrouter" not in keys and "nous" not in keys


def test_listed_canonical_providers_hide_unsupported_slugs_but_resolution_keeps_them():
    from hermes_cli.models_catalog_static import listed_canonical_providers
    from providers import get_provider_profile

    listed = {p.slug for p in listed_canonical_providers()}
    assert "openrouter" not in listed and "anthropic" in listed
    # Hidden, not deleted: an existing config naming another provider still resolves.
    assert get_provider_profile("openrouter") is not None


def test_tui_requests_fall_back_to_the_classic_cli(monkeypatch, capsys):
    from hermes_cli.main_tui_launch import _resolve_use_tui

    monkeypatch.setenv("HERMES_TUI", "1")
    assert _resolve_use_tui(argparse.Namespace(tui=True, cli=False)) is False
    assert "TUI is not included" in capsys.readouterr().err


@pytest.mark.parametrize("backend", ["docker", "ssh", "modal", "daytona", "vercel_sandbox"])
def test_builtin_terminal_backends_other_than_local_are_refused(backend):
    from tools.terminal_tool_backends import _create_environment

    with pytest.raises(ValueError, match="not available in HUNTINGTON-AGENT"):
        _create_environment(backend, image="", cwd="/tmp", timeout=5)


def test_terminal_setup_offers_only_local():
    from hermes_cli.huntington import terminal_backend_supported
    from hermes_cli.setup_terminal import _BUILTIN_TERMINAL_BACKENDS

    assert [b for b, _ in _BUILTIN_TERMINAL_BACKENDS if terminal_backend_supported(b)] == ["local"]


@pytest.mark.parametrize("configured, spoken", [
    ("", "edge"), ("edge", "edge"), ("piper", "piper"), ("elevenlabs", "edge"), ("openai", "edge"),
])
def test_tts_speaks_through_edge_or_piper(configured, spoken):
    from tools.tts_tool import _get_provider

    assert _get_provider({"provider": configured}) == spoken


@pytest.mark.parametrize("configured, expected", [
    ("", "openai"), ("openai", "openai"), ("openai-codex", "openai-codex"), ("fal", "openai"),
])
def test_image_generation_routes_to_openai(monkeypatch, configured, expected):
    import tools.image_generation_tool as igt

    monkeypatch.setattr(igt, "_read_configured_image_provider", lambda: configured or None)
    assert igt._plugin_provider_name() == expected


def test_web_search_backends_outside_the_allowlist_are_unavailable(monkeypatch):
    from tools.web_tools import _is_backend_available

    monkeypatch.setenv("EXA_API_KEY", "k")
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "k")
    assert not _is_backend_available("exa")
    assert not _is_backend_available("tavily")
    assert _is_backend_available("brave-free")


def test_keyless_free_tier_ring_is_disabled():
    from plugins.web.keyless_mcp import use_keyless

    assert not any(use_keyless(v, "") for v in ("exa", "parallel", "firecrawl", "keenable"))


def test_web_search_is_off_by_default_for_new_installs():
    from hermes_cli.tools_config import _DEFAULT_OFF_TOOLSETS

    assert "web" in _DEFAULT_OFF_TOOLSETS


def test_tools_setup_rows_match_the_policy():
    from hermes_cli.tools_config import TOOL_CATEGORIES
    from hermes_cli.tools_config_providers import _visible_providers

    def names(cat):
        return {r["name"] for r in _visible_providers(TOOL_CATEGORIES[cat], {})}

    assert names("tts") == {"Microsoft Edge TTS", "Piper"}
    assert {r.get("image_gen_plugin_name") for r in _visible_providers(TOOL_CATEGORIES["image_gen"], {})} == {
        "openai", "openai-codex"}
    assert {r.get("web_backend") for r in _visible_providers(TOOL_CATEGORIES["web"], {})} == {
        "xai", "brave-free", "ddgs", "perplexity"}
    assert not any("Nous" in n for cat in ("tts", "image_gen", "web") for n in names(cat))


def test_only_teams_email_and_a2a_platform_plugins_ship():
    shipped = {p.name for p in (ROOT / "plugins" / "platforms").iterdir()
               if p.is_dir() and not p.name.startswith("__")}
    assert shipped == {"teams", "email", "a2a"}


def test_removed_paths_are_absent_from_the_tree():
    lines = [line.strip() for line in (ROOT / "huntington" / "removed-paths.txt").read_text().splitlines()]
    kept = {line[1:] for line in lines if line.startswith("!")}
    patterns = [line for line in lines if line and not line.startswith(("#", "!"))]
    present = sorted({path.relative_to(ROOT).as_posix() for pattern in patterns for path in ROOT.glob(pattern)}
                     - kept)
    assert present == [], "run scripts/huntington/sync-upstream.sh --apply"
    assert all((ROOT / path).exists() for path in kept), "a `!` keep line names a missing path"


def test_cli_banner_and_help_carry_the_product_name():
    from hermes_cli._parser import build_top_level_parser
    from hermes_cli.skin_engine import load_skin

    parser = build_top_level_parser()
    parser = parser[0] if isinstance(parser, tuple) else parser
    assert parser.description.startswith("HUNTINGTON-AGENT")

    skin = load_skin("default")
    assert skin.branding["agent_name"] == "HUNTINGTON-AGENT"
    assert "██╗  ██╗██╗   ██╗███╗   ██╗" in skin.banner_logo


def test_auto_provider_resolution_skips_unsupported_credentials(monkeypatch):
    from hermes_cli import auth

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setenv("GEMINI_API_KEY", "g-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-" + "x" * 40)
    assert auth.resolve_provider("auto") == "anthropic"


def test_explicit_provider_choice_is_still_honoured():
    from hermes_cli import auth

    assert auth.resolve_provider("openrouter") == "openrouter"


def test_only_huntington_commands_reach_path_directories():
    from hermes_cli._launchers import ENTRY_POINTS, PUBLIC_LAUNCHERS

    assert PUBLIC_LAUNCHERS == ("huntington", "huntington-acp")
    assert ENTRY_POINTS["huntington"] == ("hermes_cli.main", "main")
    assert ENTRY_POINTS["huntington-acp"] == ("acp_adapter.entry", "main")


def test_service_identities_do_not_collide_with_an_upstream_hermes_install():
    """A shared `hermes-gateway` unit made each install adopt the other's gateway (profile_mismatch)."""
    from hermes_cli import gateway
    from hermes_cli.gateway_launchd import get_launchd_label

    assert gateway._SERVICE_BASE == "huntington-gateway"
    assert get_launchd_label().startswith("ai.huntington.gateway")


def test_huntington_env_spelling_sets_the_engine_variable_unless_already_set():
    from hermes_constants import apply_huntington_env_aliases

    env = {"HUNTINGTON_HOME": "/srv/h", "HUNTINGTON_TUI": "0", "HERMES_TUI": "1"}
    apply_huntington_env_aliases(env)
    assert env["HERMES_HOME"] == "/srv/h" and env["HERMES_TUI"] == "1"


@pytest.mark.parametrize("command", [
    "huntington gateway restart", "systemctl --user restart huntington-gateway",
    "launchctl kickstart -k gui/501/ai.huntington.gateway", "pkill -f 'huntington gateway'",
])
def test_cron_lifecycle_guard_blocks_huntington_gateway_restarts(command):
    from cron.lifecycle_guard import contains_gateway_lifecycle_command

    assert contains_gateway_lifecycle_command(command)


def test_agent_terminal_prefers_this_checkouts_launchers(tmp_path, monkeypatch):
    """An upstream `hermes` earlier on PATH must not serve this install's child processes."""
    from tools.environments import local

    own_bin = ROOT / ".huntington" / "bin"
    if not (own_bin / "huntington").is_file():
        pytest.skip("checkout launchers are not minted in this environment")
    monkeypatch.setattr(local, "_HERMES_BIN_DIR", local._SENTINEL)
    monkeypatch.setattr("pm.environments.payload_command_dir", lambda root: None)
    assert local._prepend_hermes_bin_dir(f"{tmp_path}:/usr/bin").split(":")[0] == str(own_bin)


def test_hosted_portal_commands_refuse(capsys):
    import argparse
    from hermes_cli.portal_cli import portal_command

    assert portal_command(argparse.Namespace(portal_command="info")) == 1
    assert "not available in HUNTINGTON-AGENT" in capsys.readouterr().err


@pytest.mark.parametrize("command", [
    r"type C:\Users\ann\AppData\Local\huntington\.env", "pkill -f huntington",
])
def test_approval_layer_flags_huntington_secrets_and_self_kill(command):
    from tools.approval_detection import detect_dangerous_command

    assert detect_dangerous_command(command)[0]


def test_serve_unit_validator_accepts_huntington_units():
    from hermes_cli.update_restart_recovery import _UNIT_RE

    assert _UNIT_RE.fullmatch("huntington-serve.service") and _UNIT_RE.fullmatch("huntington-dashboard-ops.service")


def test_profile_alias_wrappers_start_huntington_and_are_recognised(tmp_path, monkeypatch):
    from hermes_cli import profiles

    monkeypatch.setattr(profiles, "_get_wrapper_dir", lambda: tmp_path)
    monkeypatch.setattr(profiles, "_wrapper_path", lambda name: tmp_path / name)
    wrapper = profiles.create_wrapper_script("ops")
    assert wrapper is not None and "huntington" in wrapper.read_text() and " -p ops" in wrapper.read_text()
    assert profiles._is_our_wrapper(wrapper)
    assert profiles.build_alias_map().get("ops") == "ops"


def test_command_hints_built_from_fstrings_name_huntington():
    """f"hermes {selector}auth add ..." hints are user-facing; `hermes` is not on a user's PATH."""
    from agent.turn_failure_copy import oauth_relogin_command

    assert oauth_relogin_command("openai-codex").startswith("huntington ")
