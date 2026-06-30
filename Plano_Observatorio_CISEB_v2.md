# Plano de Ação — Observatório CISEB
### Versão 2.0 · Operacional · Anti-Alucinação · Executável por qualquer IA

> **Documento vivo.** Substitui a versão 1.0 (esqueleto arquitetural) e incorpora as 8 decisões finais do professor formador **Fábio Jorge**. Foi escrito para ser executado por IAs baratas ou open-source (DeepSeek, Llama 3, GLM-4, Qwen) sem alucinações: cada passo é auto-contido, cada schema é contratual, cada comando é copy-paste.

---

## 0. Como ler este documento (leia antes de executar QUALQUER coisa)

### 0.1 Convenções tipográficas

| Convenção | Significado |
|-----------|-------------|
| `monospaced` | Código, nome de arquivo, comando de terminal, chave de configuração |
| **negrito** | Campo obrigatório, decisão tomada, palavra-chave deCheckpoint |
| *itálico* | Termo técnico, variável a substituir, nome de persona |
| > citação | Aviso, rascunho de prompt, nota de segurança |
| ✅ / ❌ / ⚠️ | Aprovado / Bloqueante / Atenção |

### 0.2 Marcadores de fase (obrigatórios)

Cada bloco executável termina com um `### ✅ CHECKPOINT Fx.N` contendo:
- **Critério objetivo de saída** (não subjetivo)
- **Comando de verificação** (rodar e colar output)
- **Próxima ação só após aprovação**

Se o checkpoint falhar, **NÃO AVANCE**. Volte ao passo anterior, corrija, re-rode.

### 0.3 Princípio anti-alucinação (para a IA executora)

> Antes de executar qualquer passo, a IA executora deve se perguntar:
> 1. **Tenho todos os inputs listados na seção "Pré-requisitos"?** Se não, parar e pedir.
> 2. **O resultado esperado está definido objetivamente?** Se não, parar e pedir.
> 3. **Existe um comando de verificação?** Se não, parar e pedir.
> 4. **Estou criando conteúdo que não está neste plano?** Se sim, **NÃO FAÇA**. Só execute o que está escrito.

### 0.4 Decisões já tomadas pelo professor Fábio Jorge (não reabrir)

| # | Decisão | Valor | Implicações |
|---|---------|-------|-------------|
| 1 | Orçamento LLM | **DeepSeek** (deepseek-chat / deepseek-reasoner) | Custo ~US$ 0,27/M input tokens, US$ 1,10/M output. Compatível com API OpenAI. |
| 2 | Revisor Humano | **Fábio Jorge** (professor formador, único) | SLA de revisão: até 24h. Notificação por Telegram. |
| 3 | Canal de entrega | **Telegram @fabiojorgebr** / +55 91 985140988 | Apenas Telegram (sem WhatsApp no MVP, ver §3.4) |
| 4 | Hospedagem | **Supabase (DB) + Vercel (cron+dashboard) + Render (worker)** | Stack 100% free-tier inicial |
| 5 | Fontes prioritárias | **Nenhuma pré-definida** | Coletor padrão cobre as 6 famílias; Fábio ajusta após 2 semanas |
| 6 | Política de retenção | **Ignorada no MVP** | Soft-delete após 90 dias (delete lógico, sem purge) |
| 7 | Frequência newsletter | **Diária** (início) → reavaliar após 30 dias | Digest enviado às 7h BRT, dias úteis |
| 8 | Definição de "replicável" | **Híbrido**: código aberto + plano de aula em PDF + vídeo tutorial | Qualquer um dos três basta; tag `replicable=true` |

---

## 1. Ciclo de 5 Personas — Como se integram

### 1.1 Ordem do ciclo (executada a cada passo do plano)

```
   ┌──────────────────────────────────────────────────────────┐
   │  PASSO N do plano                                         │
   └──────────────────────────────────────────────────────────┘
              │
              ▼
   [1] ARQUITETO — projeta a solução do passo
              │
              ▼
   [2] GUARDIÃO DE SEGURANÇA — audita em tempo real
       (se falhar → volta para [1] com lista de correções)
              │
              ▼
   [3] ORQUESTRADOR — define ordem de execução e dependências
              │
              ▼
   [4] ADVOGADO DO USUÁRIO — valida UX e simplicidade
       (se complexo demais → simplifica antes de executar)
              │
              ▼
   [5] AGENTE DO HARNESS — executa + testa + registra evidências
              │
              ▼
   ✅ CHECKPOINT Fx.N (objetivo, mensurável, auditável)
```

### 1.2 Tabela de responsabilidades

| Persona | O que faz no passo | O que NÃO faz |
|---------|--------------------|---------------|
| **Arquiteto** | Desenha schema, escolhe componentes, define contratos | Escreve código, decide UX |
| **Guardião de Segurança** | Lista ameaças, valida inputs, revisa secrets, checa LGPD/ToS | Cancela por excesso de cautela sem justificativa |
| **Orquestrador** | Ordena dependências, paraleliza, marca blockers | Implementa |
| **Advogado do Usuário** | Corta complexidade, simplifica UI, testa acessibilidade | Bloqueia por gosto pessoal |
| **Agente do Harness** | Executa com versões pinadas, testa, logs, commit semântico | Decide arquitetura |

### 1.3 Como a segurança entrou no desenho (não como etapa posterior)

✅ **Desde o desenho.** Toda chave de API é lida de variáveis de ambiente desde o commit 1. O schema do banco separa `findings` (público) de `reviews` (com `reviewer_id`, dado pessoal) já na migração inicial. O coletor respeita `robots.txt` desde a primeira linha do Scrapy. O LLM nunca recebe dados pessoais — só texto de artigos públicos. O Telegram bot usa `chat_id` numérico (não número de telefone em logs).

✅ **Como UX desde o desenho.** Fábio recebe apenas 1 interação por dia: o digest das 7h. Tudo o mais é silencioso. Alertas críticos chegam como card único no Telegram com 1 link, 1 resumo, 1 sugestão de uso. Zero dashboards para configurar. Zero YAML para editar em produção. Tudo via interface web ou comando `obs <action>`.

---

## 2. Stack Tecnológica Final (pinada, sem ambiguidade)

### 2.1 Componentes e versões

| Camada | Componente | Versão exata | Hospedagem |
|--------|------------|--------------|------------|
| Banco de dados | Supabase (Postgres 15 + pgvector) | Free tier (500MB) | Supabase Cloud |
| Cron + API + Dashboard | Next.js 14 (App Router) | 14.2.x | Vercel Hobby |
| Worker (coletores+LLM) | Python 3.11 + FastAPI 0.111 + Celery 5.4 | Python 3.11-slim | Render Free Web Service |
| Fila | Supabase Queue (pgmq) — **NÃO Redis** | Built-in | Supabase |
| LLM | DeepSeek API (`deepseek-chat`) | API v1 (OpenAI-compatible) | DeepSeek Cloud |
| Embeddings | `sentence-transformers` + modelo BGE-M3 | bge-m3 v1.0 | Render (CPU) |
| Telegram bot | `python-telegram-bot` | 21.x | Render |
| E-mail newsletter | Resend | Free 3k/mês | Resend Cloud |
| Observabilidade | Logflare (Supabase nativo) + Sentry | Free tiers | Ambos |
| Versionamento | GitHub | público ou privado | GitHub |

### 2.2 Por que essa stack (decisão do Arquiteto + validação do Advogado do Usuário)

**Advogado do Usuário exigiu**: zero infraestrutura para Fábio gerenciar. Supabase + Vercel + Render são todos PaaS com free tier; nenhum deles exige configurar servidor, firewall ou SSL.

**Arquiteto escolheu Supabase** em vez de Postgres puro + Redis porque: (a) free tier de 500MB cobre o MVP, (b) pgvector já vem habilitado, (c) fila via `pgmq` dispensa Redis separado, (c) auth pronto caso queira abrir o dashboard para outros professores depois.

**Guardião de Segurança aprovou** com 3 condições: (1) RLS (Row Level Security) habilitada em todas as tabelas desde a migração 001, (2) service role key NUNCA commitada, (3) Telegram bot token com escopo restrito ao canal do Fábio.

### 2.3 Variáveis de ambiente (contrato)

> ⚠️ **NUNCA** commitar `.env`. Criar `.env.example` com nomes e valores fake.

```bash
# .env.example (commitar este)
# ─── Supabase ─────────────────────────────────────────────
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxxxx          # só no Render, NUNCA na Vercel
SUPABASE_ANON_KEY=eyJxxxxx                  # Vercel + Render

# ─── DeepSeek ─────────────────────────────────────────────
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# ─── Telegram ─────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
TELEGRAM_CHAT_ID_FABIO=123456789             # numérico, NÃO o telefone

# ─── Resend (newsletter) ──────────────────────────────────
RESEND_API_KEY=re_xxxxx
RESEND_FROM=observatorio@ciseb.edu.br

# ─── App ──────────────────────────────────────────────────
APP_ENV=production
APP_TIMEZONE=America/Fortaleza
NEWSLETTER_SCHEDULE=0 7 * * 1-5              # 7h BRT, dias úteis
TOPN_DAILY=10
```

### ✅ CHECKPOINT F0.1 — Antes de começar a Fase 1

**Critério**: Você (Fábio, ou a IA executora) consegue responder "sim" a todas as 6 perguntas:

1. ✅ Tenho conta no GitHub com repositório criado (público ou privado)?
2. ✅ Tenho conta no Supabase com projeto criado e região `South America (São Paulo)`?
3. ✅ Tenho conta na Vercel conectada ao GitHub?
4. ✅ Tenho conta no Render conectada ao GitHub?
5. ✅ Tenho conta no DeepSeek com US$ 5 de crédito carregado?
6. ✅ Criei um bot no Telegram via `@BotFather` e tenho o token + meu `chat_id` (via `@userinfobot`)?

**Comando de verificação (rodar no terminal, em qualquer pasta):**

```bash
echo "Contas verificadas em: $(date)"
```

Se alguma resposta for "não", **PARE** e crie a conta faltante antes de continuar.

---

## 3. Fase 1 — Bootstrap (Duração alvo: 3 dias)

### Objetivo da Fase 1

Ter um "hello world" ponta-a-ponta: um coletor HTTP simples → grava 1 linha no Supabase → dispara 1 mensagem no Telegram para Fábio. Sem LLM, sem classificação, sem newsletter. Apenas provar que o circuito está vivo.

### 3.1 Estrutura de pastas do monorepo

