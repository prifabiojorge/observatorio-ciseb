"""
Observatório CISEB — Worker principal.
Fase 1.4: Hello World ponta-a-ponta.
Pipeline: 1 requisição HTTP → 1 INSERT Supabase → 1 mensagem Telegram.

Execução:
    cd apps/worker
    python src/main.py

Pré-requisitos:
    - Arquivo .env na raiz do projeto com SUPABASE_URL,
      SUPABASE_SERVICE_ROLE_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID_FABIO.
    - Dependências instaladas: pip install -e .
"""
import asyncio
import hashlib
import os
import sys
import uuid
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

# ── Carrega .env da raiz do projeto (3 níveis acima de src/) ───────────────
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
load_dotenv(_env_path)

# ── Imports internos (src/ no path por estar no mesmo diretório) ───────────
from db.supabase import get_supabase  # noqa: E402
from delivery.telegram import send_message  # noqa: E402

# ── Constantes ──────────────────────────────────────────────────────────────
HELLO_URL = "https://www.google.com"  # URL pública para teste HTTP
SOURCE_SLUG = "hello-world"
SOURCE_FAMILY = "web"


# ── Helpers ─────────────────────────────────────────────────────────────────

def make_content_hash(url: str, title: str, text: str) -> str:
    """
    SHA-256 para deduplicação.

    Implementação idêntica ao contrato definido em
    memoria/06_CONTRATOS_E_SCHEMAS.md, seção 7.

    Args:
        url: URL de origem.
        title: Título do achado.
        text: Texto completo do conteúdo.

    Returns:
        Hash SHA-256 hexadecimal (64 caracteres).
    """
    normalized = " ".join((url + " " + title + " " + text).split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def fetch_title(url: str) -> str:
    """
    Faz GET HTTP e extrai o <title> da página HTML.

    Args:
        url: URL pública a ser acessada.

    Returns:
        Conteúdo da tag <title> ou fallback se não encontrada.

    Raises:
        httpx.HTTPError: Se a requisição HTTP falhar.
    """
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text

        # Extração simples da tag <title> — suficiente para hello world
        start = html.lower().find("<title>")
        end = html.lower().find("</title>")
        if start != -1 and end != -1:
            return html[start + 7 : end].strip()
        return "Hello World — Observatório CISEB"


async def ensure_source(supabase) -> str:
    """
    Garante que a fonte 'hello-world' existe na tabela sources.

    Estratégia: SELECT primeiro; se não encontrar, INSERT.
    Idempotente — seguro para múltiplas execuções.

    Args:
        supabase: Cliente Supabase autenticado (service_role).

    Returns:
        UUID (string) da fonte.
    """
    result = supabase.table("sources").select("id").eq("slug", SOURCE_SLUG).execute()
    if result.data:
        return result.data[0]["id"]

    source_data = {
        "slug": SOURCE_SLUG,
        "name": "Hello World (teste F1.4)",
        "family": SOURCE_FAMILY,
        "config": {"url": HELLO_URL},
        "healthy": True,
        "last_polled_at": datetime.now(timezone.utc).isoformat(),
    }
    result = supabase.table("sources").insert(source_data).execute()
    return result.data[0]["id"]


async def insert_finding(supabase, source_id: str, title: str) -> dict:
    """
    Insere 1 linha na tabela findings com verificação de duplicata.

    A deduplicação é feita via content_hash (SHA-256).
    Se já existir um finding com o mesmo hash, retorna o existente
    sem inserir novamente (idempotência).

    Args:
        supabase: Cliente Supabase autenticado.
        source_id: UUID da fonte (tabela sources).
        title: Título extraído da página.

    Returns:
        Dicionário com os dados do finding (novo ou existente).
    """
    content_text = f"Hello World do Observatório CISEB. Título capturado: {title}"
    content_hash = make_content_hash(HELLO_URL, title, content_text)

    finding = {
        "id": str(uuid.uuid4()),
        "source_id": source_id,
        "source_url": HELLO_URL,
        "title": title,
        "content_text": content_text,
        "snippet": title[:200],
        "language": "pt",
        "content_hash": content_hash,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "status": "new",
        "metadata": {"origin": "hello_world_f1.4"},
    }

    # Verifica duplicata antes de inserir (content_hash é UNIQUE no banco)
    existing = (
        supabase.table("findings")
        .select("id")
        .eq("content_hash", content_hash)
        .execute()
    )
    if existing.data:
        print(f"[main] ⚠️  Finding já existe (hash duplicado): {existing.data[0]['id']}")
        return existing.data[0]

    result = supabase.table("findings").insert(finding).execute()
    return result.data[0]


# ── Main ────────────────────────────────────────────────────────────────────

async def main() -> int:
    """
    Hello World: coletor → DB → Telegram.

    Etapas:
        1. Coleta HTTP (extrai <title> de página pública)
        2. Garante source no banco (idempotente)
        3. Insere finding com deduplicação
        4. Envia mensagem Telegram de confirmação

    Cada etapa tem tratamento de erro independente —
    se uma falhar, as outras continuam.

    Returns:
        0 em caso de sucesso, 1 em caso de falha total.
    """
    print("[main] ═══════════════════════════════════════════")
    print("[main] Observatório CISEB — Hello World Fase 1.4")
    print("[main] ═══════════════════════════════════════════")

    supabase = get_supabase()
    errors: list[str] = []

    # ── Etapa 1: Coleta HTTP ────────────────────────────────────────────
    title = "Hello World — Observatório CISEB (fallback)"
    try:
        print(f"[main] 🌐 Coletando título de {HELLO_URL}...")
        title = await fetch_title(HELLO_URL)
        print(f"[main] ✅ Título extraído: {title}")
    except httpx.HTTPError as e:
        err_msg = f"Erro HTTP ao acessar {HELLO_URL}: {e}"
        print(f"[main] ❌ {err_msg}")
        errors.append(err_msg)
    except Exception as e:
        err_msg = f"Erro inesperado na coleta: {type(e).__name__}: {e}"
        print(f"[main] ❌ {err_msg}")
        errors.append(err_msg)

    # ── Etapa 2: Garante source ─────────────────────────────────────────
    source_id = ""
    try:
        source_id = await ensure_source(supabase)
        print(f"[main] ✅ Source ID: {source_id}")
    except Exception as e:
        err_msg = f"Erro ao garantir source: {type(e).__name__}: {e}"
        print(f"[main] ❌ {err_msg}")
        errors.append(err_msg)

    # ── Etapa 3: Insere finding ─────────────────────────────────────────
    finding: dict = {}
    try:
        if source_id:
            finding = await insert_finding(supabase, source_id, title)
            print(f"[main] ✅ Finding ID: {finding['id']} | status: {finding.get('status', '?')}")
        else:
            print("[main] ⚠️  Pulando INSERT — source_id não disponível")
            errors.append("INSERT pulado: source_id inválido")
    except Exception as e:
        err_msg = f"Erro ao inserir finding: {type(e).__name__}: {e}"
        print(f"[main] ❌ {err_msg}")
        errors.append(err_msg)

    # ── Etapa 4: Envia Telegram ─────────────────────────────────────────
    try:
        finding_id_short = finding.get("id", "N/A")[:8] if finding else "N/A"
        msg = (
            f"🚀 <b>Pipeline vivo!</b>\n\n"
            f"Observatório CISEB — Hello World concluído.\n\n"
            f"📰 Título capturado: {title}\n"
            f"🆔 Finding: {finding_id_short}...\n"
            f"⏰ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        await send_message(msg)
        print("[main] ✅ Mensagem Telegram enviada!")
    except Exception as e:
        err_msg = f"Erro ao enviar Telegram: {type(e).__name__}: {e}"
        print(f"[main] ❌ {err_msg}")
        errors.append(err_msg)

    # ── Resumo final ────────────────────────────────────────────────────
    print("[main] ═══════════════════════════════════════════")
    if errors:
        print(f"[main] ⚠️  Pipeline concluído com {len(errors)} erro(s):")
        for err in errors:
            print(f"[main]    - {err}")
        print("[main] ═══════════════════════════════════════════")
        return 1
    else:
        print("[main] ✅ Hello World concluído com sucesso!")
        print("[main] ═══════════════════════════════════════════")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
