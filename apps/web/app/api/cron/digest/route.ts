import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "crypto";

/**
 * URL do endpoint /digest no Render Web Service.
 *
 * R1+R2 (auditoria Harness 2026-06-27): ver comentários em collect/route.ts.
 */
const RENDER_DIGEST_URL = process.env.RENDER_DIGEST_URL || "https://observatorio-ciseb.onrender.com/digest";
if (!process.env.RENDER_DIGEST_URL) {
    // eslint-disable-next-line no-console
    console.warn("[cron/digest] RENDER_DIGEST_URL não configurada — usando fallback público.");
}

/**
 * Segredo compartilhado entre Vercel cron e Render.
 * R2: fail-closed em runtime + log explícito se ausente.
 */
const CRON_SECRET = process.env.CRON_SECRET || "";
if (!process.env.CRON_SECRET) {
    // eslint-disable-next-line no-console
    console.error("[FATAL] [cron/digest] CRON_SECRET não configurado — todas as requisições serão 401.");
}

export async function GET(request: NextRequest) {
    // ── Verificação de autorização ──────────────────────────────────
    const authHeader = request.headers.get("authorization");
    if (!authHeader?.startsWith("Bearer ")) {
        return NextResponse.json({ error: "Unauthorized — missing Bearer token" }, { status: 401 });
    }

    const token = authHeader.slice("Bearer ".length);
    if (!token || !CRON_SECRET) {
        // eslint-disable-next-line no-console
        console.error("[cron/digest] Requisição rejeitada: token ou CRON_SECRET ausente.");
        return NextResponse.json({ error: "Unauthorized — missing credentials" }, { status: 401 });
    }

    let isValid = false;
    try {
        isValid = timingSafeEqual(Buffer.from(token), Buffer.from(CRON_SECRET));
    } catch {
        return NextResponse.json({ error: "Unauthorized — invalid token" }, { status: 401 });
    }

    if (!isValid) {
        return NextResponse.json({ error: "Unauthorized — invalid token" }, { status: 401 });
    }

    // ── Chamada ao Render ──────────────────────────────────────────
    try {
        const response = await fetch(RENDER_DIGEST_URL, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${CRON_SECRET}`,
                "Content-Type": "application/json",
            },
            signal: AbortSignal.timeout(30_000),
        });

        if (!response.ok) {
            return NextResponse.json({ error: `Render returned ${response.status}` }, { status: 502 });
        }

        const data = await response.json();
        return NextResponse.json({ ok: true, data });
    } catch (error) {
        return NextResponse.json({ error: "Failed to trigger digest", details: String(error) }, { status: 500 });
    }
}
