# Patch Consolidado — Segurança Crítica (F4) + Fase 5 (Testes, Auth, Cron)

**Branch**: `fix/seguranca-critica-f4`
**Commits**: `819da65` (F4) + `bdb2e54` (Fase 5)
**Data**: 2026-06-27
**Auditado por**: Agente do Harness (ciclo de 5 personas)
**Arquivo**: `0001-fase-5-seguranca-testes-auth-cron.patch`

---

## Resumo executivo

Este patch consolidado entrega:

1. **3 correções críticas de segurança da Fase 4** (item #1, #2, #4)
2. **Fase 5 completa** com 3 frentes priorizadas:
   - #8 — Testes automatizados (pytest + jest)
   - Supabase Auth real para o dashboard
   - #5 — GitHub Actions cron para restaurar automação de coleta

**Resultado**: 40/40 testes pytest passando · 8 arquivos novos · 11 arquivos modificados · ~1700 linhas adicionadas.

---

## Parte 1 — Correções críticas F4 (commit `819da65`)

| # | Vulnerabilidade | Solução |
|---|-----------------|---------|
| 1 | `CRON_SECRET` com fallback hardcoded | Fail-closed + `hmac.compare_digest` |
| 2 | Rotas `/api/findings/*` sem auth | `Bearer CRON_SECRET` + validação UUID v4 |
| 4 | Alerta Telegram com score errado | Usa `score_composite` real, não `confidence*100` |

---

## Parte 2 — Fase 5 (commit `bdb2e54`)

### #8 — Testes automatizados

**Worker (Python)** — 40 testes em 3 arquivos:
- `tests/test_hashing.py` (9 testes): SHA-256, dedup, TypeError
- `tests/test_verify_cron.py` (11 testes): fail-closed, timing-safe, integração
- `tests/test_classifier.py` (20 testes): compute_score, novelty_score, enrich parser
  - Documenta **bug conhecido**: `dim_alignment` não é truncado individualmente
- `pytest.ini` com `asyncio_mode = auto`

**Web (TypeScript)** — 15 testes jest:
- `__tests__/api-auth.test.ts`: 401 sem auth, 400 UUID inválido, fail-closed

**CI expandido** (`.github/workflows/ci.yml`):
- 3 jobs paralelos: `lint-python`, `test-python`, `lint-web`
- Cache de pip, instalação de `.[dev]`, rodar pytest com env vars mínimas

### Supabase Auth — auth real no dashboard

| Arquivo | Função |
|---------|--------|
| `apps/web/middleware.ts` | Protege `/dashboard` e `/api/findings/*` (401/redirect) |
| `apps/web/lib/supabase-browser.ts` | Cliente client-side (ANON_KEY) |
| `apps/web/lib/supabase-server.ts` | Cliente server-side com cookies httpOnly |
| `apps/web/app/login/page.tsx` | Magic link + OAuth Google |
| `apps/web/app/auth/callback/route.ts` | Troca code por sessão |
| `apps/web/app/dashboard/page.tsx` | Cookies (sem token), botão logout, badges com pillar_id |
| `apps/web/app/api/findings/pending/route.ts` | Usa `createServerClientFromCookies` (sem SERVICE_ROLE_KEY) |
| `apps/web/app/api/findings/decide/route.ts` | `reviewer_id` de `auth.uid()` (não hardcoded) |

**Migração RLS** (`supabase/migrations/004_rls_auth.sql`):
- Função `is_reviewer()` — `auth.uid() == app_config.reviewer_auth_uid`
- Policies `authenticated` para findings, scores, reviews, deliveries
- ANON mantém read-only em findings `reviewed`/`delivered` (catálogo público)
- AUTHENTICATED (Fábio) pode ler `scored` e escrever reviews

### #5 — GitHub Actions cron

**`.github/workflows/cron-coleta.yml`**:
- Agenda: 3x/dia às 09:00, 13:00, 17:00 BRT (12, 16, 20 UTC)
- Wake-up ping ao Render (mitiga cold start Free tier)
- Sleep 30s → dispara `/api/cron/collect` na Vercel
- Notifica Fábio via Telegram em caso de falha
- Substitui cron da Vercel (removido por limite Hobby tier: 1 cron/dia)

---

## Como aplicar

### Opção A — `git am` (recomendado, preserva commits)

```bash
cd /caminho/do/observatorio-ciseb
git checkout main
git pull origin main
git am < /home/z/my-project/download/0001-fase-5-seguranca-testes-auth-cron.patch
git log --oneline -3
# Deve mostrar: bdb2e54 (Fase 5), 819da65 (F4), e o HEAD anterior
```

### Opção B — Branch pronta (clone local)

```bash
cd /home/z/my-project/observatorio-ciseb
git checkout fix/seguranca-critica-f4
git log --oneline -3
```

---

## ⚠️ Passos OBRIGATÓRIOS antes do deploy

### 1. Variáveis de ambiente (Vercel + Render)

**Render** (Environment):
| Variável | Valor |
|----------|-------|
| `CRON_SECRET` | `openssl rand -hex 32` |

**Vercel** (Settings → Environment Variables):
| Variável | Ambiente | Valor |
|----------|----------|-------|
| `CRON_SECRET` | Production | (mesmo do Render) |
| `RENDER_RUN_URL` | Production | `https://<seu-app>.onrender.com/run` |
| `RENDER_DIGEST_URL` | Production | `https://<seu-app>.onrender.com/digest` |
| `NEXT_PUBLIC_SUPABASE_URL` | Production | `https://<ref>.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Production | `eyJ...` |
| ~~`SUPABASE_SERVICE_ROLE_KEY`~~ | ~~Production~~ | **REMOVER** (Fase 5 usa RLS) |

### 2. GitHub Secrets (para cron de coleta)

**GitHub repo → Settings → Secrets and variables → Actions**:
| Secret | Valor |
|--------|-------|
| `VERCEL_CRON_URL` | `https://observatorio-ciseb.vercel.app/api/cron/collect` |
| `CRON_SECRET` | (mesmo valor do Render/Vercel) |
| `RENDER_HEALTH_URL` | `https://<seu-app>.onrender.com/health` |
| `TELEGRAM_BOT_TOKEN` | (token do bot, opcional p/ notif. falha) |
| `TELEGRAM_CHAT_ID` | (chat_id do Fábio, opcional) |

### 3. Supabase — configurar Auth + RLS

1. **Criar conta do Fábio**: Dashboard Supabase → Auth → Users → Add user
   - Email do Fábio, magic link ou OAuth Google
   - Copiar o `auth.uid()` (UUID v4) retornado
2. **Aplicar migração**: SQL Editor → executar `004_rls_auth.sql`
   - ⚠️ Substituir `<FABIO_AUTH_UID>` pelo UUID real antes de executar
3. **Configurar redirect URLs** em Auth → URL Configuration:
   - Site URL: `https://observatorio-ciseb.vercel.app`
   - Redirect URLs: `https://observatorio-ciseb.vercel.app/auth/callback`

### 4. Deploy

1. **Render**: redeploy manual após configurar `CRON_SECRET`
2. **Vercel**: push para `main` dispara deploy automático
3. **GitHub Actions**: habilitar workflow `cron-coleta.yml` (Settings → Actions)

---

## Validação pós-deploy

### F4 — segurança

```bash
# Render — sem auth deve retornar 401
curl -i -X POST https://<seu-app>.onrender.com/run
# Esperado: 401

# Render — com auth correta deve retornar 200
curl -i -X POST -H "Authorization: Bearer <CRON_SECRET>" https://<seu-app>.onrender.com/run
# Esperado: 200
```

### Fase 5 — auth real

```bash
# Dashboard sem sessão deve redirecionar para /login
curl -i https://observatorio-ciseb.vercel.app/dashboard
# Esperado: 307 redirect para /login?redirect=/dashboard

# API sem sessão deve retornar 401
curl -i https://observatorio-ciseb.vercel.app/api/findings/pending
# Esperado: 401

# Após login (magic link), cookies de sessão são setados e:
curl -i -b cookies.txt https://observatorio-ciseb.vercel.app/api/findings/pending
# Esperado: 200 + array de findings (se for o Fábio)
```

### Fase 5 — testes

```bash
# Worker (local)
cd apps/worker && PYTHONPATH=src python -m pytest tests/ -v

# Web (local)
cd apps/web && npm install && npm test
```

### Fase 5 — cron GitHub Actions

```bash
# Disparar manualmente para testar
# GitHub repo → Actions → "Cron Coleta Observatório" → Run workflow
# Verificar logs: deve mostrar "Wake-up", "Sleep 30s", "HTTP 200"
```

---

## O que NÃO foi feito (dívida técnica restante)

| # | Item | Severidade |
|---|------|------------|
| 3 | Sanitizar histórico git + novo bot Telegram | ⚠️ Cancelado pelo usuário |
| 6 | Filtrar digest por faixa 50–74 + excluir discarded | 🟠 Alta |
| 9 | `embed_text` fail-loud em vez de vetor zero | 🟡 Média |
| 10 | Reavaliar `dim_br_luso` binário (escala 0/30/70/100) | 🟡 Média |
| 11 | Wake-up ping já no GitHub Actions cron (parcial) | ✅ Feito |
| 12 | Sentry / logging estruturado (substituir `print()`) | 🟡 Média |
| — | Bug: `dim_alignment` não truncado individualmente | 🟡 Média (documentado em teste) |
| — | JOIN com `pillars` no dashboard para mostrar slug em vez de UUID | 🟡 Baixa |

---

## Rastreabilidade

- **Auditoria original**: 2026-06-27 (Agente do Harness, ciclo de 5 personas)
- **Branch**: `fix/seguranca-critica-f4`
- **Commits**: `819da65` (F4) + `bdb2e54` (Fase 5)
- **Patch**: `0001-fase-5-seguranca-testes-auth-cron.patch`
- **Ciclo de personas**: 
  - Arquiteto: design do middleware + RLS + cron
  - Guardião: fail-closed, timing-safe, RLS com `auth.uid()`
  - Orquestrador: ordem de deploy (env vars → migration → deploy)
  - Advogado do Usuário: magic link (UX sem senha), botão logout
  - Harness: 40 testes + validação TestClient + CI
