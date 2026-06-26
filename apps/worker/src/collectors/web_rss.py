"""
Coletor RSS/Web — feeds de educação e tecnologia educacional.

Fontes:
- Porvir (https://porvir.org/feed/)

Nota: O feed da Nova Escola (https://novaescola.org.br/conteudo/feed)
foi removido em 2026-06-26 pois retornava HTTP 404 consistentemente.

Utiliza feedparser para parsing de RSS e trafilatura para extrair
texto limpo do corpo completo dos artigos (fallback para summary).
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

import feedparser
import httpx
from trafilatura import extract

from .base import BaseCollector, RawFinding

# ---------------------------------------------------------------------------
# Configuração dos feeds RSS
# ---------------------------------------------------------------------------
FEEDS: list[dict] = [
    {
        "url": "https://porvir.org/feed/",
        "slug": "porvir-rss",
        "name": "Porvir - Inovações em Educação",
    },
]


class WebRSSCollector(BaseCollector):
    """Coletor RSS/Web para feeds de educação e tecnologia educacional."""

    source_slug: str = "rss-web"
    source_name: str = "Coletor RSS/Web (Porvir)"
    family: str = "web"

    async def collect(self) -> list[RawFinding]:
        """
        Coleta entradas de todos os feeds RSS configurados.

        Cada feed contribui com até 10 entradas por rodada.
        Um erro em um feed não interrompe a coleta dos demais.
        """
        findings: list[RawFinding] = []
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "ObservatorioCISEB/1.0"},
        ) as client:
            for feed_cfg in FEEDS:
                try:
                    items = await self._fetch_feed(client, feed_cfg)
                    findings.extend(items)
                except Exception as exc:
                    print(f"[web_rss] Erro no feed {feed_cfg['slug']}: {exc}")
        return findings

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    async def _fetch_feed(
        self, client: httpx.AsyncClient, feed_cfg: dict
    ) -> list[RawFinding]:
        """
        Busca e parseia um único feed RSS.

        Args:
            client: Cliente HTTP compartilhado.
            feed_cfg: Dicionário com 'url', 'slug' e 'name' do feed.

        Returns:
            Lista de RawFinding (até 10 entradas).
        """
        response = await client.get(feed_cfg["url"])
        response.raise_for_status()

        # feedparser aceita string XML diretamente
        feed = feedparser.parse(response.text)

        items: list[RawFinding] = []
        for entry in feed.entries[:10]:  # máximo 10 entradas por feed por rodada
            try:
                item = await self._parse_entry(client, feed_cfg, entry)
                if item is not None:
                    items.append(item)
            except Exception as exc:
                print(f"[web_rss] Erro no item '{entry.get('title', '???')}': {exc}")
                continue

        return items

    async def _parse_entry(
        self,
        client: httpx.AsyncClient,
        feed_cfg: dict,
        entry: dict,
    ) -> Optional[RawFinding]:
        """
        Converte uma entrada do feedparser em RawFinding.

        Tenta extrair o texto completo do artigo via trafilatura; se falhar,
        utiliza o summary/resumo do RSS como fallback.
        """
        title = (entry.get("title") or "Sem título").strip()
        link = entry.get("link") or ""
        raw_text = entry.get("summary") or entry.get("description") or ""

        # Tenta extrair o texto completo do artigo original
        if link:
            try:
                article_resp = await client.get(link)
                # trafilatura.extract retorna None se não conseguir extrair
                extracted = extract(
                    article_resp.text,
                    include_comments=False,
                    output_format="txt",
                )
                if extracted:
                    raw_text = extracted[:10000]  # trunca para 10k caracteres
            except Exception:
                # Fallback silencioso — usa o summary do RSS
                pass

        return RawFinding(
            source_slug=feed_cfg["slug"],
            source_url=link or feed_cfg["url"],
            title=title,
            raw_text=raw_text[:10000],
            language="pt",
            metadata={
                "feed": feed_cfg["slug"],
                "published_at": entry.get("published", ""),
                "author": entry.get("author", ""),
            },
        )
