# Field Report: Broken Provenance Chain for local_md Sources

**Date:** 2026-02-01
**Context:** User asked "tell me about GA4 injector" — memory found it, but couldn't trace to source
**Severity:** Medium (found content, but retrieval required manual forensics)

## What Happened

1. Searched `mem search "GA4"` — found `local_md:projects:ga4_injection.md`
2. Drilled into it — got good extraction summary
3. Tried to read source file at indexed path:
   ```
   /Users/modha/Repos/claude-memory-feature-test/_archive/memories_phase4_complete_20251008/projects/ga4_injection.md
   ```
4. **File doesn't exist** — the archive was cleaned up or moved
5. Had to run `mdfind "GA4 Injection"` to discover the *actual* canonical source is a Google Doc on MIT shared drive
6. Extracted doc ID from `.gdoc` file, fetched via mise

## The Gap

`local_md` sources index markdown exports, not canonical sources. When the export file is deleted/moved:
- Memory still has the extraction (useful)
- But the `path` field points to nothing
- No way to know the *original* source (Google Doc, Notion page, etc.)

The indexed markdown was a point-in-time export. The Google Doc is the living source. Memory indexed the shadow, not the thing.

## Impact

- **Search works** — found the right content
- **Extraction works** — summary was accurate and useful
- **Source retrieval broken** — had to do manual forensics:
  - mdfind to find actual files
  - Guess that it came from Google Drive
  - Extract doc ID from .gdoc pointer file
  - Fetch via mise

~5 minutes of detective work that should have been instant.

## Suggested Fixes

### 1. Capture canonical source URL/ID at index time

For `local_md` sources that originated from Google Drive:
```json
{
  "type": "local_md",
  "path": "/path/to/export.md",
  "canonical_source": {
    "type": "gdoc",
    "id": "19V5vfW4Wsm3zIFzFLuqa7SAoE2YvgZFu634VPx43W2w"
  }
}
```

### 2. Stale source detection

On `drill`, check if `path` exists. If not, warn:
```
⚠️  Source file no longer exists at indexed path.
    Extraction preserved. Original source unknown.
```

### 3. Google Drive as first-class source type

Instead of indexing markdown exports that rot:
- Index Google Docs directly via mise
- Store doc ID as the canonical reference
- Fetch fresh content on drill (or cache with TTL)

This inverts the dependency: memory points to the living doc, not a snapshot.

### 4. Shorter term: Re-index from Drive

For existing `local_md` sources from `_archive/`:
- Many originated from Google Drive exports
- Could bulk-match filenames to Drive files
- Backfill `canonical_source` metadata

## Related

- The `_archive` path suggests this was test data from memory development
- Production indexing should probably skip `_archive/` paths or flag them as potentially stale
