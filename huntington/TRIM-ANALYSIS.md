# HUNTINGTON-AGENT: what was trimmed, and what else could go

This fork follows a rule: **delete whole directories, gate everything else from one policy file**.
Upstream (NousResearch/hermes-agent) merged 823 commits in the weeks before this fork synced. A fork
that hand-edits hundreds of core files would conflict on nearly every sync. So:

- Self-contained trees are deleted and listed in `huntington/removed-paths.txt`.
  `scripts/huntington/sync-upstream.sh` deletes them again after each merge.
- Choices that core code has to respect (providers, terminal backends, TTS, image generation, web
  search, the CLI skin) live in `hermes_cli/huntington.py`, a file upstream never touches. Core
  files carry one-line hooks into it.

Sizes are from the tree at the time of the sync.

## Status

Done since this analysis was first written:
- **Off-stack and risky skills removed.** That's the off-stack integrations plus pinggy-tunnel,
  here-now, cloudflare-temporary-deploy, scrapling and obliteratus.
- **Repo weight cut.** Removed upstream's docs site (only `website/static/api/model-catalog.json`
  remains), contributor data, evals, the achievements and Google Meet plugins, and every language
  except English. The plugin catalog is now a curated in-repo list, and 19 consumer MCP servers are
  gone.
- **Company defaults set.** Nous guest mode and telemetry are off, and the toolsets listed in
  `DEFAULT_OFF_TOOLSETS` start off.
- **Microsoft 365 added** to the MCP catalog.
- **Fork CI and a weekly upstream-sync workflow** replace upstream's workflows.

Still open by choice: the ML-training (mlops) optional skills stay.

## 1. Already removed in this branch

| Removed | Size / scope | How |
|---|---|---|
| Electron desktop app (`apps/desktop`), its browser-hosted Webapp build, the Tauri GUI installer (`apps/bootstrap-installer`), desktop build/release scripts, desktop CI | ~58 MB, 10 workflows | deleted; `hermes desktop` / `hermes gui` / `hermes webapp` unregistered |
| Ink TUI (`ui-tui`, `scripts/build/tui.mjs`) | ~6 MB | deleted; `--tui` / `HERMES_TUI` fall back to the CLI with a notice; the dashboard chat pane hosts the classic CLI |
| Docker install (Dockerfile, compose files, `docker/`, image CI) | — | deleted |
| Nix install (`nix/`, `flake.*`, Nix CI) | ~0.5 MB | deleted |
| Upstream release publishing (stable/canary release workflows) | — | deleted; the fork has no release infrastructure |
| 24 messaging adapters (Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Mattermost, the Chinese platforms, SMS, iMessage/Photon, IRC, …) and their `hermes whatsapp` / `hermes slack` commands | ~4 MB, ~60k LOC | deleted; only Teams, email and A2A remain |
| Yuanbao tools | 0.4k LOC | deleted, toolsets removed |
| Cloud browser vendors (Browser Use, Browserbase, Firecrawl) | small | deleted; local Chromium is the only bundled browser |
| Six image-generation backends (FAL, Krea, xAI, OpenRouter, DeepInfra, Meta AI) | ~3k LOC | deleted; OpenAI only |
| README / CONTRIBUTING / SECURITY translations | ~1.3k lines | deleted |

**Gated rather than deleted** (the code stays so upstream merges stay clean, but nothing reaches it):

| Gate | Where |
|---|---|
| Provider pickers list only Anthropic, OpenAI (API + ChatGPT), MiniMax (API + OAuth), Moonshot/Kimi, Ollama Cloud, plus the "Ollama (local) or custom endpoint" row | `providers.unlisted_provider_names`, `models_catalog_static.listed_canonical_providers` |
| Built-in terminal backends other than `local` refuse to start | `tools/terminal_tool_backends._create_environment` |
| TTS resolves to Edge or Piper | `tools/tts_tool._get_provider` |
| Image generation resolves to OpenAI (API key, then ChatGPT sign-in) | `tools/image_generation_tool._plugin_provider_name` |
| Web search is off by default; only xAI, Brave, DuckDuckGo and Perplexity report available (the keyless Exa/Parallel/Firecrawl/Keenable ring is disabled) | `tools/web_tools._is_backend_available`, `plugins/web/keyless_mcp.use_keyless`, `_DEFAULT_OFF_TOOLSETS` |
| `hermes tools` hides Nous Portal subscription rows and unsupported TTS/search rows | `hermes_cli/tools_config_providers._visible_providers` |

## 2. Recommended next trims (safe: whole directories, no core edits)

