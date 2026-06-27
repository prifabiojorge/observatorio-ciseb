"""
Coletor de Editais e Eventos — oportunidades de fomento e chamadas públicas.

Monitora páginas institucionais de agências de fomento brasileiras
(CNPq, FAPESP, MEC, CAPES) para capturar editais, chamadas e notícias
relevantes para o ecossistema de tecnologia educacional.

Estratégia de extração: identifica títulos prováveis (linhas curtas de
20-150 caracteres, iniciadas por maiúscula, sem ponto final) e associa
o parágrafo seguinte como conteúdo. Cada fonte contribui com até 8
findings por rodada, visando alcançar ≥5 findings da família events
para o CHECKPOINT F2.1.
"""

import httpx
from trafilatura import extract

from utils.text import clean

from .base import BaseCollector, RawFinding

# ---------------------------------------------------------------------------
# Fontes de eventos e editais (4 agências de fomento)
# ---------------------------------------------------------------------------
EVENT_SOURCES: list[dict] = [
    {
        "url": "https://www.gov.br/cnpq/pt-br/assuntos/noticias",
        "slug": "cnpq",
        "name": "CNPq — Notícias",
    },
    {
        "url": "https://fapesp.br/",
        "slug": "fapesp",
        "name": "FAPESP — Chamadas",
    },
    {
        "url": "https://www.gov.br/mec/pt-br/assuntos/noticias",
        "slug": "mec",
        "name": "MEC — Notícias",
    },
    {
        "url": "https://www.gov.br/capes/pt-br/assuntos/noticias",
        "slug": "capes",
        "name": "CAPES — Notícias",
    },
]

# ---------------------------------------------------------------------------
# Heurísticas de extração
# ---------------------------------------------------------------------------
TITLE_MIN_LEN: int = 20
TITLE_MAX_LEN: int = 150
CONTENT_MIN_LEN: int = 50
MAX_FINDINGS_PER_SOURCE: int = 8


class EventsCollector(BaseCollector):
    """Coletor de editais e eventos de agências de fomento brasileiras."""

    source_slug: str = "events"
    source_name: str = "Editais e Eventos (CNPq, FAPESP, MEC, CAPES)"
    family: str = "events"

    async def collect(self) -> list[RawFinding]:
        """
        Coleta conteúdo textual das 4 páginas de agências configuradas.

        Cada fonte é processada independentemente; um erro em uma fonte
        não interrompe a coleta das demais. A extração é baseada em
        heurística de título + parágrafo subsequente.

        Returns:
            Lista de RawFinding para inserção no banco.
        """
        findings: list[RawFinding] = []
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "ObservatorioCISEB/1.0"},
        ) as client:
            for src in EVENT_SOURCES:
                try:
                    items = await self._fetch_page(client, src)
                    findings.extend(items)
                except Exception as exc:
                    print(f"[events] Erro na fonte {src['slug']}: {exc}")
        return findings

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    async def _fetch_page(self, client: httpx.AsyncClient, src: dict) -> list[RawFinding]:
        """
        Busca e extrai conteúdo textual de uma página de editais.

        Utiliza trafilatura para remover boilerplate (menus, rodapés, etc.)
        e aplica heurística de título + parágrafo para identificar entradas
        individuais (notícias, chamadas, editais).

        Args:
            client: Cliente HTTP compartilhado.
            src: Dicionário com 'url', 'slug' e 'name' da fonte.

        Returns:
            Lista de RawFinding (até MAX_FINDINGS_PER_SOURCE por fonte).
        """
        # -- Requisição HTTP com tratamento de erros -----------------------
        try:
            response = await client.get(src["url"])
            if response.status_code != 200:
                print(f"[events] Status {response.status_code} para {src['slug']}")
                return []
        except Exception as exc:
            print(f"[events] Erro HTTP {src['slug']}: {exc}")
            return []

        # -- Extração limpa com trafilatura --------------------------------
        text = extract(
            response.text,
            include_comments=False,
            output_format="txt",
        )

        if not text:
            print(f"[events] Texto vazio após extração: {src['slug']}")
            return []

        # -- Heurística: identifica títulos e associa parágrafos seguintes
        lines = text.split("\n")
        items: list[RawFinding] = []

        for i, line in enumerate(lines):
            line = line.strip()

            # Título provável: linha curta, inicia com maiúscula,
            # sem ponto final (notícias/chamadas tipicamente não pontuam
            # títulos com ponto final)
            if not (
                TITLE_MIN_LEN <= len(line) <= TITLE_MAX_LEN
                and not line.endswith(".")
                and line[0].isupper()
            ):
                continue

            # Busca o próximo parágrafo longo como conteúdo associado
            content = ""
            for j in range(i + 1, min(i + 3, len(lines))):
                candidate = lines[j].strip()
                if len(candidate) > CONTENT_MIN_LEN:
                    content = candidate
                    break

            # Monta o texto bruto: título + conteúdo (se houver)
            raw_text = f"{line}\n\n{content}" if content else line

            finding = RawFinding(
                source_slug=src["slug"],
                source_url=src["url"],
                title=clean(line[:120]),
                raw_text=clean(raw_text)[:10000],
                language="pt",
                metadata={
                    "source": src["slug"],
                    "source_name": src["name"],
                },
            )
            items.append(finding)

            # Limite por fonte para evitar ruído excessivo
            if len(items) >= MAX_FINDINGS_PER_SOURCE:
                break

        return items
