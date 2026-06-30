-- =============================================================================
-- 001_init.sql — Schema inicial do Observatório CISEB
-- =============================================================================
-- Compatível com: Postgres 15 + pgvector + pgmq
-- Projeto Supabase criado com enable_automatic_rls: false
-- RLS será habilitada explicitamente na migração 003_rls.sql
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. EXTENSÕES
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pgmq";

-- ---------------------------------------------------------------------------
-- 2. TABELA: sources — Catálogo de fontes monitoradas
-- ---------------------------------------------------------------------------

CREATE TABLE sources (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    slug            text        NOT NULL UNIQUE,
    name            text        NOT NULL,
    family          text        NOT NULL CHECK (family IN (
                                    'web',
                                    'github',
                                    'forums',
                                    'social',
                                    'academic',
                                    'events'
                                )),
    config          jsonb       NOT NULL DEFAULT '{}',
    healthy         boolean     NOT NULL DEFAULT true,
    last_polled_at  timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 3. TABELA: pillars — Os 6 pilares CISEB
-- ---------------------------------------------------------------------------

CREATE TABLE pillars (
    id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    slug                text        NOT NULL UNIQUE,
    name                text        NOT NULL,
    description         text        NOT NULL,
    canonical_embedding vector(1024),           -- BGE-M3 = 1024 dimensões
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 4. TABELA: findings — Achados (tabela central do sistema)
-- ---------------------------------------------------------------------------

CREATE TABLE findings (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Origem do achado
    source_id       uuid        NOT NULL REFERENCES sources(id)
                                    ON DELETE CASCADE,
    source_url      text        NOT NULL,

    -- Conteúdo
    title           text        NOT NULL,
    content_text    text,
    snippet         text,
    language        text        DEFAULT 'pt',

    -- Deduplicação
    content_hash    text        NOT NULL UNIQUE,   -- SHA-256 hex

    -- Coleta
    collected_at    timestamptz NOT NULL DEFAULT now(),

    -- Embedding semântico (BGE-M3)
    embedding       vector(1024),

    -- Ciclo de vida
    status          text        NOT NULL DEFAULT 'new' CHECK (status IN (
                                    'new',
                                    'enriched',
                                    'scored',
                                    'reviewed',
                                    'delivered',
                                    'discarded'
                                )),

    -- Metadados flexíveis (idioma detectado, autor, tags automáticas etc.)
    metadata        jsonb       NOT NULL DEFAULT '{}',

    -- Soft-delete (Decisão #6 Fábio: nunca purge, apenas soft-delete 90d)
    soft_deleted_at timestamptz
);

-- ---------------------------------------------------------------------------
-- 5. ÍNDICES DA TABELA findings
-- ---------------------------------------------------------------------------

-- Busca por hash de conteúdo (deduplicação)
CREATE INDEX idx_findings_hash
    ON findings (content_hash);

-- Filtro por status (RLS e queries de dashboard)
CREATE INDEX idx_findings_status
    ON findings (status);

-- Ordenação cronológica (feeds, newsletters)
CREATE INDEX idx_findings_collected
    ON findings (collected_at DESC);

-- Busca vetorial por similaridade semântica (BGE-M3, 1024d)
-- IVFFlat com 100 listas: bom tradeoff speed/recall para ~100k vetores
CREATE INDEX idx_findings_embedding
    ON findings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ---------------------------------------------------------------------------
-- 6. TABELA: scores — 1:N com findings (um score por pilar)
-- ---------------------------------------------------------------------------

CREATE TABLE scores (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id      uuid        NOT NULL REFERENCES findings(id)
                                    ON DELETE CASCADE,
    pillar_id       uuid        NOT NULL REFERENCES pillars(id)
                                    ON DELETE CASCADE,

    -- Métricas do score
    confidence      real        NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    score_composite integer     NOT NULL CHECK (score_composite >= 0 AND score_composite <= 100),

    -- Dimensões do score (fórmula: alignment*0.30 + br_luso*0.20 + replicable*0.20
    --                       + practical*0.15 + level*0.10 + novelty*0.05)
    dim_alignment   integer     NOT NULL CHECK (dim_alignment >= 0 AND dim_alignment <= 100),
    dim_br_luso     integer     NOT NULL CHECK (dim_br_luso >= 0 AND dim_br_luso <= 100),
    dim_replicable  integer     NOT NULL CHECK (dim_replicable >= 0 AND dim_replicable <= 100),
    dim_practical   integer     NOT NULL CHECK (dim_practical >= 0 AND dim_practical <= 100),
    dim_level       integer     NOT NULL CHECK (dim_level >= 0 AND dim_level <= 100),
    dim_novelty     integer     NOT NULL CHECK (dim_novelty >= 0 AND dim_novelty <= 100),

    computed_at     timestamptz NOT NULL DEFAULT now(),

    -- Cada finding só pode ter UM score por pilar
    UNIQUE (finding_id, pillar_id)
);

-- ---------------------------------------------------------------------------
-- 7. TABELA: reviews — Decisão humana do curador (Fábio)
-- ---------------------------------------------------------------------------

CREATE TABLE reviews (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id      uuid        NOT NULL REFERENCES findings(id)
                                    ON DELETE CASCADE,
    reviewer_id     text        NOT NULL DEFAULT 'fabio.jorge',
    decision        text        NOT NULL CHECK (decision IN (
                                    'approved',
                                    'rejected',
                                    'edited'
                                )),
    edited_summary  text,
    feedback_tags   text[]      NOT NULL DEFAULT '{}',
    reviewed_at     timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 8. TABELA: deliveries — Auditoria de canais de entrega
-- ---------------------------------------------------------------------------

CREATE TABLE deliveries (
    id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id      uuid        NOT NULL REFERENCES findings(id)
                                    ON DELETE CASCADE,
    channel         text        NOT NULL CHECK (channel IN (
                                    'telegram',
                                    'newsletter',
                                    'dashboard'
                                )),
    sent_at         timestamptz NOT NULL DEFAULT now(),
    opened_at       timestamptz,
    payload         jsonb
);

-- =============================================================================
-- FIM 001_init.sql
-- =============================================================================
