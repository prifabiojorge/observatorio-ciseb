/**
 * Rota API — Decisão de Revisão (Fase 4)
 * 
 * Registra decisão humana (aprovar/rejeitar) sobre um finding.
 * 
 * ⚠️ MVP Exception: Usa SUPABASE_SERVICE_ROLE_KEY para escrita,
 * pois o dashboard é client-side e não deve expor a service key.
 * Em produção, mover para um BFF (Backend For Frontend) ou
 * usar Supabase Edge Functions com RLS write policies.
 * 
 * POST /api/findings/decide
 * 
 * Body (JSON):
 *   id: string (uuid do finding)
 *   decision: "approved" | "rejected"
 * 
 * Responses:
 *   200 — Decisão registrada com sucesso
 *   400 — Payload inválido
 *   500 — Erro de banco de dados
 */

import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

/**
 * Cliente Supabase com SERVICE_ROLE_KEY para escrita.
 * ⚠️ Esta rota NUNCA deve ser exposta publicamente sem autenticação adicional.
 */
const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
);

/** Decisões válidas aceitas pelo endpoint */
const VALID_DECISIONS = ["approved", "rejected"] as const;
type Decision = (typeof VALID_DECISIONS)[number];

/**
 * Valida o payload da requisição.
 * Retorna null se válido, ou uma mensagem de erro.
 */
function validatePayload(body: any): { valid: false; error: string } | { valid: true; id: string; decision: Decision } {
    if (!body || typeof body !== "object") {
        return { valid: false, error: "Request body must be a JSON object" };
    }

    const { id, decision } = body;

    if (!id || typeof id !== "string") {
        return { valid: false, error: "Required: id (uuid string)" };
    }

    if (!VALID_DECISIONS.includes(decision)) {
        return {
            valid: false,
            error: `Invalid decision. Must be one of: ${VALID_DECISIONS.join(", ")}`,
        };
    }

    return { valid: true, id, decision };
}

export async function POST(request: NextRequest): Promise<NextResponse> {
    // ── 1. Parse e validação do payload ────────────────────────────
    let body: any;
    try {
        body = await request.json();
    } catch {
        return NextResponse.json(
            { error: "Invalid JSON body" },
            { status: 400 }
        );
    }

    const validation = validatePayload(body);
    if (!validation.valid) {
        return NextResponse.json(
            { error: validation.error },
            { status: 400 }
        );
    }

    const { id, decision } = validation;

    // ── 2. Inserir registro de review ──────────────────────────────
    const { error: reviewError } = await supabase.from("reviews").insert({
        finding_id: id,
        reviewer_id: "fabio.jorge",
        decision: decision,
    });

    if (reviewError) {
        return NextResponse.json(
            { error: `Failed to insert review: ${reviewError.message}` },
            { status: 500 }
        );
    }

    // ── 3. Atualizar status do finding ─────────────────────────────
    const newStatus = decision === "approved" ? "reviewed" : "discarded";

    const { error: updateError } = await supabase
        .from("findings")
        .update({ status: newStatus })
        .eq("id", id);

    if (updateError) {
        return NextResponse.json(
            { error: `Failed to update finding: ${updateError.message}` },
            { status: 500 }
        );
    }

    // ── 4. Sucesso ─────────────────────────────────────────────────
    return NextResponse.json({
        ok: true,
        id,
        decision,
        newStatus,
    });
}
