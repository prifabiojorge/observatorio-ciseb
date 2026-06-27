"""Testes para utils/hashing.py — deduplicação SHA-256."""
import pytest
from utils.hashing import content_hash


class TestContentHash:
    """Valida o contrato de content_hash definido em memoria/06_CONTRATOS_E_SCHEMAS.md."""

    def test_retorna_hexadecimal_64_chars(self):
        """SHA-256 deve produzir 64 caracteres hexadecimais."""
        h = content_hash("https://exemplo.com", "Título", "Conteúdo")
        assert isinstance(h, str)
        assert len(h) == 64
        int(h, 16)  # levanta ValueError se não for hex válido

    def test_determinismo_mesma_entrada(self):
        """Mesma entrada sempre produz mesmo hash."""
        h1 = content_hash("https://exemplo.com", "Título", "Conteúdo")
        h2 = content_hash("https://exemplo.com", "Título", "Conteúdo")
        assert h1 == h2

    def test_dedup_normaliza_whitespace(self):
        """Whitespace extra (espaços, tabs, newlines) não deve produzir hash diferente."""
        h1 = content_hash("https://exemplo.com", "Título", "Conteúdo do artigo")
        h2 = content_hash("https://exemplo.com", "Título", "Conteúdo    do   artigo")
        h3 = content_hash("https://exemplo.com", "Título", "Conteúdo\tdo\nartigo")
        assert h1 == h2 == h3

    def test_dedup_case_insensitive(self):
        """Normalização lower() — 'Título' e 'título' produzem mesmo hash."""
        h1 = content_hash("https://exemplo.com", "Título Maiúsculo", "Texto")
        h2 = content_hash("https://exemplo.com", "título maiúsculo", "texto")
        assert h1 == h2

    def test_hashes_diferentes_para_conteudo_diferente(self):
        """Conteúdo diferente deve produzir hash diferente."""
        h1 = content_hash("https://exemplo.com", "Robótica educacional", "Arduino")
        h2 = content_hash("https://exemplo.com", "Impressão 3D", "Prusa")
        assert h1 != h2

    def test_hash_diferente_para_url_diferente(self):
        """URL diferente deve produzir hash diferente, mesmo título e texto."""
        h1 = content_hash("https://a.com", "Título", "Conteúdo")
        h2 = content_hash("https://b.com", "Título", "Conteúdo")
        assert h1 != h2

    def test_raise_typeerror_para_nao_string(self):
        """TypeError esperado para argumentos não-string (defesa contra None/int)."""
        with pytest.raises(TypeError):
            content_hash(None, "Título", "Texto")  # type: ignore
        with pytest.raises(TypeError):
            content_hash("url", 123, "Texto")  # type: ignore
        with pytest.raises(TypeError):
            content_hash("url", "Título", None)  # type: ignore

    def test_entrada_vazia_gera_hash_valido(self):
        """Strings vazias são válidas — não devem quebrar o hash."""
        h = content_hash("", "", "")
        assert len(h) == 64

    def test_exemplo_do_contrato(self):
        """Valida que o hash corresponde ao exemplo documentado."""
        # Do memoria/06_CONTRATOS_E_SCHEMAS.md — normalização manual
        import hashlib
        manual = hashlib.sha256(
            " ".join(("https://exemplo.com Título Conteúdo").split()).lower().encode("utf-8")
        ).hexdigest()
        actual = content_hash("https://exemplo.com", "Título", "Conteúdo")
        assert actual == manual
