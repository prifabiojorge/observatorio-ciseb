# Stack Tecnológica Pinada
### Versões exatas · Observatório CISEB

---

> 🔒 **Versões pinadas.** Não atualizar sem teste completo e aprovação.

---

## Componentes e versões exatas

| Camada | Componente | Versão exata | Hospedagem |
|--------|------------|--------------|------------|
| Banco de dados | Supabase (Postgres 15 + pgvector) | Free tier (500MB) | Supabase Cloud (Ohio, us-east-2) |
| Cron + API + Dashboard | Next.js 14 (App Router) | 14.2.x | Vercel Hobby |
| Worker (coletores+LLM) | Python 3.11 + FastAPI 0.135 + Uvicorn 0.49 | Python 3.11-slim | Render Free |
| Fila | Supabase Queue (pgmq) | Built-in | Supabase |
| LLM | DeepSeek API (`deepseek-chat`) | API v1 (OpenAI-compatible) | DeepSeek Cloud |
| Embeddings | HuggingFace Inference API (BGE-M3, 1024 dims, free tier) | BGE-M3 via API | HuggingFace Cloud |
| Telegram bot | `python-telegram-bot` | 21.x | Render |
| E-mail newsletter | Resend | Free 3k/mês | Resend Cloud |
| Observabilidade | Logflare (Supabase nativo) + Sentry | Free tiers | Ambos |
| Versionamento | GitHub | público ou privado | GitHub |

## Dependências Python (pyproject.toml)

```toml
[project]
name = "observatorio-worker"
version = "0.1.0"
requires-python = ">=3.11,<3.14"
dependencies = [
  "httpx==0.27.0",
  "supabase==2.5.0",
  "fastapi>=0.111.0",
  "uvicorn>=0.30.0",
  "python-dotenv==1.0.1",
  "feedparser==6.0.11",
  "trafilatura==1.12.0",
  "openai==1.35.0",
  "pydantic==2.7.4",
  "scholarly>=1.7.0",
]

[project.optional-dependencies]
dev = ["pytest==8.2.2", "pytest-cov==5.0.0", "ruff==0.5.0"]
```

## Variáveis de ambiente (contrato)

```bash
# Supabase
SUPABASE_URL=https://yefudgudlpjctmdjkkio.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx          # APENAS no Render
SUPABASE_ANON_KEY=eyJxxxxx                  # Vercel + Render

# DeepSeek
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# HuggingFace (embeddings BGE-M3 via Inference API)
HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxxxxxx

# Telegram
# TELEGRAM_BOT_TOKEN=8705525357:AAF-... (ofuscado)
# TELEGRAM_CHAT_ID_FABIO=1158904776

# Resend
RESEND_API_KEY=re_xxxxx
RESEND_FROM=observatorio@ciseb.edu.br

# App
APP_ENV=production
APP_TIMEZONE=America/Fortaleza
NEWSLETTER_SCHEDULE=0 7 * * 1-5
TOPN_DAILY=10

# Render
# RENDER_SERVICE_ID=srv-d8usrhurnols73flq750
# RENDER_DEPLOY_URL=https://observatorio-ciseb.onrender.com
```

> ⚠️ **NUNCA** commitar `.env`. O `.env.example` com valores fake é commitado.

## Justificativa da stack (resumo)

- **Advogado do Usuário**: zero infra para Fábio gerenciar. Tudo PaaS.
- **Arquiteto**: Supabase (pgvector + pgmq) dispensa Redis e banco vetorial separado.
- **Guardião**: RLS habilitada; `service_role_key` isolada no Render; `anon_key` read-only.
- **Embeddings**: HuggingFace Inference API (BGE-M3) — sem modelo local, economiza RAM

---

> **Registrado em**: 2026-06-25
