"""
Coletor Google Scholar — artigos acadêmicos de tecnologia educacional.

Utiliza a biblioteca 'scholarly' para pesquisar publicações no Google
Scholar sem necessidade de API Key. As queries são focadas em robótica
educacional, cultura maker, realidade virtual e pensamento computacional
no contexto brasileiro.

Aviso: scholarly é síncrono. Para MVP isso é aceitável; em produção,
considere executar em um thread executor para não bloquear o event loop.
"""
from datetime import datetime, timezone

from scholarly import scholarly

from ..base import BaseCollector, RawFinding

# ---------------------------------------------------------------------------
# Queries de busca — palavras-chave em português focadas no observatório
# ---------------------------------------------------------------------------
QUERIES: list[str] = [
    "robótica educacional Brasil",
    "cultura maker educação",
    "realidade virtual ensino fundamental",
    "impressão 3D educação",
    "pensamento computacional escola pública",
]


class ScholarCollector(BaseCollector):
    """Coletor de artigos acadêmicos via Google Scholar."""

    source_slug: str = "scholar"
    source_name: str = "Google Scholar — Artigos de Tecnologia Educacional"
    family: str = "academic"

    async def collect(self) -> list[RawFinding]:
        """
        Pesquisa cada query configurada e coleta até 5 publicações por query.

        Um erro em uma query não interrompe a coleta das demais.
        """
        findings: list[RawFinding] = []
        for query in QUERIES:
            try:
                items = self._search(query)
                findings.extend(items)
            except Exception as exc:
                print(f"[scholar] Erro na query '{query}': {exc}")
        return findings

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _search(self, query: str) -> list[RawFinding]:
        """
        Executa uma pesquisa no Google Scholar e converte os resultados.

        Args:
            query: String de busca (ex: 'robótica educacional Brasil').

        Returns:
            Lista de RawFinding (até 5 publicações).
        """
        search_query = scholarly.search_pubs(query)
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

    def _parse_publication(
        self, pub: dict, query: str
    ) -> RawFinding | None:
        """
        Converte um resultado do scholarly em RawFinding.

        Args:
            pub: Dicionário com os dados da publicação (formato scholarly).
            query: Query de busca original.

        Returns:
            RawFinding populado ou None se não houver dados mínimos.
        """
        bib = pub.get("bib", {})
        title = bib.get("title", "Sem título")
        abstract = bib.get("abstract", "")
        url = pub.get("pub_url") or pub.get("eprint_url") or ""

        if not title or title == "Sem título":
            return None

        return RawFinding(
            source_slug="scholar",
            source_url=url or f"https://scholar.google.com/scholar?q={query}",
            title=title,
            raw_text=abstract[:10000] if abstract else title,
            language="pt",
            metadata={
                "query": query,
                "year": bib.get("pub_year", ""),
                "author": bib.get("author", ""),
            },
        )
