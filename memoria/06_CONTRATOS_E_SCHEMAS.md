# Contratos e Schemas de API
### Interfaces entre camadas · Observatório CISEB

---

## 1. Contrato de evento (coletor → fila)

Toda fonte publica exatamente este schema. **NÃO modifique os nomes de campos.**

```json
{
  "event_id": "uuid-v4-string",
  "source_slug": "github-robotics-edu",
  "source_url": "https://...",
  "collected_at": "2026-06-25T10:30:00Z",
  "content_hash": "sha256-hex-64-chars",
  "title": "string não-vazio, máx 300 chars",
  "raw_text": "string, máx 10000 chars",
  "language": "pt|en|es",
  "metadata": {
    "author": "string opcional",
    "published_at": "ISO 8601 opcional",
    "tags": ["array opcional"],
    "extra": {}
  }
}
```

---

## 2. Contrato do classificador (LLM → pipeline)

O prompt do LLM retorna exatamente este JSON:

```json
{
  "summary": "resumo de 2-3 frases, em português, do que o achado propõe",
  "pillars": [
    {"slug": "ia", "confidence": 0.85},
    {"slug": "robotics", "confidence": 0.40}
  ],
  "audience": "basica|tecnico|superior|formacao_continuada|null",
  "geo_br": true,
  "replicable": true,
  "practical_project": true,
  "application_suggestion": "1 frase de como aplicar no CISEB"
}
```

### Regras de validação:
- `pillars` deve ser array com ≥ 1 item com `confidence ≥ 0.55`
- Slugs válidos: `ia`, `maker`, `digital`, `tech_art`, `fabrication`, `robotics`
- Se JSON inválido ou nenhum pilar com `confidence ≥ 0.55` → finding fica `status='new'` para retry

---

## 3. Contrato de card Telegram

```
🚨 <b>Alerta — score {score}/100</b>

<b>{título}</b>

📁 {emoji_pilar} {pilar} ({score}) · ...

📝 {resumo 2-3 frases}

💡 <i>Aplicação:</i> {sugestão de aplicação}

🔗 {source_url}
```

- Formato: HTML (parse_mode=HTML)
- Máx: 4000 chars (margem dos 4096 do Telegram)
- Máx alertas/dia: 5 (configurável)

---

## 4. Contrato do digest diário

```
📬 <b>Digest {YYYY-MM-DD}</b> — {N} achados

1. [{score}] <b>{título (80 chars)}</b>
   🔗 {url}

2. [{score}] <b>{título (80 chars)}</b>
   🔗 {url}
...
```

- Enviado às 7h BRT, dias úteis
- Máx 10 achados
- Quebrado em mensagens de 4000 chars se necessário

---

## 5. API Routes (Vercel/Next.js)

| Rota | Método | Auth | Descrição |
|------|--------|------|-----------|
| `/api/cron/collect` | GET | `Bearer CRON_SECRET` | Dispara rodada de coleta no Render |
| `/api/cron/digest` | GET | `Bearer CRON_SECRET` | Dispara envio de digest |
| `/api/findings/pending` | GET | Nenhuma (MVP) | Top 10 findings `scored` para revisão |
| `/api/findings/decide` | POST | Nenhuma (MVP) | Registra decisão (approved/rejected) |

### Payloads

**POST `/api/findings/decide`**:
```json
{
  "id": "uuid do finding",
  "decision": "approved" | "rejected"
}
```

---

## 6. Render Worker endpoints (FastAPI)

| Rota | Método | Descrição |
|------|--------|-----------|
| `/run` | POST | Executa uma rodada completa (coleta + enriquecimento + alertas) |
| `/digest` | POST | Envia digest Telegram com a lista de findings |

---

## 7. Hash de deduplicação

```python
def content_hash(url: str, title: str, raw_text: str) -> str:
    normalized = " ".join((url + " " + title + " " + raw_text).split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
```

- Dedup sintática: hash SHA-256 exato
- Dedup semântica (Fase 3+): embeddings com cosseno > 0.93

---

> **Registrado em**: 2026-06-25
