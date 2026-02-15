# arc

**Location:** `~/Repos/arc`

## What It Does

Arc is a lightweight work tracker designed for Claude-human collaboration using GTD vocabulary. It organizes work as **Outcomes** (desired results) and **Actions** (concrete next steps), stored in a simple JSONL file. Built to solve drift in AI-assisted work: complex tasks need clear scope, checkpoints, and handoff-friendly documentation. Every item requires a "brief" (why/what/done) that forces clarity upfront.

## Key Files & Structure

```
arc/
├── src/arc/
│   ├── cli.py          # Main CLI commands (27KB)
│   ├── storage.py      # JSONL file operations
│   ├── display.py      # Output formatting (tree, JSON, JSONL)
│   ├── ids.py          # ID generation (arc-xxxxxx format)
│   └── queries.py      # Item filtering logic
├── skill/
│   └── SKILL.md        # Claude Code skill definition
├── tests/              # pytest tests
├── pyproject.toml      # uv/pip project config
└── ORCHESTRATION.md    # Patterns used to build arc with Claude
```

**Data storage:** `.arc/items.jsonl` in project root

## How It's Used

```bash
# Install
uv sync
uv run arc init

# Create outcome (desired result)
uv run arc new "Users can export data" \
  --why "Users requesting CSV exports" \
  --what "Export button, CSV generation" \
  --done "Can export any table to CSV"

# Add action under outcome
uv run arc new "Add export button" --for arc-abcdef \
  --why "Entry point" --what "Button in toolbar" --done "Button visible"

# Work with items
uv run arc list --ready    # What can I work on now?
uv run arc show arc-xyz    # View details
uv run arc done arc-xyz    # Mark complete
uv run arc wait arc-xyz "Waiting for review"
```

**Output formats:** `--json`, `--jsonl`, `--quiet` for scripting

## Notable Patterns

1. **Brief field requirement:** Every item needs why/what/done — forces upfront clarity, enables zero-context handoffs
2. **Draw-down/draw-up:** Skill teaches Claude to "draw down" arc items into TodoWrite checkpoints (pause points), and "draw up" by filing work with complete briefs
3. **Outcome vs Action:** Two-level hierarchy — outcomes are results, actions are steps. No deeper nesting.
4. **JSONL storage:** Human-readable, git-friendly, append-optimized
5. **Ready filter:** `--ready` shows only unblocked actions, answering "what can I work on now?"
