"""
Coletor GitHub — busca repositórios de tecnologia educacional.

Estratégia: pesquisa por tópicos (topics) via GitHub Search API.
Sem autenticação = limite de 60 req/h (suficiente para MVP com
sleep de 2s entre chamadas, resultando em ~30 req/h).

Tópicos pesquisados: educational-robotics, microbit-education,
scratch-education, arduino-education, maker-education,
impressao-3d-educacao, ensino-programacao, educational-technology.
"""
import asyncio
from datetime import datetime, timezone

import httpx

from ..base import BaseCollector, RawFinding

# ---------------------------------------------------------------------------
# Tópicos de busca — palavras-chave relevantes para o observatório
# ---------------------------------------------------------------------------
TOPICS: list[str] = [
    "educational-robotics",
    "robotics-education",
    "microbit-education",
    "scratch-education",
    "arduino-education",
    "maker-education",
    "impressao-3d-educacao",
    "ensino-programacao",
    "educational-technology",
]


class GitHubCollector(BaseCollector):
    """Coletor de repositórios GitHub por tópicos educacionais."""

    source_slug: str = "github"
    source_name: str = "GitHub — Repositórios de Tecnologia Educacional"
    family: str = "github"

    async def collect(self) -> list[RawFinding]:
        """
        Pesquisa cada tópico configurado e coleta até 5 repositórios por tópico.

        Rate limiting: sleep de 2s entre tópicos (~30 req/min, seguro
        para o limite de 60 req/h sem token de autenticação).
        """
        findings: list[RawFinding] = []
        async with httpx.AsyncClient(
            timeout=15.0,
            headers={
                "User-Agent": "ObservatorioCISEB/1.0",
                "Accept": "application/vnd.github.v3+json",
            },
        ) as client:
            for topic in TOPICS:
                try:
                    items = await self._search_topic(client, topic)
                    findings.extend(items)
                    # Rate limiting: 2s entre chamadas (~30 req/min)
                    await asyncio.sleep(2)
                except Exception as exc:
                    print(f"[github] Erro no tópico {topic}: {exc}")
        return findings

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    async def _search_topic(
        self, client: httpx.AsyncClient, topic: str
    ) -> list[RawFinding]:
        """
        Busca repositórios no GitHub pelo tópico informado.

        Args:
            client: Cliente HTTP compartilhado.
            topic: Tópico a ser pesquisado (ex: 'educational-robotics').

        Returns:
            Lista de RawFinding (até 5 repositórios).
        """
        url = (
            f"https://api.github.com/search/repositories"
            f"?q=topic:{topic}+language:pt"
            f"&sort=updated"
            f"&per_page=5"
        )
        response = await client.get(url)

        # Rate limit atingido — GitHub retorna 403
        if response.status_code == 403:
            print(f"[github] Rate limit atingido para tópico '{topic}'")
            return []

        response.raise_for_status()
        data = response.json()

        items: list[RawFinding] = []
        for repo in data.get("items", []):
            try:
                finding = RawFinding(
                    source_slug="github",
                    source_url=repo.get("html_url", ""),
                    title=repo.get("full_name", ""),
                    raw_text=repo.get("description") or "",
                    language=(
                        "pt"
                        if "pt" in (repo.get("language") or "").lower()
                        else "en"
                    ),
                    metadata={
                        "topic": topic,
                        "stars": repo.get("stargazers_count", 0),
                        "updated_at": repo.get("updated_at", ""),
                        "topics": repo.get("topics", []),
                    },
                )
                items.append(finding)
            except Exception as exc:
                print(f"[github] Erro no repositório: {exc}")
                continue

        return items
