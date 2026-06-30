"""Testes para llm/embeddings.py — BGE-M3 via HuggingFace API.

Fase 7 fix: valida que:
- Payload NÃO contém mais 'options' (causava erro 400)
- Header 'X-Wait-For-Model' é enviado
- Retry funciona em caso de 503
- Vetor zero só retorna após esgotar retries
- _extract_vector suporta múltiplos formatos de resposta
- embed_pillars NÃO salva vetor zero no banco
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm.embeddings import EMBED_DIM, _extract_vector, embed_pillars, embed_text


class TestExtractVector:
    """Valida parsing dos diferentes formatos de resposta da HF API."""

    def test_formato_lista_de_listas(self):
        """Formato padrão BGE-M3: [[0.1, 0.2, ...]]"""
        data = [[0.1] * EMBED_DIM]
        vec = _extract_vector(data)
        assert vec == [0.1] * EMBED_DIM

    def test_formato_lista_direta(self):
        """Formato alternativo: [0.1, 0.2, ...]"""
        data = [0.5] * EMBED_DIM
        vec = _extract_vector(data)
        assert vec == [0.5] * EMBED_DIM

    def test_formato_embeddings_dict(self):
        """Formato raro: {"embeddings": [[...]]}"""
        data = {"embeddings": [[0.7] * EMBED_DIM]}
        vec = _extract_vector(data)
        assert vec == [0.7] * EMBED_DIM

    def test_formato_openai_compatible(self):
        """Formato OpenAI: {"data": [{"embedding": [...]}]}"""
        data = {"data": [{"embedding": [0.3] * EMBED_DIM}]}
        vec = _extract_vector(data)
        assert vec == [0.3] * EMBED_DIM

    def test_formato_invalido_retorna_none(self):
        """Formato desconhecido retorna None (vira vetor zero depois)."""
        assert _extract_vector({"unknown": "format"}) is None
        assert _extract_vector([]) is None
        assert _extract_vector("string") is None


class TestEmbedText:
    """Valida comportamento de embed_text com mock da API."""

    @pytest.mark.asyncio
    async def test_texto_vazio_retorna_vetor_zero(self):
        """Texto vazio deve retornar vetor zero sem chamar API."""
        result = await embed_text("")
        assert result == [0.0] * EMBED_DIM
        assert len(result) == EMBED_DIM

    @pytest.mark.asyncio
    async def test_texto_whitespace_retorna_vetor_zero(self):
        """Texto só com espaços deve retornar vetor zero."""
        result = await embed_text("   ")
        assert result == [0.0] * EMBED_DIM

    @pytest.mark.asyncio
    async def test_payload_nao_contem_options(self):
        """Fase 7 fix: 'options' causava erro 400 — não deve mais ser enviado."""
        captured_payload = {}

        async def mock_post(self, url, json=None, headers=None):
            captured_payload["json"] = json
            captured_payload["headers"] = headers
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json = MagicMock(return_value=[[0.1] * EMBED_DIM])
            return mock_resp

        with patch("httpx.AsyncClient.post", new=mock_post):
            await embed_text("texto de teste")

        assert "options" not in captured_payload["json"], (
            "Payload NÃO deve mais conter 'options' (causa erro 400 na HF API)"
        )
        assert captured_payload["json"]["inputs"] == "texto de teste"

    @pytest.mark.asyncio
    async def test_header_wait_for_model_enviado(self):
        """Fase 7 fix: X-Wait-For-Model header substitui options.wait_for_model."""
        captured_headers = {}

        async def mock_post(self, url, json=None, headers=None):
            captured_headers.update(headers or {})
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json = MagicMock(return_value=[[0.1] * EMBED_DIM])
            return mock_resp

        with patch("httpx.AsyncClient.post", new=mock_post):
            await embed_text("texto")

        assert captured_headers.get("X-Wait-For-Model") == "true"

    @pytest.mark.asyncio
    async def test_sucesso_retorna_vetor_correto(self):
        """Quando API responde 200 com vetor válido, retorna o vetor."""

        async def mock_post(self, url, json=None, headers=None):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json = MagicMock(return_value=[[0.42] * EMBED_DIM])
            return mock_resp

        with patch("httpx.AsyncClient.post", new=mock_post):
            result = await embed_text("teste")

        assert len(result) == EMBED_DIM
        assert result[0] == 0.42

    @pytest.mark.asyncio
    async def test_erro_400_nao_faz_retry(self):
        """Erro 400 (bad request) não vale a pena retry — falha rápido."""
        call_count = 0

        async def mock_post(self, url, json=None, headers=None):
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            mock_resp.status_code = 400
            mock_resp.text = "Bad Request"
            mock_resp.raise_for_status = MagicMock(
                side_effect=__import__("httpx").HTTPStatusError(
                    "400", request=MagicMock(), response=mock_resp
                )
            )
            return mock_resp

        with patch("httpx.AsyncClient.post", new=mock_post):
            with patch("asyncio.sleep", new=AsyncMock()):  # acelerar testes
                result = await embed_text("teste")

        assert result == [0.0] * EMBED_DIM  # vetor zero após falha
        assert call_count == 1, "Erro 400 NÃO deve fazer retry"

    @pytest.mark.asyncio
    async def test_erro_503_faz_retry(self):
        """Erro 503 (modelo carregando) deve fazer retry."""
        call_count = 0

        async def mock_post(self, url, json=None, headers=None):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                # 503 nas primeiras 2 tentativas
                mock_resp = MagicMock()
                mock_resp.status_code = 503
                mock_resp.text = "Model loading"
                mock_resp.raise_for_status = MagicMock(
                    side_effect=__import__("httpx").HTTPStatusError(
                        "503", request=MagicMock(), response=mock_resp
                    )
                )
                return mock_resp
            # Sucesso na 3ª
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json = MagicMock(return_value=[[0.1] * EMBED_DIM])
            return mock_resp

        with patch("httpx.AsyncClient.post", new=mock_post):
            with patch("asyncio.sleep", new=AsyncMock()):  # acelerar
                result = await embed_text("teste")

        assert call_count == 3, "Deve fazer 3 tentativas (2 retries)"
        assert result[0] == 0.1  # vetor válido após retry bem-sucedido


class TestEmbedPillars:
    """Valida embed_pillars — NÃO deve salvar vetor zero no banco."""

    @pytest.fixture(autouse=True)
    def _env_minimo(self, monkeypatch):
        """Garante env vars mínimas para importar db.supabase."""
        monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake-key")

    @pytest.mark.asyncio
    async def test_pilar_com_vetor_zero_nao_eh_salvo(self):
        """Fase 7 fix: antes salvava vetor zero, corrompendo o pilar."""
        # Mock Supabase — get_supabase é importado dentro da função, mockar db.supabase
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
            {
                "id": "uuid-1",
                "slug": "ia",
                "name": "IA",
                "description": "desc",
                "canonical_embedding": None,
            }
        ]
        mock_update = MagicMock()
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute = mock_update

        # Mock embed_text para retornar vetor zero (simula falha)
        with patch("db.supabase.get_supabase", return_value=mock_supabase):
            with patch(
                "llm.embeddings.embed_text",
                new=AsyncMock(return_value=[0.0] * EMBED_DIM),
            ):
                await embed_pillars()

        # NÃO deve ter chamado update (vetor zero não salva)
        mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_pilar_com_vetor_valido_eh_salvo(self):
        """Pilar com embedding válido deve ser salvo no banco."""
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
            {
                "id": "uuid-1",
                "slug": "ia",
                "name": "IA",
                "description": "desc",
                "canonical_embedding": None,
            }
        ]
        mock_update_result = MagicMock()
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute = (
            mock_update_result
        )

        valid_vec = [0.1] * EMBED_DIM

        with patch("db.supabase.get_supabase", return_value=mock_supabase):
            with patch("llm.embeddings.embed_text", new=AsyncMock(return_value=valid_vec)):
                await embed_pillars()

        # Deve ter chamado update com o vetor válido
        mock_supabase.table.return_value.update.assert_called_once_with(
            {"canonical_embedding": valid_vec}
        )

    @pytest.mark.asyncio
    async def test_pilar_com_embedding_existente_eh_pulado(self):
        """Pilar que já tem embedding deve ser pulado (idempotente)."""
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.execute.return_value.data = [
            {
                "id": "uuid-1",
                "slug": "ia",
                "name": "IA",
                "description": "desc",
                "canonical_embedding": [0.5] * EMBED_DIM,
            }  # já tem
        ]

        with patch("db.supabase.get_supabase", return_value=mock_supabase):
            with patch("llm.embeddings.embed_text", new=AsyncMock()) as mock_embed:
                await embed_pillars()

        # Não deve chamar embed_text (pilar já tem embedding)
        mock_embed.assert_not_called()
