"""Classificação multi-rótulo CISEB + enriquecimento + scoring."""
import json
import logging
from datetime import datetime, timezone
from llm.deepseek import chat

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um classificador de conteúdo educacional para o CISEB (Centro de Inovação).
Sua tarefa: ler um texto e retornar APENAS um JSON válido, sem comentários, sem markdown.

Os 6 pilares CISEB são:
- ia: Inteligência Artificial (personalização, automação, IA em educação)
- maker: Cultura Maker (projetos práticos, construção, criatividade)
- digital: Cultura Digital (RV, RA, experiências imersivas)
- tech_art: Tecnologia e Arte (jogos, animações, pensamento computacional)
- fabrication: Fabricação Digital (impressão 3D, cortadora a laser, prototipagem)
- robotics: Robótica Educacional (kits, competições, programação de robôs)

REGRAS:
1. Atribua confiança (0.0 a 1.0) para cada pilar. Se < 0.30, use 0.0.
2. Atribua no mínimo 1 pilar com confiança >= 0.55.
3. NÃO invente dados. Se não souber, use null.
4. Retorne APENAS o JSON, sem texto adicional.

Formato de saída:
{
  "summary": "resumo de 2-3 frases, em português, do que o achado propõe",
  "pillars": [{"slug": "ia", "confidence": 0.85}, {"slug": "robotics", "confidence": 0.40}],
  "audience": "basica|tecnico|superior|formacao_continuada|null",
  "geo_br": true,
  "replicable": true,
  "practical_project": true,
  "application_suggestion": "1 frase de como aplicar no CISEB"
}
"""

USER_TEMPLATE = """Título: {title}

Conteúdo:
{text}

Retorne o JSON:"""

VALID_PILLARS = {"ia", "maker", "digital", "tech_art", "fabrication", "robotics"}

async def enrich(finding: dict) -> dict | None:
    text = (finding.get("content_text") or "")[:4000]
    if len(text) < 50:
        log.info(f"finding {finding.get('id', '?')} muito curto — pulando")
        return None
    user_msg = USER_TEMPLATE.format(title=finding["title"], text=text)
    raw = await chat(SYSTEM_PROMPT, user_msg, temperature=0.1, max_tokens=600)
    if not raw:
        return None
    raw = raw.strip().strip("`").strip()
    if raw.lower().startswith("json"):
        raw = raw[4:].strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.warning(f"DeepSeek JSON inválido para {finding.get('id', '?')}: {raw[:200]}")
        return None
    if "pillars" not in data or not isinstance(data["pillars"], list):
        return None
    valid_pillars = [p for p in data["pillars"] if p.get("slug") in VALID_PILLARS and isinstance(p.get("confidence"), (int, float))]
    if not any(p.get("confidence", 0) >= 0.55 for p in valid_pillars):
        log.info(f"nenhum pilar ≥ 0.55 para {finding.get('id', '?')}")
        return None
    data["pillars"] = valid_pillars
    return data

def compute_score(enriched: dict, finding: dict | None = None) -> dict:
    pillars = enriched.get("pillars", [])
    alignment = sum(p.get("confidence", 0) for p in pillars) / max(len(pillars), 1)
    dim_alignment = int(alignment * 100)
    dim_br = 100 if enriched.get("geo_br") else 30
    dim_rep = 100 if enriched.get("replicable") else 30
    dim_pra = 100 if enriched.get("practical_project") else 40
    dim_lvl = 80 if enriched.get("audience") else 50
    dim_nov = enriched.get("_dim_novelty", 70)
    score = int(round(dim_alignment * 0.30 + dim_br * 0.20 + dim_rep * 0.20 + dim_pra * 0.15 + dim_lvl * 0.10 + dim_nov * 0.05))
    score = max(0, min(100, score))
    return {"dim_alignment": dim_alignment, "dim_br_luso": dim_br, "dim_replicable": dim_rep, "dim_practical": dim_pra, "dim_level": dim_lvl, "dim_novelty": dim_nov, "score_composite": score}

def novelty_score(collected_at_iso: str) -> int:
    try:
        collected = datetime.fromisoformat(collected_at_iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return 50
    now = datetime.now(timezone.utc)
    days = (now - collected).days
    if days <= 7: return 100
    if days <= 30: return 80
    if days <= 90: return 50
    return 30
