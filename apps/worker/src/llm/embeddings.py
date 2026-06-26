"""Embeddings via HuggingFace Inference API — BGE-M3 (1024 dims). Opção D."""
import os
import logging
import httpx

log = logging.getLogger(__name__)

HF_API_KEY = os.environ.get("HF_API_KEY", "")
HF_EMBED_URL = os.environ.get("HF_EMBED_URL", "https://api-inference.huggingface.co/models/BAAI/bge-m3")
EMBED_DIM = 1024
TIMEOUT = 30.0

_headers = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}

async def embed_text(text: str) -> list[float]:
    if not text or not text.strip():
        return [0.0] * EMBED_DIM
    payload = {"inputs": text[:3000], "options": {"wait_for_model": True}}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(HF_EMBED_URL, json=payload, headers=_headers)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                vec = data[0] if isinstance(data[0], list) else data
            elif isinstance(data, dict) and "embeddings" in data:
                vec = data["embeddings"][0]
            else:
                vec = data
            if isinstance(vec, list) and len(vec) == EMBED_DIM:
                return vec
            log.warning(f"HF API dims inesperadas: {len(vec) if isinstance(vec, list) else type(vec)}")
            return [0.0] * EMBED_DIM
    except httpx.HTTPStatusError as e:
        log.error(f"HF API HTTP {e.response.status_code}: {e.response.text[:200]}")
        return [0.0] * EMBED_DIM
    except Exception as e:
        if "No address" in str(e) or "Name or service not known" in str(e):
            log.error(f"HF API: erro de DNS/resolução de nome — possível bloqueio de rede no Render Free")
        else:
            log.error(f"HF API falhou: {e}")
        return [0.0] * EMBED_DIM

async def embed_pillars() -> None:
    """Embeda descrições dos 6 pilares CISEB. Idempotente."""
    from db.supabase import get_supabase
    supabase = get_supabase()
    pillars = supabase.table("pillars").select("*").execute().data
    for p in pillars:
        if p.get("canonical_embedding"):
            log.info(f"pilar {p['slug']} já tem embedding — pulando")
            continue
        text = f"{p['name']}. {p['description']}"
        vec = await embed_text(text)
        if vec and any(v != 0.0 for v in vec):
            supabase.table("pillars").update({"canonical_embedding": vec}).eq("id", p["id"]).execute()
            log.info(f"[ok] pilar {p['slug']} embedado")
        else:
            log.error(f"falha ao embedar pilar {p['slug']} — vetor zero")