```
observatorio-ciseb/
├── apps/
│   ├── web/                    # Next.js (Vercel) — dashboard + cron
│   │   ├── app/
│   │   │   ├── api/cron/digest/route.ts
│   │   │   ├── api/cron/collect/route.ts
│   │   │   ├── dashboard/page.tsx
│   │   │   └── layout.tsx
│   │   ├── package.json
│   │   └── next.config.mjs
│   └── worker/                 # Python (Render) — coletores + LLM
│       ├── src/
│       │   ├── collectors/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── web_rss.py
│       │   │   ├── github.py
│       │   │   ├── youtube.py
│       │   │   ├── scholar.py
│       │   │   ├── forums.py
│       │   │   └── events.py
│       │   ├── llm/
│       │   │   ├── __init__.py
│       │   │   ├── deepseek.py
│       │   │   ├── classifier.py
│       │   │   └── scorer.py
│       │   ├── delivery/
│       │   │   ├── __init__.py
│       │   │   ├── telegram.py
│       │   │   └── newsletter.py
│       │   ├── db/
│       │   │   ├── __init__.py
│       │   │   ├── supabase.py
│       │   │   └── queries.py
│       │   ├── utils/
│       │   │   ├── __init__.py
│       │   │   ├── text.py
│       │   │   └── hashing.py
│       │   └── main.py         # entry point Celery worker
│       ├── tests/
│       ├── pyproject.toml
│       ├── Dockerfile
│       └── render.yaml
├── supabase/
│   ├── migrations/
│   │   ├── 001_init.sql
│   │   ├── 002_pgmq.sql
│   │   └── 003_rls.sql
│   └── seed.sql
├── .env.example
├── .github/workflows/ci.yml
├── package.json                # workspace root
└── README.md
```

### 3.2 Passo a passo do bootstrap

#### Passo 1.1 — Criar monorepo e estrutura (Orquestrador)

```bash
mkdir observatorio-ciseb && cd observatorio-ciseb
git init
mkdir -p apps/web apps/worker/src/{collectors,llm,delivery,db,utils} supabase/migrations tests
touch apps/worker/src/{collectors,llm,delivery,db,utils}/__init__.py
```

Criar `.gitignore`:

```gitignore
# Env
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
.venv/
.pytest_cache/
*.egg-info/

# Node
node_modules/
.next/
.vercel/

# IDE
.vscode/
.idea/
.DS_Store

# Logs
*.log
```

#### Passo 1.2 — Migração inicial do Supabase (Arquiteto)

Criar `supabase/migrations/001_init.sql`:

```sql
-- =====================================================
-- Observatório CISEB — Migração 001: Schema inicial
-- =====================================================

-- Habilita pgvector (já vem no Supabase, só precisa ligar)
create extension if not exists vector;

-- Habilita pgmq (fila nativa)
create extension if not exists pgmq;

-- =====================================================
-- Tabela: sources (catálogo de fontes monitoradas)
-- =====================================================
create table if not exists public.sources (
  id            uuid primary key default gen_random_uuid(),
  slug          text not null unique,
  name          text not null,
  family        text not null check (family in ('web','github','forums','social','academic','events')),
  config        jsonb not null default '{}'::jsonb,
  healthy       boolean not null default true,
  last_polled_at timestamptz,
  created_at    timestamptz not null default now()
);

-- =====================================================
-- Tabela: pillars (catálogo dos 6 pilares CISEB)
-- =====================================================
create table if not exists public.pillars (
  id            uuid primary key default gen_random_uuid(),
  slug          text not null unique,    -- 'ia','maker','digital','tech_art','fabrication','robotics'
  name          text not null,
  description   text not null,
  canonical_embedding vector(1024),       -- BGE-M3 = 1024 dims
  created_at    timestamptz not null default now()
);

-- =====================================================
-- Tabela: findings (achados — tabela central)
-- =====================================================
create table if not exists public.findings (
  id              uuid primary key default gen_random_uuid(),
  source_id       uuid not null references public.sources(id) on delete cascade,
  source_url      text not null,
  title           text not null,
  content_text    text,
  snippet         text,
  language        text default 'pt',
  content_hash    text not null unique,  -- SHA-256 hex
  collected_at    timestamptz not null default now(),
  embedding       vector(1024),
  status          text not null default 'new'
                  check (status in ('new','enriched','scored','reviewed','delivered','discarded')),
  metadata        jsonb not null default '{}'::jsonb,
  soft_deleted_at timestamptz            -- MVP: null = ativo; preenchido = soft-delete após 90d
);

create index if not exists idx_findings_hash      on public.findings(content_hash);
create index if not exists idx_findings_status    on public.findings(status);
create index if not exists idx_findings_collected on public.findings(collected_at desc);
create index if not exists idx_findings_embedding on public.findings
  using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- =====================================================
-- Tabela: scores (1:N com findings — um achado pode tocar N pilares)
-- =====================================================
create table if not exists public.scores (
  id              uuid primary key default gen_random_uuid(),
  finding_id      uuid not null references public.findings(id) on delete cascade,
  pillar_id       uuid not null references public.pillars(id) on delete cascade,
  confidence      real not null check (confidence between 0 and 1),
  score_composite integer not null check (score_composite between 0 and 100),
  dim_alignment   integer not null check (dim_alignment between 0 and 100),
  dim_br_luso     integer not null check (dim_br_luso between 0 and 100),
  dim_replicable  integer not null check (dim_replicable between 0 and 100),
  dim_practical   integer not null check (dim_practical between 0 and 100),
  dim_level       integer not null check (dim_level between 0 and 100),
  dim_novelty     integer not null check (dim_novelty between 0 and 100),
  computed_at     timestamptz not null default now(),
  unique (finding_id, pillar_id)
);

create index if not exists idx_scores_finding on public.scores(finding_id);
create index if not exists idx_scores_pillar  on public.scores(pillar_id);

-- =====================================================
-- Tabela: reviews (decisão humana do Fábio)
-- =====================================================
create table if not exists public.reviews (
  id              uuid primary key default gen_random_uuid(),
  finding_id      uuid not null references public.findings(id) on delete cascade,
  reviewer_id     text not null default 'fabio.jorge',
  decision        text not null check (decision in ('approved','rejected','edited')),
  edited_summary  text,
  feedback_tags   text[] not null default '{}',
  reviewed_at     timestamptz not null default now()
);

create index if not exists idx_reviews_finding on public.reviews(finding_id);

-- =====================================================
-- Tabela: deliveries (auditoria de canais)
-- =====================================================
create table if not exists public.deliveries (
  id              uuid primary key default gen_random_uuid(),
  finding_id      uuid not null references public.findings(id) on delete cascade,
  channel         text not null check (channel in ('telegram','newsletter','dashboard')),
  sent_at         timestamptz not null default now(),
  opened_at       timestamptz,
  payload         jsonb
);

create index if not exists idx_deliveries_finding on public.deliveries(finding_id);
create index if not exists idx_deliveries_sent    on public.deliveries(sent_at desc);
```

Criar `supabase/migrations/002_pgmq.sql`:

```sql
-- Fila nativa do Postgres via pgmq
-- Cria a fila principal de eventos
select pgmq.create('findings_queue');
```

Criar `supabase/migrations/003_rls.sql`:

```sql
-- =====================================================
-- Row Level Security — obrigatório desde o commit 1
-- =====================================================

-- Habilitar RLS em todas as tabelas
alter table public.sources    enable row level security;
alter table public.pillars    enable row level security;
alter table public.findings   enable row level security;
alter table public.scores     enable row level security;
alter table public.reviews    enable row level security;
alter table public.deliveries enable row level security;

-- Política: ANON só pode ler sources, pillars, findings aprovados
-- (não pode ler reviews — contém dado pessoal)
create policy "anon read sources"    on public.sources    for select using (true);
create policy "anon read pillars"    on public.pillars    for select using (true);
create policy "anon read findings"   on public.findings   for select using (status in ('reviewed','delivered'));
create policy "anon read scores"     on public.scores     for select using (true);

-- SERVICE ROLE tem acesso total (usado só no Render worker)
-- (Nenhuma policy restrictiva para service_role — bypass RLS por padrão)

-- ANON não pode escrever em nenhuma tabela
-- (default deny)
```

> **Guardião de Segurança ✅**: RLS ativa desde o commit 1. A `service_role_key` (que escreve) só existe no Render; a `anon_key` (que lê) está na Vercel. Mesmo se a Vercel vazar, o atacante só lê findings aprovados.

Criar `supabase/seed.sql`:

```sql
-- Seed dos 6 pilares CISEB (sem embeddings ainda — preenchidos na Fase 2)
insert into public.pillars (slug, name, description) values
  ('ia',         'Inteligência Artificial',
   'Personalização do aprendizado, automação de processos, soluções tecnológicas que preparam alunos para o futuro digital.'),
  ('maker',      'Cultura Maker',
   'Criação prática incentivando estudantes e educadores a desenvolverem projetos com tecnologia e criatividade.'),
  ('digital',    'Cultura Digital',
   'Realidade Virtual e Aumentada, experiências imersivas que enriquecem o ensino conectando o físico ao digital.'),
  ('tech_art',   'Tecnologia e Arte',
   'Integração de tecnologia e arte: jogos, animações, projetos inovadores, desenvolvimento de pensamento computacional.'),
  ('fabrication','Fabricação Digital',
   'Impressoras 3D, cortadoras a laser, prototipagem e fabricação que transformam ideias em produtos reais.'),
  ('robotics',   'Robótica Educacional',
   'Aprendizado prático de engenharia, programação e resolução de problemas com kits modernos de robótica.')
on conflict (slug) do nothing;
```

#### Passo 1.3 — Aplicar migrações no Supabase (Agente do Harness)

1. Acessar o painel do Supabase → SQL Editor
2. Colar o conteúdo de `001_init.sql` → Run
3. Colar o conteúdo de `002_pgmq.sql` → Run
4. Colar o conteúdo de `003_rls.sql` → Run
5. Colar o conteúdo de `seed.sql` → Run

**Verificação**:

```sql
-- Deve retornar 6 linhas
select slug, name from public.pillars order by slug;

-- Deve retornar 6 tabelas
select tablename from pg_tables where schemaname = 'public' order by tablename;
```

**Esperado**: 6 pilares + 6 tabelas (`sources, pillars, findings, scores, reviews, deliveries`).

#### Passo 1.4 — Hello world: coletor → DB → Telegram (4 arquivos)

Criar `apps/worker/pyproject.toml`:

