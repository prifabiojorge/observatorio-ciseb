# Mapa de Fases e Checkpoints
### Roadmap executável · Observatório CISEB

---

## Visão geral das fases

```
┌────────────────────────────────────────────────────────────────┐
│  Fase 1 (3d) → Fase 2 (5d) → Fase 3 (7d) → Fase 4 (5d) → 5  │
│  Bootstrap     Coleta Real    LLM+Score      Entrega     Loop  │
└────────────────────────────────────────────────────────────────┘
```

---

## Fase 0 — Pré-requisitos (ANTES de tudo)

### ✅ CHECKPOINT F0.1

6 perguntas, todas devem ser "sim":

1. ✅ Conta GitHub com repositório criado?
2. ✅ Conta Supabase com projeto em East US (Ohio)?  ← aceito, região ajustada
3. ✅ Conta Vercel conectada ao GitHub?
4. ✅ Conta Render conectada ao GitHub?
5. ✅ Conta DeepSeek com US$ 5 de crédito?
6. ✅ Bot Telegram via @BotFather com token + chat_id?

**Status**: `[x] COMPLETO — 6/6 contas verificadas em 2026-06-25`

---

## Fase 1 — Bootstrap (3 dias) ✅ CONCLUÍDA

**Objetivo**: Hello world ponta-a-ponta. 1 coletor HTTP → grava 1 linha no Supabase → dispara 1 msg Telegram.

### Passos

| # | Passo | Persona | Arquivos |
|---|-------|---------|----------|
| 1.1 | Criar monorepo e estrutura | Orquestrador | Diretórios + `.gitignore` |
| 1.2 | Migração inicial Supabase | Arquiteto | `001_init.sql`, `002_pgmq.sql`, `003_rls.sql`, `seed.sql` |
| 1.3 | Aplicar migrações no Supabase | Harness | SQL Editor |
| 1.4 | Hello world: coletor → DB → Telegram | Harness | `supabase.py`, `telegram.py`, `main.py` |
| 1.5 | Deploy worker no Render | Harness | `render.yaml` |

### ✅ CHECKPOINT F1.1

1. Render status `Live` sem erros
2. `findings` tem ≥ 1 linha
3. Fábio recebeu msg Telegram "pipeline vivo"

**Status**: `[x] COMPLETO — Pipeline vivo (3/3 critérios atendidos em 2026-06-26)`

---

## Fase 2 — Coleta Real (5 dias) ✅ CONCLUÍDA

**Objetivo**: 6 coletores reais. Sem LLM. Apenas coleta + armazenamento.

### Passos

| # | Passo | Arquivos |
|---|-------|----------|
| 4.2 | Utilitários (hashing, text) | `hashing.py`, `text.py` |
| 4.3 | Coletor base (ABC) | `base.py` |
| 4.4 | Coletor RSS/Web | `web_rss.py` |
| 4.5 | Coletor GitHub | `github.py` |
| 4.6 | Coletor YouTube | `youtube.py` |
| 4.7 | Coletores Scholar, Reddit, Events | `scholar.py`, `forums.py`, `events.py` |
| 4.8 | Orquestrador dos coletores | `main.py` (substitui hello world) |

### ✅ CHECKPOINT F2.1

1. `python -m src.main` sem exceções
2. `findings` ≥ 50 linhas
3. Pelo menos 4 famílias com ≥ 5 achados
4. 0 duplicatas

**Status**: `[x] COMPLETO — 123 findings, 4 famílias ≥5 (web, github, academic, events)`

---

## Fase 3 — Classificação + Scoring + Embeddings (7 dias) ✅ CONCLUÍDA

**Objetivo**: LLM enriquece findings: resumo + classificação em pilares + score 0-100.

### Passos

| # | Passo | Arquivos |
|---|-------|----------|
| 5.1 | Embeddings dos 6 pilares | `embeddings.py` |
| 5.2 | Cliente DeepSeek | `deepseek.py` |
| 5.3 | Classificador multi-rótulo | `classifier.py` |
| 5.4 | Pipeline de processamento | `main.py` (completo) |

### ✅ CHECKPOINT F3.1

1. `findings` com `status='scored'` ≥ 20
2. `scores` tem ≥ 20 linhas
3. Todos pilares com `canonical_embedding` preenchido
4. Custo DeepSeek: ~US$ 0,01/rodada

**Status**: `[x] COMPLETO — 30 findings scored, 6 embeddings, scores populados, custo ~US$0.015`

---

