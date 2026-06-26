"""
Queries reutilizáveis para Supabase.
Centraliza operações comuns de banco para evitar duplicação nos coletores.
"""
from __future__ import annotations
from typing import Optional
from src.db.supabase import get_supabase


def ensure_source(slug: str, name: str, family: str, config: dict | None = None) -> str:
    """
    Garante que uma fonte existe na tabela sources.
    Retorna o source_id (cria se não existir).
    """
    supabase = get_supabase()
    result = supabase.table("sources").select("id").eq("slug", slug).execute()
    if result.data:
        return result.data[0]["id"]

    data = {
        "slug": slug,
        "name": name,
        "family": family,
        "config": config or {},
        "healthy": True,
    }
    result = supabase.table("sources").insert(data).execute()
    return result.data[0]["id"]


def finding_exists(content_hash: str) -> Optional[str]:
    """
    Verifica se um finding já existe pelo hash.
    Retorna o finding_id ou None.
    """
    supabase = get_supabase()
    result = supabase.table("findings").select("id").eq("content_hash", content_hash).execute()
    if result.data:
        return result.data[0]["id"]
    return None


def insert_finding(finding_data: dict) -> str:
    """
    Insere um finding na tabela findings.
    Retorna o finding_id.
    """
    supabase = get_supabase()
    result = supabase.table("findings").insert(finding_data).execute()
    return result.data[0]["id"]


def update_source_polled(slug: str) -> None:
    """Atualiza last_polled_at de uma fonte."""
    from datetime import datetime, timezone
    supabase = get_supabase()
    supabase.table("sources").update(
        {"last_polled_at": datetime.now(timezone.utc).isoformat()}
    ).eq("slug", slug).execute()
