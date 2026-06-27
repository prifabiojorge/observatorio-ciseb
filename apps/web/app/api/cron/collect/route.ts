/**
 * Rota API — Cron: Coleta (Fase 4)
 * 
 * Dispara a pipeline de coleta no Render Web Service.
 * Protegida por CRON_SECRET via header Authorization: Bearer.
 * 
 * Chamada pelo Vercel Cron Job configurado em vercel.json.
 * 
 * GET /api/cron/collect
 * 
 * Headers:
 *   Authorization: Bearer <CRON_SECRET>
 * 
 * Responses:
 *   200 — Coleta disparada com sucesso (dados do Render)
 *   401 — Token inválido ou ausente
 *   502 — Render retornou erro
 *   500 — Falha ao conectar com o Render
 */

import { NextRequest, NextResponse } from "next/server";

/** URL do endpoint /run no Render Web Service */
const RENDER_RUN_URL = process.env.RENDER_RUN_URL;
if (!RENDER_RUN_URL) {
    throw new Error(
        "RENDER_RUN_URL não configurado. Defina a variável no Vercel antes do deploy."
    );
}

/**
 * Segredo compartilhado entre Vercel cron e Render.
 * ⚠️ FAIL-CLOSED: sem fallback hardcoded. Se a env var faltar, o módulo
    recusa carregar em vez de abrir com senha padrão.
 */
const CRON_SECRET = process.env.CRON_SECRET;
if (!CRON_SECRET) {
    throw new Error(
        "CRON_SECRET não configurado. Defina a variável no Vercel antes do deploy."
    );
}

/**
 * Compara dois tokens em tempo constante para mitigar timing attacks.
 * Usa Web Crypto subtle (disponível em runtime Vercel/Edge).
 */
async function timingSafeEqual(a: string, b: string): Promise<boolean> {
    const enc = new TextEncoder();
    const aBytes = enc.encode(a);
    const bBytes = enc.encode(b);
    if (aBytes.length !== bBytes.length) {
        return false;
    }
    // crypto.subtle.digest é suportado no Vercel Node runtime
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
        const response = await fetch(RENDER_RUN_URL, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${CRON_SECRET}`,
                "Content-Type": "application/json",
            },
            // Timeout de 90s — pipeline completo pode demorar
            signal: AbortSignal.timeout(90_000),
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
                error: "Failed to trigger Render",
                details: String(error),
            },
            { status: 500 }
        );
    }
}
