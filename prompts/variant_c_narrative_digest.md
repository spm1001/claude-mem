# Prompt Variant C: Narrative Digest

Event-focused extraction that tells the story of what happened.

## Prompt

```
You are creating a digest of a conversation that captures what happened, not just what was mentioned.

<content>
{content}
</content>

Create a structured narrative digest:

## 1. SUMMARY (2-3 sentences)
What was this conversation about? What was the goal?

## 2. ARC
The journey of the conversation:
- **Started with**: Initial problem, question, or goal
- **Key turns**: Pivots, discoveries, or changes in direction
- **Ended at**: Final state, resolution, or stopping point

## 3. BREAKTHROUGHS
Moments of discovery or insight (if any):
- What was realized or figured out
- Why it matters
- What enabled it (debugging, research, experimentation)

## 4. FRICTION
What was hard or didn't work:
- Problems encountered
- Dead ends explored
- Workarounds needed

## 5. PATTERNS
Recurring themes or notable behaviors:
- Collaboration patterns (who drove what)
- Tool/approach preferences
- Decision-making style

## 6. OPEN THREADS
Unfinished business:
- Questions raised but not answered
- Work deferred for later
- Dependencies on external factors

{voice_note}

Output JSON:
{{
  "summary": "Built a session-end hook for automatic entity extraction. Debugged terminal corruption issues. Landed on full daemonization approach.",
  "arc": {{
    "started_with": "Need to wire hook extraction output into database",
    "key_turns": [
      "Discovered CLAUDE_CONFIG_DIR isolates auth tokens",
      "Pivoted from config isolation to daemonization approach"
    ],
    "ended_at": "Working hook that calls mem process on session end"
  }},
  "breakthroughs": [
    {{
      "insight": "Full daemonization (nohup + disown + redirect) prevents terminal corruption",
      "why_it_matters": "Enables background processing without affecting user's terminal",
      "how_discovered": "Debugging after research brief identified three root causes"
    }}
  ],
  "friction": [
    {{
      "problem": "CLAUDE_CONFIG_DIR looked promising but isolated auth",
      "dead_end": true,
      "time_spent": "significant"
    }}
  ],
  "patterns": [
    "Research brief → deep investigation → synthesis pattern worked well",
    "Asking 'what could go wrong?' surfaced issues earlier"
  ],
  "open_threads": [
    "Session pollution (extraction sessions in Resume picker) - accepted for now",
    "Subscription vs API option not yet implemented"
  ]
}}

Focus on the STORY of the conversation, not just facts. What would someone need to know to continue this work?
```

## Design Rationale

**Why narrative over entities?**
Some benchmark questions need the arc, not just nouns:
- Q1 (improve /open /close) → patterns[], friction[], what works/doesn't
- Q3 (TIL blog posts) → breakthroughs[] with context
- Q4 (interaction differences) → patterns[] across source types

**Trade-offs:**
- More interpretive = more variability between extractions
- Story-focused = harder to aggregate across sessions
- Open threads explicitly capture handoff context

**Hypothesis:**
Variant C might excel at Q3 (TIL posts) and Q1 (ritual improvement) because it captures the *why* and *how*, not just the *what*.

May struggle with:
- Q5 (skill usage patterns) - needs quantitative aggregation
- Cross-session queries that need consistent structure

## Key Difference from Variant B

| Variant B | Variant C |
|-----------|-----------|
| Facts: what was decided, built, learned | Story: how we got there |
| Structured categories | Narrative arc |
| Easier to aggregate | Richer context per session |
| "What" focused | "How" and "why" focused |
