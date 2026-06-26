"""
Coletor YouTube — busca vídeos educacionais via feeds RSS públicos.

O YouTube disponibiliza feeds RSS para canais sem necessidade de
API Key. Este coletor extrai os vídeos mais recentes de canais
brasileiros de tecnologia educacional, maker e programação.

Canais monitorados:
- Manual do Mundo (maker, experimentos)
- Canal do Ensino (educação geral)
- MakerBot Industries (impressão 3D)
"""
import asyncio
import html
import re
from datetime import datetime, timezone

import httpx

from ..base import BaseCollector, RawFinding

# ---------------------------------------------------------------------------
# Canais YouTube — identificadores usados na URL do feed RSS
#   Formato: "c/NOME" para canais customizados, "user/NOME" para legacy
# ---------------------------------------------------------------------------
CHANNELS: list[str] = [
    "c/ManualdoMundo",          # Maker, experimentos científicos
    "c/CanalDoEnsino",          # Educação em geral
    "user/MakerBotIndustries",  # Impressão 3D e fabricação digital
]


class YouTubeCollector(BaseCollector):
    """Coletor de vídeos educacionais via feeds RSS do YouTube."""

    source_slug: str = "youtube"
    source_name: str = "YouTube — Vídeos Educacionais (feeds RSS)"
    family: str = "social"

    async def collect(self) -> list[RawFinding]:
        """
        Coleta os vídeos mais recentes de cada canal configurado.

        Cada canal contribui com até 5 vídeos por rodada.
        Um erro em um canal não interrompe a coleta dos demais.
        """
        findings: list[RawFinding] = []
        async with httpx.AsyncClient(
            timeout=15.0,
            headers={"User-Agent": "ObservatorioCISEB/1.0"},
        ) as client:
            for channel in CHANNELS:
                try:
                    items = await self._fetch_channel(client, channel)
                    findings.extend(items)
                except Exception as exc:
                    print(f"[youtube] Erro no canal {channel}: {exc}")
        return findings

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    async def _fetch_channel(
        self, client: httpx.AsyncClient, channel: str
    ) -> list[RawFinding]:
        """
        Busca o feed RSS de um canal YouTube e extrai entradas via regex.

        Nota: utiliza regex para parsing XML por simplicidade (MVP).
        Em produção, considere usar xml.etree.ElementTree ou feedparser.

        Args:
            client: Cliente HTTP compartilhado.
            channel: Identificador do canal (ex: 'c/ManualdoMundo').

        Returns:
            Lista de RawFinding (até 5 vídeos).
        """
        # Extrai o nome do canal removendo os prefixos 'c/' ou 'user/'
        channel_name = channel.replace("c/", "").replace("user/", "")
        url = f"https://www.youtube.com/feeds/videos.xml?user={channel_name}"

        response = await client.get(url)
        if response.status_code != 200:
            return []

        # Parse simples do XML via regex (evita dependência extra de XML parser)
        items: list[RawFinding] = []
        entries = re.findall(
            r"<entry>(.*?)</entry>", response.text, re.DOTALL
        )

        for entry_xml in entries[:5]:  # máximo 5 vídeos por canal
            try:
                finding = self._parse_entry(entry_xml, channel)
                if finding is not None:
                    items.append(finding)
            except Exception as exc:
                print(f"[youtube] Erro no item: {exc}")
                continue

        return items

    def _parse_entry(self, entry_xml: str, channel: str) -> RawFinding | None:
        """
        Extrai título e link de uma entrada <entry> do feed RSS do YouTube.

        Args:
            entry_xml: Fragmento XML de uma <entry>.
            channel: Identificador do canal de origem.

        Returns:
            RawFinding populado ou None se não for possível extrair.
        """
        title_match = re.search(r"<title>(.*?)</title>", entry_xml)
        link_match = re.search(
            r'<link rel="alternate" href="([^"]+)"', entry_xml
        )

        if not title_match:
            return None

        title = html.unescape(title_match.group(1))
        link = link_match.group(1) if link_match else ""

        return RawFinding(
            source_slug="youtube",
            source_url=link,
            title=f"[YouTube] {title}",
            raw_text=f"Vídeo educativo: {title}. Disponível em: {link}",
            language="pt",
            metadata={
                "channel": channel,
                "platform": "youtube",
            },
        )