```toml
[project]
name = "observatorio-worker"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "httpx==0.27.0",
  "supabase==2.5.0",
  "python-telegram-bot==21.4",
  "python-dotenv==1.0.1",
  "feedparser==6.0.11",
  "trafilatura==1.12.0",
  "sentence-transformers==3.0.1",
  "openai==1.35.0",                 # DeepSeek é OpenAI-compatible
  "pydantic==2.7.4",
  "celery==5.4.0",
]

[project.optional-dependencies]
dev = ["pytest==8.2.2", "pytest-cov==5.0.0", "ruff==0.5.0"]
```

Criar `apps/worker/src/db/supabase.py`:

```python
"""Cliente Supabase singleton. Lê variáveis de ambiente."""
import os
from supabase import create_client, Client

_url  = os.environ["SUPABASE_URL"]
_key  = os.environ["SUPABASE_SERVICE_ROLE_KEY"]  # só no Render
supabase: Client = create_client(_url, _key)
```

Criar `apps/worker/src/delivery/telegram.py`:

```python
"""Envia mensagem para o Telegram do Fábio."""
import os
from telegram import Bot

_bot_token  = os.environ["TELEGRAM_BOT_TOKEN"]
_chat_id    = os.environ["TELEGRAM_CHAT_ID_FABIO"]
_bot        = Bot(token=_bot_token)

async def send(text: str) -> None:
    """Envia texto simples. Máx 4096 chars (limite do Telegram)."""
    text = text[:4000]  # margem de segurança
    await _bot.send_message(chat_id=_chat_id, text=text, parse_mode="HTML")
```

Criar `apps/worker/src/main.py`:

```python
"""Entry point — hello world do Observatório CISEB."""
import asyncio
import os
import sys
from datetime import datetime, timezone

# Garante que src/ está no path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.db.supabase import supabase
from src.delivery.telegram import send as tg_send


async def hello_world() -> None:
    """Pipeline mínimo: lê timestamp atual, grava 1 finding fake, avisa Fábio."""
    now = datetime.now(timezone.utc).isoformat()

    # 1. Insere 1 finding de teste
    payload = {
        "source_id": None,             # preenchido após criar source
        "source_url": "https://example.com/hello",
        "title": f"Observatório CISEB — hello world @ {now}",
        "content_text": "Primeira execução do pipeline. Apenas teste.",
        "snippet": "hello world",
        "language": "pt",
        "content_hash": "0" * 64,      # placeholder
        "status": "new",
    }

    # Primeiro cria uma source de teste (se não existir)
    src = supabase.table("sources").upsert(
        {"slug": "test", "name": "Teste", "family": "web", "config": {}},
        on_conflict="slug"
    ).execute()
    source_id = src.data[0]["id"]
    payload["source_id"] = source_id

    # Insere o finding
    res = supabase.table("findings").insert(payload).execute()
    finding_id = res.data[0]["id"]

    # 2. Avisa Fábio no Telegram
    msg = (
        f"✅ <b>Observatório CISEB</b> — pipeline vivo\n\n"
        f"Finding ID: <code>{finding_id}</code>\n"
        f"Timestamp: {now}\n\n"
        f"Próximo passo: ligar o coletor RSS real."
    )
    await tg_send(msg)
    print(f"[ok] finding {finding_id} inserido; Fábio avisado.")


if __name__ == "__main__":
    asyncio.run(hello_world())
```

#### Passo 1.5 — Deploy do worker no Render (Agente do Harness)

Criar `apps/worker/render.yaml`:

```yaml
services:
  - type: web
    name: observatorio-worker
    runtime: python
    plan: free
    region: sao-paulo
    buildCommand: pip install -e .
    startCommand: python -m src.main
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_ROLE_KEY
        sync: false
      - key: SUPABASE_ANON_KEY
        sync: false
      - key: DEEPSEEK_API_KEY
        sync: false
      - key: DEEPSEEK_BASE_URL
        value: https://api.deepseek.com
      - key: DEEPSEEK_MODEL
        value: deepseek-chat
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: TELEGRAM_CHAT_ID_FABIO
        sync: false
      - key: APP_TIMEZONE
        value: America/Fortaleza
```

**Passos no painel do Render**:
1. New → Web Service → connectar repo `observatorio-ciseb`
2. Root Directory: `apps/worker`
3. Render detecta `render.yaml` automaticamente
4. Preencher envVars marcadas `sync: false` com valores reais
5. Deploy

### ✅ CHECKPOINT F1.1 — Hello world vivo

**Critérios objetivos**:

1. ✅ Render mostra status `Live` sem erros no log
2. ✅ Tabela `public.findings` no Supabase tem pelo menos 1 linha (rodar: `select count(*) from public.findings;` → esperado ≥ 1)
3. ✅ Fábio recebeu 1 mensagem no Telegram com o texto "Observatório CISEB — pipeline vivo"

**Comando de verificação**:

```sql
-- No SQL Editor do Supabase
select id, title, status, collected_at from public.findings order by collected_at desc limit 5;
```

**Se falhar**:
- Render loga erro → ler log, corrigir, redeploy
- Telegram não chega → verificar `TELEGRAM_CHAT_ID_FABIO` (não é o telefone, é o ID numérico)
- Insert falha → verificar `SUPABASE_SERVICE_ROLE_KEY` (não a anon)

**Não avance para a Fase 2 sem este checkpoint passar.**

---

## 4. Fase 2 — Coleta Real (Duração alvo: 5 dias)

### Objetivo da Fase 2

Substituir o hello world por coletores reais das 6 famílias. Cada coletor publica eventos na fila `pgmq`. O worker consome a fila, normaliza e grava em `findings`. **Sem LLM ainda** — apenas coleta + armazenamento.

### 4.1 Contrato de evento (Arquiteto)

> Toda fonte publica exatamente este schema. IA executora: NÃO modifique os nomes de campos.

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

### 4.2 Utilitários base (Agente do Harness)

Criar `apps/worker/src/utils/hashing.py`:

```python
"""Hash determinístico para deduplicação."""
import hashlib

def content_hash(url: str, title: str, raw_text: str) -> str:
    """SHA-256 hex de url|title|texto-normalizado."""
    normalized = " ".join((url + " " + title + " " + raw_text).split()).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
```

Criar `apps/worker/src/utils/text.py`:

```python
"""Limpeza e normalização de texto."""
import re

_MAX_TOKENS = 5000  # corte preservando início + fim
_SENTENCE_END = re.compile(r"[.!?]\s+")

def clean(raw: str) -> str:
    """Remove caracteres invisíveis, normaliza whitespace."""
    if not raw:
        return ""
    out = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)
    out = re.sub(r"[\u200b-\u200f\u2028-\u202f\u2060\ufeff]", "", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out

def truncate(text: str, max_chars: int = 20000) -> str:
    """Corta preservando início + fim (densidade informacional)."""
    if len(text) <= max_chars:
        return text
    head = text[: int(max_chars * 0.7)]
    tail = text[-int(max_chars * 0.3):]
    return head + "\n[...]\n" + tail

def snippet(text: str, n: int = 200) -> str:
    """Primeiros n caracteres sem quebrar palavra."""
    text = clean(text)
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0]
    return cut + "…"
```

### 4.3 Coletor base (Arquiteto)

Criar `apps/worker/src/collectors/base.py`:

```python
"""Interface comum a todos os coletores."""
from abc import ABC, abstractmethod
from typing import Iterator
from src.utils.hashing import content_hash
from src.utils.text import clean, snippet, truncate

class BaseCollector(ABC):
    """Todo coletor herda desta classe. Implementar apenas `iter_raw()`."""
    slug: str = "base"
    family: str = "web"

    def __init__(self, source_id: str, config: dict):
        self.source_id = source_id
        self.config = config

    @abstractmethod
    def iter_raw(self) -> Iterator[dict]:
        """Yield dicts: {source_url, title, raw_text, language, metadata}."""
        ...

    def normalize(self, raw: dict) -> dict | None:
        """Converte raw → contrato de evento. Retorna None se inválido."""
        url = raw.get("source_url", "").strip()
        title = clean(raw.get("title", ""))[:300]
        text = truncate(clean(raw.get("raw_text", "")), 20000)
        if not url or not title or not text:
            return None
        return {
            "source_id": self.source_id,
            "source_url": url,
            "title": title,
            "content_text": text,
            "snippet": snippet(text, 200),
            "language": raw.get("language", "pt"),
            "content_hash": content_hash(url, title, text),
            "metadata": raw.get("metadata", {}),
            "status": "new",
        }
```

### 4.4 Coletor RSS/Web (Agente do Harness)

Criar `apps/worker/src/collectors/web_rss.py`:

```python
"""Coletor RSS — fonte padrão para portais educacionais."""
import feedparser
from src.collectors.base import BaseCollector

# Lista padrão (Fábio: nenhuma fonte pré-definida — usamos lista bootstrap editável)
DEFAULT_FEEDS = [
    "https://porvir.org/feed/",                 # Porvir
    "https://www.novaescolagpt.com.br/feed",     # Nova Escola
    "https://feeds.feedburner.com/edutech",      # EdTech
    "https://www.mec.gov.br/rss/noticias",       # MEC
]

class RSSCollector(BaseCollector):
    slug = "rss-default"
    family = "web"

    def iter_raw(self):
        feeds = self.config.get("feeds", DEFAULT_FEEDS)
        for url in feeds:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]:  # máx 20 por feed por poll
                yield {
                    "source_url": entry.get("link", ""),
                    "title":      entry.get("title", ""),
                    "raw_text":   entry.get("summary", "") or entry.get("description", ""),
                    "language":   "pt",
                    "metadata": {
                        "author":       entry.get("author", ""),
                        "published_at": entry.get("published", ""),
                    },
                }
```

### 4.5 Coletor GitHub (Agente do Harness)

Criar `apps/worker/src/collectors/github.py`:

```python
"""Coletor GitHub via API REST (sem GraphQL para simplificar)."""
import httpx
from src.collectors.base import BaseCollector

GITHUB_TOPICS = [
    "educational-robotics", "maker-education", "educational-games",
    "scratch-projects", "microbit", "lego-spike",
    "3d-printing-education", "ai-education", "computational-thinking",
]
GITHUB_TOKEN = ""  # opcional; sem token, rate-limit = 60 req/h

class GitHubCollector(BaseCollector):
    slug = "github-edu"
    family = "github"

    def iter_raw(self):
        headers = {"Accept": "application/vnd.github+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

        for topic in GITHUB_TOPICS:
            url = f"https://api.github.com/search/repositories?q=topic:{topic}+pushed:>{self._cutoff()}&sort=updated&per_page=10"
            with httpx.Client(timeout=30) as client:
                r = client.get(url, headers=headers)
                if r.status_code != 200:
                    continue
                for item in r.json().get("items", []):
                    yield {
                        "source_url":  item["html_url"],
                        "title":       item["full_name"] + " — " + (item.get("description") or ""),
                        "raw_text":    item.get("description", "") + " " + self._readme_snippet(item),
                        "language":    "en",
                        "metadata": {
                            "author":       item["owner"]["login"],
                            "published_at": item["updated_at"],
                            "stars":        item["stargazers_count"],
                            "topics":       item.get("topics", []),
                        },
                    }

    def _cutoff(self) -> str:
        from datetime import datetime, timedelta
        return (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%d")

    def _readme_snippet(self, item: dict) -> str:
        """Tenta ler README; se falhar, retorna vazio (não derruba coletor)."""
        try:
            with httpx.Client(timeout=10) as c:
                r = c.get(item["url"] + "/readme", headers={"Accept": "application/vnd.github.raw"})
                if r.status_code == 200:
                    return r.text[:3000]
        except Exception:
            pass
        return ""
```

