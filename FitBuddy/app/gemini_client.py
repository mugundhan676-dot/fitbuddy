from __future__ import annotations

from functools import lru_cache

from google import genai
from google.genai import types

from .config import settings


@lru_cache
def get_client():
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Add it to .env or set MOCK_AI=true for local testing."
        )
    return genai.Client(api_key=settings.gemini_api_key)


def generate_structured(*, model: str, prompt: str, response_schema, temperature: float = 0.7):
    client = get_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return response_schema.model_validate_json(response.text)


def generate_text(*, model: str, prompt: str, temperature: float = 0.5) -> str:
    client = get_client()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return response.text.strip()
