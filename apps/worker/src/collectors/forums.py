"""
Coletor Reddit/Forums — posts de comunidades de tecnologia e educação.

Utiliza a Reddit JSON API pública (sem autenticação) para buscar os posts
mais recentes de subreddits relevantes. Basta adicionar '.json' ao final
de qualquer URL do Reddit para obter os dados em formato JSON.

Subreddits monitorados (comunidades ativas e verificadas):
- r/Python (programação — comunidade enorme, sempre ativa)
- r/arduino (Arduino — projetos, tutoriais)
- r/3Dprinting (impressão 3D)
- r/robotics (robótica)
- r/learnprogramming (aprendizado de programação)
- r/educationalgifs (GIFs educativos)
"""

import httpx

from .base import BaseCollector, RawFinding

# ---------------------------------------------------------------------------
# Subreddits monitorados — comunidades ativas verificadas em 2026-06
# ---------------------------------------------------------------------------
SUBREDDITS: list[str] = [
    "Python",
    "arduino",
    "3Dprinting",
    "robotics",
    "learnprogramming",
    "educationalgifs",
]


class ForumsCollector(BaseCollector):
    """Coletor de posts do Reddit em comunidades de tecnologia e educação."""

    source_slug: str = "reddit"
    source_name: str = "Reddit — Comunidades de Tecnologia e Educação"
    family: str = "forums"

    async def collect(self) -> list[RawFinding]:
        """
        Busca os posts mais recentes de cada subreddit configurado.

        Cada subreddit contribui com até 5 posts por rodada.
        Um erro em um subreddit não interrompe a coleta dos demais.
        """
        findings: list[RawFinding] = []
        async with httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": "ObservatorioCISEB/1.0"},
        ) as client:
            for sub in SUBREDDITS:
                try:
                    items = await self._fetch_subreddit(client, sub)
                    findings.extend(items)
                except Exception as exc:
                    print(f"[forums] Erro no subreddit r/{sub}: {exc}")
        return findings

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    async def _fetch_subreddit(self, client: httpx.AsyncClient, sub: str) -> list[RawFinding]:
        """
        Busca posts recentes de um subreddit via API JSON pública.

        Args:
            client: Cliente HTTP compartilhado.
            sub: Nome do subreddit (ex: 'programacao').

        Returns:
            Lista de RawFinding (até 5 posts).
        """
        url = f"https://www.reddit.com/r/{sub}/new.json?limit=10"
        response = await client.get(url)

        if response.status_code != 200:
            return []

        data = response.json()
        items: list[RawFinding] = []

        for post in data.get("data", {}).get("children", []):
            try:
                finding = self._parse_post(post, sub)
                if finding is not None:
                    items.append(finding)
            except Exception as exc:
                print(f"[forums] Erro no post de r/{sub}: {exc}")
                continue

        return items

    def _parse_post(self, post: dict, sub: str) -> RawFinding | None:
        """
        Converte um post da API do Reddit em RawFinding.

        Args:
            post: Dicionário do post (formato Reddit JSON API).
            sub: Nome do subreddit de origem.

        Returns:
            RawFinding populado ou None se não houver dados mínimos.
        """
        post_data = post.get("data", {})
        title = post_data.get("title", "").strip()
        selftext = post_data.get("selftext", "").strip()
        permalink = post_data.get("permalink", "")

        if not title:
            return None

        # Constrói URL completa do post
        full_url = f"https://www.reddit.com{permalink}" if permalink else ""

        # Todos os subreddits monitorados são comunidades em inglês
        language = "en"

        return RawFinding(
            source_slug="reddit",
            source_url=full_url,
            title=f"[r/{sub}] {title}",
            raw_text=selftext[:10000] if selftext else title,
            language=language,
            metadata={
                "subreddit": sub,
                "score": post_data.get("score", 0),
                "num_comments": post_data.get("num_comments", 0),
            },
        )
