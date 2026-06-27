/**
 * Rota API — Cron: Digest Diário (Fase 4)
 * 
 * Dispara o digest diário no Render Web Service.
 * Protegida por CRON_SECRET via header Authorization: Bearer.
 * 
 * Chamada pelo Vercel Cron Job (agendamento diário).
 * 
 * GET /api/cron/digest
 * 
 * Headers:
 *   Authorization: Bearer <CRON_SECRET>
 * 
 * Responses:
 *   200 — Digest disparado com sucesso (dados do Render)
 *   401 — Token inválido ou ausente
 *   502 — Render retornou erro
 *   500 — Falha ao conectar com o Render
 */

import { NextRequest, NextResponse } from "next/server";

/** URL do endpoint /digest no Render Web Service */
const RENDER_DIGEST_URL =
    process.env.RENDER_DIGEST_URL ||
    "https://observatorio-ciseb.onrender.com/digest";

/** Segredo compartilhado entre Vercel cron e Render */
const CRON_SECRET =
    process.env.CRON_SECRET || "observatorio-ciseb-f1-2026";

export async function GET(request: NextRequest): Promise<NextResponse> {
    // ── Verificação de autorização ──────────────────────────────────
    const authHeader = request.headers.get("authorization");

    if (!authHeader || authHeader !== `Bearer ${CRON_SECRET}`) {
        return NextResponse.json(
            { error: "Unauthorized" },
            { status: 401 }
        );
    }

    // ── Chamada ao Render ──────────────────────────────────────────
    try {
        const response = await fetch(RENDER_DIGEST_URL, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${CRON_SECRET}`,
                "Content-Type": "application/json",
            },
            // Timeout de 30s — digest é mais rápido que coleta completa
            signal: AbortSignal.timeout(30_000),
        });

        if (!response.ok) {
            return NextResponse.json(
                { error: `Render returned ${response.status}` },
                { status: 502 }
            );
        }

        const data = await response.json();
        return NextResponse.json({ ok: true, data });
    } catch (error) {
        return NextResponse.json(
            {
                error: "Failed to trigger digest",
                details: String(error),
            },
            { status: 500 }
        );
    }
}
