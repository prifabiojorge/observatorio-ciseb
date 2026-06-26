"""Utilitários de limpeza e truncamento de texto."""


def clean_text(text: str, max_length: int = 10_000) -> str:
    """
    Remove espaços extras e trunca no comprimento máximo.

    Conforme contrato em memoria/06_CONTRATOS_E_SCHEMAS.md:
    raw_text máximo de 10000 caracteres.

    Args:
        text: Texto a ser limpo.
        max_length: Comprimento máximo (default 10000, conforme contrato).

    Returns:
        Texto limpo, sem espaços duplicados e truncado no limite.

    Raises:
        ValueError: Se max_length for negativo.
    """
    if max_length < 0:
        raise ValueError(f"max_length deve ser >= 0, recebido: {max_length}")

    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    cleaned = " ".join(text.split())
    return cleaned[:max_length]


def truncate(text: str, max_chars: int = 300) -> str:
    """
    Trunca texto preservando palavras inteiras.

    Útil para títulos e snippets exibidos em cards Telegram
    (máx 300 chars conforme contrato).

    Args:
        text: Texto a ser truncado.
        max_chars: Número máximo de caracteres (default 300).

    Returns:
        Texto truncado em limite de palavra, com "..." se houve corte.

    Raises:
        ValueError: Se max_chars for negativo.
    """
    if max_chars < 0:
        raise ValueError(f"max_chars deve ser >= 0, recebido: {max_chars}")

    if not isinstance(text, str):
        text = str(text) if text is not None else ""

    if len(text) <= max_chars:
        return text

    # Corta no último espaço antes do limite para preservar palavras
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        return truncated[:last_space] + "..."
    return truncated[:max_chars] + "..."
