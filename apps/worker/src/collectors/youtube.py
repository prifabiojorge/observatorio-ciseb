"""
Coletor YouTube — busca vídeos educacionais.

Fase 8.2 (auditoria Harness 2026-06-29):
- Primário: YouTube Data API v3 (oficial Google, 10k quota/dia gratuito)
- Fallback: Invidious API (5 instâncias públicas)
- Antes: apenas Invidious (0 findings desde F2.1)

Estratégia:
  1. Se YOUTUBE_API_KEY configurada → usar Data API v3
  2. Se API falhar/quota exceder → tentar Invidious (5 instâncias)
  3. Se nenhuma responder → retorna lista vazia

Quota: 1 search = 100 units. 8 queries = 800 units/dia (limite 10k).
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote_plus

import httpx

from .base import BaseCollector, RawFinding

# ---------------------------------------------------------------------------
# Configuração — YouTube Data API v3 (primário)
# ---------------------------------------------------------------------------
YOUTUBE_API_KEY: str = os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_API_URL: str = "https://www.googleapis.com/youtube/v3/search"

# ---------------------------------------------------------------------------
# Configuração — Invidious (fallback)
# ---------------------------------------------------------------------------
INVIDIOUS_INSTANCES: list[str] = [
    "https://yewtu.be",
    "https://invidious.nerdvpn.de",
    "https://inv.nadeko.net",
    "https://invidious.jing.rocks",
    "https://invidious.slipfox.xyz",
    "https://invidious.reallyaweso.me",
]

# ---------------------------------------------------------------------------
# Palavras-chave de busca — diversificadas (Fase 8.3)
# ---------------------------------------------------------------------------
SEARCH_QUERIES: list[str] = [
    # Robótica / Maker / 3D (existentes)
    "robótica educacional",
    "impressão 3D escola",
    "programação crianças scratch",
    "arduino projeto educativo",
    # Fase 8.3: IA (diversificado)
    "inteligência artificial educação",
    "ChatGPT professores",
    "Gemini AI Google educação",
    "Google AI Studio tutorial",
    "IA sala de aula ensino médio",
]

MAX_VIDEOS_PER_QUERY: int = 3
YOUTUBE_TIMEOUT: float = 15.0


class YouTubeCollector(BaseCollector):
    """Coletor de vídeos educacionais via YouTube Data API v3 + Invidious fallback."""

    source_slug: str = "youtube"
    source_name: str = "YouTube — Vídeos Educacionais (Data API v3 + Invidious)"
    family: str = "social"

    async def collect(self) -> list[RawFinding]:
        """
        Coleta vídeos para cada palavra-chave configurada.

        Estratégia Fase 8.2:
        1. Se YOUTUBE_API_KEY configurada → Data API v3 (primário)
        2. Se API falhar/quota exceder → Invidious (fallback)
        3. Se nenhuma responder → lista vazia

        Returns:
            Lista de RawFinding para inserção no banco.
        """
        findings: list[RawFinding] = []

        for query in SEARCH_QUERIES:
            try:
                if YOUTUBE_API_KEY:
                    items = await self._search_via_api(query)
                    if items:
                        findings.extend(items)
                        continue  # API v3 sucesso, não tenta Invidious
                # Fallback Invidious
                items = await self._search_via_invidious(query)
                findings.extend(items)
            except Exception as exc:
                print(f"[youtube] Erro na query '{query}': {exc}")
        return findings

    # ------------------------------------------------------------------
    # Primário: YouTube Data API v3
    # ------------------------------------------------------------------

    async def _search_via_api(self, query: str) -> list[RawFinding]:
        """
        Busca vídeos via YouTube Data API v3.

        Custo: 100 units por search. 8 queries = 800 units/dia (limite 10k).
        Filtro: order=date + publishedAfter=últimos 30 dias (Fase 8.1).
        """
        # Fase 8.1: apenas vídeos dos últimos 30 dias
        published_after = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": MAX_VIDEOS_PER_QUERY,
            "order": "date",  # mais recentes primeiro
            "publishedAfter": published_after,
            "relevanceLanguage": "pt",  # priorizar português
            "key": YOUTUBE_API_KEY,
        }

        try:
            async with httpx.AsyncClient(timeout=YOUTUBE_TIMEOUT) as client:
                response = await client.get(YOUTUBE_API_URL, params=params)

                if response.status_code == 403:
                    # Quota excedida ou API key inválida
                    print(
                        f"[youtube] API v3 403 (quota/key) para query '{query}': "
                        f"{response.text[:100]}"
                    )
                    return []

                response.raise_for_status()
                data = response.json()

                items: list[RawFinding] = []
                for video in data.get("items", []):
                    finding = self._parse_api_video(video, query)
                    if finding is not None:
                        items.append(finding)

                print(f"[youtube] API v3 query '{query}' → {len(items)} vídeos")
                return items

        except Exception as exc:
            print(f"[youtube] API v3 erro na query '{query}': {exc}")
            return []

    def _parse_api_video(self, video: dict, query: str) -> Optional[RawFinding]:
        """Converte resultado da Data API v3 em RawFinding."""
        video_id = video.get("id", {}).get("videoId", "")
        if not video_id:
            return None

        snippet = video.get("snippet", {})
        title = snippet.get("title", "").strip()
        if not title:
            return None

        author = snippet.get("channelTitle", "Canal desconhecido")
        description = snippet.get("description", "")[:500]
        published_at = snippet.get("publishedAt", "")

        return RawFinding(
            source_slug="youtube",
            source_url=f"https://youtube.com/watch?v={video_id}",
            title=f"[YouTube] {title}",
            raw_text=f"Vídeo: {title}. Canal: {author}. Publicado: {published_at}. {description}",
            language="pt",
            metadata={
                "query": query,
                "channel": author,
                "platform": "youtube",
                "published_at": published_at,
                "video_id": video_id,
            },
        )

    # ------------------------------------------------------------------
    # Fallback: Invidious
    # ------------------------------------------------------------------

    async def _search_via_invidious(self, query: str) -> list[RawFinding]:
        """
        Busca vídeos via Invidious API com fallback entre instâncias.

        Usado quando YOUTUBE_API_KEY não configurada ou quota excedida.
        """
        async with httpx.AsyncClient(
            timeout=YOUTUBE_TIMEOUT,
            headers={"User-Agent": "ObservatorioCISEB/1.0"},
        ) as client:
            for instance in INVIDIOUS_INSTANCES:
                try:
                    url = (
                        f"{instance}/api/v1/search"
                        f"?q={quote_plus(query)}"
                        f"&type=video"
                        f"&sort_by=date"  # Fase 8.1: mais recentes primeiro
                    )
                    response = await client.get(url)

                    if response.status_code != 200:
                        print(f"[youtube] Invidious {instance} status {response.status_code}")
                        continue

                    data = response.json()
                    items: list[RawFinding] = []
                    for video in data[:MAX_VIDEOS_PER_QUERY]:
                        video_id = video.get("videoId", "")
                        title = video.get("title", "")
                        if not video_id or not title:
                            continue

                        author = video.get("author", "Canal desconhecido")
                        duration = video.get("lengthSeconds", 0)
                        description = video.get("description", "")[:500]
                        published_at = video.get("published", "")

                        finding = RawFinding(
                            source_slug="youtube",
                            source_url=f"https://youtube.com/watch?v={video_id}",
                            title=f"[YouTube] {title}",
                            raw_text=(
                                f"Vídeo: {title}. "
                                f"Canal: {author}. "
                                f"Duração: {duration}s. "
                                f"Publicado: {published_at}. "
                                f"{description}"
                            ),
                            language="pt",
                            metadata={
                                "query": query,
                                "channel": author,
                                "platform": "youtube",
                                "published_at": published_at,
                                "duration_seconds": duration,
                            },
                        )
                        items.append(finding)

                    print(f"[youtube] Invidious {instance} query '{query}' → {len(items)} vídeos")
                    return items

                except Exception as exc:
                    print(f"[youtube] Erro Invidious {instance}: {exc}")
                    continue

        return []
