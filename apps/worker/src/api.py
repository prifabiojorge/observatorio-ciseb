"""
API mínima do worker — FastAPI wrapper para Render Web Service.
Resolve o health check do Render (port binding) e expõe endpoints para Vercel cron.
"""
import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from main import main as run_pipeline

logger = logging.getLogger(__name__)
app = FastAPI(title="Observatório CISEB Worker", version="0.1.0")

CRON_SECRET = os.environ.get("CRON_SECRET", "observatorio-ciseb-f1-2026")
security = HTTPBearer(auto_error=False)


def verify_cron(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> bool:
    """Verifica se a requisição tem o token CRON_SECRET."""
    if credentials and credentials.credentials == CRON_SECRET:
        return True
    raise HTTPException(status_code=401, detail="Unauthorized — CRON_SECRET required")


@app.get("/health")
async def health():
    """Health check para o Render. Retorna 200 se o worker está vivo."""
    return {"status": "ok", "service": "observatorio-ciseb-worker"}


@app.post("/run")
async def run(_: bool = Depends(verify_cron)):
    """
    Executa uma rodada completa do pipeline.
    Chamado pelo cron da Vercel via /api/cron/collect.
    Requer header Authorization: Bearer CRON_SECRET.
    """
    try:
        await run_pipeline()
        return {"status": "ok", "message": "Pipeline executado com sucesso"}
    except Exception as e:
        logger.error(f"Erro no pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/digest")
async def digest(_: bool = Depends(verify_cron)):
    """
    Envia digest diário com os top 10 findings por score composto.
    Chamado pelo cron da Vercel via /api/cron/digest.
    Requer header Authorization: Bearer CRON_SECRET.

    A mensagem é enviada via Telegram em formato HTML com links
    para as fontes originais de cada achado.
    """
    from db.supabase import get_supabase
    from delivery.telegram import send_message
    from datetime import datetime, timezone

    supabase = get_supabase()

    # Busca top 10 scores (maior score_composite)
    scores_data = (
        supabase.table("scores")
        .select("finding_id, score_composite")
        .order("score_composite", desc=True)
        .limit(10)
        .execute()
        .data
    )

    if not scores_data:
        return {"status": "ok", "message": "Nenhum finding para o digest"}

    # Busca detalhes dos findings correspondentes
    finding_ids = list({s["finding_id"] for s in scores_data})
    findings = (
        supabase.table("findings")
        .select("id, title, source_url")
        .in_("id", finding_ids)
        .execute()
        .data
    )
    finding_map = {f["id"]: f for f in findings}

    # Monta mensagem do digest
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"📬 <b>Digest {today}</b> — {len(findings)} achados\n"]

    for i, s in enumerate(scores_data[:10], 1):
        f = finding_map.get(s["finding_id"])
        if not f:
            continue
        title = f["title"][:80]
        url = f["source_url"]
        lines.append(
            f'{i}. [{s["score_composite"]}] <b>{title}</b>\n'
            f'   🔗 {url}'
        )

    await send_message("\n".join(lines))
    return {"status": "ok", "message": f"Digest enviado com {len(findings)} achados"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
