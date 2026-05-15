"""
LLM service abstraction — Ollama and OpenAI-compatible backends.

Provides a unified interface for:
- Sending prompts to local Ollama models
- Streaming responses via SSE
- Token management
- Retry handling

Full implementation in Phase 4–5.
"""

import logging
from typing import AsyncGenerator, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Unified LLM interface supporting Ollama and OpenAI-compatible APIs."""

    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        default_model: str = settings.OLLAMA_DEFAULT_MODEL,
        timeout: int = settings.OLLAMA_TIMEOUT,
    ):
        self.base_url = base_url
        self.default_model = default_model
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> dict:
        """
        Generate a complete response from the LLM.

        Returns dict with 'response', 'model', 'prompt_tokens', 'completion_tokens'.
        """
        model = model or self.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return {
            "response": data.get("response", ""),
            "model": model,
            "prompt_tokens": data.get("prompt_eval_count"),
            "completion_tokens": data.get("eval_count"),
        }

    async def generate_stream(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """
        Stream response tokens from the LLM.

        Yields individual token strings as they're generated.
        """
        model = model or self.default_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        chunk = json.loads(line)
                        token = chunk.get("response", "")
                        if token:
                            yield token
                        if chunk.get("done", False):
                            break

    async def health_check(self) -> bool:
        """Check if the LLM service is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
