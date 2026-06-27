-- =============================================================================
-- 004_rls_auth.sql — Row Level Security com Supabase Auth (Fase 5)
-- =============================================================================
-- SUBSTITUI a exceção MVP (SERVICE_ROLE_KEY na Vercel) por RLS real baseada
-- em auth.uid(). Apenas o Fábio (UUID configurado) pode ler findings scored
-- e inserir reviews.
--
-- ⚠️ ANTES DE APLICAR:
--   1. Criar conta do Fábio no Supabase Auth (Dashboard → Auth → Users → Add)
--   2. Copiar o auth.uid() retornado (UUID v4)
--   3. Substituir '<FABIO_AUTH_UID>' abaixo pelo UUID real
--   4. Aplicar esta migração
--   5. Remover SERVICE_ROLE_KEY da Vercel (Settings → Environment Variables)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Configuração: UUID do Fábio no Supabase Auth
-- ---------------------------------------------------------------------------
-- ⚠️ Substitua pelo UUID real do Fábio no Supabase Auth.
-- Para testar antes: SELECT auth.uid(); depois de logar.
-- Em produção, use uma variável ou tabela de config.
CREATE TABLE IF NOT EXISTS app_config (
    key text PRIMARY KEY,
    value text NOT NULL,
    updated_at timestamptz DEFAULT now()
);

-- Insere o UUID do Fábio (substituir pelo valor real)
INSERT INTO app_config (key, value) VALUES
    ('reviewer_auth_uid', '<FABIO_AUTH_UID>')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Habilita RLS em app_config (qualquer um pode ler a chave, mas só service_role pode escrever)
ALTER TABLE app_config ENABLE ROW LEVEL SECURITY;
CREATE POLICY "anon_read_app_config" ON app_config FOR SELECT TO anon USING (true);
CREATE POLICY "authenticated_read_app_config" ON app_config FOR SELECT TO authenticated USING (true);

-- ---------------------------------------------------------------------------
-- 2. Função utilitária: é o Fábio autenticado?
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION is_reviewer()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
    SELECT COALESCE(
        auth.uid()::text = (SELECT value FROM app_config WHERE key = 'reviewer_auth_uid'),
        false
    );
$$;

-- ---------------------------------------------------------------------------
-- 3. Políticas RLS para ANON (mantém as existentes + adiciona authenticated)
-- ---------------------------------------------------------------------------
-- ANON continua podendo ler apenas findings reviewed/delivered (catálogo público)

-- 3.1 Findings — ANON lê apenas aprovados; AUTHENTICATED (Fábio) lê scored também
DROP POLICY IF EXISTS "anon_read_findings" ON findings;
CREATE POLICY "anon_read_findings"
    ON findings FOR SELECT TO anon
    USING (status IN ('reviewed', 'delivered'));

CREATE POLICY "reviewer_read_findings"
    ON findings FOR SELECT TO authenticated
    USING (is_reviewer() AND status IN ('scored', 'reviewed', 'delivered', 'discarded'));

-- 3.2 Scores — ANON lê só de aprovados; AUTHENTICATED lê todos
DROP POLICY IF EXISTS "anon_read_scores" ON scores;
CREATE POLICY "anon_read_scores"
    ON scores FOR SELECT TO anon
    USING (
        EXISTS (
            SELECT 1 FROM findings f
            WHERE f.id = scores.finding_id
              AND f.status IN ('reviewed', 'delivered')
        )
    );

CREATE POLICY "reviewer_read_scores"
    ON scores FOR SELECT TO authenticated
    USING (is_reviewer());

-- 3.3 Reviews — apenas AUTHENTICATED (Fábio) pode ler e escrever
CREATE POLICY "reviewer_read_reviews"
    ON reviews FOR SELECT TO authenticated
    USING (is_reviewer());

CREATE POLICY "reviewer_insert_reviews"
    ON reviews FOR INSERT TO authenticated
    WITH CHECK (is_reviewer());

-- 3.4 Findings UPDATE — apenas AUTHENTICATED pode mudar status (approve/reject)
CREATE POLICY "reviewer_update_findings_status"
    ON findings FOR UPDATE TO authenticated
    USING (is_reviewer())
    WITH CHECK (is_reviewer());

-- 3.5 Deliveries — AUTHENTICATED pode ler (auditoria) e inserir (envio de alertas)
CREATE POLICY "reviewer_read_deliveries"
    ON deliveries FOR SELECT TO authenticated
    USING (is_reviewer());

CREATE POLICY "reviewer_insert_deliveries"
    ON deliveries FOR INSERT TO authenticated
    WITH CHECK (is_reviewer());

-- ---------------------------------------------------------------------------
-- 4. Sources e Pillars — permanecem públicos (catálogo)
--    (políticas existentes em 003_rls.sql já cobrem ANON)
-- ---------------------------------------------------------------------------
-- Adiciona leitura para authenticated também (herdam de anon por padrão,
-- mas explicitar é boa prática)
CREATE POLICY "authenticated_read_sources"
    ON sources FOR SELECT TO authenticated USING (true);

CREATE POLICY "authenticated_read_pillars"
    ON pillars FOR SELECT TO authenticated USING (true);

-- =============================================================================
-- VERIFICAÇÃO PÓS-MIGRAÇÃO
-- =============================================================================
-- 1. Políticas por role:
--    SELECT tablename, policyname, roles, cmd
--    FROM pg_policies
--    WHERE schemaname = 'public'
--    ORDER BY tablename, policyname;
--
-- 2. Teste como ANON (deve falhar em scored):
--    SET ROLE anon;
--    SELECT count(*) FROM findings WHERE status = 'scored';
--    -- Esperado: ERROR ou 0 (RLS bloqueia)
--
-- 3. Teste como Fábio autenticado (deve funcionar):
--    -- Conectar via Supabase client com sessão do Fábio
--    -- SELECT count(*) FROM findings WHERE status = 'scored';
--    -- Esperado: N > 0
-- =============================================================================
-- FIM 004_rls_auth.sql
-- =============================================================================
