"""
Coletor YouTube — busca vídeos educacionais via feed RSS de pesquisa.

O YouTube disponibiliza feeds RSS para resultados de busca sem
necessidade de API Key. Este coletor pesquisa palavras-chave
relevantes (robótica educacional, impressão 3D, programação para
crianças, Arduino, micro:bit, cultura maker) e extrai os vídeos
mais recentes dos resultados.

Cada query retorna até 3 vídeos, totalizando potencialmente 18
findings por rodada (6 queries × 3 vídeos), garantindo volume
suficiente para o CHECKPOINT F2.1.
"""
import html
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx

from .base import BaseCollector, RawFinding

# ---------------------------------------------------------------------------
# Palavras-chave de busca no YouTube (feed RSS público)
# ---------------------------------------------------------------------------
SEARCH_QUERIES: list[str] = [
    "robótica educacional",
    "impressão 3D educação",
    "programação para crianças",
    "arduino aula",
    "microbit tutorial",
    "cultura maker escola",
]


class YouTubeCollector(BaseCollector):
    """Coletor de vídeos educacionais via feed RSS de busca do YouTube."""

    source_slug: str = "youtube"
    source_name: str = "YouTube — Vídeos Educacionais (busca RSS)"
    family: str = "social"

    async def collect(self) -> list[RawFinding]:
        """
        Coleta vídeos para cada palavra-chave configurada.

        Cada query contribui com até 3 vídeos por rodada.
        Um erro em uma query não interrompe a coleta das demais.
        """
        findings: list[RawFinding] = []
        async with httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": "ObservatorioCISEB/1.0"},
        ) as client:
            for query in SEARCH_QUERIES:
                try:
                    items = await self._search(client, query)
                    findings.extend(items)
                    print(
                        f"[youtube] Query '{query}' → {len(items)} vídeos"
                    )
                except Exception as exc:
                    print(f"[youtube] Erro na query '{query}': {exc}")
        return findings

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    async def _search(
        self, client: httpx.AsyncClient, query: str
    ) -> list[RawFinding]:
        """
        Busca vídeos via feed RSS de pesquisa do YouTube.

        O endpoint https://www.youtube.com/feeds/videos.xml?q=...
        retorna um feed Atom com os resultados da busca, sem
        necessidade de autenticação.

        Args:
            client: Cliente HTTP compartilhado.
            query: Palavra-chave de busca (será URL-encoded).

        Returns:
            Lista de RawFinding (até 3 vídeos por query).
        """
        url = (
            f"https://www.youtube.com/feeds/videos.xml"
            f"?q={quote_plus(query)}"
        )
        response = await client.get(url)

        if response.status_code != 200:
            print(
                f"[youtube] Status {response.status_code} "
                f"para query '{query}'"
            )
            return []

        items: list[RawFinding] = []
        entries = re.findall(
            r"<entry>(.*?)</entry>", response.text, re.DOTALL
        )

        for entry_xml in entries[:3]:  # máximo 3 vídeos por query
            try:
                finding = self._parse_entry(entry_xml, query)
                if finding is not None:
                    items.append(finding)
            except Exception as exc:
                print(f"[youtube] Erro ao parse entry: {exc}")
                continue

        return items

    def _parse_entry(self, entry_xml: str, query: str) -> RawFinding | None:
        """
        Extrai título, link e autor de uma entrada <entry> do feed Atom.

        Args:
            entry_xml: Fragmento XML de uma <entry>.
            query: Palavra-chave de busca que originou este resultado.

        Returns:
            RawFinding populado ou None se não for possível extrair
            os campos mínimos (título).
        """
        # Extrai título (obrigatório)
        title_match = re.search(r"<title>(.*?)</title>", entry_xml)
        if not title_match:
            return None

        # Extrai link alternativo (href do vídeo)
        link_match = re.search(
            r'<link rel="alternate" href="([^"]+)"', entry_xml
        )

        # Extrai nome do autor/canal
        author_match = re.search(
            r"<author>.*?<name>(.*?)</name>", entry_xml, re.DOTALL
        )

        title = html.unescape(title_match.group(1))
        link = link_match.group(1) if link_match else ""
        author = (
            html.unescape(author_match.group(1))
            if author_match
            else "Canal desconhecido"
        )

        return RawFinding(
            source_slug="youtube",
            source_url=link,
            title=f"[YouTube] {title}",
            raw_text=(
                f"Vídeo educativo sobre '{query}': {title}. "
                f"Canal: {author}. Link: {link}"
            ),
            language="pt",
            metadata={
                "query": query,
                "channel": author,
                "platform": "youtube",
            },
        )
