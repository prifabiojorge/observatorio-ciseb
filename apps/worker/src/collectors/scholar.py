"""
Coletor Google Scholar — artigos acadêmicos de tecnologia educacional.

Fase 8.9: scholarly executado em SUBPROCESSO ISOLADO com timeout.
Se scholarly receber CAPTCHA ou crashar (OOM), o processo principal
continua intacto.
"""
import asyncio
import json
import logging
import re
import sys
from datetime import datetime, timezone

from .base import BaseCollector, RawFinding

log = logging.getLogger(__name__)

QUERIES: list[str] = [
    "robótica educacional Brasil",
    "cultura maker educação",
    "realidade virtual ensino fundamental",
    "impressão 3D educação",
    "pensamento computacional escola pública",
    "inteligência artificial educação Brasil",
    "ChatGPT sala de aula professores",
    "IA generativa personalização aprendizado",
    "machine learning ensino fundamental",
    "Gemini AI educação",
    "LLM tutor inteligente ensino",
    "Google AI Studio educação",
    "prompt engineering professores",
]

SCHOLAR_TIMEOUT_SECONDS = 60


class ScholarCollector(BaseCollector):
    """Coletor de artigos acadêmicos via Google Scholar (subprocesso isolado)."""

    source_slug: str = "scholar"
    source_name: str = "Google Scholar — Artigos de Tecnologia Educacional"
    family: str = "academic"

    async def collect(self) -> list[RawFinding]:
        findings: list[RawFinding] = []
        for query in QUERIES:
            try:
                items = await self._search_isolated(query)
                findings.extend(items)
            except Exception as exc:
                log.warning(f"[scholar] Erro na query '{query}': {exc}")
            await asyncio.sleep(5)
        return findings

    async def _search_isolated(self, query: str) -> list[RawFinding]:
        """Executa busca em subprocesso isolado com timeout."""
        script = f"""
import json, sys
try:
    from scholarly import scholarly
    pubs = list(scholarly.search_pubs({repr(query)}))[:5]
    results = []
    for pub in pubs:
        bib = pub.get("bib", {{}})
        results.append({{
            "title": bib.get("title", ""),
            "abstract": bib.get("abstract", ""),
            "url": pub.get("pub_url") or pub.get("eprint_url") or "",
            "pub_year": bib.get("pub_year", ""),
            "author": bib.get("author", ""),
        }})
    print(json.dumps(results))
except SystemExit:
    print("[]")
except Exception:
    print("[]")
"""
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-c", script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/app",
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=SCHOLAR_TIMEOUT_SECONDS
            )
            if proc.returncode != 0:
                log.warning(f"[scholar] Subprocesso falhou para '{query}'")
                return []
            data = json.loads(stdout.decode().strip())
            if not data:
                return []
            items: list[RawFinding] = []
            for pub_data in data:
                finding = self._parse_publication(pub_data, query)
                if finding is not None:
                    items.append(finding)
            log.info(f"[scholar] Query '{query}' → {len(items)} publicações")
            return items
        except asyncio.TimeoutError:
            log.warning(f"[scholar] Timeout ({SCHOLAR_TIMEOUT_SECONDS}s) para '{query}'")
            return []
        except Exception as exc:
            log.warning(f"[scholar] Erro para '{query}': {exc}")
            return []

    def _parse_publication(self, pub: dict, query: str) -> RawFinding | None:
        title = pub.get("title", "Sem título")
        abstract = pub.get("abstract", "")
        url = pub.get("url", "")
        pub_year = pub.get("pub_year", "")

        if not title or title == "Sem título":
            return None

        current_year = datetime.now(timezone.utc).year
        if not pub_year and url:
            year_match = (
                re.search(r"/(20\d{2})/", url)
                or re.search(r"[?&_](?:year|y)=(20\d{2})", url, re.IGNORECASE)
                or re.search(r"[_-](20\d{2})[_-]", url)
            )
            if year_match:
                pub_year = year_match.group(1)

        if pub_year:
            try:
                year_int = int(pub_year)
                if year_int < current_year - 1:
                    return None
            except (ValueError, TypeError):
                pass

        return RawFinding(
            source_slug="scholar",
            source_url=url or f"https://scholar.google.com/scholar?q={query}",
            title=title,
            raw_text=abstract[:10000] if abstract else title,
            language="pt",
            metadata={
                "query": query,
                "year": pub_year or "unknown",
                "author": pub.get("author", ""),
            },
        )
