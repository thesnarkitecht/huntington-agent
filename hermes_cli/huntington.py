"""HUNTINGTON-AGENT fork policy: branding, supported providers, supported terminal backends.

Every fork-specific decision that core code consults lives here, in a file upstream
(NousResearch/hermes-agent) never touches, so `scripts/huntington/sync-upstream.sh` merges new
upstream features without conflicts in this policy. Core files carry only one-line hooks into it.
"""
from __future__ import annotations

PRODUCT_NAME = "HUNTINGTON-AGENT"
PRODUCT_TAGLINE = "HUNTINGTON-AGENT - AI assistant with tool-calling capabilities"

# Provider slugs the pickers (`hermes model`, `hermes setup`, `/model`, dashboard) offer.
# Each vendor keeps both of its upstream auth routes where upstream has them:
#   Anthropic  - API key, or sign in with a Claude subscription (Claude Code credentials)
#   OpenAI     - API key (openai-api), or sign in with ChatGPT (openai-codex)
#   MiniMax    - API key (minimax), or sign in through the browser (minimax-oauth)
#   Moonshot   - API key (kimi-coding: api.moonshot.ai / api.kimi.com); upstream has no sign-in flow
#   Ollama     - Ollama Cloud API key (ollama-cloud); a local Ollama server is the picker's
#                "Ollama (local) or custom endpoint" row (the `custom` provider, no key needed)
SUPPORTED_PROVIDERS: frozenset[str] = frozenset({
    "anthropic",
    "openai-api", "openai-codex",
    "minimax", "minimax-oauth",
    "kimi-coding",
    "ollama-cloud",
})


def provider_supported(name: str) -> bool:
    """True when *name* (a canonical provider slug) is one this fork offers."""
    return (name or "").strip().lower() in SUPPORTED_PROVIDERS


# Built-in terminal backends `terminal.backend` may name. "local" runs commands on this machine.
# Upstream's docker/ssh/modal/daytona/vercel_sandbox are refused. Plugin backends
# (agent/terminal_env_registry) are not gated here: the Huntington VM service ships as one.
SUPPORTED_TERMINAL_BACKENDS: frozenset[str] = frozenset({"local"})


def terminal_backend_supported(name: str) -> bool:
    return (name or "").strip().lower() in SUPPORTED_TERMINAL_BACKENDS


# Image generation: OpenAI only, by API key (`openai` plugin) or ChatGPT sign-in (`openai-codex`
# plugin), tried in this order when `image_gen.provider` is unset. Local image generation is
# planned for later.
IMAGE_GEN_PROVIDERS: tuple[str, ...] = ("openai", "openai-codex")

# Text-to-speech: Microsoft Edge TTS (free, the default) and Piper (local). Any other
# `tts.provider` value speaks through Edge. Qwen TTS is planned for later.
TTS_PROVIDERS: tuple[str, ...] = ("edge", "piper")

# Web search: off by default for new installs (`hermes tools` opts in). The only backends are xAI,
# Brave Search, DuckDuckGo (ddgs) and Perplexity; any other configured or keyless backend is
# reported unavailable.
WEB_SEARCH_BACKENDS: frozenset[str] = frozenset({"xai", "brave-free", "ddgs", "perplexity"})


def tool_row_supported(row: dict) -> bool:
    """Whether a `hermes tools` / `hermes setup` provider row is offered. Nous Portal subscription
    rows are hidden (the Nous Portal is not a supported provider), and so are TTS, image and web
    rows outside their allowlists."""
    if row.get("managed_nous_feature") or row.get("requires_nous_auth"):
        return False
    tts = row.get("tts_provider")
    if tts and tts not in TTS_PROVIDERS:
        return False
    image = row.get("image_gen_plugin_name")
    if image and image not in IMAGE_GEN_PROVIDERS:
        return False
    web = row.get("web_backend") or row.get("web_search_backend")
    return not web or web in WEB_SEARCH_BACKENDS