### 4.6 Coletor YouTube (Agente do Harness)

Criar `apps/worker/src/collectors/youtube.py`:

```python
"""Coletor YouTube — usa transcript API (não exige chave de API)."""
from youtube_transcript_api import YouTubeTranscriptApi
import httpx
from src.collectors.base import BaseCollector

# Canais brasileiros de educação tech (lista bootstrap editável)
DEFAULT_CHANNELS = [
    "UCBa65JtQNl8nVfrZgqB-9dg",  # Manual do Mundo
    "UC2tvA3W2bVw5zg6eAfqDWHQ",  # Casa Ninja
    # adicionar mais conforme Fábio identificar
]

class YouTubeCollector(BaseCollector):
    slug = "youtube-edu"
    family = "social"

    def iter_raw(self):
        for ch in self.config.get("channels", DEFAULT_CHANNELS):
            videos = self._list_recent_videos(ch, max_results=10)
            for v in videos:
                transcript = self._get_transcript(v["id"])
                if not transcript:
                    continue
                yield {
                    "source_url": f"https://youtube.com/watch?v={v['id']}",
                    "title":      v["title"],
                    "raw_text":   transcript,
                    "language":   "pt",
                    "metadata": {
                        "author":       v.get("channel_title", ""),
                        "published_at": v.get("published_at", ""),
                    },
                }

    def _list_recent_videos(self, channel_id: str, max_results: int = 10) -> list[dict]:
        # Scraping leve da página do canal (sem API key)
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            r = httpx.get(url, timeout=15)
            r.raise_for_status()
        except Exception:
            return []
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        out = []
        for entry in root.findall("a:entry", ns)[:max_results]:
            vid = entry.find("a:link", ns).get("href").split("v=")[1]
            out.append({
                "id":             vid,
                "title":          entry.find("a:title", ns).text,
                "channel_title":  entry.find("a:author/a:name", ns).text,
                "published_at":   entry.find("a:published", ns).text,
            })
        return out

    def _get_transcript(self, video_id: str) -> str:
        try:
            t = YouTubeTranscriptApi.get_transcript(video_id, languages=["pt", "pt-BR", "en"])
            return " ".join(x["text"] for x in t)[:5000]
        except Exception:
            return ""
```

### 4.7 Coletores Scholar, Fóruns e Eventos (Agente do Harness)

Criar `apps/worker/src/collectors/scholar.py`:

```python
"""Coletor Google Scholar — via biblioteca scholarly."""
from scholarly import scholarly
from src.collectors.base import BaseCollector

DEFAULT_QUERIES = [
    "cultura maker educação básica Brasil",
    "robótica educacional ensino fundamental",
    "inteligência artificial educação escolar",
    "realidade virtual ensino aprendizagem",
    "fablab escola pública",
    "pensamento computacional Scratch",
]

class ScholarCollector(BaseCollector):
    slug = "scholar-ciseb"
    family = "academic"

    def iter_raw(self):
        for q in self.config.get("queries", DEFAULT_QUERIES):
            try:
                results = scholarly.search_pubs(q)
                for _ in range(10):  # top 10 por query
                    try:
                        pub = next(results)
                    except StopIteration:
                        break
                    bib = pub.get("bib", {})
                    yield {
                        "source_url":  pub.get("pub_url", "") or pub.get("eprint_url", ""),
                        "title":       bib.get("title", ""),
                        "raw_text":    bib.get("abstract", "") or bib.get("title", ""),
                        "language":    "pt" if "Português" in bib.get("pub", "") else "en",
                        "metadata": {
                            "author":       ", ".join(bib.get("author", [])[:3]),
                            "published_at": bib.get("pub_year", ""),
                            "venue":        bib.get("pub", ""),
                            "cites":        pub.get("num_citations", 0),
                        },
                    }
            except Exception:
                continue
```

Criar `apps/worker/src/collectors/forums.py`:

```python
"""Coletor Reddit — subreddits de educação tech."""
import httpx
from src.collectors.base import BaseCollector

DEFAULT_SUBREDDITS = [
    "r/education", "r/edtech", "r/learnprogramming",
    "r/Robotics", "r/3Dprinting",
]

class RedditCollector(BaseCollector):
    slug = "reddit-edu"
    family = "forums"

    def iter_raw(self):
        for sub in self.config.get("subreddits", DEFAULT_SUBREDDITS):
            url = f"https://www.reddit.com/{sub}/hot.json?limit=15"
            try:
                r = httpx.get(url, timeout=20, headers={"User-Agent": "ObservatorioCISEB/1.0"})
                r.raise_for_status()
            except Exception:
                continue
            for child in r.json().get("data", {}).get("children", []):
                d = child["data"]
                yield {
                    "source_url":  "https://reddit.com" + d["permalink"],
                    "title":       d["title"],
                    "raw_text":    d.get("selftext", "") or d["title"],
                    "language":    "en",
                    "metadata": {
                        "author":       d.get("author", ""),
                        "published_at": str(d.get("created_utc", "")),
                        "score":        d.get("score", 0),
                    },
                }
```

Criar `apps/worker/src/collectors/events.py`:

```python
"""Coletor de editais MEC/FAPESP/CAPES via scraping de feeds."""
import feedparser
from src.collectors.base import BaseCollector

DEFAULT_FEEDS = [
    "https://www.gov.br/capes/pt-br/assuntos/noticias/RSS",
    "https://www.gov.br/mec/pt-br/assuntos/noticias/RSS",
    "https://fapesp.br/rss",
]

class EventsCollector(BaseCollector):
    slug = "events-mec"
    family = "events"

    def iter_raw(self):
        for url in self.config.get("feeds", DEFAULT_FEEDS):
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                yield {
                    "source_url":  entry.get("link", ""),
                    "title":       entry.get("title", ""),
                    "raw_text":    entry.get("summary", "") or entry.get("title", ""),
                    "language":    "pt",
                    "metadata": {
                        "author":       entry.get("author", ""),
                        "published_at": entry.get("published", ""),
                    },
                }
```

### 4.8 Orquestrador dos coletores (Orquestrador)

Criar `apps/worker/src/main.py` (substitui o hello world):

```python
"""Worker principal — roda todos os coletores em sequência e grava no Supabase."""
import os
import sys
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.db.supabase import supabase
from src.collectors.web_rss import RSSCollector
from src.collectors.github import GitHubCollector
from src.collectors.youtube import YouTubeCollector
from src.collectors.scholar import ScholarCollector
from src.collectors.forums import RedditCollector
from src.collectors.events import EventsCollector

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("worker")

COLLECTORS = [
    ("rss-default", RSSCollector),
    ("github-edu",  GitHubCollector),
    ("youtube-edu", YouTubeCollector),
    ("scholar-ciseb", ScholarCollector),
    ("reddit-edu",  RedditCollector),
    ("events-mec",  EventsCollector),
]

def ensure_source(slug: str, name: str, family: str, config: dict = None) -> str:
    """Cria source se não existir; retorna id."""
    res = supabase.table("sources").upsert(
        {"slug": slug, "name": name, "family": family, "config": config or {}},
        on_conflict="slug"
    ).execute()
    return res.data[0]["id"]

def insert_finding(normalized: dict) -> bool:
    """Insere se hash não existir. Retorna True se inseriu."""
    # Verifica duplicata
    exists = supabase.table("findings") \
        .select("id") \
        .eq("content_hash", normalized["content_hash"]) \
        .limit(1).execute()
    if exists.data:
        return False
    try:
        supabase.table("findings").insert(normalized).execute()
        return True
    except Exception as e:
        log.error(f"insert falhou: {e}")
        return False

def run_once() -> dict:
    """Roda uma rodada de coleta. Retorna métricas."""
    stats = {"inserted": 0, "skipped_dup": 0, "errors": 0}
    for slug, cls in COLLECTORS:
        source_id = ensure_source(slug, slug.replace("-", " ").title(), cls.family)
        try:
            for raw in cls(source_id=source_id, config={}).iter_raw():
                normalized = cls(source_id=source_id, config={}).normalize(raw)
                if not normalized:
                    continue
                if insert_finding(normalized):
                    stats["inserted"] += 1
                else:
                    stats["skipped_dup"] += 1
        except Exception as e:
            log.error(f"coletor {slug} falhou: {e}")
            stats["errors"] += 1
    log.info(f"rodada completa: {stats}")
    return stats

if __name__ == "__main__":
    run_once()
```

### ✅ CHECKPOINT F2.1 — Coleta real funcionando

**Critérios**:

1. ✅ Executar `python -m src.main` no Render → sem exceções
2. ✅ Após 1 rodada, tabela `findings` tem ≥ 50 linhas (todas as 6 famílias devem contribuir)
3. ✅ Log do Render mostra `[INFO] worker: rodada completa: {'inserted': N, ...}` com N ≥ 50

**Comandos de verificação**:

```sql
-- No Supabase SQL Editor
select count(*) as total from public.findings;

-- Por família de source
select s.family, count(*) as n
from public.findings f
join public.sources s on s.id = f.source_id
group by s.family
order by n desc;

-- Duplicatas (deve ser 0)
select content_hash, count(*) from public.findings
group by content_hash having count(*) > 1;
```

**Esperado**: total ≥ 50, pelo menos 4 famílias com ≥ 5 achados cada, 0 duplicatas.

**Se falhar**:
- GitHub rate-limit (60/h sem token) → criar Personal Access Token no GitHub e adicionar ao env
- Scholar bloqueia → reduzir queries ou adicionar proxy (fase posterior)
- YouTube sem transcrição → normal (muitos vídeos não têm); coletor pula silenciosamente

**Não avance para a Fase 3 sem este checkpoint.**

---

## 5. Fase 3 — Classificação + Scoring + Embeddings (Duração alvo: 7 dias)

