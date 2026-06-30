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
import os
from datetime import datetime, timedelta, timezone

import httpx

from .base import BaseCollector, RawFinding

# Fase 8.5: GitHub token opcional (aumenta limite de 60 → 5000 req/h)
# Criar em: https://github.com/settings/tokens → Fine-grained PAT → Contents: Read-only
GITHUB_TOKEN: str = os.environ.get("GITHUB_TOKEN", "")

# ---------------------------------------------------------------------------
# Tópicos de busca — palavras-chave relevantes para o observatório
# ---------------------------------------------------------------------------
TOPICS: list[str] = [
    # Robótica / Maker / 3D / Programação (existentes)
    "educational-robotics",
    "robotics-education",
    "microbit-education",
    "scratch-education",
    "arduino-education",
    "maker-education",
    "impressao-3d-educacao",
    "ensino-programacao",
    "educational-technology",
    # Fase 8.3: IA generativa (diversificado)
    "ai-education",
    "ai-teaching",
    "chatgpt-education",
    "llm-education",
    "machine-learning-education",
    "gemini-education",
    "ai-studio",
    "prompt-engineering-education",
    "generative-ai-education",
    "ai-tutor",
]


class GitHubCollector(BaseCollector):
    """Coletor de repositórios GitHub por tópicos educacionais."""

    source_slug: str = "github"
    source_name: str = "GitHub — Repositórios de Tecnologia Educacional"
    family: str = "github"

    async def collect(self) -> list[RawFinding]:
        """
        Pesquisa cada tópico configurado e coleta até 5 repositórios por tópico.

        Fase 8.5: rate limiting ajustado.
        - Com GITHUB_TOKEN: 1s entre topics (limite 5000 req/h)
        - Sem GITHUB_TOKEN: 4s entre topics (limite 60 req/h, 19 topics = 76s)
        """
        findings: list[RawFinding] = []
        headers = {
            "User-Agent": "ObservatorioCISEB/1.0",
            "Accept": "application/vnd.github.v3+json",
        }
        # Fase 8.5: adicionar Authorization header se token configurado
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"

        sleep_seconds = 1 if GITHUB_TOKEN else 4

        async with httpx.AsyncClient(
            timeout=15.0,
            headers=headers,
        ) as client:
            for topic in TOPICS:
                try:
                    items = await self._search_topic(client, topic)
                    findings.extend(items)
                    # Rate limiting: 1s com token, 4s sem token
                    await asyncio.sleep(sleep_seconds)
                except Exception as exc:
                    print(f"[github] Erro no tópico {topic}: {exc}")
        return findings

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    async def _search_topic(self, client: httpx.AsyncClient, topic: str) -> list[RawFinding]:
        """
        Busca repositórios no GitHub pelo tópico informado.

        Args:
            client: Cliente HTTP compartilhado.
            topic: Tópico a ser pesquisado (ex: 'educational-robotics').

        Returns:
            Lista de RawFinding (até 5 repositórios).
        """
        # Fase 8.1: apenas repos atualizados nos últimos 90 dias
        # Antes: retornava repos antigos, causando alertas com conteúdo stale
        date_filter = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
        url = (
            f"https://api.github.com/search/repositories"
            f"?q=topic:{topic}+pushed:>{date_filter}"
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
                    language="pt",  # Idioma do conteúdo assumido pt-BR para tópicos educacionais brasileiros
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
