"""
Pacote de coletores do Observatório CISEB.

Cada coletor estende BaseCollector e implementa collect() -> list[RawFinding].
As 6 famílias de fontes cobertas:
  - web      (WebRSSCollector)
  - github   (GitHubCollector)
  - social   (YouTubeCollector)
  - academic (ScholarCollector)
  - forums   (ForumsCollector)
  - events   (EventsCollector)
"""

from .base import BaseCollector, RawFinding
from .events import EventsCollector
from .forums import ForumsCollector
from .github import GitHubCollector
from .scholar import ScholarCollector
from .web_rss import WebRSSCollector
from .youtube import YouTubeCollector

__all__ = [
    "BaseCollector",
    "RawFinding",
    "WebRSSCollector",
    "GitHubCollector",
    "YouTubeCollector",
    "ScholarCollector",
    "ForumsCollector",
    "EventsCollector",
]
