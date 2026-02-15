# claude-config

**Location:** `~/Repos/claude-config` (symlinked to `~/.claude`)

## What It Does

claude-config is "dotfiles for AI" — version-controlled configuration that shapes Claude Code's behavior across all sessions. It defines communication style, development workflows, security policies, and integrates custom capabilities through Skills and MCP servers. The repo distinguishes between tracked config (reusable across machines) and ephemeral session data (gitignored), making it portable and shareable.

## Key Files & Structure

```
claude-config/
├── CLAUDE.md           # Global behavioral instructions (21KB of preferences)
├── settings.json       # Base Claude Code settings, hooks, plugins
├── skills/             # On-demand workflow extensions
│   └── anthropic/      # Official Anthropic skills (git submodule)
├── hooks/              # Session lifecycle hooks
├── scripts/
│   ├── web-init.sh     # Bootstrap for Claude Code web sessions
│   └── setup-machine.sh # First-time machine setup
├── handoffs/           # Session handoff archives
├── memory/             # Session context and notes
└── rules/              # Additional behavioral rules
```

**Gitignored:** `history.jsonl`, `todos/`, `projects/`, `settings.local.json`, `plugins/`

## How It's Used

- **Installation:** Clone to `~/.claude` with `--recurse-submodules`
- **Machine setup:** Run `scripts/setup-machine.sh` for symlinks
- **Web sessions:** Use `$WEBINIT` env var pattern to curl `web-init.sh`
- **Skills:** Symlinked from external repos (todoist-gtd, arc, etc.)
- **MCP:** Configures mcp-google-workspace for Drive/Gmail access

## Notable Patterns

1. **Separation of concerns:** Tracked config vs. ephemeral state clearly distinguished via `.gitignore`
2. **Submodule strategy:** Official Anthropic skills included as git submodule for clean updates
3. **Environment-agnostic:** Same config works locally, on Sprites.dev VMs, and in ephemeral web sessions
4. **Philosophy codified:** "Elegance over speed," "side quests are work" — preferences documented in CLAUDE.md
