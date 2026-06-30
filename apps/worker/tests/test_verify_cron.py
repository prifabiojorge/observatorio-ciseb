"""Testes para api.verify_cron — validação de Bearer CRON_SECRET.

Estes testes validam o patch #1 (fail-closed + timing-safe comparison).
"""

import os
import sys
from pathlib import Path

import pytest

# Adiciona src/ ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def setup_crhon_secret(value: str | None):
    """Configura (ou remove) CRON_SECRET no ambiente e recarrega o módulo api."""
    if value is None:
        os.environ.pop("CRON_SECRET", None)
    else:
        os.environ["CRON_SECRET"] = value
    # Recarrega api (foi importado com valor anterior)
    if "api" in sys.modules:
        del sys.modules["api"]
    import api

    return api


# Ambiente mínimo para api.py carregar (supabase, telegram, etc.)
@pytest.fixture(autouse=True)
def _env_minimo(monkeypatch):
    """Garante variáveis de ambiente mínimas para importar api.py sem falhar."""
    monkeypatch.setenv("SUPABASE_URL", "https://fake.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake-service-role")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID_FABIO", "fake-chat-id")


class TestFailClosed:
    """Valida que o módulo recusa carregar sem CRON_SECRET (fail-closed)."""

    def test_sem_cron_secret_levanta_runtime_error(self, monkeypatch):
        """Sem CRON_SECRET no ambiente, RuntimeError deve ser levantado."""
        monkeypatch.delenv("CRON_SECRET", raising=False)
        # Limpa cache de módulos para forçar reimportação
        for mod in list(sys.modules):
            if mod in ("api", "main") or mod.startswith("collectors") or mod.startswith("db."):
                del sys.modules[mod]
        with pytest.raises(RuntimeError, match="CRON_SECRET não configurado"):
            import api  # noqa: F401


class TestVerifyCron:
    """Valida verify_cron — aceita token certo, rejeita errado/ausente."""

    def setup_method(self):
        """Carrega api.py com CRON_SECRET conhecido antes de cada teste."""
        self.api = setup_crhon_secret("teste-secreto-valido-12345")

    def test_token_certo_retorna_true(self):
        """Token correto deve retornar True (sem exceção)."""
        from fastapi.security import HTTPAuthorizationCredentials

        cred = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="teste-secreto-valido-12345"
        )
        assert self.api.verify_cron(cred) is True

    def test_token_errado_levanta_401(self):
        """Token errado deve levantar HTTPException 401."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-errado")
        with pytest.raises(HTTPException) as exc:
            self.api.verify_cron(cred)
        assert exc.value.status_code == 401
        assert "invalid" in exc.value.detail.lower()

    def test_sem_credenciais_levanta_401(self):
        """None (sem header Authorization) deve levantar 401."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            self.api.verify_cron(None)
        assert exc.value.status_code == 401
        assert "bearer" in exc.value.detail.lower()

    def test_credenciais_vazias_levanta_401(self):
        """Token vazio deve levantar 401."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")
        with pytest.raises(HTTPException) as exc:
            self.api.verify_cron(cred)
        assert exc.value.status_code == 401


class TestTimingSafeComparison:
    """Valida que hmac.compare_digest é usado (não vazio de timing)."""

    def setup_method(self):
        self.api = setup_crhon_secret("abc123")

    def test_token_com_comprimento_diferente_eh_rejeitado(self):
        """compare_digest rejeita strings de comprimento diferente sem timing leak."""
        from fastapi import HTTPException
        from fastapi.security import HTTPAuthorizationCredentials

        # Token muito mais curto que o secret
        cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials="a")
        with pytest.raises(HTTPException) as exc:
            self.api.verify_cron(cred)
        assert exc.value.status_code == 401


class TestEndpointsIntegracao:
    """Testes de integração via FastAPI TestClient (sem rodar pipeline real)."""

    def setup_method(self):
        self.api = setup_crhon_secret("teste-secreto-valido-12345")

    def test_run_sem_auth_retorna_401(self):
        from fastapi.testclient import TestClient

        client = TestClient(self.api.app)
        r = client.post("/run")
        assert r.status_code == 401

    def test_run_auth_errada_retorna_401(self):
        from fastapi.testclient import TestClient

        client = TestClient(self.api.app)
        r = client.post("/run", headers={"Authorization": "Bearer errado"})
        assert r.status_code == 401

    def test_digest_sem_auth_retorna_401(self):
        from fastapi.testclient import TestClient

        client = TestClient(self.api.app)
        r = client.post("/digest")
        assert r.status_code == 401

    def test_health_nao_requer_auth(self):
        """Health check é usado pelo Render para liveness — não deve exigir auth."""
        from fastapi.testclient import TestClient

        client = TestClient(self.api.app)
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
