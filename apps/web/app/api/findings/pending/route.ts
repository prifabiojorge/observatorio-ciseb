/**
 * Rota API — Findings Pendentes de Revisão (Fase 4)
 *
 * Lista os top 10 findings com status "scored" para revisão humana,
 * enriquecidos com os scores por pilar.
 *
 * ⚠️ Exceção MVP: usa SUPABASE_SERVICE_ROLE_KEY (bypass RLS).
 *    A política RLS para ANON só permite status IN ('reviewed','delivered'),
 *    mas o dashboard precisa ler status='scored' para revisão.
 *    Em produção, migrar para um token de serviço dedicado com RLS customizada.
 *
 * GET /api/findings/pending
 *
 * Responses:
 *   200 — Array de findings com scores aninhados
 *   500 — Erro de banco de dados
 */

import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

/**
 * Cliente Supabase com SERVICE_ROLE_KEY — bypass RLS.
 *
 * Motivo: a política `anon_read_findings` (003_rls.sql:48) restringe
 * ANON a `status IN ('reviewed','delivered')`, mas o dashboard de
 * revisão humana precisa ler `status='scored'`.
 *
 * ⚠️ Esta chave NUNCA deve ser exposta ao client-side.
 *    A rota é server-only (Next.js API Route) e a variável de ambiente
 *    SUPABASE_SERVICE_ROLE_KEY é injetada apenas no backend Vercel.
 */
const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function GET(): Promise<NextResponse> {
    // ── 1. Buscar findings scored ──────────────────────────────────
    const { data: findings, error } = await supabase
        .from("findings")
        .select("id, title, snippet, source_url, metadata, collected_at, status")
        .eq("status", "scored")
        .order("collected_at", { ascending: false })
        .limit(10);

    if (error) {
        return NextResponse.json(
            { error: error.message },
            { status: 500 }
        );
    }

    // ── 2. Se não há findings, retorna array vazio ─────────────────
    if (!findings || findings.length === 0) {
        return NextResponse.json([]);
    }

    // ── 3. Buscar scores para todos os findings retornados ─────────
    const ids: string[] = findings.map((f: any) => f.id);

    const { data: scores } = await supabase
        .from("scores")
        .select("finding_id, pillar_id, score_composite, confidence")
        .in("finding_id", ids);

    // ── 4. Agrupar scores por finding_id ───────────────────────────
    const scoresByFinding: Record<string, any[]> = {};
    (scores || []).forEach((s: any) => {
        if (!scoresByFinding[s.finding_id]) {
            scoresByFinding[s.finding_id] = [];
        }
        scoresByFinding[s.finding_id].push(s);
    });

    // ── 5. Montar resultado com scores aninhados ───────────────────
    const result = findings.map((f: any) => ({
        ...f,
        scores: scoresByFinding[f.id] || [],
    }));

    return NextResponse.json(result);
}