# CLI skin: upstream's "default" skin restyled in the Huntington brand (the mark's #50291B brown,
# lifted to readable tans on dark terminals). Applied by hermes_cli/skin_engine.py at import.
_BANNER_LOGO = """[bold #E2B48A]██╗  ██╗██╗   ██╗███╗   ██╗████████╗██╗███╗   ██╗ ██████╗████████╗ ██████╗ ███╗   ██╗       █████╗  ██████╗ ███████╗███╗   ██╗████████╗[/]
[bold #E2B48A]██║  ██║██║   ██║████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝╚══██╔══╝██╔═══██╗████╗  ██║      ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝[/]
[#C8915F]███████║██║   ██║██╔██╗ ██║   ██║   ██║██╔██╗ ██║██║  ███╗  ██║   ██║   ██║██╔██╗ ██║█████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║[/]
[#C8915F]██╔══██║██║   ██║██║╚██╗██║   ██║   ██║██║╚██╗██║██║   ██║  ██║   ██║   ██║██║╚██╗██║╚════╝██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║[/]
[#A86F45]██║  ██║╚██████╔╝██║ ╚████║   ██║   ██║██║ ╚████║╚██████╔╝  ██║   ╚██████╔╝██║ ╚████║      ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║[/]
[#A86F45]╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝      ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝[/]"""

_BANNER_HERO = """[#E2B48A]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#E2B48A]⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⣿⣿⡇⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#E2B48A]⠀⠀⠀⠀⠀⠀⠀⣠⣾⣿⡿⠛⣿⣿⡇⠀⢸⣷⣄⠀⠀⠀⠀⠀⠀⠀[/]
[#E2B48A]⠀⠀⠀⠀⠀⣠⣾⣿⡿⠋⠀⠀⣿⣿⠀⠀⢸⣿⣿⣷⣄⠀⠀⠀⠀⠀[/]
[#E2B48A]⠀⠀⠀⣠⣾⣿⡿⠋⠀⠀⠀⠀⣿⣿⠀⠀⢸⣿⣿⢿⣿⣷⣄⠀⠀⠀[/]
[#E2B48A]⠀⢀⣾⣿⡿⠋⠀⢀⣴⡇⠀⠀⣿⣿⠀⠀⢸⣿⣿⠀⠙⢿⣿⣷⡀⠀[/]
[#C8915F]⢀⣾⣿⡟⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⢻⣿⣷⡀[/]
[#C8915F]⣸⣿⡿⠀⠀⠀⠀⣿⣿⣷⣶⣶⣶⣶⣶⣶⣾⣿⣿⠀⠀⠀⠀⢻⣿⣧[/]
[#C8915F]⣿⣿⡇⠀⠀⠀⠀⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠀⠀⠀⠀⢸⣿⣿[/]
[#C8915F]⣿⣿⡇⠀⠀⠀⠀⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⠀⠀⠀⠀⢸⣿⣿[/]
[#C8915F]⢻⣿⣷⠀⠀⠀⠀⣿⣿⡿⠿⠿⠿⠿⠿⠿⢿⣿⣿⠀⠀⠀⠀⣼⣿⡟[/]
[#C8915F]⠈⢿⣿⣧⠀⠀⠀⣿⣿⡇⠀⠀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⣼⣿⡿⠁[/]
[#A86F45]⠀⠈⢿⣿⣷⣄⠀⣿⣿⡇⠀⠀⣿⣿⠀⠀⢸⠟⠁⠀⣠⣾⣿⡿⠁⠀[/]
[#A86F45]⠀⠀⠀⠙⢿⣿⣷⣿⣿⡇⠀⠀⣿⣿⠀⠀⠀⠀⣠⣾⣿⡿⠋⠀⠀⠀[/]
[#A86F45]⠀⠀⠀⠀⠀⠙⢿⣿⣿⡇⠀⠀⣿⣿⠀⠀⣠⣾⣿⡿⠋⠀⠀⠀⠀⠀[/]
[#A86F45]⠀⠀⠀⠀⠀⠀⠀⠙⢿⡇⠀⠀⣿⣿⣥⣾⣿⡿⠋⠀⠀⠀⠀⠀⠀⠀[/]
[#A86F45]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⣿⣿⣿⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]
[#A86F45]⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[/]"""

