/**
 * Rota API — Findings Pendentes de Revisão (Fase 4)
 * 
 * Lista os top 10 findings com status "scored" para revisão humana,
 * enriquecidos com os scores por pilar.
 * 
 * Usa SUPABASE_ANON_KEY (read-only pública) — seguro para client-side.
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
 * Cliente Supabase com ANON_KEY para leitura pública.
 * RLS garante que apenas dados permitidos sejam expostos.
 */
const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_ANON_KEY!
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
