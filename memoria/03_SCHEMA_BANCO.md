# Schema do Banco de Dados
### Contratos das 6 tabelas · Observatório CISEB

---

## Visão geral

```
sources ──────────── findings ──────────── scores
                        │                    │
                        │                    └── pillars
                        ├── reviews
                        └── deliveries
```

6 tabelas. Postgres 15 + pgvector + pgmq. RLS desde o commit 1.

---

## Tabela: `sources` — Catálogo de fontes monitoradas

| Coluna | Tipo | Constraints |
|--------|------|------------|
| `id` | uuid PK | `default gen_random_uuid()` |
| `slug` | text | NOT NULL, UNIQUE |
| `name` | text | NOT NULL |
| `family` | text | NOT NULL, CHECK in ('web','github','forums','social','academic','events') |
| `config` | jsonb | NOT NULL, default '{}' |
| `healthy` | boolean | NOT NULL, default true |
| `last_polled_at` | timestamptz | nullable |
| `created_at` | timestamptz | NOT NULL, default now() |

---

## Tabela: `pillars` — Os 6 pilares CISEB

| Coluna | Tipo | Constraints |
|--------|------|------------|
| `id` | uuid PK | `default gen_random_uuid()` |
| `slug` | text | NOT NULL, UNIQUE |
| `name` | text | NOT NULL |
| `description` | text | NOT NULL |
| `canonical_embedding` | vector(1024) | BGE-M3 = 1024 dims |
| `created_at` | timestamptz | NOT NULL, default now() |

**Seed (6 pilares)**: `ia`, `maker`, `digital`, `tech_art`, `fabrication`, `robotics`

---

## Tabela: `findings` — Achados (tabela central)

| Coluna | Tipo | Constraints |
|--------|------|------------|
| `id` | uuid PK | `default gen_random_uuid()` |
| `source_id` | uuid FK → sources | NOT NULL, CASCADE |
| `source_url` | text | NOT NULL |
| `title` | text | NOT NULL |
| `content_text` | text | nullable |
| `snippet` | text | nullable |
| `language` | text | default 'pt' |
| `content_hash` | text | NOT NULL, UNIQUE (SHA-256 hex) |
| `collected_at` | timestamptz | NOT NULL, default now() |
| `embedding` | vector(1024) | nullable |
| `status` | text | NOT NULL, default 'new', CHECK in ('new','enriched','scored','reviewed','delivered','discarded') |
| `metadata` | jsonb | NOT NULL, default '{}' |
| `soft_deleted_at` | timestamptz | null = ativo |

**Índices**:
- `idx_findings_hash` — content_hash
- `idx_findings_status` — status
- `idx_findings_collected` — collected_at DESC
- `idx_findings_embedding` — IVFFlat (vector_cosine_ops, lists=100)

**Ciclo de vida do status**:
```
new → enriched → scored → reviewed → delivered
                    └──────────────→ discarded
```

---

## Tabela: `scores` — 1:N com findings (N pilares)

| Coluna | Tipo | Constraints |
|--------|------|------------|
| `id` | uuid PK | |
| `finding_id` | uuid FK → findings | NOT NULL, CASCADE |
| `pillar_id` | uuid FK → pillars | NOT NULL, CASCADE |
| `confidence` | real | NOT NULL, CHECK 0..1 |
| `score_composite` | integer | NOT NULL, CHECK 0..100 |
| `dim_alignment` | integer | NOT NULL, CHECK 0..100 |
| `dim_br_luso` | integer | NOT NULL, CHECK 0..100 |
| `dim_replicable` | integer | NOT NULL, CHECK 0..100 |
| `dim_practical` | integer | NOT NULL, CHECK 0..100 |
| `dim_level` | integer | NOT NULL, CHECK 0..100 |
| `dim_novelty` | integer | NOT NULL, CHECK 0..100 |
| `computed_at` | timestamptz | NOT NULL, default now() |

**Unique**: `(finding_id, pillar_id)`

### Fórmula do score composto

```python
score = (
    dim_alignment * 0.30 +  # alinhamento ao pilar
    dim_br_luso   * 0.20 +  # Brasil/Lusofonia
    dim_replicable* 0.20 +  # replicabilidade
    dim_practical * 0.15 +  # projeto prático
    dim_level     * 0.10 +  # nível educacional
    dim_novelty   * 0.05    # novidade temporal
)
```

---

## Tabela: `reviews` — Decisão humana do Fábio

| Coluna | Tipo | Constraints |
|--------|------|------------|
| `id` | uuid PK | |
| `finding_id` | uuid FK → findings | NOT NULL, CASCADE |
| `reviewer_id` | text | NOT NULL, default 'fabio.jorge' |
| `decision` | text | NOT NULL, CHECK in ('approved','rejected','edited') |
| `edited_summary` | text | nullable |
| `feedback_tags` | text[] | NOT NULL, default '{}' |
| `reviewed_at` | timestamptz | NOT NULL, default now() |

---

## Tabela: `deliveries` — Auditoria de canais

| Coluna | Tipo | Constraints |
|--------|------|------------|
| `id` | uuid PK | |
| `finding_id` | uuid FK → findings | NOT NULL, CASCADE |
| `channel` | text | NOT NULL, CHECK in ('telegram','newsletter','dashboard') |
| `sent_at` | timestamptz | NOT NULL, default now() |
| `opened_at` | timestamptz | nullable |
| `payload` | jsonb | nullable |

---

## Políticas RLS (003_rls.sql)

- **ANON** pode ler: sources, pillars, findings aprovados/delivered, scores
- **ANON** NÃO pode ler: reviews (dado pessoal)
- **ANON** NÃO pode escrever em nenhuma tabela
- **SERVICE ROLE** tem acesso total (bypass RLS, usado só no Render)

---

## Thresholds de roteamento

| Score | Destino |
|-------|---------|
| ≥ 75 | Alerta instantâneo Telegram |
| 50–74 | Newsletter diária |
| 30–49 | Arquivado (busca no dashboard) |
| < 30 | Descartado (soft-delete após 7d) |

---

> **Registrado em**: 2026-06-25