## Fase 4 — Entrega + Revisão Humana (5 dias) ✅ CONCLUÍDA

**Objetivo**: Alertas Telegram (score ≥ 75). Digest diário 7h BRT. Interface web de revisão.

### Passos

| # | Passo | Arquivos |
|---|-------|----------|
| 6.1 | Alertas Telegram (cards) | `telegram.py` (refactored) |
| 6.2 | Worker com alertas integrados | `main.py` |
| 6.3 | Cron na Vercel | `route.ts` (collect), `vercel.json` |
| 6.4 | Interface de revisão web | `dashboard/page.tsx`, `pending/route.ts`, `decide/route.ts` |
| 6.5 | Digest diário via cron | `digest/route.ts` |

### ✅ CHECKPOINT F4.1

1. Dashboard lista 10 findings para revisar
2. Aprovar/Rejeitar grava em `reviews`
3. Score ≥ 75 chega no Telegram
4. Cron 7h BRT dispara digest

**Status**: `[x] COMPLETO — Dashboard live, Aprovar/Rejeitar funcional, 5 alertas Telegram, cron digest configurado`

---

## Fase 5 — Operação Contínua + Loops de Aprendizado ✅ CONCLUÍDA

**Objetivo**: KPIs, recalibração mensal, auditoria de segurança, backup.

### KPIs (apenas 4)

| KPI | Meta |
|-----|------|
| Achados/dia | 50–300 |
| Taxa aprovação | ≥ 50% |
| Alertas Telegram/dia | ≤ 5 |
| Custo DeepSeek/mês | ≤ US$ 5 |

### Cadência mensal

- Dia 1: análise de reviews → ajustar pesos do scorer
- Dia 1: auditoria de segurança (checklist 5 itens)
- Dia 1: backup manual do Supabase

**Status**: `[x] CONCLUÍDA — Deploy Vercel + Render em produção. Login, dashboard, auth, cron, 40 testes, segurança.`

---

## Fase 6 — Correções pós-auditoria Harness ✅ CONCLUÍDA

**Objetivo**: Corrigir 3 regressões sutis introduzidas nos commits "fix type error" da Fase 5 + 4 gaps da FASE 7 do Plano original.

### Correções aplicadas

| # | Item | Severidade | Arquivo |
|---|------|------------|---------|
| R3 | `console.error` sempre (não só em dev) em decide/route.ts | 🟠 Alta | `apps/web/app/api/findings/decide/route.ts` |
| R2 | Log `[FATAL]` quando `CRON_SECRET` ausente | 🟡 Média | `apps/web/app/api/cron/collect+digest/route.ts` |
| R1 | Comentários explicam trade-off fail-closed runtime vs build-time | 🟡 Média | `apps/web/app/api/cron/collect+digest/route.ts` |
| 7.1 | Bug `dim_alignment` não truncado individualmente | 🟡 Média | `apps/worker/src/llm/classifier.py` |
| 7.2 | Rate limiting `asyncio.sleep(5)` no scholar.py | 🟡 Média | `apps/worker/src/collectors/scholar.py` |
| 7.3 | Retry para findings `new` stale (>1h) | 🟡 Média | `apps/worker/src/main.py` |
| 7.4 | Substituir `print()` por `logging` estruturado | 🟡 Média | `apps/worker/src/main.py` |

### ✅ CHECKPOINT F6.1 + F6.2

**Critério objetivo**:
1. `grep -c "NODE_ENV === 'development'" apps/web/app/api/findings/decide/route.ts` = 0
2. `grep -c "FATAL" apps/web/app/api/cron/collect/route.ts` ≥ 1
3. `grep "max(0, min(100" apps/worker/src/llm/classifier.py` retorna linha com `dim_alignment`
4. `grep "asyncio.sleep(5)" apps/worker/src/collectors/scholar.py` retorna linha
5. `grep "stale_threshold" apps/worker/src/main.py` retorna linha
6. `grep -c "print(" apps/worker/src/main.py` = 0
7. `grep -c "log\." apps/worker/src/main.py` ≥ 30
8. `PYTHONPATH=src python -m pytest tests/ -q` → 40 passed

**Status**: `[x] COMPLETO — 40/40 testes passando após todas as correções. Auditoria Harness externa endereçada.`

---

## Regra de ouro

> **Se o checkpoint falhar, NÃO AVANCE.** Volte, corrija, re-rode.

---

> **Registrado em**: 2026-06-25 | **Última atualização**: 2026-06-27T16:10:00-03:00
