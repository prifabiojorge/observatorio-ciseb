"""
Módulo de entrega via Telegram.

Envia mensagens formatadas em HTML para o chat do professor Fábio Jorge.
Suporta envio simples e alertas formatados conforme contrato em
memoria/06_CONTRATOS_E_SCHEMAS.md.

Uso:
    from delivery.telegram import send_message, send_alert
    await send_message("Olá, mundo!")
    await send_alert("Título", "Resumo", 85, "ia", "https://...")
"""

import os

import httpx

# ── Configuração via variáveis de ambiente (NUNCA hardcoded) ──────────────
BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID: str = os.environ["TELEGRAM_CHAT_ID_FABIO"]
BASE_URL: str = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def send_message(text: str, parse_mode: str = "HTML") -> dict:
    """
    Envia mensagem de texto para o Telegram.

    Args:
        text: Conteúdo da mensagem (HTML permitido quando parse_mode='HTML').
        parse_mode: Modo de parsing ('HTML' ou 'Markdown'). Default: 'HTML'.

    Returns:
        Resposta JSON da API do Telegram em caso de sucesso.

    Raises:
        httpx.HTTPError: Se a API retornar erro HTTP (rede, timeout, status >= 400).
        httpx.RequestError: Se houver falha de conexão.
        KeyError: Se TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID_FABIO não estiverem
                  definidas no ambiente.
    """
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()


async def send_alert(
    title: str,
    summary: str,
    score: int,
    pillar: str,
    source_url: str,
    application_suggestion: str = "",
) -> dict:
    """
    Envia alerta formatado de finding com score alto e sugestão de aplicação.

    Template conforme contrato em memoria/06_CONTRATOS_E_SCHEMAS.md,
    seção 3 — Contrato de card Telegram.

    Args:
        title: Título do achado.
        summary: Resumo de 2-3 frases.
        score: Score composto (0-100).
        pillar: Slug do pilar (ex: 'ia', 'robotics').
        source_url: URL de origem do achado.
        application_suggestion: Sugestão de aplicação prática (opcional).

    Returns:
        Resposta JSON da API do Telegram.

    Raises:
        httpx.HTTPError: Se a API retornar erro.
        httpx.RequestError: Se houver falha de conexão.
    """
    text = (
        f"🚨 <b>Alerta — score {score}/100</b>\n\n"
        f"<b>{title}</b>\n\n"
        f"📁 {pillar} ({score})\n\n"
        f"📝 {summary}\n\n"
    )
    if application_suggestion:
        text += f"💡 <i>Aplicação:</i> {application_suggestion}\n\n"
    text += f"🔗 {source_url}"
    return await send_message(text)