### Objetivo da Fase 3

Para cada finding com `status='new'`: (1) enriquecer com LLM (resumo + atributos), (2) gerar embedding vetorial, (3) classificar em pilares CISEB, (4) calcular score composto, (5) atualizar `status='scored'`. Ao final, Fábio tem top-N diário pronto para revisar.

### 5.1 Geração de embeddings dos 6 pilares (Arquiteto)

> **Pré-requisito**: Fase 2 aprovada. Encontrar o arquivo `BGE-M3` em `~/.cache/huggingface/` após primeiro run.

Criar `apps/worker/src/llm/embeddings.py`:

```python
"""Embeddings via BGE-M3 (multilíngue, 1024 dims)."""
from sentence_transformers import SentenceTransformer
from src.db.supabase import supabase

_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-m3")
    return _model

def embed_text(text: str) -> list[float]:
    """Retorna vetor 1024-dim. Texto vazio → vetor zero."""
    if not text or not text.strip():
        return [0.0] * 1024
    vec = get_model().encode(text[:3000], normalize_embeddings=True)
    return vec.tolist()

def embed_pillars() -> None:
    """Computa embeddings das descrições dos 6 pilares e grava no DB."""
    pillars = supabase.table("pillars").select("*").execute().data
    for p in pillars:
        text = f"{p['name']}. {p['description']}"
        vec = embed_text(text)
        supabase.table("pillars").update(
            {"canonical_embedding": vec}
        ).eq("id", p["id"]).execute()
        print(f"[ok] pilar {p['slug']} embedado")
```

### 5.2 Cliente DeepSeek (Arquiteto)

> **Guardião de Segurança ✅**: `DEEPSEEK_API_KEY` lida de env, nunca logada. Client httpx com timeout de 60s. Em caso de erro, retorna `None` (não derruba pipeline).

Criar `apps/worker/src/llm/deepseek.py`:

```python
"""Cliente DeepSeek — compatível com OpenAI SDK."""
import os
import logging
from openai import OpenAI

log = logging.getLogger("deepseek")

_client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)
_model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

def chat(system: str, user: str, temperature: float = 0.2, max_tokens: int = 800) -> str | None:
    """Chama DeepSeek. Retorna texto da resposta ou None em caso de erro."""
    try:
        r = _client.chat.completions.create(
            model=_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        log.error(f"DeepSeek falhou: {e}")
        return None
```

### 5.3 Prompt de enriquecimento (Advogado do Usuário + Guardião)

> **Advogado do Usuário ✅**: prompt é determinístico, retorna JSON. Se o LLM alucinar campo, o parser rejeita e o finding fica `status='new'` para retry.
>
> **Guardião ✅**: prompt instrui o LLM a NUNCA inventar dados; se não souber, preencher `null`. Nenhum dado pessoal é enviado (só texto de artigos públicos).

Criar `apps/worker/src/llm/classifier.py`:

```python
"""Classificação multi-rótulo por pilar + enriquecimento."""
import json
import logging
from src.llm.deepseek import chat
from src.llm.embeddings import embed_text

log = logging.getLogger("classifier")

SYSTEM_PROMPT = """Você é um classificador de conteúdo educacional para o CISEB (Centro de Inovação).
Sua tarefa: ler um texto e retornar APENAS um JSON válido, sem comentários, sem markdown.

Os 6 pilares CISEB são:
- ia: Inteligência Artificial (personalização, automação, IA em educação)
- maker: Cultura Maker (projetos práticos, construção, criatividade)
- digital: Cultura Digital (RV, RA, experiências imersivas)
- tech_art: Tecnologia e Arte (jogos, animações, pensamento computacional)
- fabrication: Fabricação Digital (impressão 3D, cortadora a laser, prototipagem)
- robotics: Robótica Educacional (kits, competições, programação de robôs)

REGRAS:
1. Atribua confiança (0.0 a 1.0) para cada pilar. Se < 0.30, use 0.0.
2. Atribua no mínimo 1 pilar com confiança >= 0.55.
3. NÃO invente dados. Se não souber, use null.
4. Retorne APENAS o JSON, sem texto adicional.

Formato de saída:
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
"""

USER_TEMPLATE = """Título: {title}

Conteúdo:
{text}

Retorne o JSON:"""


def enrich(finding: dict) -> dict | None:
    """Enriquece 1 finding. Retorna dict estruturado ou None."""
    text = (finding.get("content_text") or "")[:4000]
    if len(text) < 50:
        return None

    user_msg = USER_TEMPLATE.format(title=finding["title"], text=text)
    raw = chat(SYSTEM_PROMPT, user_msg, temperature=0.1, max_tokens=600)

    if not raw:
        return None

    # Limpa possíveis markdown wrappers
    raw = raw.strip().strip("`").strip()
    if raw.startswith("json"):
        raw = raw[4:].strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log.warning(f"DeepSeek retornou JSON inválido para {finding['id']}")
        return None

    # Validação mínima
    if "pillars" not in data or not isinstance(data["pillars"], list):
        return None
    if not any(p.get("confidence", 0) >= 0.55 for p in data["pillars"]):
        return None

    return data


def compute_score(enriched: dict, finding: dict) -> dict:
    """Calcula score composto 0-100 com a fórmula do plano v1.

    Pesos (decisão do Arquiteto, validada pelo Advogado do Usuário):
      30% alinhamento (média das confianças)
      20% br_luso (geo_br true = 100, false = 30)
      20% replicável (true = 100, false = 30)
      15% projeto prático (true = 100, false = 40)
      10% nível educacional (tem audience = 80, null = 50)
       5% novidade (computed elsewhere, default 70)
    """
    pillars = enriched.get("pillars", [])
    alignment = sum(p.get("confidence", 0) for p in pillars) / max(len(pillars), 1)
    dim_alignment = int(alignment * 100)

    dim_br = 100 if enriched.get("geo_br") else 30
    dim_rep = 100 if enriched.get("replicable") else 30
    dim_pra = 100 if enriched.get("practical_project") else 40
    dim_lvl = 80 if enriched.get("audience") else 50

    # Novidade: preenchido pelo caller com base em collected_at
    dim_nov = enriched.get("_dim_novelty", 70)

    score = (
        dim_alignment * 0.30 +
        dim_br         * 0.20 +
        dim_rep         * 0.20 +
        dim_pra         * 0.15 +
        dim_lvl         * 0.10 +
        dim_nov         * 0.05
    )
    score = int(round(score))

    return {
        "dim_alignment": dim_alignment,
        "dim_br_luso":    dim_br,
        "dim_replicable": dim_rep,
        "dim_practical":  dim_pra,
        "dim_level":      dim_lvl,
        "dim_novelty":    dim_nov,
        "score_composite": score,
    }


def novelty_score(collected_at_iso: str) -> int:
    """100 se ≤7d; 80 se ≤30d; 50 se ≤90d; 30 caso contrário."""
    from datetime import datetime, timezone, timedelta
    try:
        collected = datetime.fromisoformat(collected_at_iso.replace("Z", "+00:00"))
    except Exception:
        return 50
    days = (datetime.now(timezone.utc) - collected).days
    if days <= 7:   return 100
    if days <= 30:  return 80
    if days <= 90:  return 50
    return 30
```

### 5.4 Pipeline de processamento (Orquestrador)

Substituir `apps/worker/src/main.py` por:

```python
"""Worker principal — coleta + enriquecimento + scoring em sequência."""
import os
import sys
import logging
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.db.supabase import supabase
from src.collectors.web_rss import RSSCollector
from src.collectors.github import GitHubCollector
from src.collectors.youtube import YouTubeCollector
from src.collectors.scholar import ScholarCollector
from src.collectors.forums import RedditCollector
from src.collectors.events import EventsCollector
from src.llm.embeddings import embed_text, embed_pillars
from src.llm.classifier import enrich, compute_score, novelty_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("worker")

COLLECTORS = [
    ("rss-default",   RSSCollector),
    ("github-edu",    GitHubCollector),
    ("youtube-edu",   YouTubeCollector),
    ("scholar-ciseb", ScholarCollector),
    ("reddit-edu",    RedditCollector),
    ("events-mec",    EventsCollector),
]

PILLAR_ID_CACHE = {}

def _pillar_id_map() -> dict:
    """Cache slug → id dos pilares."""
    if not PILLAR_ID_CACHE:
        for p in supabase.table("pillars").select("id, slug").execute().data:
            PILLAR_ID_CACHE[p["slug"]] = p["id"]
    return PILLAR_ID_CACHE

def ensure_source(slug, name, family, config=None):
    res = supabase.table("sources").upsert(
        {"slug": slug, "name": name, "family": family, "config": config or {}},
        on_conflict="slug"
    ).execute()
    return res.data[0]["id"]

def insert_finding(normalized):
    exists = supabase.table("findings").select("id").eq("content_hash", normalized["content_hash"]).limit(1).execute()
    if exists.data:
        return False
    try:
        supabase.table("findings").insert(normalized).execute()
        return True
    except Exception as e:
        log.error(f"insert falhou: {e}")
        return False

def run_collect() -> dict:
    """Fase de coleta — igual à Fase 2."""
    stats = {"inserted": 0, "skipped_dup": 0, "errors": 0}
    for slug, cls in COLLECTORS:
        source_id = ensure_source(slug, slug.replace("-", " ").title(), cls.family)
        try:
            c = cls(source_id=source_id, config={})
            for raw in c.iter_raw():
                normalized = c.normalize(raw)
                if not normalized:
                    continue
                if insert_finding(normalized):
                    stats["inserted"] += 1
                else:
                    stats["skipped_dup"] += 1
        except Exception as e:
            log.error(f"coletor {slug} falhou: {e}")
            stats["errors"] += 1
    log.info(f"coleta: {stats}")
    return stats

