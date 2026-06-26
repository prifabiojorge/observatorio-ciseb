"""Cliente DeepSeek — compatível com OpenAI SDK. Lazy init."""
import os
import logging
from openai import AsyncOpenAI

log = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY não configurada no ambiente")
        _client = AsyncOpenAI(
            api_key=api_key,
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            timeout=60.0,
        )
    return _client

_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

async def chat(system: str, user: str, temperature: float = 0.2, max_tokens: int = 800) -> str | None:
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature, max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.error(f"DeepSeek falhou: {e}")
        return None
