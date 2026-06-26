"""
Coletor de Editais e Eventos — oportunidades de fomento e chamadas públicas.

Monitora páginas institucionais de agências de fomento brasileiras
(CNPq, FAPESP) para capturar editais, chamadas e notícias relevantes
para o ecossistema de tecnologia educacional.

Utiliza httpx para requisições HTTP e trafilatura para extração limpa
do conteúdo textual das páginas.
"""
from datetime import datetime, timezone

import httpx
from trafilatura import extract

from .base import BaseCollector, RawFinding
from utils.text import clean

# ---------------------------------------------------------------------------
# Fontes de eventos e editais
# ---------------------------------------------------------------------------
EVENT_SOURCES: list[dict] = [
    {
        "url": "https://www.gov.br/cnpq/pt-br/assuntos/noticias",
        "slug": "cnpq",
        "name": "CNPq — Notícias e Editais",
    },
    {
        "url": "https://fapesp.br/",
        "slug": "fapesp",
        "name": "FAPESP — Chamadas",
    },
]


class EventsCollector(BaseCollector):
    """Coletor de editais e eventos de agências de fomento brasileiras."""

    source_slug: str = "events"
    source_name: str = "Editais e Eventos (CNPq, FAPESP, CAPES)"
    family: str = "events"

    async def collect(self) -> list[RawFinding]:
        """
        Coleta conteúdo textual das páginas de editais configuradas.

        Cada fonte contribui com até 5 parágrafos relevantes por rodada.
        Um erro em uma fonte não interrompe a coleta das demais.
        """
        findings: list[RawFinding] = []
        async with httpx.AsyncClient(
            timeout=20.0,
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

    async def _fetch_page(
        self, client: httpx.AsyncClient, src: dict
    ) -> list[RawFinding]:
        """
        Busca e extrai conteúdo textual de uma página de editais.

        Utiliza trafilatura para remover boilerplate (menus, rodapés, etc.)
        e extrair apenas o conteúdo relevante.

        Args:
            client: Cliente HTTP compartilhado.
            src: Dicionário com 'url', 'slug' e 'name' da fonte.

        Returns:
            Lista de RawFinding (até 5 parágrafos).
        """
        response = await client.get(src["url"])
        response.raise_for_status()

        # Extrai texto limpo com trafilatura
        text = extract(
            response.text,
            include_comments=False,
            output_format="txt",
        )

        if not text:
            return []

        # Divide o texto em parágrafos significativos
        # (ignora linhas muito curtas, que provavelmente são ruído)
        paragraphs = [
            p.strip()
            for p in text.split("\n\n")
            if len(p.strip()) > 100
        ]

        items: list[RawFinding] = []
        for i, para in enumerate(paragraphs[:5]):  # máximo 5 parágrafos
            if len(para) < 50:
                continue

            finding = RawFinding(
                source_slug=src["slug"],
                source_url=src["url"],
                title=clean(para[:120]) if len(para) > 10 else f"{src['name']} #{i + 1}",
                raw_text=para[:10000],
                language="pt",
                metadata={
                    "source": src["slug"],
                    "source_name": src["name"],
                },
            )
            items.append(finding)

        return items
