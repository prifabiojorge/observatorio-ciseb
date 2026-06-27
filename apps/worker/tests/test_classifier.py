"""Testes para llm/classifier.py — compute_score, novelty_score, enrich.

Valida a fórmula de scoring documentada em memoria/03_SCHEMA_BANCO.md
e a robustez do parser JSON contra alucinações do LLM.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm.classifier import VALID_PILLARS, compute_score, enrich, novelty_score


class TestComputeScore:
    """Valida a fórmula do score composto (0-100) com 6 dimensões ponderadas."""

    def test_score_maximo_para_finding_perfeito(self):
        """Todos flags True → dimensões máximas → score próximo de 100.

        Nota: dim_level=80 quando audience presente (não 100), então
        score composto = 100*0.30+100*0.20+100*0.20+100*0.15+80*0.10+100*0.05
                       = 30+20+20+15+8+5 = 98
        """
        enriched = {
            "pillars": [{"slug": "ia", "confidence": 1.0}],
            "geo_br": True,
            "replicable": True,
            "practical_project": True,
            "audience": "basica",
            "_dim_novelty": 100,
        }
        sc = compute_score(enriched, {})
        assert sc["score_composite"] == 98  # 80 em dim_level reduz de 100
        assert sc["dim_alignment"] == 100
        assert sc["dim_br_luso"] == 100
        assert sc["dim_replicable"] == 100
        assert sc["dim_practical"] == 100
        assert sc["dim_level"] == 80  # audience presente → 80, não 100
        assert sc["dim_novelty"] == 100

    def test_score_minimo_para_finding_fraco(self):
        """Todos flags False → dimensões baixas → score baixo."""
        enriched = {
            "pillars": [{"slug": "ia", "confidence": 0.0}],
            "geo_br": False,
            "replicable": False,
            "practical_project": False,
            "audience": None,
            "_dim_novelty": 30,
        }
        sc = compute_score(enriched, {})
        assert sc["dim_alignment"] == 0
        assert sc["dim_br_luso"] == 30  # geo_br False → 30
        assert sc["dim_replicable"] == 30
        assert sc["dim_practical"] == 40
        assert sc["dim_level"] == 50  # audience None → 50
        assert sc["dim_novelty"] == 30
        # Score = 0*0.30 + 30*0.20 + 30*0.20 + 40*0.15 + 50*0.10 + 30*0.05
        #       = 0 + 6 + 6 + 6 + 5 + 1.5 = 24.5 → 24 (int(round(24.5)) = 24 em Python)
        assert sc["score_composite"] == 24

    def test_pesos_da_formula_somam_1(self):
        """Os pesos 0.30+0.20+0.20+0.15+0.10+0.05 devem somar 1.0."""
        # Documentado em memoria/03_SCHEMA_BANCO.md
        pesos = [0.30, 0.20, 0.20, 0.15, 0.10, 0.05]
        assert sum(pesos) == pytest.approx(1.0)

    def test_score_sempre_entre_0_e_100(self):
        """Score composto E dim_alignment nunca devem sair do intervalo [0, 100].

        7.1 (corrigido em 2026-06-27): dim_alignment agora é truncado com
        max(0, min(100, ...)). Antes, confidence anômala (>1.0) produzia
        dim_alignment=500. Agora é truncado para 100.
        """
        enriched = {
            "pillars": [{"slug": "ia", "confidence": 5.0}],  # anômalo
            "geo_br": True,
            "replicable": True,
            "practical_project": True,
            "audience": "basica",
            "_dim_novelty": 100,
        }
        sc = compute_score(enriched, {})
        # Ambos são truncados para [0, 100]
        assert 0 <= sc["score_composite"] <= 100
        assert 0 <= sc["dim_alignment"] <= 100
        # Especificamente: confidence=5.0 → alignment=5.0 → 500 → truncado para 100
        assert sc["dim_alignment"] == 100

    def test_confianca_media_calculada_corretamente(self):
        """dim_alignment = média das confianças * 100."""
        enriched = {
            "pillars": [
                {"slug": "ia", "confidence": 0.80},
                {"slug": "robotics", "confidence": 0.60},
            ],
            "geo_br": False,
            "replicable": False,
            "practical_project": False,
            "audience": None,
            "_dim_novelty": 50,
        }
        sc = compute_score(enriched, {})
        # média = (0.80 + 0.60) / 2 = 0.70 → 70
        assert sc["dim_alignment"] == 70

    def test_pillars_vazio_nao_quebra(self):
        """Lista de pillars vazia não deve causar ZeroDivisionError."""
        enriched = {
            "pillars": [],
            "geo_br": False,
            "replicable": False,
            "practical_project": False,
            "audience": None,
            "_dim_novelty": 50,
        }
        sc = compute_score(enriched, {})
        assert sc["dim_alignment"] == 0  # max(len(pillars), 1) evita divisão por zero

    def test_threshold_alerta_75_eh_atingivel(self):
        """Valida que findings brasileiros replicáveis podem atingir 75+."""
        enriched = {
            "pillars": [{"slug": "ia", "confidence": 0.85}],
            "geo_br": True,
            "replicable": True,
            "practical_project": True,
            "audience": "basica",
            "_dim_novelty": 80,
        }
        sc = compute_score(enriched, {})
        # dim_alignment=85, dim_br=100, dim_rep=100, dim_pra=100, dim_lvl=80, dim_nov=80
        # = 85*0.30 + 100*0.20 + 100*0.20 + 100*0.15 + 80*0.10 + 80*0.05
        # = 25.5 + 20 + 20 + 15 + 8 + 4 = 92.5 → 93
        assert sc["score_composite"] >= 75  # deve disparar alerta Telegram


class TestNoveltyScore:
    """Valida novelty_score — decai com a idade do achado."""

    def test_7_dias_ou_menos_retorna_100(self):
        from datetime import datetime, timedelta, timezone

        recent = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        assert novelty_score(recent) == 100

    def test_8_a_30_dias_retorna_80(self):
        from datetime import datetime, timedelta, timezone

        mid = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
        assert novelty_score(mid) == 80

    def test_31_a_90_dias_retorna_50(self):
        from datetime import datetime, timedelta, timezone

        old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        assert novelty_score(old) == 50

    def test_mais_de_90_dias_retorna_30(self):
        from datetime import datetime, timedelta, timezone

        very_old = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat()
        assert novelty_score(very_old) == 30

    def test_iso_com_z_suffix_funciona(self):
        """ISO 8601 com Z (UTC) deve ser parseado corretamente."""
        from datetime import datetime, timedelta, timezone

        recent_z = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert novelty_score(recent_z) == 100

    def test_data_invalida_retorna_50(self):
        """String inválida não deve quebrar — retorna 50 (neutro)."""
        assert novelty_score("data-invalida") == 50
        assert novelty_score("") == 50
        assert novelty_score(None) == 50  # type: ignore


class TestEnrichParser:
    """Valida que enrich rejeita JSON inválido e alucinações do LLM."""

    @pytest.mark.asyncio
    async def test_enrich_retorna_none_para_json_invalido(self):
        """Se DeepSeek retornar texto não-JSON, enrich deve retornar None (não crashar)."""
        finding = {"id": "test-1", "title": "Teste", "content_text": "x" * 100}
        with patch(
            "llm.classifier.chat",
            new_callable=AsyncMock,
            return_value="isso não é JSON",
        ):
            result = await enrich(finding)
        assert result is None

    @pytest.mark.asyncio
    async def test_enrich_retorna_none_para_json_sem_pillars(self):
        """JSON válido mas sem 'pillars' deve ser rejeitado."""
        finding = {"id": "test-2", "title": "Teste", "content_text": "x" * 100}
        bad_json = '{"summary": "ok", "geo_br": true}'  # sem pillars
        with patch("llm.classifier.chat", new_callable=AsyncMock, return_value=bad_json):
            result = await enrich(finding)
        assert result is None

    @pytest.mark.asyncio
    async def test_enrich_rejeita_pillars_com_confianca_baixa(self):
        """Nenhum pilar com confidence ≥ 0.55 → None."""
        finding = {"id": "test-3", "title": "Teste", "content_text": "x" * 100}
        json_low_conf = '{"summary":"ok","pillars":[{"slug":"ia","confidence":0.30}]}'
        with patch("llm.classifier.chat", new_callable=AsyncMock, return_value=json_low_conf):
            result = await enrich(finding)
        assert result is None

    @pytest.mark.asyncio
    async def test_enrich_aceita_json_valido_com_pilar_alto(self):
        """JSON válido com pilar ≥ 0.55 deve retornar dict enriquecido."""
        finding = {"id": "test-4", "title": "Teste", "content_text": "x" * 100}
        good_json = """{
            "summary": "Resumo do achado",
            "pillars": [{"slug": "ia", "confidence": 0.85}],
            "audience": "basica",
            "geo_br": true,
            "replicable": true,
            "practical_project": true,
            "application_suggestion": "Aplicar em sala"
        }"""
        with patch("llm.classifier.chat", new_callable=AsyncMock, return_value=good_json):
            result = await enrich(finding)
        assert result is not None
        assert result["pillars"][0]["slug"] == "ia"
        assert result["geo_br"] is True

    @pytest.mark.asyncio
    async def test_enrich_filtrar_pillars_invalidos(self):
        """Slugs não reconhecidos devem ser filtrados, mantendo apenas válidos."""
        finding = {"id": "test-5", "title": "Teste", "content_text": "x" * 100}
        json_with_bad_slugs = """{
            "summary": "ok",
            "pillars": [
                {"slug": "ia", "confidence": 0.85},
                {"slug": "slug_inexistente", "confidence": 0.90},
                {"slug": "maker", "confidence": 0.70}
            ]
        }"""
        with patch(
            "llm.classifier.chat",
            new_callable=AsyncMock,
            return_value=json_with_bad_slugs,
        ):
            result = await enrich(finding)
        assert result is not None
        slugs = [p["slug"] for p in result["pillars"]]
        assert "slug_inexistente" not in slugs
        assert set(slugs).issubset(VALID_PILLARS)

    @pytest.mark.asyncio
    async def test_enrich_strips_markdown_fences(self):
        """DeepSeek às vezes envolve JSON em ```json ... ``` — deve ser tratado."""
        finding = {"id": "test-6", "title": "Teste", "content_text": "x" * 100}
        fenced_json = '```json\n{"summary":"ok","pillars":[{"slug":"ia","confidence":0.85}]}\n```'
        with patch("llm.classifier.chat", new_callable=AsyncMock, return_value=fenced_json):
            result = await enrich(finding)
        assert result is not None

    @pytest.mark.asyncio
    async def test_enrich_texto_curto_retorna_none(self):
        """Texto < 50 chars deve ser pulado (insuficiente para classificar)."""
        finding = {"id": "test-7", "title": "T", "content_text": "curto"}
        result = await enrich(finding)
        assert result is None  # nem chama o LLM

    @pytest.mark.asyncio
    async def test_enrich_llm_retorna_none_retorna_none(self):
        """Se chat() retorna None (erro de API), enrich deve propagar None."""
        finding = {"id": "test-8", "title": "Teste", "content_text": "x" * 100}
        with patch("llm.classifier.chat", new_callable=AsyncMock, return_value=None):
            result = await enrich(finding)
        assert result is None
