"""
API mínima do worker — FastAPI wrapper para Render Web Service.
Resolve o health check do Render (port binding) e expõe endpoints para Vercel cron.

Fase 7 (auditoria Harness 2026-06-27): Sentry integrado para captura de erros
em produção. Inicializado ANTES de qualquer import interno.
"""

import logging
import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Fase 7: inicializar Sentry PRIMEIRO, antes de qualquer outro import.
# Isto garante que erros durante o carregamento de main.py também sejam capturados.
from sentry_init import init_sentry

init_sentry()

logger = logging.getLogger(__name__)

# ⚠️ FAIL-CLOSED: sem fallback. Se CRON_SECRET não estiver no ambiente,
# o serviço recusa iniciar em vez de abrir com senha padrão.
# Este valor NUNCA deve ser hardcoded no repositório.
# NOTA: A verificação ocorre ANTES de qualquer import interno que possa
# disparar load_dotenv() (ex: main.py), garantindo que o fail-closed
# não seja burlado por um .env local com fallback.
CRON_SECRET = os.environ.get("CRON_SECRET")
if not CRON_SECRET:
    raise RuntimeError(
        "CRON_SECRET não configurado no ambiente. "
        "Defina a variável CRON_SECRET no Render/Vercel antes de iniciar. "
        "Recusa a iniciar sem autenticação (fail-closed)."
    )

# Só importa main após a verificação de CRON_SECRET — main.py chama
# load_dotenv() que poderia popular CRON_SECRET de um .env local,
# burlando o fail-closed.
from main import main as run_pipeline  # noqa: E402

app = FastAPI(title="Observatório CISEB Worker", version="0.1.0")

security = HTTPBearer(auto_error=False)


def verify_cron(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> bool:
    """
    Verifica se a requisição tem o token CRON_SECRET no header Authorization.

    Usa comparação em tempo constante (hmac.compare_digest) para mitigar
    timing attacks na validação do token.
    """
    import hmac

    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Unauthorized — Bearer token required")
    if not hmac.compare_digest(credentials.credentials, CRON_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized — invalid CRON_SECRET")
    return True


@app.get("/health")
async def health():
    """Health check para o Render. Retorna 200 se o worker está vivo."""
    return {"status": "ok", "service": "observatorio-ciseb-worker"}


# Controle de concorrência — evita 2 pipelines rodando simultaneamente
_pipeline_running = False


async def _run_pipeline_background():
    """Wrapper para executar pipeline em background com error handling."""
    global _pipeline_running
    _pipeline_running = True
    try:
        logger.info("[api] Pipeline background iniciado")
        await run_pipeline()
        logger.info("[api] Pipeline background concluído com sucesso")
    except Exception as e:
        # Fase 7: capturar erro no Sentry
        from sentry_init import capture_exception

        capture_exception(e, tags={"endpoint": "/run", "component": "pipeline"})
        logger.error(f"[api] Pipeline background falhou: {e}")
    finally:
        _pipeline_running = False


@app.post("/run")
async def run(_: bool = Depends(verify_cron)):
    """
    Dispara uma rodada completa do pipeline EM BACKGROUND.
    Retorna 200 imediatamente — o pipeline continua rodando após a resposta.

    Fase 8.8 (auditoria Harness 2026-07-01):
    Render Free Tier tem timeout de 60s para requisições HTTP. O pipeline
    demora 2-5 minutos. Antes, await run_pipeline() bloqueava a resposta,
    causando HTTP 502 (Bad Gateway) em todas as execuções do cron.

    Solução: usar asyncio.create_task() para rodar o pipeline em background.
    O endpoint retorna 200 imediatamente. O pipeline continua executando
    após a resposta ser enviada. Erros são capturados pelo Sentry.

    Chamado pelo cron do GitHub Actions diretamente (F8.7).
    """
    global _pipeline_running
    if _pipeline_running:
        return {
            "status": "skipped",
            "message": "Pipeline já está em execução — requisição ignorada",
        }

    asyncio.create_task(_run_pipeline_background())
    return {
        "status": "ok",
        "message": "Pipeline disparado em background — monitorar logs do Render",
    }


@app.post("/digest")
async def digest(_: bool = Depends(verify_cron)):
    """
    Envia digest diário com os top 10 findings por score composto.
    Chamado pelo cron da Vercel via /api/cron/digest.
    Requer header Authorization: Bearer CRON_SECRET.

    A mensagem é enviada via Telegram em formato HTML com links
    para as fontes originais de cada achado.
    """
    from datetime import datetime, timezone

    from db.supabase import get_supabase
    from delivery.telegram import send_message

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
        lines.append(f"{i}. [{s['score_composite']}] <b>{title}</b>\n   🔗 {url}")

    await send_message("\n".join(lines))
    return {"status": "ok", "message": f"Digest enviado com {len(findings)} achados"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
