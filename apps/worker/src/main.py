"""
Observatório CISEB — Worker Principal.
Fase 2: Orquestrador de coleta — executa os 6 coletores e persiste no Supabase.

Execução: python src/main.py  (ou via api.py: POST /run)
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

# Carrega .env da raiz (3 níveis acima de src/)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

# ─── Imports internos ────────────────────────────────────
from src.collectors.base import RawFinding
from src.collectors.web_rss import WebRSSCollector
from src.collectors.github import GitHubCollector
from src.collectors.youtube import YouTubeCollector
from src.collectors.scholar import ScholarCollector
from src.collectors.forums import ForumsCollector
from src.collectors.events import EventsCollector
from src.db.supabase import get_supabase
from src.db.queries import ensure_source, finding_exists, insert_finding, update_source_polled
from src.utils.hashing import content_hash
from src.utils.text import clean, snippet

# ─── Constantes ──────────────────────────────────────────
ALL_COLLECTORS = [
    WebRSSCollector(),
    GitHubCollector(),
    YouTubeCollector(),
    ScholarCollector(),
    ForumsCollector(),
    EventsCollector(),
]


# ─── Pipeline ────────────────────────────────────────────

async def process_finding(finding: RawFinding) -> Optional[str]:
    """
    Processa um RawFinding: hash → dedup → ensure_source → insert.
    Retorna o finding_id ou None se duplicado.
    """
    supabase = get_supabase()
    
    # 1. Gerar hash de deduplicação
    text_for_hash = finding.raw_text or finding.title
    hash_val = content_hash(finding.source_url, finding.title, text_for_hash)
    
    # 2. Verificar duplicata
    existing = finding_exists(hash_val)
    if existing:
        return None  # duplicado, pular silenciosamente
    
    # 3. Garantir source
    source_id = ensure_source(
        slug=finding.source_slug,
        name=finding.source_slug,  # será atualizado pelo coletor
        family=finding.metadata.get("family", "web"),
    )
    
    # 4. Inserir finding
    finding_data = {
        "id": str(uuid.uuid4()),
        "source_id": source_id,
        "source_url": finding.source_url,
        "title": clean(finding.title)[:300],
        "content_text": clean(finding.raw_text)[:10000],
        "snippet": snippet(finding.raw_text, 200),
        "language": finding.language,
        "content_hash": hash_val,
        "collected_at": finding.collected_at or datetime.now(timezone.utc).isoformat(),
        "status": "new",
        "metadata": finding.metadata,
    }
    
    try:
        return insert_finding(finding_data)
    except Exception as e:
        print(f"[main] Erro ao inserir finding: {e}")
        return None


async def run_collector(collector) -> tuple[str, int, int]:
    """
    Executa um coletor e processa seus findings.
    Retorna (nome, total_coletado, total_inserido).
    """
    name = collector.source_name
    try:
        raw_findings = await collector.collect()
        total = len(raw_findings)
        inserted = 0
        
        for finding in raw_findings:
            fid = await process_finding(finding)
            if fid:
                inserted += 1
        
        # Atualiza timestamp da fonte
        try:
            update_source_polled(collector.source_slug)
        except Exception:
            pass
        
        return (name, total, inserted)
    except Exception as e:
        print(f"[main] Erro no coletor {name}: {e}")
        return (name, 0, 0)


# ─── Entry Point ─────────────────────────────────────────

async def main():
    """
    Orquestrador principal.
    Executa todos os coletores em paralelo e imprime estatísticas.
    """
    print("[main] ═══════════════════════════════════════════")
    print(f"[main] Observatório CISEB — Coleta Fase 2")
    print(f"[main] {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("[main] ═══════════════════════════════════════════")
    print(f"[main] Coletores ativos: {len(ALL_COLLECTORS)}")
    print()
    
    # Executa todos os coletores em paralelo
    results = await asyncio.gather(
        *[run_collector(c) for c in ALL_COLLECTORS],
        return_exceptions=False
    )
    
    # ─── Estatísticas ──────────────────────────────────
    total_collected = sum(r[1] for r in results)
    total_inserted = sum(r[2] for r in results)
    duplicates = total_collected - total_inserted
    
    print()
    print("[main] ═══════════════════════════════════════════")
    print("[main] 📊 RESUMO DA COLETA")
    print("[main] ═══════════════════════════════════════════")
    for name, collected, inserted in results:
        dup = collected - inserted
        print(f"[main]   {name:.<40s} {collected:>3d} coletados  {inserted:>3d} inseridos  {dup:>3d} duplicados")
    print("[main] ───────────────────────────────────────────")
    print(f"[main]   TOTAL: {total_collected} coletados | {total_inserted} inseridos | {duplicates} duplicados")
    print("[main] ═══════════════════════════════════════════")
    
    # Verifica se atingiu CHECKPOINT F2.1
    if total_inserted >= 50:
        print("[main] ✅ CHECKPOINT F2.1: ≥50 findings atingido!")
    else:
        print(f"[main] ⚠️  Faltam {50 - total_inserted} findings para CHECKPOINT F2.1")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
