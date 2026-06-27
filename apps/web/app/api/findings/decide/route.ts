/**
 * Rota API — Decisão de Curadoria (Fase 4)
 *
 * Registra a decisão do revisor (approve/reject) sobre um finding.
 *
 * 🔒 AUTENTICAÇÃO OBRIGATÓRIA: Bearer CRON_SECRET no header Authorization.
 *    Previne que qualquer pessoa com a URL do dashboard manipule a curadoria.
 *
 * POST /api/findings/decide
 *
 * Headers:
 *   Authorization: Bearer <CRON_SECRET>
 *   Content-Type: application/json
 *
 * Body:
 *   { "id": "<uuid>", "decision": "approved" | "rejected" }
 *
 * Responses:
 *   200 — Decisão registrada (reviews + findings.status atualizado)
 *   400 — Payload inválido
 *   401 — Token inválido ou ausente
 *   500 — Erro de banco
 */

import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
);

/** Segredo compartilhado — fail-closed, sem fallback. */
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

async function isAuthorized(request: NextRequest): Promise<boolean> {
    const authHeader = request.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) return false;
    const token = authHeader.slice("Bearer ".length);
    return timingSafeEqual(token, CRON_SECRET);
}

// Regex UUID v4 — valida que o id recebido é um UUID válido antes de
// enviá-lo ao Supabase (defesa em profundidade contra injeção).
const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function POST(request: NextRequest) {
    // ── Autenticação ────────────────────────────────────────────────
    if (!(await isAuthorized(request))) {
        return NextResponse.json(
            { error: "Unauthorized — Bearer CRON_SECRET required" },
            { status: 401 }
        );
    }

    try {
        const body = await request.json();
        const { id, decision } = body;

        // ── Validação de payload ────────────────────────────────────
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

        // ── 1. Insere a review ──────────────────────────────────────
        const { error: reviewError } = await supabase
            .from("reviews")
            .insert({
                finding_id: id,
                reviewer_id: "fabio.jorge",
                decision: decision,
            });

        if (reviewError) {
            return NextResponse.json({ error: reviewError.message }, { status: 500 });
        }

        // ── 2. Atualiza o status do finding ────────────────────────
        const newStatus = decision === "approved" ? "reviewed" : "discarded";
        const { error: updateError } = await supabase
            .from("findings")
            .update({ status: newStatus })
            .eq("id", id);

        if (updateError) {
            // ⚠️ Review foi inserida mas findings não foi atualizado.
            //    Estado inconsistente — logar e retornar erro para o cliente.
            //    Em produção, idealmente usar RPC Postgres transacional.
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