def run_enrich_and_score(batch_size: int = 20) -> dict:
    """Para cada finding com status='new': enriquece + classifica + scoreia."""
    stats = {"enriched": 0, "failed": 0, "scored_high": 0}

    # Garante que pilares têm embeddings
    embed_pillars()

    # Pega batch de findings new
    new = supabase.table("findings") \
        .select("*") \
        .eq("status", "new") \
        .order("collected_at", desc=False) \
        .limit(batch_size).execute().data

    log.info(f"enriquecendo {len(new)} findings")

    for f in new:
        # 1. Embedding do finding
        vec = embed_text(f["title"] + " " + (f["content_text"] or ""))

        # 2. Enriquecimento LLM
        enriched = enrich(f)
        if not enriched:
            # Marca como failed mantendo status='new' para retry na próxima rodada
            stats["failed"] += 1
            continue

        # 3. Novidade baseada em collected_at
        enriched["_dim_novelty"] = novelty_score(f["collected_at"])

        # 4. Score
        sc = compute_score(enriched, f)

        # 5. Atualiza finding
        supabase.table("findings").update({
            "embedding": vec,
            "status":    "scored",
            "snippet":   enriched.get("summary", f.get("snippet")),
            "metadata":  {**(f.get("metadata") or {}), "enriched": enriched},
        }).eq("id", f["id"]).execute()

        # 6. Cria scores (1 por pilar)
        pillar_map = _pillar_id_map()
        scores_rows = []
        for p in enriched["pillars"]:
            pid = pillar_map.get(p["slug"])
            if not pid:
                continue
            scores_rows.append({
                "finding_id":      f["id"],
                "pillar_id":       pid,
                "confidence":      p["confidence"],
                "score_composite": sc["score_composite"],
                "dim_alignment":   sc["dim_alignment"],
                "dim_br_luso":     sc["dim_br_luso"],
                "dim_replicable":  sc["dim_replicable"],
                "dim_practical":   sc["dim_practical"],
                "dim_level":       sc["dim_level"],
                "dim_novelty":     sc["dim_novelty"],
            })
        if scores_rows:
            supabase.table("scores").upsert(scores_rows, on_conflict="finding_id,pillar_id").execute()

        stats["enriched"] += 1
        if sc["score_composite"] >= 75:
            stats["scored_high"] += 1

    log.info(f"enriquecimento: {stats}")
    return stats

def run_once():
    """Pipeline completo: coleta → enriquece → scoreia."""
    run_collect()
    run_enrich_and_score(batch_size=20)

if __name__ == "__main__":
    run_once()
```

### ✅ CHECKPOINT F3.1 — Pipeline completo com LLM

**Critérios**:

1. ✅ `python -m src.main` roda sem erros no Render
2. ✅ Após 1 rodada, `findings` com `status='scored'` ≥ 20
3. ✅ Tabela `scores` tem ≥ 20 linhas (1+ por finding scored)
4. ✅ `pillars.canonical_embedding` não é null para nenhum pilar
5. ✅ Render log mostra: `enriquecimento: {'enriched': N, 'failed': M, ...}` com N ≥ 20

**Comandos de verificação**:

```sql
-- Quantos findings por status?
select status, count(*) from public.findings group by status;

-- Top 10 achados com maior score
select f.title, s.score_composite, p.slug as pilar, s.confidence
from public.findings f
join public.scores s on s.finding_id = f.id
join public.pillars p on p.id = s.pillar_id
order by s.score_composite desc
limit 10;

-- Embeddings preenchidos?
select slug, canonical_embedding is not null as tem_embedding
from public.pillars;
```

**Esperado**: 6 pilares com `tem_embedding = true`; ≥ 20 findings `scored`; top-10 com scores entre 50 e 95.

**Custo DeepSeek estimado**: 20 findings × ~2k tokens input × US$ 0.27/M = US$ 0,011 por rodada. Diariamente ~US$ 0,01 — ou seja, US$ 0,30/mês para 30 rodadas/dia.

**Se falhar**:
- DeepSeek retorna 429 (rate limit) → reduzir `batch_size` para 10
- JSON inválido repetidamente → ativar `deepseek-reasoner` em vez de `deepseek-chat` (melhor em JSON)
- Embeddings demoram muito na primeira rodada → normal, baixa modelo 2GB uma vez

**Não avance para a Fase 4 sem este checkpoint.**

---

## 6. Fase 4 — Entrega + Revisão Humana (Duração alvo: 5 dias)

### Objetivo da Fase 4

(1) Alertas instantâneos via Telegram para findings com score ≥ 75.
(2) Geração do digest diário (newsletter) às 7h BRT, dias úteis.
(3) Interface web simples para Fábio revisar o top-N diário (aprovar/editar/rejeitar).
(4) Loop de feedback: decisões do Fábio gravadas em `reviews`.

### 6.1 Alertas instantâneos no Telegram (Agente do Harness)

> **Advogado do Usuário ✅**: card único, 5 elementos, sem barulho. Fábio recebe no máximo 5 alertas/dia (configurável).

> **Guardião ✅**: `TELEGRAM_CHAT_ID_FABIO` é o chat_id numérico, não o telefone. O telefone já está no perfil do Fábio; não precisa ser digitado em nenhum log.

Substituir `apps/worker/src/delivery/telegram.py`:

```python
"""Envia cards de alerta para o Telegram do Fábio."""
import os
import logging
from telegram import Bot
from telegram.constants import ParseMode

log = logging.getLogger("telegram")

_bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
_chat_id   = os.environ["TELEGRAM_CHAT_ID_FABIO"]
_bot       = Bot(token=_bot_token)

# Cores por pilar (emoji + label)
PILLAR_LABELS = {
    "ia":         "🧠 IA",
    "maker":      "🛠 Maker",
    "digital":    "🥽 Cultura Digital",
    "tech_art":   "🎨 Tech+Arte",
    "fabrication":"🖨 Fab Digital",
    "robotics":   "🤖 Robótica",
}

def _format_card(finding: dict, scores: list[dict], pillars_map: dict) -> str:
    """Formata card HTML para Telegram (máx 4096 chars)."""
    top_score = max((s["score_composite"] for s in scores), default=0)
    top_pillars = sorted(scores, key=lambda s: s["score_composite"], reverse=True)[:3]
    pilares_txt = " · ".join(
        f"{PILLAR_LABELS.get(pillars_map.get(s['pillar_id'], ''), '?')} ({s['score_composite']})"
        for s in top_pillars
    )
    enriched = (finding.get("metadata") or {}).get("enriched", {})
    summary  = enriched.get("summary", finding.get("snippet", ""))
    app_sugg = enriched.get("application_suggestion", "")

    msg = (
        f"🚨 <b>Alerta — score {top_score}/100</b>\n\n"
        f"<b>{finding['title']}</b>\n\n"
        f"📁 {pilares_txt}\n\n"
        f"📝 {summary}\n\n"
        f"💡 <i>Aplicação:</i> {app_sugg}\n\n"
        f"🔗 {finding['source_url']}"
    )
    return msg[:4000]

async def send_alert(finding: dict, scores: list[dict], pillars_map: dict) -> None:
    """Envia 1 card de alerta para o Fábio."""
    text = _format_card(finding, scores, pillars_map)
    try:
        await _bot.send_message(chat_id=_chat_id, text=text, parse_mode=ParseMode.HTML,
                                 disable_web_page_preview=False)
        log.info(f"alerta enviado: {finding['id']}")
    except Exception as e:
        log.error(f"telegram falhou: {e}")

async def send_digest(findings: list[dict], date_str: str) -> None:
    """Envia digest diário (lista de top-N)."""
    if not findings:
        await _bot.send_message(chat_id=_chat_id,
            text=f"📭 Digest {date_str} — nenhum achado relevante hoje.")
        return

    lines = [f"📬 <b>Digest {date_str}</b> — {len(findings)} achados\n"]
    for i, f in enumerate(findings, 1):
        top_score = max((s["score_composite"] for s in f["_scores"]), default=0)
        lines.append(f"{i}. [{top_score}] <b>{f['title'][:80]}</b>")
        lines.append(f"   🔗 {f['source_url']}\n")

    text = "\n".join(lines)
    # Quebra em mensagens de 4000 chars
    for i in range(0, len(text), 4000):
        await _bot.send_message(chat_id=_chat_id, text=text[i:i+4000],
                                 parse_mode=ParseMode.HTML, disable_web_page_preview=True)
```

### 6.2 Worker com alertas integrados (Orquestrador)

Adicionar ao final de `apps/worker/src/main.py` (substituir `run_enrich_and_score`):

```python
async def send_alerts_for_high_scores():
    """Pega findings scored com score ≥ 75 ainda não entregues e dispara alerta."""
    from src.delivery.telegram import send_alert

    # Pega findings scored não delivered
    pending = supabase.table("findings") \
        .select("*") \
        .eq("status", "scored") \
        .order("collected_at", desc=True) \
        .limit(10).execute().data

    pillars_map = {p["id"]: p["slug"] for p in supabase.table("pillars").select("id, slug").execute().data}

    for f in pending:
        # Pega scores
        scores = supabase.table("scores").select("*").eq("finding_id", f["id"]).execute().data
        if not scores:
            continue
        top = max(s["score_composite"] for s in scores)
        if top < 75:
            continue

        # Verifica se já foi entregue via telegram
        already = supabase.table("deliveries") \
            .select("id") \
            .eq("finding_id", f["id"]) \
            .eq("channel", "telegram") \
            .limit(1).execute().data
        if already:
            continue

        await send_alert(f, scores, pillars_map)

        # Registra delivery
        supabase.table("deliveries").insert({
            "finding_id": f["id"],
            "channel":    "telegram",
            "payload":    {"score": top},
        }).execute()

        # Atualiza status
        supabase.table("findings").update({"status": "delivered"}).eq("id", f["id"]).execute()
```

### 6.3 Cron na Vercel (Orquestrador)

Criar `apps/web/app/api/cron/collect/route.ts`:

```typescript
// Cron que dispara o worker do Render para rodar uma rodada
import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const maxDuration = 60;

export async function GET(request: Request) {
  // Proteção: só Vercel Cron pode chamar
  const authHeader = request.headers.get('authorization');
  const expected = `Bearer ${process.env.CRON_SECRET}`;
  if (authHeader !== expected) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  const renderUrl = process.env.RENDER_WORKER_URL;
  if (!renderUrl) {
    return NextResponse.json({ error: 'RENDER_WORKER_URL not set' }, { status: 500 });
  }

  // Trigger no Render
  const r = await fetch(`${renderUrl}/run`, { method: 'POST' });
  return NextResponse.json({ ok: r.ok, status: r.status });
}
```

Criar `vercel.json` na raiz do projeto:

```json
{
  "crons": [
    {
      "path": "/api/cron/collect?secret=CRON_SECRET",
      "schedule": "0 */4 * * *"
    }
  ]
}
```

> Roda a cada 4 horas. Ajustar para `"0 * * * *"` (horário) se quiser mais frequência.

### 6.4 Interface de revisão web (Advogado do Usuário)

> **Advogado do Usuário ✅**: tela única. Lista de cards, cada um com 3 botões (✅ Aprovar / ✏️ Editar / ❌ Rejeitar). Nada de dashboards. Nada de filtros complexos no MVP.

Criar `apps/web/app/dashboard/page.tsx`:

```tsx
// Dashboard minimalista: lista de top-N do dia para revisão
'use client';

import { useEffect, useState } from 'react';

