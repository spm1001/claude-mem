"""LLM client for entity extraction and hybrid summarization."""

import json
import os
from typing import Any

import anthropic

# Default model for entity extraction (fast, cheap)
DEFAULT_MODEL = "claude-3-5-haiku-20241022"

# Model for hybrid extraction (quality matters — Haiku loses ~40%)
HYBRID_MODEL = "claude-sonnet-4-20250514"


def get_client() -> anthropic.Anthropic:
    """Get Anthropic client. Raises if no API key configured."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    # Also check ~/.claude/memory/env file
    if not api_key:
        env_file = os.path.expanduser("~/.claude/memory/env")
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if line.startswith("export ANTHROPIC_API_KEY="):
                        # Extract value, handling quotes
                        value = line.split("=", 1)[1].strip()
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        api_key = value
                        break

    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. "
            "Set it in your environment or ~/.claude/memory/env"
        )
    return anthropic.Anthropic(api_key=api_key)


EXTRACTION_PROMPT = """You are extracting named entities from a conversation or document.

<known_entities>
{glossary_sample}
</known_entities>

<content>
{content}
</content>

Extract entities in these categories:
- People: Named individuals (not roles like "the manager")
- Products: Named tools, systems, products
- Projects: Named initiatives, projects
- Organizations: Companies, teams, departments
- Concepts: Technical terms, methodologies (only if domain-specific)

For each entity, provide:
1. The exact mention text
2. Your confidence (high/medium/low)
3. Suggested canonical name (may match known entity)
4. Why you think this is an entity

{voice_note}

Output JSON:
{{
  "entities": [
    {{
      "mention": "GeoX",
      "confidence": "high",
      "suggested_canonical": "Region:Lift",
      "reasoning": "Appears to be alternative name for Region:Lift based on context"
    }}
  ]
}}

Be conservative. Better to miss an entity than hallucinate one."""


def format_glossary_sample(glossary: dict, max_entities: int = 20) -> str:
    """Format a sample of glossary entities for the prompt.

    Prioritizes entities with aliases (more useful for matching)
    and includes category structure.
    """
    lines = []
    count = 0

    # Flatten glossary categories
    for category, entities in glossary.items():
        if not isinstance(entities, dict):
            continue
        for name, details in entities.items():
            if count >= max_entities:
                break

            # Format: "Name (Category): description [aliases: a, b, c]"
            line = f"- {name} ({category})"
            if isinstance(details, dict):
                if details.get("description"):
                    line += f": {details['description']}"
                if details.get("aliases"):
                    aliases = ", ".join(details["aliases"])
                    line += f" [aliases: {aliases}]"
            lines.append(line)
            count += 1

        if count >= max_entities:
            break

    if not lines:
        return "(No known entities yet)"

    return "\n".join(lines)


def build_extraction_prompt(
    content: str,
    glossary: dict,
    is_voice: bool = False,
    max_content_chars: int = 50000
) -> str:
    """Build the entity extraction prompt."""
    sample = format_glossary_sample(glossary, max_entities=20)

    voice_note = ""
    if is_voice:
        voice_note = """Note: This is a voice-transcribed conversation. Expect transcription
errors (homophones, mishearings). Focus on entities that are clearly intentional
references despite any transcription artifacts."""

    # Truncate content if too long
    truncated = content[:max_content_chars]
    if len(content) > max_content_chars:
        truncated += f"\n\n[... truncated, {len(content) - max_content_chars} chars omitted ...]"

    return EXTRACTION_PROMPT.format(
        glossary_sample=sample,
        content=truncated,
        voice_note=voice_note
    )


def extract_entities(
    content: str,
    glossary: dict,
    is_voice: bool = False,
    model: str = DEFAULT_MODEL
) -> list[dict[str, Any]]:
    """Extract entities from content using LLM.

    Returns list of entity dicts with keys:
        - mention: str (exact text found)
        - confidence: str (high/medium/low)
        - suggested_canonical: str | None
        - reasoning: str

    Raises RuntimeError if API key not set or API call fails.
    """
    client = get_client()
    prompt = build_extraction_prompt(content, glossary, is_voice)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse JSON from response
    response_text = response.content[0].text

    # Try to find JSON in response (may have preamble)
    try:
        # Look for JSON object
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            result = json.loads(json_str)
            return result.get("entities", [])
    except json.JSONDecodeError:
        pass

    # If parsing fails, return empty (conservative)
    return []


def confidence_to_float(confidence: str) -> float:
    """Convert confidence string to float for storage."""
    return {
        "high": 0.9,
        "medium": 0.6,
        "low": 0.3
    }.get(confidence.lower(), 0.5)


# Hybrid extraction prompt - validated against 5 benchmark questions
HYBRID_EXTRACTION_PROMPT = """Extract a structured digest from this conversation.

<content>
{content}
</content>

Output JSON with these fields:

1. **summary**: 2-3 sentences — what happened and why it matters

2. **arc**: the journey
   - started_with: initial goal/problem
   - key_turns: array of pivots, discoveries, changes in direction
   - ended_at: final state

3. **builds**: array of things created or modified
   - what: the thing
   - details: context

4. **learnings**: array of insights discovered
   - insight: what was learned
   - why_it_matters: significance (not just "it's useful" — be specific)
   - context: how discovered

5. **friction**: array of problems encountered
   - problem: what was hard
   - resolution: how resolved (or "unresolved")

6. **patterns**: array of recurring themes, collaboration style, meta-observations

7. **open_threads**: array of unfinished business, deferred work

Focus on OUTCOMES and STORY, not just entities mentioned.
Return ONLY valid JSON, no markdown code blocks."""


def extract_hybrid(
    content: str,
    model: str = HYBRID_MODEL,
    max_content_chars: int = 140000,
) -> dict[str, Any]:
    """Extract structured digest from conversation using hybrid prompt.

    Returns dict with keys:
        - summary: str
        - arc: dict with started_with, key_turns, ended_at
        - builds: list of {what, details}
        - learnings: list of {insight, why_it_matters, context}
        - friction: list of {problem, resolution}
        - patterns: list of str
        - open_threads: list of str

    Raises RuntimeError if API key not set or API call fails.
    """
    client = get_client()

    # Truncate if needed (Sonnet context is ~200k tokens, ~150k chars safe)
    truncated = content[:max_content_chars]
    if len(content) > max_content_chars:
        truncated += f"\n\n[... truncated, {len(content) - max_content_chars} chars omitted ...]"

    prompt = HYBRID_EXTRACTION_PROMPT.format(content=truncated)

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    # Parse JSON from response
    try:
        # Look for JSON object
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response_text[start:end]
            result = json.loads(json_str)
            return result
    except json.JSONDecodeError:
        pass

    # Return empty structure if parsing fails
    return {
        "summary": None,
        "arc": None,
        "builds": [],
        "learnings": [],
        "friction": [],
        "patterns": [],
        "open_threads": [],
    }
