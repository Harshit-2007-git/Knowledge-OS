"""
LLM client — Groq (primary), Ollama (local fallback).

Switching provider: set LLM_PROVIDER in .env to "groq" or "ollama".
The RAGService calls GroqClient / OllamaClient through the same interface:
  - generate_chat(messages, model) -> str
  - generate_chat_stream(messages, model) -> AsyncGenerator[str, None]
"""

import json
import logging
from typing import AsyncGenerator

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# ── Groq client ───────────────────────────────────────────────────────────────

class GroqClient:
    """
    Async client for the Groq API (OpenAI-compatible).
    Uses httpx directly so we don't need the groq SDK — simpler dependency.
    """

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(
        self,
        api_key: str = settings.GROQ_API_KEY,
        default_model: str = settings.GROQ_MODEL,
    ):
        self.api_key = api_key
        self.default_model = default_model
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat request and return the full response string."""
        model = model or self.default_model
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error("Groq API error %s: %s", e.response.status_code, e.response.text)
            return f"[LLM Error: Groq returned {e.response.status_code}. Check your GROQ_API_KEY.]"
        except Exception as e:
            logger.error("Groq generation failed: %s", e)
            return f"[LLM Error: {e}]"

    async def generate_chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens from Groq via SSE."""
        model = model or self.default_model
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.BASE_URL}/chat/completions",
                    headers=self._headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        raw = line[len("data: "):]
                        if raw.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(raw)
                            delta = chunk["choices"][0].get("delta", {})
                            token = delta.get("content", "")
                            if token:
                                yield token
                        except (json.JSONDecodeError, KeyError):
                            continue
        except Exception as e:
            logger.error("Groq streaming failed: %s", e)
            yield f"[LLM Error: {e}]"


# ── Ollama client (local fallback) ────────────────────────────────────────────

class OllamaClient:
    """Client for local Ollama LLM — used when LLM_PROVIDER=ollama."""

    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL):
        self.base_url = base_url

    async def generate_chat(
        self,
        messages: list[dict],
        model: str = settings.OLLAMA_DEFAULT_MODEL,
        **kwargs,
    ) -> str:
        """Generate a complete chat response."""
        try:
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={"model": model, "messages": messages, "stream": False},
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception as e:
            logger.error("Ollama generation failed: %s", e)
            return f"[LLM Error: Could not reach Ollama at {self.base_url}. Is it running? Error: {e}]"

    async def generate_chat_stream(
        self,
        messages: list[dict],
        model: str = settings.OLLAMA_DEFAULT_MODEL,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming chat response."""
        try:
            async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json={"model": model, "messages": messages, "stream": True},
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield token
        except Exception as e:
            logger.error("Ollama streaming failed: %s", e)
            yield f"[LLM Error: Could not reach Ollama. Error: {e}]"


# ── Factory — picks the right client from config ──────────────────────────────

def get_llm_client() -> GroqClient | OllamaClient:
    """
    Return the configured LLM client.
    Set LLM_PROVIDER=groq (default) or LLM_PROVIDER=ollama in .env.
    """
    provider = settings.LLM_PROVIDER.lower()
    if provider == "groq":
        if not settings.GROQ_API_KEY:
            logger.warning("LLM_PROVIDER=groq but GROQ_API_KEY is empty — falling back to Ollama")
            return OllamaClient()
        return GroqClient()
    if provider == "ollama":
        return OllamaClient()
    logger.warning("Unknown LLM_PROVIDER '%s', defaulting to Groq", provider)
    return GroqClient()