# Huntington CLI Reference

Live sources when anything looks stale: `huntington --help`, `hermes <command> --help`,
https://hermes-agent.nousresearch.com/docs/reference/cli-commands

### Global Flags

```
hermes [flags] [command]        (no subcommand = interactive chat)

  --version, -V             Show version
  -z, --oneshot PROMPT      One-shot: print ONLY the final response (for scripts/pipes)
  -m MODEL  --provider P    Model/provider override for this invocation
  -t, --toolsets LIST       Comma-separated toolsets for this invocation
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --tui / --cli             Force the Ink TUI / classic REPL
  --ignore-rules            Skip AGENTS.md/SOUL.md/memory/skill injection
  --safe-mode               Disable ALL customizations (troubleshooting)
  --pass-session-id         Include session ID in system prompt
```

### Chat

```
huntington chat [flags]
  -q, --query TEXT          Single query, non-interactive
  --image PATH              Attach a local image to a single query
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --max-turns N             Cap tool-calling iterations
  --source TAG              Session source tag (default: cli)
```
(plus the global flags above)

### Configuration

```
huntington setup [section]      Wizard (model|tts|terminal|gateway|tools|agent)
huntington model                Interactive model/provider picker
huntington fallback [add|remove|list]  Fallback provider chain
huntington config [show|edit|get|set|unset|path|env-path|check|migrate]
huntington login / logout       OAuth sign-in / clear stored auth
huntington doctor [--fix]       Check dependencies and config
huntington status [--full]      Component summary (--full: every section)
```

### Tools & Skills

```
huntington tools [list|enable NAME|disable NAME]   Per-platform toolsets (curses UI with no args)

huntington skills list|browse|search QUERY|inspect ID
huntington skills install ID    Hub identifier OR a direct https://…/SKILL.md URL
huntington skills config        Enable/disable skills per platform
huntington skills check|update|uninstall|publish PATH
huntington skills tap add REPO  Add a GitHub repo as a skill source
huntington bundles              Skill bundles (one /<name> alias loads several skills)
```

### MCP Servers

```
huntington mcp add NAME (--url or --command) | remove | list | test NAME
huntington mcp catalog | install NAME     Curated catalog install
huntington mcp configure NAME             Toggle tool selection
huntington mcp-serve                      Run Huntington as an MCP server (mcp-serve plugin)
```
Details (transport, tool discovery, catalog): `references/native-mcp.md`.

### Gateway (Messaging Platforms)

```
huntington gateway run|install|start|stop|restart|status|setup
```

20+ platforms: Telegram, Discord, Slack, WhatsApp (Baileys + Business Cloud API), iMessage (Photon — `huntington photon setup`), Signal, Email, SMS, Matrix, Mattermost, Teams, LINE, SimpleX, ntfy, Google Chat, Home Assistant, DingTalk, Feishu, WeCom, Weixin, API Server, Webhooks. Open WebUI connects via the API Server adapter. Most adapters ship under `plugins/platforms/`.
Docs: https://hermes-agent.nousresearch.com/docs/user-guide/messaging/

### Sessions

```
huntington sessions list|browse|rename ID TITLE|delete ID|export OUT|prune|stats
```

### Cron / Webhooks

```
huntington cron list|create SCHED|edit ID|pause|resume|run ID|remove|status
    Schedules: '30m', 'every 2h', '0 9 * * *', ISO timestamp
huntington webhook subscribe NAME|list|remove NAME|test NAME
```
Webhook payloads/routes: `references/webhooks.md`.

### Profiles

```
huntington profile list|create NAME (--clone|--clone-all|--clone-from)|use|show|delete
huntington profile rename A B | alias NAME | export NAME | import FILE
huntington profile migrate-identity A B   Retry a completed rename's session/routing identity migration
```

### Credentials & Pools

```
huntington auth                 Interactive credential manager
huntington auth add [PROVIDER]  Add OAuth or API-key credential (nous, openai-codex, qwen-oauth, …)
huntington auth list|remove P IDX|reset PROVIDER|status
```
Multiple credentials per provider form a pool that rotates automatically and skips exhausted keys.

### Other

```
huntington desktop / gui        Native desktop app
huntington dashboard            Web admin panel + embedded chat (--stop / --status)
huntington proxy                OpenAI-compatible local proxy backed by an OAuth provider
huntington portal               Quick setup / sign in via HIP Portal
huntington kanban <verb>        Multi-agent work-queue board
huntington project              Named multi-folder workspaces (see references/projects-and-folders.md)
huntington skin list|use|set    Switch/tweak skins (see references/themes.md)
huntington pets <verb>          Pet mascots (see references/petdex.md)
huntington memory setup|status|off|reset   Memory provider
huntington secrets bitwarden|onepassword   External secret stores
huntington moa                  Mixture-of-Agents slots
huntington hooks / security / backup / import / checkpoints / console
huntington logs [-f] [errors]   View agent/error logs
huntington send                 One-off message through a gateway platform
huntington pairing / plugins / insights / journey / computer-use
huntington acp                  ACP server (IDE integration)
huntington completion bash|zsh|fish
huntington update / uninstall
```

Plugin- and provider-supplied subcommands (e.g. `huntington photon setup`) only appear once their plugin is installed/active. Importing from OpenClaw, Claude Code, Codex CLI or Cursor (`huntington import-agent <agent>`, plus the older `huntington claw migrate|cleanup`) comes from the `agent-importers` plugin; a fresh `huntington setup` that finds one of those agents offers to install it.

### Where to Find Things

| Looking for... | Location |
|---|---|
| Config options | `huntington config edit` · [Configuration docs](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Tools / toolsets | `huntington tools list` · [Tools reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Skills catalog | `huntington skills browse` · [Skills catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Provider setup | `huntington model` · [Providers guide](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Env variables | `huntington config env-path` · [Env vars reference](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) |
| Gateway logs | `~/.huntington/logs/gateway.log` (or `huntington logs`) |
| Sessions | `huntington sessions browse` (reads state.db) |