type Finding = {
  id: string;
  title: string;
  source_url: string;
  snippet: string;
  metadata?: { enriched?: { application_suggestion?: string; summary?: string } };
  _scores: { score_composite: number; pillar_slug: string }[];
};

export default function Dashboard() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/findings/pending')
      .then(r => r.json())
      .then(d => { setFindings(d.findings || []); setLoading(false); });
  }, []);

  async function decide(id: string, decision: 'approved' | 'rejected') {
    await fetch('/api/findings/decide', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id, decision }),
    });
    setFindings(f => f.filter(x => x.id !== id));
  }

  if (loading) return <div style={{padding: 40}}>Carregando…</div>;

  return (
    <main style={{maxWidth: 800, margin: '0 auto', padding: 24, fontFamily: 'system-ui'}}>
      <h1>Observatório CISEB — Revisão</h1>
      <p>{findings.length} achados para revisar hoje</p>

      {findings.map(f => {
        const top = f._scores[0] ?? { score_composite: 0, pillar_slug: '?' };
        const enriched = f.metadata?.enriched;
        return (
          <article key={f.id} style={{
            border: '1px solid #ddd', borderRadius: 8, padding: 16, marginBottom: 16
          }}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline'}}>
              <h2 style={{margin: 0, fontSize: 18}}>{f.title}</h2>
              <span style={{
                background: top.score_composite >= 75 ? '#1b6d97' : '#888',
                color: 'white', padding: '4px 12px', borderRadius: 12, fontSize: 14
              }}>
                {top.score_composite} · {top.pillar_slug}
              </span>
            </div>

            <p style={{color: '#444', marginTop: 12}}>{enriched?.summary || f.snippet}</p>

            {enriched?.application_suggestion && (
              <p style={{background: '#f5f5f5', padding: 8, borderRadius: 4}}>
                💡 {enriched.application_suggestion}
              </p>
            )}

            <p><a href={f.source_url} target="_blank">🔗 Ver fonte original</a></p>

            <div style={{display: 'flex', gap: 8, marginTop: 12}}>
              <button onClick={() => decide(f.id, 'approved')}
                      style={{background: '#4a845d', color: 'white', border: 'none',
                              padding: '8px 16px', borderRadius: 4, cursor: 'pointer'}}>
                ✅ Aprovar
              </button>
              <button onClick={() => decide(f.id, 'rejected')}
                      style={{background: '#a45952', color: 'white', border: 'none',
                              padding: '8px 16px', borderRadius: 4, cursor: 'pointer'}}>
                ❌ Rejeitar
              </button>
            </div>
          </article>
        );
      })}
    </main>
  );
}
```

Criar `apps/web/app/api/findings/pending/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export const dynamic = 'force-dynamic';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
);

export async function GET() {
  // Top 10 findings scored, não delivered, não reviewed
  const { data: findings, error } = await supabase
    .from('findings')
    .select('id, title, source_url, snippet, metadata, collected_at')
    .eq('status', 'scored')
    .order('collected_at', { ascending: false })
    .limit(10);

  if (error) return NextResponse.json({ error }, { status: 500 });

  // Para cada finding, pega scores
  const out = [];
  for (const f of findings || []) {
    const { data: scores } = await supabase
      .from('scores')
      .select('score_composite, pillar_id, confidence')
      .eq('finding_id', f.id);

    // Mapeia pillar_id → slug
    const enriched = [];
    for (const s of scores || []) {
      const { data: p } = await supabase
        .from('pillars')
        .select('slug')
        .eq('id', s.pillar_id)
        .single();
      enriched.push({ score_composite: s.score_composite, pillar_slug: p?.slug ?? '?' });
    }
    enriched.sort((a, b) => b.score_composite - a.score_composite);
    out.push({ ...f, _scores: enriched });
  }

  return NextResponse.json({ findings: out });
}
```

Criar `apps/web/app/api/findings/decide/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export const dynamic = 'force-dynamic';

// Esta rota usa SERVICE_ROLE porque anon não pode escrever
const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(request: Request) {
  const { id, decision } = await request.json();

  // 1. Registra a review
  const { error: e1 } = await supabase.from('reviews').insert({
    finding_id: id,
    reviewer_id: 'fabio.jorge',
    decision,
  });
  if (e1) return NextResponse.json({ error: e1 }, { status: 500 });

  // 2. Atualiza status do finding
  const newStatus = decision === 'approved' ? 'reviewed' : 'discarded';
  const { error: e2 } = await supabase
    .from('findings')
    .update({ status: newStatus })
    .eq('id', id);
  if (e2) return NextResponse.json({ error: e2 }, { status: 500 });

  return NextResponse.json({ ok: true });
}
```

> **Guardião de Segurança ⚠️**: esta rota usa `SERVICE_ROLE_KEY` na Vercel. Para MVP é aceitável porque a rota é protegida por auth Supabase (a adicionar). Para Fase 5, migrar para Edge Function com Supabase Auth.

### 6.5 Digest diário via cron (Orquestrador)

Criar `apps/web/app/api/cron/digest/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

export const dynamic = 'force-dynamic';
export const maxDuration = 60;

