# Estrutura de Arquivos do Monorepo
### Referência rápida · Observatório CISEB

---

## Árvore completa planejada

```
observatorio-ciseb/
│
├── 📄 Plano_Observatorio_CISEB_v2.md          ← Plano operacional (documento-fonte)
├── 📄 USOINTERNOORQUESTRADOR&ARQUITET.md      ← Esqueleto arquitetural v1 (referência)
├── 📄 Observatorio_CISEB_Esqueleto_Arquitetural.pdf  ← PDF original
│
├── 📁 memoria/                                ← PERSISTÊNCIA DA IA (este diretório)
│   ├── 00_MANIFESTO_IA.md
│   ├── 01_DECISOES_TOMADAS.md
│   ├── 02_STACK_TECNOLOGICA.md
│   ├── 03_SCHEMA_BANCO.md
│   ├── 04_MAPA_FASES.md
│   ├── 05_SEGURANCA_DESDE_DESENHO.md
│   ├── 06_CONTRATOS_E_SCHEMAS.md
│   ├── 07_CONTEXTO_PEDAGOGICO.md
│   ├── 08_LOG_EXECUCAO.md
│   └── 09_ESTRUTURA_ARQUIVOS.md               ← Este arquivo
│
├── 📁 apps/
│   ├── 📁 web/                                ← Next.js 14 (Vercel)
│   │   ├── 📁 app/
│   │   │   ├── 📁 api/
│   │   │   │   ├── 📁 cron/
│   │   │   │   │   ├── 📁 collect/
│   │   │   │   │   │   └── route.ts           ← Dispara coleta no Render
│   │   │   │   │   └── 📁 digest/
│   │   │   │   │       └── route.ts           ← Dispara digest Telegram
│   │   │   │   └── 📁 findings/
│   │   │   │       ├── 📁 pending/
│   │   │   │       │   └── route.ts           ← Top 10 para revisão
│   │   │   │       └── 📁 decide/
│   │   │   │           └── route.ts           ← Registra aprovação/rejeição
│   │   │   ├── 📁 dashboard/
│   │   │   │   └── page.tsx                   ← Interface de revisão
│   │   │   └── layout.tsx
│   │   ├── package.json
│   │   └── next.config.mjs
│   │
│   └── 📁 worker/                             ← Python 3.11 (Render)
│       ├── 📁 src/
│       │   ├── 📁 collectors/
│       │   │   ├── __init__.py
│       │   │   ├── base.py                    ← BaseCollector (ABC)
│       │   │   ├── web_rss.py                 ← RSS/Web (Porvir, Nova Escola, MEC)
│       │   │   ├── github.py                  ← GitHub API (topics educação)
│       │   │   ├── youtube.py                 ← YouTube (feeds XML + transcrições)
│       │   │   ├── scholar.py                 ← Google Scholar (scholarly)
│       │   │   ├── forums.py                  ← Reddit (subreddits educação)
│       │   │   └── events.py                  ← Editais (MEC, FAPESP, CAPES)
│       │   ├── 📁 llm/
│       │   │   ├── __init__.py
│       │   │   ├── deepseek.py                ← Cliente DeepSeek (OpenAI-compatible)
│       │   │   ├── embeddings.py              ← BGE-M3 (1024 dims)
│       │   │   ├── classifier.py              ← Classificador multi-rótulo + scorer
│       │   │   └── scorer.py                  ← (opcional, funções em classifier.py)
│       │   ├── 📁 delivery/
│       │   │   ├── __init__.py
│       │   │   ├── telegram.py                ← Bot Telegram (cards + digest)
│       │   │   └── newsletter.py              ← Resend (e-mail)
│       │   ├── 📁 db/
│       │   │   ├── __init__.py
│       │   │   ├── supabase.py                ← Cliente Supabase singleton
│       │   │   └── queries.py                 ← Queries reutilizáveis
│       │   ├── 📁 utils/
│       │   │   ├── __init__.py
│       │   │   ├── text.py                    ← Limpeza e truncamento de texto
│       │   │   └── hashing.py                 ← SHA-256 para deduplicação
│       │   └── main.py                        ← Entry point do worker
│       ├── 📁 tests/
│       ├── pyproject.toml
│       ├── Dockerfile
│       └── render.yaml
│
├── 📁 supabase/
│   ├── 📁 migrations/
│   │   ├── 001_init.sql                       ← Schema inicial (6 tabelas + pgvector)
│   │   ├── 002_pgmq.sql                      ← Fila nativa Postgres
│   │   └── 003_rls.sql                       ← Row Level Security
│   └── seed.sql                               ← 6 pilares CISEB
│
├── .env.example                               ← Variáveis com valores fake (commitado)
├── .gitignore                                 ← .env, __pycache__, node_modules, etc.
├── .github/
│   └── workflows/
│       └── ci.yml                             ← CI básico
├── vercel.json                                ← Cron schedules
├── package.json                               ← Workspace root
└── README.md
```

---

## Mapeamento persona → arquivos

| Persona | Arquivos que cria/modifica |
|---------|---------------------------|
| **Arquiteto** | `001_init.sql`, `base.py`, `embeddings.py`, `deepseek.py`, `classifier.py` |
| **Guardião** | `003_rls.sql`, `.env.example`, `.gitignore`, auditoria mensal |
| **Orquestrador** | `main.py`, `render.yaml`, `vercel.json`, `ci.yml` |
| **Advogado do Usuário** | `dashboard/page.tsx`, `telegram.py` (formato card) |
| **Harness** | Todos os demais + testes + deploy |

---

> **Registrado em**: 2026-06-25