DEFAULT_SKIN_OVERRIDES: dict = {
    "description": "HUNTINGTON-AGENT - brand browns",
    "banner_logo": _BANNER_LOGO,
    "banner_hero": _BANNER_HERO,
    "branding": {
        "agent_name": PRODUCT_NAME,
        "welcome": f"Welcome to {PRODUCT_NAME}! Type your message or /help for commands.",
        "goodbye": "Goodbye!", "response_label": " ◆ HUNTINGTON ", "prompt_symbol": "❯",
        "help_header": "(◆) Available Commands"},
}
DEFAULT_SKIN_COLORS: dict = {
    "banner_border": "#A86F45", "banner_title": "#E2B48A", "banner_accent": "#C8915F",
    "banner_dim": "#8A6A55", "banner_text": "#F3E6D8", "ui_accent": "#C8915F", "ui_label": "#D2A47A",
    "prompt": "#F3E6D8", "input_rule": "#A86F45", "response_border": "#C8915F",
    "status_bar_strong": "#E2B48A", "status_bar_dim": "#8A6A55", "session_label": "#D2A47A"}
DEFAULT_SKIN_LIGHT_COLORS: dict = {
    "banner_border": "#7A4A2E", "banner_title": "#50291B", "banner_accent": "#7A4A2E",
    "banner_dim": "#8A6A55", "banner_text": "#3B2014", "ui_accent": "#7A4A2E", "ui_label": "#6B3F27",
    "prompt": "#3B2014", "response_border": "#50291B", "status_bar_strong": "#50291B",
    "session_label": "#6B3F27"}


def apply_default_skin(skins: dict) -> None:
    """Restyle upstream's built-in ``default`` skin in place (called once from skin_engine)."""
    default = skins["default"]
    default.update(DEFAULT_SKIN_OVERRIDES)
    default["colors"] = {**default.get("colors", {}), **DEFAULT_SKIN_COLORS}
    default["light_colors"] = {**default.get("light_colors", {}), **DEFAULT_SKIN_LIGHT_COLORS}


BANNER_LOGO_WIDTH = 135


# Plugin catalog: only the curated in-tree list (plugin-catalog/), never upstream's live catalog.
LIVE_PLUGIN_CATALOG = False


# Company defaults for new installs (`huntington tools` can still switch any of these on):
# web search is opt-in, and desktop control, Nous-hosted connectors, video analysis and the
# removed Discord platform's tools start off.
DEFAULT_OFF_TOOLSETS: frozenset[str] = frozenset({
    "web", "computer_use", "connections", "video", "discord", "discord_admin",
})

# Config defaults this build changes (deep-merged into upstream's DEFAULT_CONFIG at import).
CONFIG_DEFAULT_OVERRIDES: dict = {
    # Never provision a free Nous Portal identity or send inference there.
    "nous": {"guest": False},
    # Telemetry stays off and points nowhere upstream.
    "telemetry": {"shared_metrics": {"enabled": False, "send": False}},
}


def apply_config_defaults(defaults: dict) -> None:
    """Deep-merge CONFIG_DEFAULT_OVERRIDES into upstream's DEFAULT_CONFIG (called by config_defaults)."""
    def merge(into: dict, update: dict) -> None:
        for key, value in update.items():
            if isinstance(value, dict) and isinstance(into.get(key), dict):
                merge(into[key], value)
            else:
                into[key] = value
    merge(defaults, CONFIG_DEFAULT_OVERRIDES)


# The Nous Portal (upstream's hosted subscription) is not a supported provider: `setup --portal`
# and `huntington portal` refuse with this instead of signing in.
PORTAL_UNAVAILABLE = ("The hosted portal is not available in HUNTINGTON-AGENT. "
                      "Pick a supported provider with `huntington model`.")