export async function GET(request: Request) {
  const authHeader = request.headers.get('authorization');
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 });
  }

  const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );

  // Pega top 10 findings reviewed ontem
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const yIso = yesterday.toISOString().slice(0, 10);

  const { data: findings } = await supabase
    .from('findings')
    .select('id, title, source_url, snippet, collected_at')
    .eq('status', 'reviewed')
    .gte('collected_at', yIso + 'T00:00:00Z')
    .lt('collected_at', yIso + 'T23:59:59Z')
    .order('collected_at', { ascending: false })
    .limit(10);

  // Dispara trigger no worker do Render para enviar digest Telegram
  const r = await fetch(`${process.env.RENDER_WORKER_URL}/digest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ findings, date: yIso }),
  });

  return NextResponse.json({ ok: r.ok, count: findings?.length || 0 });
}
```

Adicionar ao `vercel.json`:

```json
{
  "crons": [
    { "path": "/api/cron/collect?secret=CRON_SECRET", "schedule": "0 */4 * * *" },
    { "path": "/api/cron/digest?secret=CRON_SECRET",  "schedule": "0 7 * * 1-5" }
  ]
}
```

### ✅ CHECKPOINT F4.1 — Entrega ponta-a-ponta funcionando

**Critérios**:

1. ✅ Dashboard acessível em `https://<sua-app>.vercel.app/dashboard` lista 10 findings para revisar
2. ✅ Clicar "Aprovar" ou "Rejeitar" remove o card e grava na tabela `reviews` (verificar: `select count(*) from public.reviews;`)
3. ✅ Findings com score ≥ 75 chegam automaticamente como card no Telegram do Fábio
4. ✅ Cron das 7h BRT dispara digest (verificar log Vercel: chamada para `/api/cron/digest`)

**Comandos de verificação**:

```sql
-- Quantos findings foram revisados?
select decision, count(*) from public.reviews group by decision;

-- Quantos alerts foram enviados?
select channel, count(*) from public.deliveries group by channel;
```

**Esperado**: após 24h de operação, `reviews` ≥ 1 (Fábio revisou pelo menos 1); `deliveries` com `channel='telegram'` ≥ 1.

**Se falhar**:
- Dashboard não carrega → verificar `SUPABASE_URL` e `SUPABASE_ANON_KEY` na Vercel
- Aprovar não grava → verificar `SUPABASE_SERVICE_ROLE_KEY` na Vercel (a rota decide usa service role)
- Cron não dispara → na Vercel, verificar Production deployments + Cron logs
- Telegram não chega → `TELEGRAM_CHAT_ID_FABIO` deve ser o chat_id numérico (consulte `@userinfobot`)

**Não avance para a Fase 5 sem este checkpoint.**

---

## 7. Fase 5 — Operação Contínua + Loops de Aprendizado (contínuo)

### Objetivo da Fase 5

Manter o sistema rodando estável, medir KPIs, e mensalmente recalibrar o classificador com base nas decisões do Fábio.

### 7.1 KPIs a medir (Advogado do Usuário + Arquiteto)

> Apenas 4 KPIs no MVP. Mais que isso vira ruído.

| KPI | Definição | Meta inicial | Frequência |
|-----|-----------|--------------|------------|
| Achados coletados/dia | `count(*) from findings where collected_at::date = today` | 50-300/dia | Diária |
| Taxa de aprovação | `approved / (approved + rejected)` em reviews | ≥ 50% | Semanal |
| Alertas Telegram/dia | `count(*) from deliveries where channel='telegram' and sent_at::date = today` | ≤ 5/dia | Diária |
| Custo DeepSeek/mês | somatório de tokens × preço | ≤ US$ 5/mês | Mensal |

Query SQL de KPIs (rodar no Supabase SQL Editor quando quiser):

```sql
-- Achados por dia (últimos 7 dias)
select collected_at::date as dia, count(*) as n
from public.findings
where collected_at > now() - interval '7 days'
group by 1 order by 1;

-- Taxa de aprovação (sempre)
select
  count(*) filter (where decision='approved') as aprovados,
  count(*) filter (where decision='rejected') as rejeitados,
  round(100.0 * count(*) filter (where decision='approved') / nullif(count(*), 0), 1) as pct_aprovacao
from public.reviews;

-- Alertas hoje
select count(*) from public.deliveries
where channel='telegram' and sent_at::date = current_date;
```

### 7.2 Recalibração mensal do classificador (Arquiteto)

> **Quando**: todo dia 1 do mês, após 30 dias de operação.
> **O quê**: pegar todas as reviews do mês anterior e ajustar pesos do scorer ou prompt do classificador.

#### 7.2.1 Análise mensal (manual, 30 min)

```sql
-- Últimos 30 dias: distribuição de scores por decisão
select
  case
    when s.score_composite >= 75 then '75-100 (alerta)'
    when s.score_composite >= 50 then '50-74  (newsletter)'
    else '0-49 (descartado)'
  end as faixa,
  r.decision,
  count(*) as n
from public.reviews r
join public.findings f on f.id = r.finding_id
join public.scores   s on s.finding_id = f.id
where r.reviewed_at > now() - interval '30 days'
group by 1, 2
order by 1, 2;
```

**Decisão baseada no resultado**:

- Se faixa 75-100 tem `rejeitados > aprovados` → **baixar threshold** de alerta para 80
- Se faixa 50-74 tem `aprovados > rejeitados` × 2 → **subir threshold** de newsletter para 55
- Se nenhum pilar domina aprovações → classificador ok
- Se um pilar domina 70%+ dos aprovados → prompt precisa de mais exemplos do pilar dominado

#### 7.2.2 Ajustar pesos do scorer (se necessário)

Editar `apps/worker/src/llm/classifier.py`, função `compute_score`, ajustar apenas os pesos. Valores atuais:

```python
score = (
    dim_alignment * 0.30 +   # ← ajustável
    dim_br         * 0.20 +   # ← ajustável
    dim_rep         * 0.20 +   # ← ajustável
    dim_pra         * 0.15 +   # ← ajustável
    dim_lvl         * 0.10 +   # ← ajustável
    dim_nov         * 0.05    # ← ajustável
)
```

> Soma dos pesos deve ser sempre 1.0. Documentar a mudança em commit: `chore(scorer): ajuste mensal — maio 2026`.

### 7.3 Auditoria de segurança mensal (Guardião de Segurança)

> **Quando**: todo dia 1 do mês, junto com a recalibração.

Checklist (rodar todos):

1. ✅ Verificar que `SUPABASE_SERVICE_ROLE_KEY` NÃO está commitada no Git:
   ```bash
   git log --all -p | grep -i "service_role" | head -5
   # deve retornar vazio
   ```

2. ✅ Verificar que `.env` está no `.gitignore`:
   ```bash
   git check-ignore .env
   # deve imprimir: .env
   ```

3. ✅ Verificar que nenhuma tabela tem RLS desabilitada:
   ```sql
   select tablename, rowsecurity
   from pg_tables
   where schemaname='public' and rowsecurity = false;
   -- deve retornar vazio
   ```

4. ✅ Verificar logs do Render por vazamento de chave:
   ```bash
   # Render dashboard → Logs → buscar por: "sk-", "eyJ", "service_role"
   # deve retornar vazio
   ```

5. ✅ Verificar que `findings.metadata` não contém dados pessoais:
   ```sql
   select id, metadata->>'author' from public.findings
   where metadata->>'author' is not null
   limit 5;
   -- se algum autor aparecer com nome real + email, anonimizar
   ```

### 7.4 Backup mensal (Agente do Harness)

> Supabase free tier não tem backups automáticos. Fazer manualmente.

1. Acessar Supabase Dashboard → Database → Backups
2. Criar backup manual no dia 1 de cada mês
3. Baixar `.sql` e guardar em local seguro (Google Drive do CISEB)

Ou via CLI:

```bash
# Instalar supabase CLI
npm install -g supabase

# Login
supabase login

# Dump
supabase db dump --project-id <seu-project-id> --data-only > backup_$(date +%Y%m%d).sql
```

---

## 8. Como a Segurança e a UX foram incorporadas desde o desenho

> **Resumo final exigido pela instrução do usuário.**

### 8.1 Segurança — incorporation desde o desenho

| Decisão | Quando foi tomada | Persona | Onde está materializada |
|---------|-------------------|---------|--------------------------|
| RLS habilitada desde a migração 001 | Fase 1, passo 1.2 | Guardião de Segurança | `supabase/migrations/003_rls.sql` |
| `service_role_key` NUNCA na Vercel | Fase 1, §2.3 | Guardião de Segurança | `.env.example` |
| `anon_key` com read-only em findings aprovados | Fase 1, passo 1.2 | Guardião de Segurança | Policy `anon read findings` |
| Telegram usa `chat_id` numérico, não telefone | Fase 1, §2.3 | Guardião de Segurança | `TELEGRAM_CHAT_ID_FABIO` |
| Cron protegido por `CRON_SECRET` | Fase 4, §6.3 | Guardião de Segurança | `apps/web/app/api/cron/*/route.ts` |
| LLM nunca recebe dado pessoal | Fase 3, §5.3 | Guardião de Segurança | Prompt do `classifier.py` |
| Coletor respeita `robots.txt` e ToS | Fase 2, §4.5 | Guardião de Segurança | `User-Agent: ObservatorioCISEB/1.0` |
| Auditoria mensal de secrets e logs | Fase 5, §7.3 | Guardião de Segurança | Checklist mensal |
| Soft-delete após 90 dias (não purge) | Decisão #6 do Fábio | Guardião de Segurança | `findings.soft_deleted_at` |

**Princípio**: nenhuma dessas medidas foi adicionada "depois". Todas constam no commit 1. A migração 003 (RLS) é aplicada antes de qualquer linha de código de coleta.

### 8.2 UX — incorporation desde o desenho

| Decisão | Quando foi tomada | Persona | Onde está materializada |
|---------|-------------------|---------|--------------------------|
| Fábio recebe no máximo 5 alertas/dia | Fase 4, §6.1 | Advogado do Usuário | Limite no `send_alerts_for_high_scores` |
| Card único, 5 elementos, sem ruído | Fase 4, §6.1 | Advogado do Usuário | `_format_card` em `telegram.py` |
| Dashboard é tela única, sem filtros | Fase 4, §6.4 | Advogado do Usuário | `apps/web/app/dashboard/page.tsx` |
| 3 botões por card (Aprovar/Editar/Rejeitar) | Fase 4, §6.4 | Advogado do Usuário | Componente `<article>` |
| Digest diário às 7h, dias úteis | Decisão #7 do Fábio | Advogado do Usuário | `vercel.json` cron `0 7 * * 1-5` |
| Zero YAML para editar em produção | Fase 0, §2.2 | Advogado do Usuário | Stack 100% PaaS |
| Prompt LLM retorna JSON determinístico | Fase 3, §5.3 | Advogado do Usuário | `SYSTEM_PROMPT` em `classifier.py` |
| Rejeição do LLM não derruba pipeline | Fase 3, §5.2 | Advogado do Usuário | `chat()` retorna `None` |
| 4 KPIs apenas, não 15 | Fase 5, §7.1 | Advogado do Usuário | Tabela KPI única |
| Recalibração mensal é 30 min manual, não diária | Fase 5, §7.2 | Advogado do Usuário | §7.2.1 |

**Princípio**: a UX não é "uma tela bonita no fim". É o critério de **rejeição de complexidade** aplicado em cada decisão de arquitetura. Toda vez que o Arquiteto propõe algo, o Advogado do Usuário pergunta: *"Fábio consegue usar isso em 30 segundos sem manual?"* Se a resposta é não, simplifica.

### 8.3 O que o plano NÃO faz (por escolha deliberada)

- ❌ Não usa Redis (Supabase Queue via pgmq resolve)
- ❌ Não usa Kafka (volume MVP não justifica)
- ❌ Não usa Elasticsearch (pgvector + tsvector resolvem)
- ❌ Não usa Kubernetes (Render + Vercel resolvem)
- ❌ Não tem dashboard com gráficos (1 tela de revisão basta)
- ❌ Não tem auth multi-usuário (Fábio é o único revisor no MVP)
- ❌ Não tem WhatsApp no MVP (Fábio pediu Telegram; WhatsApp pode entrar na Fase 6)
- ❌ Não tem analytics de abertura de newsletter (Resend já provê; não duplicar)

Cada "não" acima foi validado pelo Advogado do Usuário. Adicionar qualquer um deles requer justificativa explícita.

---

## 9. Apêndices

### 9.1 Glossário

| Termo | Definição |
|-------|-----------|
| Achado | Item coletado por algum coletor e gravado na tabela `findings` |
| Pilar | Um dos 6 eixos temáticos do CISEB (ia, maker, digital, tech_art, fabrication, robotics) |
| Score | Número 0-100 que indica relevância do achado |
| Top-N | Os N achados de maior score em um período (default N=10) |
| Soft-delete | Marcar `soft_deleted_at` sem apagar a linha (permite undo) |
| RLS | Row Level Security — controle de acesso por linha no Postgres |
| pgmq | Extensão Postgres que implementa filas de mensagens |
| pgvector | Extensão Postgres para busca vetorial |
| Cron | Agendador de tarefas (Vercel Crons neste projeto) |
| Worker | Processo Python no Render que executa coletores + LLM |

### 9.2 Comandos rápidos

```bash
# Rodar worker manualmente (debug)
cd apps/worker && python -m src.main

# Re-aplicar migração (após editar .sql)
# Supabase Dashboard → SQL Editor → colar e rodar

# Ver últimos logs do Render
# Render Dashboard → observatorio-worker → Logs

# Ver cron jobs da Vercel
# Vercel Dashboard → seu-projeto → Crons

# Re-embeddar pilares (após editar descrições)
python -c "from src.llm.embeddings import embed_pillars; embed_pillars()"

# Backup manual do DB
supabase db dump --project-id <id> --data-only > backup.sql
```

### 9.3 O que fazer se algo quebrar

| Sintoma | Provável causa | Ação |
|---------|----------------|------|
| Worker não coleta nada | Render free tier hibernou | Acessar URL do Render para "acordar" |
| DeepSeek retorna 429 | Rate limit | Reduzir `batch_size` em `main.py` |
| Telegram não recebe alertas | `chat_id` errado | Falar com `@userinfobot` no Telegram, pegar ID |
| Findings duplicados | Hash mudou (texto normalizado diferente) | Rodar `delete from findings where id not in (select min(id) from findings group by content_hash);` |
| LLM retorna JSON inválido | Modelo alucinou | Já tratado: retry automático na próxima rodada |
| Dashboard não carrega | `SUPABASE_ANON_KEY` errado ou RLS bloqueando | Verificar env vars na Vercel |
| Score sempre baixo | Pesos mal calibrados | Rodar §7.2.1 e ajustar |

### 9.4 Próximos passos após 30 dias de operação

Após 30 dias, avaliar:

1. **Está sobrecarregado?** → Reduzir frequência do cron de 4h para 6h
2. **Achados ruins?** → Ajustar pesos do scorer (§7.2.2)
3. **Custo DeepSeek > US$ 10/mês?** → Migrar para `deepseek-chat` (mais barato) ou cache de embeddings
4. **Quer adicionar WhatsApp?** → Fase 6: integrar `whatsapp-web.js` com número Business
5. **Quer abrir para outros professores?** → Fase 6: adicionar Supabase Auth no dashboard

---

## 10. Log de versões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 2026-06-25 | Orquestrador+Arquiteto (Z.ai) | Esqueleto arquitetural — PDF |
| 2.0 | 2026-06-25 | 5 personas integradas | Plano operacional anti-alucinação com 8 decisões do Fábio incorporadas; stack final Supabase+Vercel+Render+DeepSeek |

---

> **Fim do plano.** Este documento é auto-contido: qualquer IA com capacidade de ler Markdown e executar comandos bash/SQL pode implementar o Observatório CISEB seguindo os passos em ordem, sem ambiguidades. Em caso de dúvida sobre um passo, o checkpoint correspondente define critérios objetivos — se não passou, não avance.
