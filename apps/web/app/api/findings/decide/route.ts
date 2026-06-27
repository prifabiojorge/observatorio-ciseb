/**
 * Rota API — Decisão de Curadoria (Fase 5 — Supabase Auth)
 *
 * Registra a decisão do revisor (approve/reject) sobre um finding.
 *
 * 🔒 AUTENTICAÇÃO REAL via Supabase Auth.
 *    O middleware.ts bloqueia sem sessão (401). Aqui usamos cookies.
 *    RLS policy "reviewer_insert_reviews" e "reviewer_update_findings_status"
 *    permitem escrita apenas se is_reviewer() = true.
 *
 * ⚠️ Não usa mais SERVICE_ROLE_KEY nem CRON_SECRET.
 *
 * POST /api/findings/decide
 *
 * Body:
 *   { "id": "<uuid>", "decision": "approved" | "rejected" }
 *
 * Responses:
 *   200 — Decisão registrada
 *   400 — Payload inválido
 *   401 — Não autenticado
 *   403 — Autenticado mas não é revisor (RLS bloqueia insert/update)
 *   500 — Erro de banco
 */

import { NextRequest, NextResponse } from "next/server";
import { createServerClientFromCookies } from "@/lib/supabase-server";

// Regex UUID v4 — defesa em profundidade contra injeção.
const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function POST(request: NextRequest) {
    // ── 1. Cliente Supabase com sessão ────────────────────────────────
    const supabase = await createServerClientFromCookies();
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
        return NextResponse.json(
            { error: "Unauthorized — sessão inválida" },
            { status: 401 }
        );
    }

    // reviewer_id agora vem do auth.uid() real, não hardcoded
    const reviewerId = session.user.id;

    try {
        const body = await request.json();
        const { id, decision } = body;

        // ── 2. Validação de payload ────────────────────────────────────
        if (typeof id !== "string" || !UUID_V4.test(id)) {
            return NextResponse.json(
                { error: "Invalid 'id'. Expected UUID v4." },
                { status: 400 }
            );
        }
        if (!["approved", "rejected"].includes(decision)) {
            return NextResponse.json(
                { error: "Invalid 'decision'. Expected 'approved' or 'rejected'." },
                { status: 400 }
            );
        }

        // ── 3. Insere a review (RLS permite apenas se is_reviewer) ────
        // Se o usuário não for o Fábio, RLS bloqueia e reviewError é retornado.
        const { error: reviewError } = await supabase
            .from("reviews")
            .insert({
                finding_id: id,
                reviewer_id: reviewerId,  // auth.uid() real, não hardcoded
                decision: decision,
            });

        if (reviewError) {
            // RLS bloqueou ou erro de DB
            if (reviewError.code === "42501") {  // insufficient_privilege
                return NextResponse.json(
                    { error: "Forbidden — você não tem permissão de revisor" },
                    { status: 403 }
                );
            }
            return NextResponse.json(
                { error: reviewError.message },
                { status: 500 }
            );
        }

        // ── 4. Atualiza status do finding ─────────────────────────────
        const newStatus = decision === "approved" ? "reviewed" : "discarded";
        const { error: updateError } = await supabase
            .from("findings")
            .update({ status: newStatus })
            .eq("id", id);

        if (updateError) {
            console.error(
                `[decide] Estado inconsistente: review inserida para ${id} ` +
                `mas findings.status não atualizado: ${updateError.message}`
            );
            return NextResponse.json(
                { error: "Review inserted but finding status update failed", id },
                { status: 500 }
            );
        }

        return NextResponse.json({ ok: true, id, decision, newStatus });
    } catch (error) {
        return NextResponse.json(
            { error: "Invalid request", details: String(error) },
            { status: 400 }
        );
    }
}
