# Prompt Variant B: Entities + Outcomes

Extends entity extraction to also capture decisions, builds, learnings, and friction points.

## Prompt

```
You are analyzing a conversation to extract both entities and outcomes.

<known_entities>
{glossary_sample}
</known_entities>

<content>
{content}
</content>

Extract TWO types of information:

## 1. ENTITIES
Named things mentioned in the conversation:
- People: Named individuals
- Products: Tools, systems, products
- Projects: Named initiatives
- Organizations: Companies, teams
- Concepts: Domain-specific technical terms

## 2. OUTCOMES
What happened in this conversation:
- Decisions: Choices made, approaches selected (include WHY)
- Builds: Things created, implemented, or modified
- Learnings: Discoveries, insights, "aha" moments
- Friction: Problems encountered, things that were hard, blockers

{voice_note}

Output JSON:
{{
  "entities": [
    {{
      "mention": "Claude Code",
      "confidence": "high",
      "suggested_canonical": "Claude Code",
      "category": "product"
    }}
  ],
  "outcomes": {{
    "decisions": [
      {{
        "what": "Use Haiku for extraction instead of Sonnet",
        "why": "Cost savings, extraction is structured enough for smaller model",
        "confidence": "high"
      }}
    ],
    "builds": [
      {{
        "what": "SessionEnd hook for automatic entity extraction",
        "details": "Triggers on /exit, runs mem process in background"
      }}
    ],
    "learnings": [
      {{
        "insight": "CLAUDE_CONFIG_DIR isolates auth tokens too",
        "context": "Discovered while debugging hook authentication"
      }}
    ],
    "friction": [
      {{
        "problem": "Hook subprocess corrupted terminal output",
        "resolution": "Full daemonization (nohup + disown) fixed it"
      }}
    ]
  }}
}}

Be thorough on outcomes - these power questions like "what did we learn?" and "what was hard?"
Be conservative on entities - better to miss than hallucinate.
```

## Design Rationale

**Why add outcomes?**
User's benchmark questions require more than entities:
- Q1 (improve /open /close) → needs friction points, learnings
- Q2 (big builds and learnings) → needs builds, learnings
- Q3 (TIL blog posts) → needs learnings, decisions with "why"
- Q4 (Claude.ai vs Code differences) → needs patterns across sessions
- Q5 (skill improvements) → needs friction, usage patterns

**Trade-offs:**
- More output = more tokens = higher cost
- More structured fields = easier to query/aggregate
- Might increase hallucination risk on outcomes (harder to verify than entities)

## Evaluation Criteria

For the 5 benchmark questions, variant B should excel at:
- Q2: "big builds" directly captured in builds[]
- Q3: "TIL posts" from learnings[] + decisions[].why
- Friction points give material for Q1 (ritual improvements)

May underperform on:
- Q4: Interaction patterns not explicitly captured (need cross-session aggregation)
- Q5: Skill usage patterns (already in metadata, but context missing)
