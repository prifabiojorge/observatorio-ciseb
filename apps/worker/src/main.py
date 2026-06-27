"""
Observatório CISEB — Worker Principal.
Fase 2: Orquestrador de coleta — executa os 6 coletores e persiste no Supabase.

Execução:
  python src/main.py                   # pipeline completo (coleta + enriquecimento)
  python src/main.py --collect-only    # apenas coleta
  python src/main.py --enrich-only     # apenas enriquecimento
"""
import asyncio
import os
import sys
import sys as _sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv

# Carrega .env da raiz (3 níveis acima de src/)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

# ─── Imports internos ────────────────────────────────────
from collectors.base import RawFinding
from collectors.web_rss import WebRSSCollector
from collectors.github import GitHubCollector
from collectors.youtube import YouTubeCollector
from collectors.scholar import ScholarCollector
from collectors.forums import ForumsCollector
from collectors.events import EventsCollector
from db.supabase import get_supabase
from db.queries import ensure_source, finding_exists, insert_finding, update_source_polled
from delivery.telegram import send_alert
from utils.hashing import content_hash
from utils.text import clean, snippet

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

async def process_finding(
    finding: RawFinding,
    family: str = "web",
    source_name: str = "",
) -> Optional[str]:
    """
    Processa um RawFinding: hash → dedup → ensure_source → insert.
    Retorna o finding_id ou None se duplicado.

    Args:
        finding: RawFinding a ser processado.
        family: Família da fonte (ex: 'web', 'github', 'social'), vinda do coletor.
        source_name: Nome legível da fonte, vindo do coletor.
    """
    supabase = get_supabase()
    
    # 1. Gerar hash de deduplicação
    text_for_hash = finding.raw_text or finding.title
    hash_val = content_hash(finding.source_url, finding.title, text_for_hash)
    
    # 2. Verificar duplicata
    existing = finding_exists(hash_val)
    if existing:
        return None  # duplicado, pular silenciosamente
    
    # 3. Garantir source (family e source_name recebidos do coletor)
    source_id = ensure_source(
        slug=finding.source_slug,
        name=source_name or finding.source_slug,
        family=family,
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
            fid = await process_finding(finding, collector.family, collector.source_name)
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


# ─── Fase 3: Enriquecimento + Scoring ─────────────────────

_pillar_id_cache: dict[str, str] = {}

def _get_pillar_id_map() -> dict[str, str]:
    global _pillar_id_cache
    if not _pillar_id_cache:
        supabase = get_supabase()
        for p in supabase.table("pillars").select("id, slug").execute().data:
            _pillar_id_cache[p["slug"]] = p["id"]
    return _pillar_id_cache

async def run_enrich_and_score(batch_size: int = 20) -> dict:
    from llm.embeddings import embed_text, embed_pillars
    from llm.classifier import enrich, compute_score, novelty_score

    stats = {"enriched": 0, "failed": 0, "scored_high": 0}

    supabase = get_supabase()

    print("[main] Embedando pilares CISEB...")
    await embed_pillars()

    new_findings = (
        supabase.table("findings").select("*").eq("status", "new")
        .order("collected_at", desc=False).limit(batch_size).execute().data
    )
    print(f"[main] Enriquecendo {len(new_findings)} findings...")

    for f in new_findings:
        fid = f["id"]
        text_to_embed = (f["title"] or "") + " " + (f.get("content_text") or "")
        vec = await embed_text(text_to_embed)
        enriched = await enrich(f)
        if not enriched:
            stats["failed"] += 1
            continue
        enriched["_dim_novelty"] = novelty_score(f.get("collected_at", ""))
        sc = compute_score(enriched, f)

        supabase.table("findings").update({
            "embedding": vec,
            "status": "scored",
            "snippet": enriched.get("summary", f.get("snippet")),
            "metadata": {**(f.get("metadata") or {}), "enriched": enriched},
        }).eq("id", fid).execute()

        pillar_map = _get_pillar_id_map()
        scores_rows = []
        for p in enriched.get("pillars", []):
            pid = pillar_map.get(p["slug"])
            if not pid:
                continue
            scores_rows.append({
                "finding_id": fid, "pillar_id": pid,
                "confidence": p["confidence"],
                "score_composite": sc["score_composite"],
                "dim_alignment": sc["dim_alignment"],
                "dim_br_luso": sc["dim_br_luso"],
                "dim_replicable": sc["dim_replicable"],
                "dim_practical": sc["dim_practical"],
                "dim_level": sc["dim_level"],
                "dim_novelty": sc["dim_novelty"],
            })
        if scores_rows:
            supabase.table("scores").upsert(scores_rows, on_conflict="finding_id,pillar_id").execute()

        stats["enriched"] += 1
        if sc["score_composite"] >= 75:
            stats["scored_high"] += 1
        print(f"[main]   [{sc['score_composite']:>3}] {f['title'][:60]}...")

    print(f"[main] Enriquecimento: {stats}")

    # ─── Alertas Telegram (score composto ≥ 75) ─────────────────
    # Após enriquecer e pontuar, envia alertas para os achados
    # de maior relevância que ainda não foram notificados.
    # Limite de 5 alertas/dia para evitar flood no Telegram.
    #
    # ⚠️ CORREÇÃO: o score exibido no card é o score_composite (0-100)
    #    calculado pela fórmula em memoria/03_SCHEMA_BANCO.md, NÃO a
    #    confiança do pilar (0-1). Antes desta correção, o card mostrava
    #    confidence*100, que pode divergir significativamente do
    #    score_composite real (ex: confidence=0.95 mas score_composite=60
    #    se dim_br_luso=30 e dim_replicable=30).

    # Busca findings scored com seus scores compostos
    scored_findings = (
        supabase.table("findings")
        .select("id, title, source_url, metadata, collected_at")
        .eq("status", "scored")
        .execute()
        .data
    )

    if not scored_findings:
        stats["alerts_sent"] = 0
        return stats

    # Busca os score_composite reais do banco para cada finding
    finding_ids = [f["id"] for f in scored_findings]
    scores_data = (
        supabase.table("scores")
        .select("finding_id, score_composite, pillar_id")
        .in_("finding_id", finding_ids)
        .execute()
        .data
    )

    # Agrupa por finding_id e seleciona o score_composite máximo
    # (um finding pode ter múltiplos scores, um por pilar)
    score_by_finding: dict[str, int] = {}
    pillar_by_finding: dict[str, str] = {}
    for s in scores_data:
        fid = s["finding_id"]
        sc = int(s["score_composite"])
        if fid not in score_by_finding or sc > score_by_finding[fid]:
            score_by_finding[fid] = sc
            # pillar_id é UUID; precisamos do slug para o card
            pillar_by_finding[fid] = s.get("pillar_id", "")

    # Cache reverso pillar_id → slug (para exibição no card)
    pillar_id_to_slug = {v: k for k, v in _get_pillar_id_map().items()}

    # Filtra apenas findings com score_composite ≥ 75 (threshold de alerta)
    alert_candidates = [
        f for f in scored_findings
        if score_by_finding.get(f["id"], 0) >= 75
    ]
    # Ordena por score decrescente (prioriza alertas mais relevantes)
    alert_candidates.sort(
        key=lambda f: score_by_finding.get(f["id"], 0),
        reverse=True,
    )

    alerts_sent = 0
    max_alerts = 5  # Máx 5 alertas por rodada para evitar spam

    for f_alert in alert_candidates:
        if alerts_sent >= max_alerts:
            break

        fid = f_alert["id"]
        best_score = score_by_finding.get(fid, 0)
        if best_score < 75:
            continue

        pillar_id = pillar_by_finding.get(fid, "")
        pillar_slug = pillar_id_to_slug.get(pillar_id, "ia")

        enriched_meta = (f_alert.get("metadata") or {}).get("enriched", {})
        if not enriched_meta:
            continue

        # Verifica se já foi enviado alerta para este finding
        existing_alerts = (
            supabase.table("deliveries")
            .select("id")
            .eq("finding_id", fid)
            .eq("channel", "telegram")
            .execute()
            .data
        )
        if existing_alerts:
            continue

        try:
            await send_alert(
                title=f_alert["title"],
                summary=enriched_meta.get("summary", f_alert.get("snippet", "")),
                score=best_score,  # ✅ score_composite real, não confidence*100
                pillar=pillar_slug,
                source_url=f_alert["source_url"],
                application_suggestion=enriched_meta.get("application_suggestion", ""),
            )

            # Registra a entrega para evitar reenvio
            supabase.table("deliveries").insert({
                "finding_id": fid,
                "channel": "telegram",
                "payload": {
                    "score": best_score,
                    "pillar": pillar_slug,
                },
            }).execute()

            alerts_sent += 1
            print(
                f"[main] 📤 Alerta Telegram enviado: "
                f"[{best_score}] {f_alert['title'][:50]}..."
            )
        except Exception as e:
            print(f"[main] Erro ao enviar alerta Telegram: {e}")

    stats["alerts_sent"] = alerts_sent
    return stats


# ─── Entry Point ─────────────────────────────────────────

async def main():
    """Orquestrador principal."""
    import os as _os
    
    # ── Diagnóstico ─────────────────────────────────────
    _hf = "✅" if _os.environ.get("HF_API_KEY") else "❌"
    _ds = "✅" if _os.environ.get("DEEPSEEK_API_KEY") else "❌"
    phase = "coleta" if "--collect-only" in _sys.argv else ("enrich" if "--enrich-only" in _sys.argv else "full")
    
    print("[main] ═══════════════════════════════════════════")
    print(f"[main] Observatório CISEB — Fase {'Coleta' if phase != 'enrich' else 'Enriquecimento'}")
    print(f"[main] {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("[main] ═══════════════════════════════════════════")
    print(f"[main] Env: HF_API_KEY={_hf} DEEPSEEK_API_KEY={_ds} | Modo: {phase}")
    
    # ── Coleta ─────────────────────────────────────────
    if phase in ("coleta", "full"):
        print(f"[main] Coletores ativos: {len(ALL_COLLECTORS)}")
        results = await asyncio.gather(*[run_collector(c) for c in ALL_COLLECTORS], return_exceptions=False)
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
        if total_inserted >= 50:
            print("[main] ✅ CHECKPOINT F2.1: ≥50 findings atingido!")
        else:
            print(f"[main] ⚠️  Faltam {50 - total_inserted} findings para CHECKPOINT F2.1")
    
    # ── Enriquecimento ─────────────────────────────────
    if phase in ("enrich", "full"):
        print()
        print("[main] ═══════════════════════════════════════════")
        print("[main] 🔬 FASE 3 — ENRIQUECIMENTO + SCORING")
        print("[main] ═══════════════════════════════════════════")
        enrich_stats = await run_enrich_and_score(batch_size=20)
        if enrich_stats["enriched"] >= 20:
            print("[main] ✅ CHECKPOINT F3.1: ≥20 findings scored!")
        else:
            print(f"[main] ⚠️  Faltam {20 - enrich_stats['enriched']} scored para CHECKPOINT F3.1")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
