# Memory CLI Reference

Full command reference for `mem` CLI. All commands require `uv run` from `~/Repos/claude-mem`.

---

## mem search

Full-text search across indexed sources using FTS5.

```bash
uv run mem search "query"
```

### Options

| Flag | Description | Example |
|------|-------------|---------|
| `--type TYPE` | Filter by source type | `--type claude_code` |
| `--project PATH` | Filter by project path | `--project .` (current dir) |
| `-n, --limit N` | Max results (default: 10) | `-n 20` |

### Source Types

- `claude_code` — Local Claude Code sessions (JSONL from `~/.claude/projects/`)
- `handoff` — Session handoff files (from `~/.claude/handoffs/`)
- `claude_ai` — Claude.ai conversations (synced via claude-data-sync)
- `cloud_session` — Claude Code web sessions

### Search Syntax

**Basic search:**
```bash
uv run mem search "entity resolution"
```

**Hyphenated terms:** Auto-quoted by CLI
```bash
uv run mem search "claude-memory"  # Works (auto-quoted internally)
```

**Exact phrase:**
```bash
uv run mem search '"extraction pipeline"'  # Explicit quoting
```

**What's indexed:**
- Extraction summaries (arc, learnings, patterns, builds, friction)
- Titles
- Source metadata (project_path, updated_at)

### Examples

```bash
# Search all sources
uv run mem search "JWT authentication"

# Current project only
uv run mem search "deployment" --project .

# Only handoffs
uv run mem search "phase 3" --type handoff

# More results
uv run mem search "MCP server" -n 25
```

---

## mem drill

View source details with progressive disclosure.

```bash
uv run mem drill <source_id>
```

### Modes

| Flag | What it shows |
|------|---------------|
| (none) | Extraction summary only (arc, learnings, builds, patterns) |
| `--outline` | Extraction + numbered turn index |
| `--turn N` | Specific turn in full |
| `--full` | All turns (truncated if large) |

### Progressive Disclosure Pattern

1. **Default:** Read extraction summary first
2. **If not enough:** Use `--outline` to see turn index
3. **If specific context needed:** Use `--turn N` for that turn

### Examples

```bash
# View extraction summary
uv run mem drill claude_code:28478c48-ba93-47ea-9741-e6cf1215e9e0

# See turn structure
uv run mem drill claude_code:28478c48 --outline

# Read turn 5 in full
uv run mem drill claude_code:28478c48 --turn 5

# Full conversation (if really needed)
uv run mem drill claude_code:28478c48 --full
```

---

## mem recent

Show recent activity, optionally filtered to current project.

```bash
uv run mem recent
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--all` | All sources (ignore project detection) | Project-filtered |
| `--days N` | Lookback period | 7 |
| `--type TYPE` | Filter by source type | All types |

### Project Detection

When run from a git repo, `mem recent` auto-detects the project and filters to matching sources. Uses path encoding: `/Users/jane/Repos/foo` → `-Users-jane-Repos-foo`.

Outside a git repo, defaults to all sources.

### Examples

```bash
# Current project's recent activity
uv run mem recent

# All sources, last 2 weeks
uv run mem recent --all --days 14

# Only handoffs from current project
uv run mem recent --type handoff
```

---

## mem status

Show database statistics and extraction coverage.

```bash
uv run mem status
```

### Output

- Total sources by type
- Extraction coverage (% with extractions)
- Last scan timestamp
- Database size

### When to Use

- Before searching, to verify database is populated
- After `mem scan` to confirm indexing worked
- Debugging "no results" issues

---

## mem scan

Index sources into the database. Run periodically to pick up new sessions.

```bash
uv run mem scan
```

### Options

| Flag | Description |
|------|-------------|
| `--source TYPE` | Only scan specific source type |
| `--quiet` | Minimal output |

### Source Types for Scan

- `claude_code` — `~/.claude/projects/**/*.jsonl`
- `handoffs` — `~/.claude/handoffs/**/*.md`
- `claude_ai` — `~/.claude/claude-ai/cache/conversations/`
- `cloud_sessions` — `~/.claude/claude-ai/cache/sessions/`

### Examples

```bash
# Full scan
uv run mem scan

# Just handoffs
uv run mem scan --source handoffs
```

---

## mem backfill

Run LLM extraction on sources without extractions.

```bash
uv run mem backfill
```

### Options

| Flag | Description |
|------|-------------|
| `--source-type TYPE` | Only backfill specific type |
| `--limit N` | Max sources to process |
| `--dry-run` | Show what would be processed |

### Prerequisites

- API key in `~/.claude/memory/env`
- Sources must be scanned first (`mem scan`)

### Examples

```bash
# Backfill all pending
uv run mem backfill

# Only handoffs
uv run mem backfill --source-type handoff

# Preview
uv run mem backfill --dry-run
```

---

## mem sync-fts

Update FTS index with extraction content. Run after backfill to make learnings searchable.

```bash
uv run mem sync-fts
```

### When to Use

After running `mem backfill`, extraction summaries need to be flattened into FTS. This command does that.

**The pipeline:**
```
mem scan → mem backfill → mem sync-fts
```

---

## mem list

List sources with optional filtering.

```bash
uv run mem list
```

### Options

| Flag | Description |
|------|-------------|
| `--type TYPE` | Filter by source type |
| `--limit N` | Max results |
| `--has-extraction` | Only sources with extractions |
| `--no-extraction` | Only sources without extractions |

---

## Common Patterns

### Full refresh
```bash
uv run mem scan && uv run mem backfill && uv run mem sync-fts
```

### Check coverage then search
```bash
uv run mem status
uv run mem search "topic"
```

### Triage → drill workflow
```bash
uv run mem search "authentication"
# Pick a result
uv run mem drill claude_code:abc123
# Need more detail on turn 7
uv run mem drill claude_code:abc123 --turn 7
```