| Candidate | Size | Why it can go | Notes |
|---|---|---|---|
| `optional-skills/` | 14 MB, 149 skills | Ships inactive until installed. Mostly creative, MLOps, blockchain, gaming and health | Keep any category you actually want, e.g. `security` |
| Bundled `skills/` categories `apple`, `creative`, `social-media`, `media/youtube` | ~2.5 MB | Each installed skill adds to every system prompt | Only `hermes-agent` is essential |
| `plugins/hermes-achievements` | 1.6 MB | Gamification dashboard | |
| `plugins/google_meet` | 156 KB | Meeting bot; pulls Playwright | Teams users rarely need it |
| `plugins/video_gen` | 112 KB | Video generation (FAL/xAI) | Already default-off |
| Unused `plugins/model-providers/*` (openrouter, nous, gemini, bedrock, vertex, deepseek, xai, zai, qwen, …) | ~400 KB | Already hidden from pickers | **Keep** `anthropic`, `minimax`, `kimi-coding`, `ollama-cloud`, `openai-codex`, `custom`. Deleting `openrouter`/`nous` needs a check that auxiliary-model "auto" routing still resolves |
| `contributors/` | 8.9 MB | Upstream attribution data | Used by upstream's contributor CI only |
| `evals/` | 4.3 MB | Upstream dev probes | |
| `locales/` except `en.yaml` | ~6.7 MB | i18n for 34 languages | Only if English-only is acceptable |
| `native/fts5_cjk` | 720 KB | CJK full-text search extension | Loaded optionally |
| `batch_runner.py`, `mini_swe_runner.py`, `trajectory_compressor.py`, `toolset_distributions.py` | ~2.4k LOC | RL / training-data tooling | Import only each other |
| `website/` | 30 MB | Upstream Docusaurus docs | Also publishes the plugin/model catalogs; replace with internal docs first |
| Remaining Nous CI workflows (`deploy-site`, `docs-search-monitor`, `skills-index*`, `live-providers`, …) | — | Need Nous secrets and runners (`blacksmith-*`), so they won't run on this fork | Replace with a small fork CI: lint + `scripts/run_tests.sh tests/hermes_cli tests/tools` |

## 3. Worth trimming, but each needs core edits (do these deliberately)

| Feature | Size | Coupling | Suggested approach |
|---|---|---|---|
| Desktop-only Python backend (`hermes_cli/main_desktop*.py`, `desktop_*`, `linux_desktop_entry.py`, `tui_gateway` desktop RPCs, Bot Mode) | ~10k LOC | `main.py` re-exports these as the "frozen updater surface" that `hermes update` resolves | Now inert, because nothing under `apps/desktop` exists. Remove together with the updater call sites in one PR, with `hermes update` E2E-tested |
| `tui_gateway/` (JSON-RPC backend) | 2.5 MB | Still the backend for the dashboard's sidebar widgets and ACP | Keep while the dashboard is kept |
| Web dashboard (`web/`, `hermes_cli/web_server*`, `web_routers/`) | ~3.4 MB frontend + large backend | Its chat pane now hosts the classic CLI | Decide whether Huntington wants a browser UI at all; if not, delete it and `hermes dashboard` |
| Kanban (multi-agent task board) | ~22k LOC | 93 core files reference it | Leave it default-off. Removing it costs the most and gains the least |
| Mixture of Agents (`moa`) | ~2.3k LOC | Wired into `agent_init`, `conversation_loop`, `turn_request_assembly` | Already hidden from the provider picker |
| Computer use + Bot Screen (VNC desktop) | ~6.5k LOC | `prompt_builder.py`, toolsets | Disable the toolset in config. A future VM backend may want it |
| Voice / STT / wake word | ~5k LOC + heavy extras (torch via KittenTTS, faster-whisper) | 18 core files | Don't install the `voice`/`stt-*`/`kittentts` extras; Edge and Piper cover TTS |
| Nous Portal connectors (`tools/connectors/`) | 6.5k LOC | Only active when signed in to Nous | Inert. Removable with a toolset edit |
| Docker / SSH / Modal / Daytona / Vercel terminal backends (`tools/environments/*`) | ~3.4k LOC | `docker.py` is imported by code execution, Bot Screen and kanban | Gated off. Delete after the VM backend exists and those imports are re-pointed |
| ACP editor server (`acp_adapter/`) | 6.6k LOC | Lazy imports from `model_tools.py` and the gateway | Keep if anyone uses editor integration (Zed, VS Code ACP) |
| `api_server` and webhook gateway platforms (`gateway/platforms/api_server*`, `webhook*`) | ~12k LOC | Core gateway | Integration endpoints, not chat apps. `msgraph_webhook` serves Teams. Kept |
| Discord/Feishu tool modules (`tools/discord_tool.py`, `tools/feishu_*`) | ~1k LOC | Toolset entries in `toolsets.py` | Their platforms are gone and the tools never load. Remove with the toolset entries |

## 4. Cheapest token savings (config only, no code)

Every core tool's schema is sent on every model call. For a lean default profile, put this in
`~/.hermes/config.yaml`:

```yaml
agent:
  disabled_toolsets: [image_gen, tts, computer_use, kanban, video_gen]  # add browser if unused
```

To start a profile without the bundled skills, use `hermes profile create <name> --no-skills`.
To measure the effect, use `hermes prompt-size`.

## 5. Follow-ups that need decisions or credentials

- **Huntington VM terminal backend**: build it as a terminal-environment plugin
  (`agent/terminal_env_registry`). Plugin backends bypass the built-in gate, so it needs no core edit.
- **Local image generation** and **Qwen TTS**: listed as planned. Add each as a plugin plus an
  allowlist entry in `hermes_cli/huntington.py`.
- **Icons**: `scripts/generate_icons.py` still renders upstream's mascot into the generated icon
  set. The CLI banner, README, dashboard favicon and `assets/huntington-logo.{svg,png}` use the
  Huntington mark. Replacing the generated icon set means swapping `assets/nous-girl-*.svg` for
  the Huntington SVG and adjusting the generator's geometry.
- **Moonshot sign-in**: upstream has no Kimi/Moonshot OAuth flow, so it is API-key only.
