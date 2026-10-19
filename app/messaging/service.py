import asyncio
import json
import logging
from functools import lru_cache

import openai

from app import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a real-time message rephraser. Improve the clarity and
politeness of the user's message.

1. Correct spelling and grammar.
2. Give up to three concise alternative suggestions.
3. Return ONLY a JSON array of strings, with no headers or extra text.
4. If you run out of tokens, return fewer suggestions rather than an incomplete sentence.
"""


@lru_cache
def _client() -> openai.OpenAI:
    return openai.OpenAI(api_key=config.OPENAI_API_KEY)


async def rephrase(message: str) -> list[str]:
    """Return rephrased suggestions without blocking the event loop."""
    return await asyncio.to_thread(_rephrase_sync, message)


def _rephrase_sync(message: str) -> list[str]:
    response = _client().chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        max_tokens=50,
    )
    content = response.choices[0].message.content or ""
    return _complete_sentences(_parse_suggestions(content))


def _parse_suggestions(content: str) -> list[str]:
    """Parse a JSON array of strings, repairing a reply cut off by max_tokens."""
    body = content.strip().strip("[]")
    if not body.endswith('"'):
        body += '"'
    try:
        suggestions = json.loads(f"[{body}]")
    except json.JSONDecodeError:
        logger.warning("Could not parse model output: %r", content)
        return []
    return [s for s in suggestions if isinstance(s, str)]


def _complete_sentences(sentences: list[str]) -> list[str]:
    return [s for s in sentences if s.endswith((".", "!", "?"))]
