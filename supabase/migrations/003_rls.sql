-- =============================================================================
-- 003_rls.sql — Row Level Security
-- =============================================================================
-- ⚠️  CRÍTICO: O projeto Supabase foi criado com enable_automatic_rls: false.
--     Portanto, RLS DEVE ser explicitamente habilitada em CADA tabela.
--     Nenhuma tabela pública pode ficar sem RLS.
-- =============================================================================
-- POLÍTICA GERAL:
--   ANON (anon key)     → somente leitura de dados públicos/aprovados
--   SERVICE_ROLE        → acesso total (bypass RLS — padrão Supabase)
--   ANON NUNCA escreve  → sem policies INSERT/UPDATE/DELETE para anon
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. HABILITAR RLS EM TODAS AS TABELAS
-- ---------------------------------------------------------------------------

ALTER TABLE sources    ENABLE ROW LEVEL SECURITY;
ALTER TABLE pillars    ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings   ENABLE ROW LEVEL SECURITY;
ALTER TABLE scores     ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews    ENABLE ROW LEVEL SECURITY;
ALTER TABLE deliveries ENABLE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 2. POLÍTICAS ANON — LEITURA (SELECT)
-- ---------------------------------------------------------------------------

-- 2.1 Fontes: catálogo público — qualquer visitante pode ver quais fontes
--     o observatório monitora
CREATE POLICY "anon_read_sources"
    ON sources
    FOR SELECT
    TO anon
    USING (true);

-- 2.2 Pilares: catálogo público — os 6 pilares e suas descrições são
--     informação pública do projeto CISEB
CREATE POLICY "anon_read_pillars"
    ON pillars
    FOR SELECT
    TO anon
    USING (true);

-- 2.3 Findings: SOMENTE aprovados ('reviewed') ou já entregues ('delivered')
--     Findings em 'new', 'enriched', 'scored', 'discarded' são internos
--     e NÃO devem ser expostos ao público
CREATE POLICY "anon_read_findings"
    ON findings
    FOR SELECT
    TO anon
    USING (status IN ('reviewed', 'delivered'));

-- 2.4 Scores: somente de findings aprovados
--     Usa subquery EXISTS para garantir que scores de findings não revisados
--     não vazem. Um score sem finding aprovado é invisível para ANON.
CREATE POLICY "anon_read_scores"
    ON scores
    FOR SELECT
    TO anon
    USING (
        EXISTS (
            SELECT 1 FROM findings f
            WHERE f.id = scores.finding_id
              AND f.status IN ('reviewed', 'delivered')
        )
    );

-- ---------------------------------------------------------------------------
-- 3. POLÍTICAS ANON — BLOQUEIO IMPLÍCITO (sem policy = negado)
-- ---------------------------------------------------------------------------

-- ANON NÃO pode ler reviews (contém reviewer_id — dado pessoal, LGPD)
-- ANON NÃO pode ler deliveries (contém payload com metadados internos)
-- ANON NÃO tem INSERT/UPDATE/DELETE em nenhuma tabela
--
-- O PostgreSQL, com RLS habilitada, nega por padrão qualquer operação
-- que não tenha uma policy correspondente. Portanto, a ausência de
-- policies para INSERT/UPDATE/DELETE + a ausência de policy SELECT
-- em reviews/deliveries garante o bloqueio total para o role anon.

-- ---------------------------------------------------------------------------
-- 4. SERVICE_ROLE — ACESSO TOTAL
-- ---------------------------------------------------------------------------

-- O Supabase concede automaticamente bypass de RLS para o role service_role.
-- Nenhuma policy adicional é necessária.
-- A service_role_key NUNCA é exposta na Vercel (apenas no Render).
--
-- Verificação:
--   SELECT rolname, rolsuper, rolbypassrls
--   FROM pg_roles
--   WHERE rolname = 'service_role';
--   -- Esperado: rolsuper=false, rolbypassrls=true

-- =============================================================================
-- VERIFICAÇÃO PÓS-MIGRAÇÃO (CHECKLIST DE AUDITORIA)
-- =============================================================================
-- Execute após aplicar a migração para validar:
--
--   -- Nenhuma tabela pública com RLS desabilitada:
--   SELECT tablename, rowsecurity
--   FROM pg_tables
--   WHERE schemaname = 'public' AND rowsecurity = false;
--   -- Esperado: 0 linhas
--
--   -- Políticas criadas para o role anon:
--   SELECT tablename, policyname, cmd, qual
--   FROM pg_policies
--   WHERE schemaname = 'public' AND roles @> ARRAY['anon']::name[];
--   -- Esperado: 4 políticas (sources, pillars, findings, scores)
--
-- =============================================================================
-- FIM 003_rls.sql
-- =============================================================================
