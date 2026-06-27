/**
 * Rota API — Findings Pendentes de Revisão (Fase 5 — Supabase Auth)
 *
 * Lista os top 10 findings com status "scored" para revisão humana.
 *
 * 🔒 AUTENTICAÇÃO REAL via Supabase Auth (não mais CRON_SECRET).
 *    O middleware.ts já bloqueia requisições sem sessão válida (401).
 *    Aqui, criamos cliente com cookies do usuário autenticado.
 *    A RLS policy "reviewer_read_findings" permite ler status='scored'
 *    apenas se is_reviewer() = true (auth.uid() == Fábio).
 *
 * ⚠️ Não usa mais SERVICE_ROLE_KEY — RLS governa o acesso.
 *
 * GET /api/findings/pending
 *
 * Responses:
 *   200 — Array de findings com scores aninhados
 *   401 — Não autenticado (bloqueado pelo middleware)
 *   403 — Autenticado mas não é o revisor (RLS bloqueia)
 *   500 — Erro de banco de dados
 */

import { NextRequest, NextResponse } from "next/server";
import * as Sentry from "@sentry/nextjs";
import { createServerClientFromCookies } from "@/lib/supabase-server";

export async function GET(_request: NextRequest): Promise<NextResponse> {
    // ── 1. Cliente Supabase com sessão do usuário (cookies httpOnly) ──
    // Se não houver sessão, middleware já retornou 401 antes de chegar aqui.
    const supabase = await createServerClientFromCookies();

    // ── 2. Verifica sessão explícita (defesa em profundidade) ─────────
    const { data: { session }, error: sessionError } = await supabase.auth.getSession();
    if (sessionError || !session) {
        return NextResponse.json(
            { error: "Unauthorized — sessão inválida" },
            { status: 401 }
        );
    }

    // ── 3. Buscar findings scored ─────────────────────────────────────
    // RLS policy "reviewer_read_findings" filtra: só retorna linhas se
    // is_reviewer() = true. Se não for o Fábio, retorna array vazio.
    const { data: findings, error } = await supabase
        .from("findings")
        .select("id, title, snippet, source_url, metadata, collected_at, status")
        .eq("status", "scored")
        .order("collected_at", { ascending: false })
        .limit(10);

    if (error) {
        // Fase 7: capturar erro de banco no Sentry
        Sentry.captureException(error, {
            tags: { component: "api/findings/pending" },
        });
        return NextResponse.json(
            { error: error.message },
            { status: 500 }
        );
    }

    if (!findings || findings.length === 0) {
        return NextResponse.json([]);
    }

    // ── 4. Buscar scores para os findings retornados ──────────────────
    const ids: string[] = findings.map((f: any) => f.id);
    const { data: scores } = await supabase
        .from("scores")
        .select("finding_id, pillar_id, score_composite, confidence")
        .in("finding_id", ids);

    // ── 5. Agrupar scores por finding_id ──────────────────────────────
    const scoresByFinding: Record<string, any[]> = {};
    (scores || []).forEach((s: any) => {
        if (!scoresByFinding[s.finding_id]) {
            scoresByFinding[s.finding_id] = [];
        }
        scoresByFinding[s.finding_id].push(s);
    });

    // ── 6. Montar resultado ───────────────────────────────────────────
    const result = findings.map((f: any) => ({
        ...f,
        scores: scoresByFinding[f.id] || [],
    }));

    return NextResponse.json(result);
}
