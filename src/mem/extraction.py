"""Entity extraction from sources.

Extracts entities using LLM, matches against glossary, and queues unknowns.
"""

from dataclasses import dataclass
from typing import Any

from .database import Database
from .glossary import Glossary
from .llm import extract_entities, confidence_to_float


@dataclass
class ExtractionResult:
    """Result of extracting entities from a source."""
    source_id: str
    entities_found: int
    matched: int      # Matched existing glossary entity
    pending: int      # Queued for resolution
    entities: list[dict]


def extract_from_source(
    source_id: str,
    full_text: str,
    glossary: Glossary,
    db: Database,
    is_voice: bool = False,
) -> ExtractionResult:
    """Extract entities from source content.

    Args:
        source_id: The source identifier
        full_text: Full text content to extract from
        glossary: Loaded glossary for matching
        db: Database connection
        is_voice: Whether this is voice-transcribed content

    Returns:
        ExtractionResult with counts and entity details
    """
    # Extract entities via LLM
    entities = extract_entities(full_text, glossary.raw, is_voice=is_voice)

    matched = 0
    pending = 0

    for entity in entities:
        mention = entity['mention']
        confidence = confidence_to_float(entity.get('confidence', 'medium'))
        suggested = entity.get('suggested_canonical')

        # Try to match against glossary
        resolved = glossary.resolve(mention)

        if resolved:
            # Known entity - store as resolved
            db.add_source_entity(
                source_id=source_id,
                entity_id=resolved,
                mention_text=mention,
                confidence=confidence,
            )
            matched += 1
        elif suggested:
            # Has suggestion - check if suggestion is known
            resolved_suggestion = glossary.resolve(suggested)
            if resolved_suggestion:
                db.add_source_entity(
                    source_id=source_id,
                    entity_id=resolved_suggestion,
                    mention_text=mention,
                    confidence=confidence,
                )
                matched += 1
            else:
                # Suggested entity not in glossary - queue for review
                db.queue_pending_entity(
                    mention_text=mention,
                    source_id=source_id,
                    suggested_entity=suggested,
                    confidence=confidence,
                )
                pending += 1
        else:
            # Completely unknown - queue for review
            db.queue_pending_entity(
                mention_text=mention,
                source_id=source_id,
                suggested_entity=None,
                confidence=confidence,
            )
            pending += 1

    return ExtractionResult(
        source_id=source_id,
        entities_found=len(entities),
        matched=matched,
        pending=pending,
        entities=entities,
    )


def get_source_content(source_id: str, db: Database, config: dict) -> tuple[str, bool]:
    """Load full text content for a source.

    Returns:
        Tuple of (full_text, is_voice)
    """
    source = db.get_source(source_id)
    if not source:
        raise ValueError(f"Source not found: {source_id}")

    source_type = source['source_type']
    path = source['path']
    is_voice = source.get('input_mode') == 'voice'

    from pathlib import Path

    if source_type == 'claude_code':
        from .adapters.claude_code import ClaudeCodeSource
        conv = ClaudeCodeSource.from_file(Path(path))
        return conv.full_text(), is_voice

    elif source_type == 'claude_ai':
        from .adapters.claude_ai import ClaudeAISource
        # Virtual path format: claude_ai:{uuid}
        if path.startswith('claude_ai:'):
            uuid = path.split(':', 1)[1]
            base_path = config.get('sources', {}).get('claude_ai', {}).get(
                'path', '~/.claude/claude-ai/cache/conversations'
            )
            actual_path = Path(base_path).expanduser() / f"{uuid}.json"
        else:
            actual_path = Path(path)
        conv = ClaudeAISource.from_file(actual_path)
        return conv.full_text(), is_voice

    elif source_type == 'cloud_session':
        from .adapters.cloud_sessions import CloudSessionSource
        conv = CloudSessionSource.from_file(Path(path))
        return conv.full_text(), is_voice

    elif source_type == 'handoff':
        from .adapters.handoffs import HandoffSource
        handoff = HandoffSource.from_file(Path(path))
        return handoff.full_text(), False

    else:
        raise ValueError(f"Unknown source type: {source_type}")
