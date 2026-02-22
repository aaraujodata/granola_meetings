"""Claude API-powered meeting analysis: action items, tags, knowledge extraction."""

import json
import logging

log = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a meeting analyst. Extract structured information from meeting transcripts and summaries.

Return valid JSON only, no markdown fencing. Follow the exact schema requested."""

ACTION_ITEMS_PROMPT = """Analyze this meeting content and extract:
1. Action items with owner and task description
2. Key decisions made
3. People mentioned
4. Topic tags (lowercase, hyphenated, e.g. "data-engineering", "sprint-review")

Meeting Title: {title}

SUMMARY:
{summary}

TRANSCRIPT (partial):
{transcript}

Return JSON with this exact schema:
{{
  "action_items": [
    {{"owner": "Person Name", "task": "Description of what needs to be done", "due": null}}
  ],
  "key_decisions": ["Decision 1", "Decision 2"],
  "people_mentioned": ["Name1", "Name2"],
  "tags": ["tag-1", "tag-2", "tag-3"],
  "topics": ["Topic 1", "Topic 2"]
}}

If no action items or decisions are found, return empty arrays."""


def extract_meeting_intelligence(
    title: str,
    summary_text: str,
    transcript_text: str,
    api_key: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    max_transcript_chars: int = 8000,
) -> dict:
    """Extract action items, tags, and decisions from meeting content.

    Args:
        title: Meeting title.
        summary_text: AI-generated summary (markdown).
        transcript_text: Raw transcript (markdown, may be truncated).
        api_key: Anthropic API key (reads ANTHROPIC_API_KEY env var if None).
        model: Claude model to use.
        max_transcript_chars: Truncate transcript to this length.

    Returns dict with action_items, key_decisions, people_mentioned, tags, topics.
    """
    try:
        import anthropic
    except ImportError:
        log.error("anthropic package not installed. Run: pip install anthropic")
        return _empty_result()

    # Truncate transcript to stay within token budget
    truncated_transcript = transcript_text[:max_transcript_chars]
    if len(transcript_text) > max_transcript_chars:
        truncated_transcript += "\n\n[... transcript truncated ...]"

    prompt = ACTION_ITEMS_PROMPT.format(
        title=title,
        summary=summary_text or "(no summary available)",
        transcript=truncated_transcript or "(no transcript available)",
    )

    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model=model,
            max_tokens=2000,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response
        result = json.loads(response_text)
        return {
            "action_items": result.get("action_items", []),
            "key_decisions": result.get("key_decisions", []),
            "people_mentioned": result.get("people_mentioned", []),
            "tags": result.get("tags", []),
            "topics": result.get("topics", []),
        }

    except json.JSONDecodeError as e:
        log.error("Failed to parse Claude response as JSON: %s", e)
        return _empty_result()
    except Exception as e:
        log.error("Claude API error: %s", e)
        return _empty_result()


def _empty_result() -> dict:
    return {
        "action_items": [],
        "key_decisions": [],
        "people_mentioned": [],
        "tags": [],
        "topics": [],
    }
