import json

from openai import AsyncOpenAI

from api.config import get_settings


def _default_client() -> AsyncOpenAI:
    """Construct the real OpenAI client from application settings.

    Called lazily from ``analyze_journal_entry`` so tests can inject a
    ``MockAsyncOpenAI`` without ever triggering this code path.
    """
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


async def analyze_journal_entry(
    entry_id: str,
    entry_text: str,
    client: AsyncOpenAI | None = None,
) -> dict:
    """Analyze a journal entry using an OpenAI-compatible LLM.

    Args:
        entry_id: ID of the entry being analyzed (pass through to the result).
        entry_text: Combined work + struggle + intention text.
        client: OpenAI client. If None, a default one is constructed from
            application settings. Tests pass in a MockAsyncOpenAI here; production code
            in the router calls this with no ``client`` argument.

    Returns:
        A dict matching AnalysisResponse:
            {
                "entry_id":  str,
                "sentiment": str,   # "positive" | "negative" | "neutral"
                "summary":   str,
                "topics":    list[str],
            }
    """
    if not client:
        client = _default_client()

    settings = get_settings()
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Analyze the user journal entry. Respond strictly in json.",
            },
            {"role": "user", "content": entry_text},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "sentiment_entry",
                "schema": {
                    "type": "object",
                    "properties": {
                        "entry_id": {"type": "string"},
                        "sentiment": {
                            "type": "string",
                            "enum": ["positive", "negative", "neutral"],
                        },
                        "summary": {"type": "string"},
                        "topics": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["entry_id", "sentiment", "summary", "topics"],
                    "additionalProperties": False,
                },
            },
        },
    )
    analysis = json.loads(response.choices[0].message.content or "")
    return {"entry_id": entry_id, **analysis}
