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
const RENDER_DIGEST_URL = process.env.RENDER_DIGEST_URL;
if (!RENDER_DIGEST_URL) {
    throw new Error(
        "RENDER_DIGEST_URL não configurado. Defina a variável no Vercel antes do deploy."
    );
}

/**
 * Segredo compartilhado entre Vercel cron e Render.
 * ⚠️ FAIL-CLOSED: sem fallback hardcoded.
 */
const CRON_SECRET = process.env.CRON_SECRET;
if (!CRON_SECRET) {
    throw new Error(
        "CRON_SECRET não configurado. Defina a variável no Vercel antes do deploy."
    );
}

/**
 * Compara dois tokens em tempo constante para mitigar timing attacks.
 */
async function timingSafeEqual(a: string, b: string): Promise<boolean> {
    const enc = new TextEncoder();
    const aBytes = enc.encode(a);
    const bBytes = enc.encode(b);
    if (aBytes.length !== bBytes.length) {
        return false;
    }
    const diff = new Uint8Array(aBytes.length);
    for (let i = 0; i < aBytes.length; i++) {
        diff[i] = aBytes[i] ^ bBytes[i];
    }
    return diff.every((b) => b === 0);
}

export async function GET(request: NextRequest): Promise<NextResponse> {
    // ── Verificação de autorização ──────────────────────────────────
    const authHeader = request.headers.get("authorization");

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
        return NextResponse.json(
            { error: "Unauthorized — Bearer token required" },
            { status: 401 }
        );
    }

    const token = authHeader.slice("Bearer ".length);
    const isValid = await timingSafeEqual(token, CRON_SECRET);
    if (!isValid) {
        return NextResponse.json(
            { error: "Unauthorized — invalid token" },
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
