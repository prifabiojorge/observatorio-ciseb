"""Utilitário de hashing SHA-256 para deduplicação de findings."""
import hashlib


def content_hash(url: str, title: str, raw_text: str) -> str:
    """
    Hash SHA-256 normalizado para deduplicação sintática.

    Contrato idêntico ao definido em memoria/06_CONTRATOS_E_SCHEMAS.md.

    Args:
        url: URL de origem do achado.
        title: Título do achado.
        raw_text: Texto completo do achado.

    Returns:
        String hexadecimal de 64 caracteres representando o hash SHA-256.

    Raises:
        TypeError: Se qualquer argumento não for string.
    """
    if not isinstance(url, str) or not isinstance(title, str) or not isinstance(raw_text, str):
        raise TypeError("Todos os argumentos (url, title, raw_text) devem ser strings.")

    normalized = " ".join((url + " " + title + " " + raw_text).split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
