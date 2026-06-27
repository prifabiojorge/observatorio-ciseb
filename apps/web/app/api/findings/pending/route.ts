/**
 * Rota API — Findings Pendentes de Revisão (Fase 4)
 *
 * Lista os top 10 findings com status "scored" para revisão humana,
 * enriquecidos com os scores por pilar.
 *
 * 🔒 AUTENTICAÇÃO OBRIGATÓRIA: Bearer CRON_SECRET no header Authorization.
 *    Previne acesso público a findings ainda não curados (status='scored').
 *
 * ⚠️ Exceção MVP: usa SUPABASE_SERVICE_ROLE_KEY (bypass RLS).
 *    A política RLS para ANON só permite status IN ('reviewed','delivered'),
 *    mas o dashboard precisa ler status='scored' para revisão.
 *
 * GET /api/findings/pending
 *
 * Headers:
 *   Authorization: Bearer <CRON_SECRET>
 *
 * Responses:
 *   200 — Array de findings com scores aninhados
 *   401 — Token inválido ou ausente
 *   500 — Erro de banco de dados
 */

import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

/**
 * Cliente Supabase com SERVICE_ROLE_KEY — bypass RLS.
 *
 * ⚠️ Esta chave NUNCA deve ser exposta ao client-side.
 *    A rota é server-only (Next.js API Route) e a variável de ambiente
 *    SUPABASE_SERVICE_ROLE_KEY é injetada apenas no backend Vercel.
 */
const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
);

/**
 * Segredo compartilhado — fail-closed, sem fallback.
 */
const CRON_SECRET = process.env.CRON_SECRET;
if (!CRON_SECRET) {
    throw new Error(
        "CRON_SECRET não configurado. Defina a variável no Vercel antes do deploy."
    );
}

/** Compara tokens em tempo constante (mitiga timing attacks). */
async function timingSafeEqual(a: string, b: string): Promise<boolean> {
    const enc = new TextEncoder();
    const aBytes = enc.encode(a);
    const bBytes = enc.encode(b);
    if (aBytes.length !== bBytes.length) return false;
    const diff = new Uint8Array(aBytes.length);
    for (let i = 0; i < aBytes.length; i++) {
        diff[i] = aBytes[i] ^ bBytes[i];
    }
    return diff.every((b) => b === 0);
}

/** Verifica o header Authorization. Retorna true se válido, false caso contrário. */
async function isAuthorized(request: NextRequest): Promise<boolean> {
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) return false;
    const token = authHeader.slice("Bearer ".length);
    return timingSafeEqual(token, CRON_SECRET);
}

export async function GET(request: NextRequest): Promise<NextResponse> {
    // ── Autenticação ────────────────────────────────────────────────
    if (!(await isAuthorized(request))) {
        return NextResponse.json(
            { error: "Unauthorized — Bearer CRON_SECRET required" },
            { status: 401 }
        );
    }

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
