"""
Inicialização do Sentry para o Worker Python (Fase 7).

Captura erros em:
- API FastAPI (/run, /digest, /health)
- Coletores (web_rss, github, scholar, events, forums, youtube)
- Pipeline principal (main.py)
- Cliente DeepSeek + HuggingFace
- Cliente Supabase

DSN vem de SENTRY_DSN. Sem DSN, Sentry fica inativo (fail-safe).

Uso:
    from sentry_init import init_sentry
    init_sentry()  # chamar no topo de api.py e main.py
"""
import os
import logging

log = logging.getLogger(__name__)

_SENTRY_INITIALIZED = False


def init_sentry() -> None:
    """
    Inicializa Sentry SDK com integração FastAPI.

    Idempotente: pode ser chamada múltiplas vezes sem re-init.
    Sem SENTRY_DSN no ambiente: loga warning e retorna (não quebra).
    """
    global _SENTRY_INITIALIZED
    if _SENTRY_INITIALIZED:
        return

    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        log.warning(
            "[sentry] SENTRY_DSN não configurado — captura de erros desativada. "
            "Crie conta em https://sentry.io e configure SENTRY_DSN no Render."
        )
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.threading import ThreadingIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=os.environ.get("APP_ENV", "production"),
            release=f"observatorio-worker@{os.environ.get('RENDER_SERVICE_ID', 'dev')}",

            # Sampling: 100% erros, 20% transactions (para performance monitoring)
            traces_sample_rate=0.2,

            # Integrar com logging Python (captura log.error e log.critical)
            integrations=[
                FastApiIntegration(),
                LoggingIntegration(
                    level=logging.INFO,        # captura INFO+ como breadcrumbs
                    event_level=logging.ERROR,  # captura ERROR+ como eventos
                ),
                ThreadingIntegration(propagate_hub=True),
            ],

            # Não enviar PII (LGPD)
            send_default_pii=False,

            # Antes de enviar evento, filtra ruído
            before_send=_filter_event,

            # Não falhar se DSN estiver inválido
            before_send_transaction=None,
        )

        _SENTRY_INITIALIZED = True
        log.info("[sentry] SDK inicializado com sucesso — captura de erros ativa")

    except ImportError:
        log.warning("[sentry] sentry-sdk não instalado — rode 'pip install sentry-sdk[fastapi]'")
    except Exception as e:
        log.error(f"[sentry] Falha ao inicializar Sentry: {e}")


def _filter_event(event: dict, hint: dict) -> dict | None:
    """
    Filtro executado antes de enviar cada evento ao Sentry.
    Retorna None para descartar eventos que não queremos ver.
    """
    # Filtrar AbortError (cancelamento de fetch não é erro real)
    exc = hint.get("exc_info", [None, None, None])
    if exc and exc[0] and "AbortError" in str(exc[0]):
        return None

    # Filtrar erros de rede temporários (vão retry automaticamente)
    if exc and exc[0] and "httpx.ConnectError" in str(exc[0]):
        # Ainda enviar, mas marcar como warning (não erro crítico)
        event["level"] = "warning"

    return event


def capture_exception(error: Exception, **kwargs) -> None:
    """
    Wrapper para sentry_sdk.capture_exception — seguro de chamar
    mesmo se Sentry não estiver inicializado (silencia + loga).
    """
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(error, **kwargs)
    except ImportError:
        log.error(f"[sentry] (não capturado) {error}")
