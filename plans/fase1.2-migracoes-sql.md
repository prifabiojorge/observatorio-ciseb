# Plano de Migração SQL — Fase 1.2

## Status: ✅ VALIDADO — Aguardando implementação em Code mode

---

## Verificação de Conformidade

### Schema vs [`03_SCHEMA_BANCO.md`](../memoria/03_SCHEMA_BANCO.md:1)

| # | Tabela | Colunas | Constraints | Índices | Doc Match |
|---|--------|---------|-------------|---------|-----------|
| 1 | `sources` | 8 | PK uuid, UNIQUE slug, CHECK family (6 valores), NOT NULLs | — | ✅ |
| 2 | `pillars` | 5 + vector(1024) | PK uuid, UNIQUE slug, NOT NULLs | — | ✅ |
| 3 | `findings` | 15 + vector(1024) | PK uuid, FK→sources CASCADE, UNIQUE content_hash, CHECK status (6 valores), NOT NULLs | 4: hash, status, collected DESC, embedding IVFFlat(lists=100) | ✅ |
| 4 | `scores` | 11 | PK uuid, FK→findings CASCADE, FK→pillars CASCADE, 8 CHECKs (0..100 / 0..1), UNIQUE(finding_id,pillar_id) | — | ✅ |
| 5 | `reviews` | 6 | PK uuid, FK→findings CASCADE, CHECK decision (3 valores), NOT NULLs | — | ✅ |
| 6 | `deliveries` | 5 | PK uuid, FK→findings CASCADE, CHECK channel (3 valores), NOT NULLs | — | ✅ |

### RLS vs [`05_SEGURANCA_DESDE_DESENHO.md`](../memoria/05_SEGURANCA_DESDE_DESENHO.md:1)

| # | Regra | Decisão Doc | SQL Gerado |
|---|-------|-------------|------------|
| 1 | RLS explícita em todas as tabelas | ⚠️ Linha 15: `enable_automatic_rls: false` → habilitar manualmente | `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` ×6 |
| 2 | ANON lê sources/pillars | Linha 145 | `anon_read_sources`, `anon_read_pillars` — USING (true) |
| 3 | ANON lê findings aprovados | Linha 145 | `anon_read_findings` — USING (status IN ('reviewed','delivered')) |
| 4 | ANON lê scores (somente findings aprovados) | Linha 145 | `anon_read_scores` — EXISTS subquery com filtro de status |
| 5 | ANON bloqueado de reviews | Linha 146 | Sem policy SELECT = negado por padrão |
| 6 | ANON sem INSERT/UPDATE/DELETE | Linha 147 | Nenhuma policy de escrita |
| 7 | SERVICE_ROLE bypass | Linha 148 | Padrão Supabase (rolbypassrls=true) |

---

## Arquivos a Criar

| # | Arquivo | Propósito | Linhas |
|---|---------|-----------|--------|
| 1 | `supabase/migrations/001_init.sql` | Schema: 3 extensões + 6 tabelas + 4 índices | ~160 |
| 2 | `supabase/migrations/002_pgmq.sql` | Fila pgmq: 1 queue + função helper `enqueue_finding()` | ~55 |
| 3 | `supabase/migrations/003_rls.sql` | RLS: habilitação ×6 + 4 políticas ANON + verificação | ~95 |
| 4 | `supabase/migrations/seed.sql` | Seed idempotente: 6 pilares CISEB com ON CONFLICT | ~45 |

---

## Decisões de Design Registradas

1. **`enqueue_finding()` com SECURITY DEFINER** — Necessário porque o worker (service_role) precisa enfileirar após INSERT em findings, e a função precisa ignorar RLS.
2. **Seed com `ON CONFLICT (slug) DO NOTHING`** — Torna a seed idempotente; segura para re-execução.
3. **IVFFlat com lists=100** — Tradeoff documentado: bom para ~100k vetores; se o volume crescer para >1M, migrar para HNSW.
4. **Índice `idx_findings_collected` com DESC** — Otimiza queries de "últimos findings" sem re-sort.
5. **Zero políticas para `reviews` e `deliveries`** — O PostgreSQL nega acesso por padrão quando RLS está habilitada e não há policy. Isso é intencional e documentado.
6. **`soft_deleted_at` nullable** — null = ativo. A limpeza é feita por job agendado (não por trigger), conforme Decisão #6 do Fábio.

---

## Pontos de Atenção para Code Mode

- **Encoding**: UTF-8 sem BOM
- **Line endings**: LF (não CRLF — Supabase espera LF)
- **Ordem de execução**: 001 → 002 → 003 → seed (numérica)
- **Supabase CLI**: `supabase db push` ou `supabase migration up` aplica na ordem
- **Verificação pós-deploy**: executar checklist SQL do [`05_SEGURANCA_DESDE_DESENHO.md`](../memoria/05_SEGURANCA_DESDE_DESENHO.md:27)
