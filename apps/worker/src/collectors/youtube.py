"""
Coletor YouTube — busca vídeos educacionais via Invidious API pública.

O Invidious é um proxy front-end para o YouTube que oferece uma API
REST pública sem necessidade de API Key. Este coletor utiliza instâncias
públicas do Invidious como fallback para garantir resiliência.

Cada query retorna até 3 vídeos. Com 4 queries, o potencial máximo é
de 12 findings por rodada, visando alcançar ≥5 findings da família
social para o CHECKPOINT F2.1.

Estratégia de fallback:
  1. Tenta instância primária (slipfox.xyz)
  2. Em caso de falha, tenta instância secundária (reallyaweso.me)
  3. Se nenhuma responder, retorna lista vazia para a query
"""

from urllib.parse import quote_plus

import httpx

from .base import BaseCollector, RawFinding

# ---------------------------------------------------------------------------
# Instâncias públicas do Invidious (ordenadas por preferência)
# ---------------------------------------------------------------------------
INVIDIOUS_INSTANCES: list[str] = [
    "https://invidious.slipfox.xyz",
    "https://invidious.reallyaweso.me",
]

# ---------------------------------------------------------------------------
# Palavras-chave de busca em português
# ---------------------------------------------------------------------------
SEARCH_QUERIES: list[str] = [
    "robótica educacional",
    "impressão 3D escola",
    "programação crianças scratch",
    "arduino projeto educativo",
]

# ---------------------------------------------------------------------------
# Constantes de coleta
# ---------------------------------------------------------------------------
MAX_VIDEOS_PER_QUERY: int = 3
INVIDIOUS_TIMEOUT: float = 15.0


class YouTubeCollector(BaseCollector):
    """Coletor de vídeos educacionais via Invidious API pública."""

    source_slug: str = "youtube"
    source_name: str = "YouTube — Vídeos Educacionais (Invidious)"
    family: str = "social"

    async def collect(self) -> list[RawFinding]:
        """
        Coleta vídeos para cada palavra-chave configurada.

        Cada query é processada independentemente; um erro em uma query
        não interrompe a coleta das demais. O mecanismo de fallback entre
        instâncias Invidious garante resiliência contra indisponibilidade
        de servidores proxy.

        Returns:
            Lista de RawFinding para inserção no banco.
        """
        findings: list[RawFinding] = []
        async with httpx.AsyncClient(
            timeout=INVIDIOUS_TIMEOUT,
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
        Busca vídeos via Invidious API com fallback entre instâncias.

        O endpoint utilizado é:
          {instance}/api/v1/search?q={query}&type=video&sort=relevance

        A API do Invidious é gratuita, não requer autenticação e retorna
        JSON estruturado com campos como: title, videoId, author,
        lengthSeconds, description.

        Args:
            client: Cliente HTTP compartilhado.
            query: Palavra-chave de busca (será URL-encoded).

        Returns:
            Lista de RawFinding (até MAX_VIDEOS_PER_QUERY por query).
            Lista vazia se nenhuma instância responder com sucesso.
        """
        for instance in INVIDIOUS_INSTANCES:
            try:
                url = (
                    f"{instance}/api/v1/search"
                    f"?q={quote_plus(query)}"
                    f"&type=video"
                    f"&sort=relevance"
                )
                response = await client.get(url)

                if response.status_code != 200:
                    print(
                        f"[youtube] Invidious {instance} "
                        f"status {response.status_code}"
                    )
                    continue  # Tenta próxima instância

                data = response.json()

                items: list[RawFinding] = []
                for video in data[:MAX_VIDEOS_PER_QUERY]:
                    # Validação mínima: precisa de videoId e title
                    video_id = video.get("videoId", "")
                    title = video.get("title", "")
                    if not video_id or not title:
                        continue

                    # Monta texto bruto com metadados do vídeo
                    author = video.get("author", "Canal desconhecido")
                    duration = video.get("lengthSeconds", 0)
                    description = video.get("description", "")[:500]

                    finding = RawFinding(
                        source_slug="youtube",
                        source_url=(
                            f"https://youtube.com/watch?v={video_id}"
                        ),
                        title=f"[YouTube] {title}",
                        raw_text=(
                            f"Vídeo: {title}. "
                            f"Canal: {author}. "
                            f"Duração: {duration}s. "
                            f"{description}"
                        ),
                        language="pt",
                        metadata={
                            "query": query,
                            "channel": author,
                            "platform": "youtube",
                            "duration_seconds": duration,
                        },
                    )
                    items.append(finding)

                return items  # Sucesso — não tenta outras instâncias

            except Exception as exc:
                print(
                    f"[youtube] Erro Invidious {instance}: {exc}"
                )
                continue  # Tenta próxima instância

        # Nenhuma instância respondeu com sucesso
        return []
