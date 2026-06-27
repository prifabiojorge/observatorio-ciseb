"""Embeddings via HuggingFace Inference API — BGE-M3 (1024 dims). Opção D.

Fase 7 fix (auditoria Harness 2026-06-27): HF API mudou e o parâmetro
'options' passou a causar erro 400 'SentenceSimilarityPipeline.__call__()
missing'. Corrigido removendo 'options' do payload e usando header
'X-Wait-For-Model: true' em vez disso.

Adicionado:
- Retry com backoff exponencial (3 tentativas)
- Fallback para vetor zero apenas após esgotar retries
- Log estruturado para Sentry rastrear falhas
- Validação de dimensão antes de salvar (evita corromper pilares)
"""
import asyncio
import os
import logging
import httpx

log = logging.getLogger(__name__)

HF_API_KEY = os.environ.get("HF_API_KEY", "")
HF_EMBED_URL = os.environ.get(
    "HF_EMBED_URL",
    "https://router.huggingface.co/hf-inference/models/BAAI/bge-m3",
)
EMBED_DIM = 1024
TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_BACKOFF = [2, 5, 10]  # segundos entre tentativas

_headers = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}


async def embed_text(text: str) -> list[float]:
    """
    Gera embedding BGE-M3 (1024 dims) via HuggingFace Inference API.

    Fase 7 fix: usa header 'X-Wait-For-Model' em vez de 'options.wait_for_model'
    no payload (API mudou em 2026 e 'options' causa erro 400).

    Args:
        text: Texto para embedar (truncado em 3000 chars).

    Returns:
        Lista de 1024 floats. Retorna vetor zero SOMENTE após esgotar retries.
    """
    if not text or not text.strip():
        return [0.0] * EMBED_DIM

    # Fase 7 fix: payload sem 'options' (causava erro 400)
    # X-Wait-For-Model header substitui a funcionalidade
    payload = {"inputs": text[:3000]}
    headers = {**_headers, "X-Wait-For-Model": "true"}

    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(HF_EMBED_URL, json=payload, headers=headers)

                # 503 = modelo carregando, retry após backoff
                if response.status_code == 503:
                    log.warning(
                        f"HF API 503 (modelo carregando), tentativa {attempt + 1}/{MAX_RETRIES}"
                    )
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(RETRY_BACKOFF[attempt])
                        continue

                response.raise_for_status()
                data = response.json()

                # HF API retorna formatos diferentes dependendo do modelo
                vec = _extract_vector(data)
                if isinstance(vec, list) and len(vec) == EMBED_DIM:
                    return vec

                log.warning(
                    f"HF API dims inesperadas: "
                    f"esperado={EMBED_DIM}, recebido={len(vec) if isinstance(vec, list) else type(vec)}"
                )
                # Não retornar vetor inválido — tentar de novo
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_BACKOFF[attempt])
                    continue

        except httpx.HTTPStatusError as e:
            last_error = e
            log.error(
                f"HF API HTTP {e.response.status_code} (tentativa {attempt + 1}/{MAX_RETRIES}): "
                f"{e.response.text[:200]}"
            )
            # 4xx (exceto 429) não vale a pena retry — erro de payload/auth
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                break
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_BACKOFF[attempt])
                continue

        except Exception as e:
            last_error = e
            if "No address" in str(e) or "Name or service not known" in str(e):
                log.error(
                    "HF API: erro de DNS/resolução de nome — possível bloqueio de rede no Render Free"
                )
                break  # DNS não resolve com retry
            log.error(f"HF API falhou (tentativa {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_BACKOFF[attempt])
                continue

    # Esgotou retries — capturar no Sentry e retornar vetor zero
    try:
        from sentry_init import capture_exception
        capture_exception(
            last_error or RuntimeError("HF API falhou após retries"),
            tags={"component": "embeddings", "model": "bge-m3"},
        )
    except ImportError:
        pass

    log.error(f"HF API esgotou {MAX_RETRIES} tentativas — retornando vetor zero")
    return [0.0] * EMBED_DIM


def _extract_vector(data) -> list[float] | None:
    """
    Extrai vetor de embedding de diferentes formatos de resposta da HF API.

    Formatos suportados:
    - [[0.1, 0.2, ...]] (lista de listas — padrão BGE-M3)
    - [0.1, 0.2, ...] (lista direta)
    - {"embeddings": [[0.1, ...]]} (formato alternativo)
    - {"data": [{"embedding": [0.1, ...]}]} (formato OpenAI-compatible)
    """
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], list):
            return data[0]  # [[...]] → pegar primeiro
        if isinstance(data[0], (int, float)):
            return data  # [...] direto
    if isinstance(data, dict):
        if "embeddings" in data and isinstance(data["embeddings"], list):
            return data["embeddings"][0]
        if "data" in data and isinstance(data["data"], list) and data["data"]:
            return data["data"][0].get("embedding")
    return None


async def embed_pillars() -> None:
    """
    Embeda descrições dos 6 pilares CISEB. Idempotente.

    Fase 7 fix: se embed_text retornar vetor zero, NÃO salva no banco
    (antes salvava, corrompendo o pilar). Agora loga erro e segue.
    """
    from db.supabase import get_supabase
    supabase = get_supabase()
    pillars = supabase.table("pillars").select("*").execute().data

    for p in pillars:
        if p.get("canonical_embedding"):
            log.info(f"pilar {p['slug']} já tem embedding — pulando")
            continue

        text = f"{p['name']}. {p['description']}"
        vec = await embed_text(text)

        # Fase 7 fix: validar que vetor não é zero antes de salvar
        if vec and any(v != 0.0 for v in vec):
            supabase.table("pillars").update(
                {"canonical_embedding": vec}
            ).eq("id", p["id"]).execute()
            log.info(f"[ok] pilar {p['slug']} embedado")
        else:
            log.error(
                f"falha ao embedar pilar {p['slug']} — vetor zero (NÃO salvo, tentará próxima rodada)"
            )
            # Capturar no Sentry para diagnóstico
            try:
                from sentry_init import capture_exception
                capture_exception(
                    RuntimeError(f"Pilar {p['slug']} ficou sem embedding"),
                    tags={"component": "embed_pillars", "pillar": p["slug"]},
                )
            except ImportError:
                pass
