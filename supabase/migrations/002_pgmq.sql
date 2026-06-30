-- =============================================================================
-- 002_pgmq.sql — Fila nativa de processamento (pgmq)
-- =============================================================================
-- pgmq é a fila nativa do Supabase/Postgres. NÃO usa Redis.
-- Workers no Render consomem desta fila via polling (pgmq.read).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. CRIAÇÃO DA QUEUE PRINCIPAL
-- ---------------------------------------------------------------------------

-- Queue para processamento assíncrono de findings:
--   new → enfileirar → worker coleta → enrich → score → review → deliver
SELECT pgmq.create('findings_queue');

-- ---------------------------------------------------------------------------
-- 2. FUNÇÃO HELPER: enfileirar um finding recém-coletado
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION enqueue_finding(finding_id uuid)
RETURNS void AS $$
BEGIN
    PERFORM pgmq.send('findings_queue', jsonb_build_object(
        'finding_id', finding_id,
        'action',     'process',
        'queued_at',  now()
    ));
END;
$$ LANGUAGE plpgsql
   SECURITY DEFINER;
-- SECURITY DEFINER é necessário para que o worker (service_role) possa
-- enfileirar mesmo com RLS habilitada nas tabelas. A função executa com
-- os privilégios do owner (postgres), não do caller.

-- ---------------------------------------------------------------------------
-- 3. COMENTÁRIOS DE USO (referência para o worker Python)
-- ---------------------------------------------------------------------------

-- Enfileirar um finding:
--   SELECT enqueue_finding('uuid-do-finding');
--
-- Consumir (worker Python no Render):
--   SELECT * FROM pgmq.read('findings_queue', vt => 60, qty => 5);
--   -- vt = visibility timeout (segundos) — se o worker morrer, a msg
--   --     volta para a fila após vt segundos
--   -- qty = batch size
--
-- Confirmar processamento (ACK):
--   SELECT pgmq.delete('findings_queue', msg_id);
--
-- Arquivar mensagens processadas (mantém audit trail):
--   SELECT pgmq.archive('findings_queue', msg_id);

-- =============================================================================
-- FIM 002_pgmq.sql
-- =============================================================================
