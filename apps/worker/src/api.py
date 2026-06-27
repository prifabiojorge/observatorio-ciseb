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


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
