# Segurança Desde o Desenho
### Rastreabilidade completa · Observatório CISEB

---

> 🛡️ **Princípio**: Nenhuma medida de segurança foi adicionada "depois". 
> Todas constam no commit 1.

---

## Decisões de segurança materializadas no código

| # | Decisão | Quando definida | Persona | Onde materializada |
|---|---------|-----------------|---------|-------------------|
| 1 | RLS habilitada desde migração 001 | Fase 1, Passo 1.2 | Guardião | `supabase/migrations/003_rls.sql` | ⚠️ RLS automática desabilitada no provisionamento; habilitar manualmente |
| 2 | `service_role_key` NUNCA na Vercel | Fase 1, §2.3 | Guardião | `.env.example` |
| 3 | `anon_key` com read-only em findings aprovados | Fase 1, Passo 1.2 | Guardião | Policy `anon read findings` |
| 4 | Telegram usa `chat_id` numérico, não telefone | Fase 1, §2.3 | Guardião | `TELEGRAM_CHAT_ID_FABIO` |
| 5 | Cron protegido por `CRON_SECRET` | Fase 4, §6.3 | Guardião | `apps/web/app/api/cron/*/route.ts` |
| 6 | LLM nunca recebe dado pessoal | Fase 3, §5.3 | Guardião | Prompt do `classifier.py` |
| 7 | Coletor respeita `robots.txt` e ToS | Fase 2, §4.5 | Guardião | `User-Agent: ObservatorioCISEB/1.0` |
| 8 | Auditoria mensal de secrets e logs | Fase 5, §7.3 | Guardião | Checklist mensal |
| 9 | Soft-delete, nunca purge (90d) | Decisão #6 Fábio | Guardião | `findings.soft_deleted_at` |

---

## Checklist de auditoria mensal (dia 1 de cada mês)

```bash
# 1. service_role_key NÃO commitada
git log --all -p | grep -i "service_role" | head -5
# Esperado: vazio

# 2. .env no .gitignore
git check-ignore .env
# Esperado: imprime ".env"
```

```sql
-- 3. Nenhuma tabela com RLS desabilitada
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname='public' AND rowsecurity = false;
-- Esperado: vazio

-- 4. findings.metadata sem dados pessoais
SELECT id, metadata->>'author' FROM public.findings
WHERE metadata->>'author' IS NOT NULL
LIMIT 5;
-- Se contiver nome + email → anonimizar
```

```
5. Render Dashboard → Logs → buscar por: "sk-", "eyJ", "service_role"
   Esperado: vazio
```

---

## Separação de chaves por ambiente

| Chave | Vercel | Render |
|-------|--------|--------|
| `SUPABASE_URL` | ✅ | ✅ |
| `SUPABASE_ANON_KEY` | ✅ | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | ❌ NUNCA | ✅ |
| `DEEPSEEK_API_KEY` | ❌ | ✅ |
| `TELEGRAM_BOT_TOKEN` | ❌ | ✅ |
| `CRON_SECRET` | ✅ | ❌ |

> **⚠️ Exceção MVP**: A rota `/api/findings/decide` na Vercel usa `SERVICE_ROLE_KEY` para escrever reviews.
> Para Fase 5, migrar para Edge Function com Supabase Auth.

---

## Modelo de ameaças simplificado

| Ameaça | Probabilidade | Mitigação |
|--------|--------------|-----------|
| Vazamento de `anon_key` Vercel | Média | RLS garante que atacante só lê findings aprovados |
| Vazamento de `service_role_key` | Baixa | Isolada no Render; nunca commitada |
| LLM alucina dados pessoais | Baixa | Prompt instrui NÃO inventar; parser rejeita |
| Rate-limit de APIs (GitHub, Scholar) | Alta | Retry com backoff; fallback para outras fontes |
| Banimento por scraping | Média | User-Agent identificável; delay entre requests |

---

## Privacidade (LGPD)

- `reviews.reviewer_id` é o único campo com dado pessoal (nome do revisor)
- RLS bloqueia ANON de ler `reviews`
- `findings.metadata` pode conter nomes de autores de artigos públicos → aceitável
- Telefone do Fábio NUNCA aparece em logs → apenas `chat_id` numérico

---

> **Registrado em**: 2026-06-25
