"""
Cliente Supabase — singleton thread-safe.

Usa SERVICE_ROLE_KEY para acesso total (bypass RLS).
ANON_KEY seria insuficiente para INSERT/UPDATE/DELETE.

Uso:
    from db.supabase import get_supabase
    supabase = get_supabase()
    result = supabase.table("findings").select("*").execute()
"""
import os
from supabase import create_client, Client

# ── Configuração via variáveis de ambiente (NUNCA hardcoded) ──────────────
_url: str = os.environ["SUPABASE_URL"]
_key: str = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
_supabase: Client | None = None


def get_supabase() -> Client:
    """
    Retorna instância singleton do cliente Supabase.

    Thread-safe na prática para CPython (GIL), mas não é
    formalmente thread-safe. Para ambientes multi-thread,
    usar um lock explícito.

    Returns:
        Cliente Supabase autenticado com service_role key.

    Raises:
        KeyError: Se SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY
                  não estiverem definidas no ambiente.
    """
    global _supabase
    if _supabase is None:
        _supabase = create_client(_url, _key)
    return _supabase
