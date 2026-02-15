# claude-suite

**Location:** `~/Repos/claude-suite`

## What It Does

claude-suite is a collection of behavioral skills that enhance Claude Code's capabilities. It provides session lifecycle management (startup context, handoffs between sessions), quality tools (multi-lens code review), and utility skills (diagrams, screenshots, filing). One install script symlinks everything into `~/.claude/skills/` and configures hooks for automatic session management.

## Key Files & Structure

```
claude-suite/
├── install.sh          # Installer: symlinks skills, configures hooks
├── skills/
│   ├── session-start/  # Shows time, handoffs, ready work on startup
│   ├── session-close/  # Creates handoff for next session (/close)
│   ├── titans/         # Three-lens code review (/titans, /review)
│   ├── diagram/        # Iterative diagram creation (/diagram)
│   ├── screenshot/     # Screen capture verification (/screenshot)
│   ├── filing/         # PARA-method file organization (/filing)
│   ├── picture/        # AI image generation (/picture)
│   ├── server-checkup/ # Linux server management
│   ├── github-cleanup/ # Stale fork auditing
│   ├── sprite/         # Sprites.dev VM management
│   └── beads/          # Issue tracking integration
├── hooks/              # Hook scripts for session lifecycle
└── references/         # Supporting documentation
```

## How It's Used

```bash
cd ~/Repos/claude-suite
./install.sh           # Creates symlinks to ~/.claude/skills/
./install.sh --verify  # Check installation
./install.sh --uninstall
```

**Commands after install:**
- `/open` — Resume context from previous session
- `/close` — Create handoff for next session
- `/titans` or `/review` — Three-lens code review (hindsight, craft, foresight)
- `/diagram` — Create diagrams with iterative render-and-check

**Updating:** Just `git pull` — symlinks automatically reflect changes.

## Notable Patterns

1. **Symlink architecture:** Skills live in the repo but are symlinked to `~/.claude/skills/`, enabling easy updates via git pull
2. **Session continuity:** Startup/close hooks solve Claude's "fresh session" problem by persisting context
3. **Three-lens review:** `/titans` applies hindsight (what went wrong before), craft (code quality), and foresight (future risks)
4. **Optional tools:** External repos (todoist-gtd, claude-mem) integrate as additional skills
