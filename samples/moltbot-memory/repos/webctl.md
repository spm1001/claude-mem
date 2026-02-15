# webctl

**Location:** `~/Repos/webctl`

## What It Does

webctl is browser automation for AI agents via CLI, built on Playwright. Unlike MCP browser tools where the server controls context window usage, webctl puts the agent in control — filter output before it enters context, pipe through Unix tools, cache snapshots. The CLI talks to a persistent daemon over Unix socket; the browser stays open across commands with cookies persisting to disk.

## Key Files & Structure

```
webctl/
├── src/webctl/
│   ├── cli/            # Click-based command definitions
│   ├── daemon/         # Browser management server
│   │   └── server.py   # Playwright browser control
│   ├── protocol/       # JSON-RPC communication
│   ├── query/          # ARIA role-based element queries
│   ├── security/       # IPC authentication (SO_PEERCRED)
│   ├── views/          # Output formatters
│   ├── config.py       # Session/socket configuration
│   └── exceptions.py   # Error types
├── skills/             # Generated agent skills
└── pyproject.toml
```

**Architecture:** CLI (stateless) → Unix Socket (JSON-RPC) → Daemon (Playwright/Chromium)

## How It's Used

```bash
pip install webctl
webctl setup            # Downloads Chromium
webctl init             # Generate skills for all supported agents

# Core workflow
webctl start                              # Opens visible browser
webctl navigate "https://example.com"
webctl snapshot --interactive-only        # Only buttons, links, inputs
webctl click 'role=button name~="Submit"'
webctl type 'role=textbox' "query" --submit
webctl stop --daemon
```

**Filtering (CLI advantage over MCP):**
```bash
webctl snapshot --within "role=main"     # Skip nav/footer
webctl snapshot | grep -i "submit"       # Unix tools
```

**Multi-agent support:** `webctl init --agents claude,gemini`

## Notable Patterns

1. **CLI over MCP:** Agent controls what enters context — filter with flags, grep, jq. MCP servers dump everything.
2. **ARIA queries:** Semantic targeting (`role=button name~="Submit"`) survives CSS refactors
3. **Daemon architecture:** Browser persists across commands; session state (cookies) survives; daemon auto-starts
4. **Security:** Kernel-level IPC auth (SO_PEERCRED on Linux) prevents other users from hijacking sessions
5. **Agent-agnostic:** Generates skills/prompts for Claude, Goose, Gemini, Copilot, Codex
