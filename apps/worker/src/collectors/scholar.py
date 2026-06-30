"""
Coletor Google Scholar — artigos acadêmicos de tecnologia educacional.

Utiliza a biblioteca 'scholarly' para pesquisar publicações no Google
Scholar sem necessidade de API Key. As queries são focadas em robótica
educacional, cultura maker, realidade virtual e pensamento computacional
no contexto brasileiro.

Aviso: scholarly é síncrono. Para MVP isso é aceitável; em produção,
considere executar em um thread executor para não bloquear o event loop.
"""

import asyncio
import logging
from datetime import datetime, timezone

from scholarly import scholarly

from .base import BaseCollector, RawFinding

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Queries de busca — palavras-chave em português focadas no observatório
# ---------------------------------------------------------------------------
QUERIES: list[str] = [
    # Robótica / Maker / 3D / Pensamento Computacional (existentes)
    "robótica educacional Brasil",
    "cultura maker educação",
    "realidade virtual ensino fundamental",
    "impressão 3D educação",
    "pensamento computacional escola pública",
    # Fase 8.3: IA generativa (diversificado)
    "inteligência artificial educação Brasil",
    "ChatGPT sala de aula professores",
    "IA generativa personalização aprendizado",
    "machine learning ensino fundamental",
    "Gemini AI educação",
    "LLM tutor inteligente ensino",
    "Google AI Studio educação",
    "prompt engineering professores",
]


class ScholarCollector(BaseCollector):
    """Coletor de artigos acadêmicos via Google Scholar."""

    source_slug: str = "scholar"
    source_name: str = "Google Scholar — Artigos de Tecnologia Educacional"
    family: str = "academic"

    async def collect(self) -> list[RawFinding]:
        """
        Pesquisa cada query configurada e coleta até 5 publicações por query.

        7.2 (auditoria Harness 2026-06-27): adicionado asyncio.sleep(5) entre
        queries para evitar banimento por IP no Google Scholar. Sem isto,
        5 queries em sequência podem disparar CAPTCHA ou bloqueio temporário.

        Um erro em uma query não interrompe a coleta das demais.
        """
        findings: list[RawFinding] = []
        for query in QUERIES:
            try:
                items = await self._search(query)
                findings.extend(items)
            except Exception as exc:
                print(f"[scholar] Erro na query '{query}': {exc}")
            # Rate limiting: 5s entre queries (Google Scholar é sensível a scraping)
            await asyncio.sleep(5)
        return findings

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    async def _search(self, query: str) -> list[RawFinding]:
        """
        Executa uma pesquisa no Google Scholar e converte os resultados.

        Args:
            query: String de busca (ex: 'robótica educacional Brasil').

        Returns:
            Lista de RawFinding (até 5 publicações).
        """
        search_query = await asyncio.to_thread(scholarly.search_pubs, query)
        items: list[RawFinding] = []

        for i, pub in enumerate(search_query):
            if i >= 5:  # máximo 5 publicações por query
                break
            try:
                finding = self._parse_publication(pub, query)
                if finding is not None:
                    items.append(finding)
            except Exception as exc:
                print(f"[scholar] Erro na publicação #{i}: {exc}")
                continue

        return items

    def _parse_publication(self, pub: dict, query: str) -> RawFinding | None:
        """
        Converte um resultado do scholarly em RawFinding.

        Args:
            pub: Dicionário com os dados da publicação (formato scholarly).
            query: Query de busca original.

        Returns:
            RawFinding populado ou None se não houver dados mínimos.
        """
        import re

        bib = pub.get("bib", {})
        title = bib.get("title", "Sem título")
        abstract = bib.get("abstract", "")
        url = pub.get("pub_url") or pub.get("eprint_url") or ""
        pub_year = bib.get("pub_year", "")

        if not title or title == "Sem título":
            return None

        # Fase 8.1: filtrar publicações com mais de 1 ano
        # Antes: retornava papers de qualquer época, causando alertas com conteúdo antigo
        current_year = datetime.now(timezone.utc).year

        # Fase 8.4: se pub_year faltar, tentar extrair da URL
        # Muitos papers antigos no Scholar não têm pub_year preenchido,
        # mas a URL frequentemente contém o ano (ex: /2017/, /2022/).
        if not pub_year and url:
            # Padrões comuns:
            # /2017/ (path) | ?year=2020 | &year=2022 | _2021_ | /2024-06-
            year_match = (
                re.search(r"/(20\d{2})/", url)
                or re.search(r"[?&_](?:year|y)=(20\d{2})", url, re.IGNORECASE)
                or re.search(r"[_-](20\d{2})[_-]", url)
            )
            if year_match:
                # Pegar o grupo de captura (apenas os 4 dígitos do ano)
                pub_year = year_match.group(1)
                log.info(f"[scholar] Ano extraído da URL: {pub_year} para '{title[:40]}...'")

        if pub_year:
            try:
                year_int = int(pub_year)
                if year_int < current_year - 1:
                    log.info(
                        f"[scholar] Filtrando paper antigo: '{title[:40]}...' "
                        f"(ano {year_int}, mínimo {current_year - 1})"
                    )
                    return None
            except (ValueError, TypeError):
                pass  # ano inválido, manter finding

        return RawFinding(
            source_slug="scholar",
            source_url=url or f"https://scholar.google.com/scholar?q={query}",
            title=title,
            raw_text=abstract[:10000] if abstract else title,
            language="pt",
            metadata={
                "query": query,
                "year": pub_year or "unknown",
                "author": bib.get("author", ""),
            },
        )
