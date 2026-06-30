"""
Coletor base abstrato — interface comum para todos os coletores.
Cada coletor implementa collect() e retorna lista de RawFinding.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class RawFinding:
    """
    Achado bruto antes da inserção no banco.
    Representa o contrato de evento definido em memoria/06_CONTRATOS_E_SCHEMAS.md.
    """

    source_slug: str
    source_url: str
    title: str
    raw_text: str
    language: str = "pt"
    metadata: dict = field(default_factory=dict)
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BaseCollector(ABC):
    """
    Coletor abstrato. Subclasses devem implementar:
    - collect() -> list[RawFinding]

    Opcionalmente:
    - source_slug: str (identificador único da fonte)
    - source_name: str (nome legível da fonte)
    - family: str (uma das 6 famílias: web, github, forums, social, academic, events)
    """

    @property
    @abstractmethod
    def source_slug(self) -> str:
        """Slug único da fonte (ex: 'porvir-rss')."""
        ...

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Nome legível da fonte (ex: 'Porvir - RSS')."""
        ...

    @property
    @abstractmethod
    def family(self) -> str:
        """Família da fonte: web | github | forums | social | academic | events."""
        ...

    @abstractmethod
    async def collect(self) -> list[RawFinding]:
        """
        Coleta achados da fonte.

        Returns:
            Lista de RawFinding para inserção no banco.
        """
        ...

    def get_source_config(self) -> dict:
        """Retorna configuração da fonte para a tabela sources."""
        return {
            "slug": self.source_slug,
            "name": self.source_name,
            "family": self.family,
            "config": {},
            "healthy": True,
        }
