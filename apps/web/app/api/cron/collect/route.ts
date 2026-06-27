import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "crypto";

/**
 * URL do endpoint /run no Render Web Service.
 * Fallback para o URL de produção caso a env var não esteja definida.
 */
const RENDER_RUN_URL = process.env.RENDER_RUN_URL || "https://observatorio-ciseb.onrender.com/run";

/**
 * Segredo compartilhado entre Vercel cron e Render.
 * Fallback para string vazia — todas as requisições serão rejeitadas
 * como 401 se a env var não estiver configurada (FAIL-CLOSED).
 */
const CRON_SECRET = process.env.CRON_SECRET || "";

export async function GET(request: NextRequest) {
    // ── Verificação de autorização ──────────────────────────────────
    const authHeader = request.headers.get("authorization");
    if (!authHeader?.startsWith("Bearer ")) {
        return NextResponse.json({ error: "Unauthorized — missing Bearer token" }, { status: 401 });
    }

    const token = authHeader.slice("Bearer ".length);
    if (!token || !CRON_SECRET) {
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
        const response = await fetch(RENDER_RUN_URL, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${CRON_SECRET}`,
                "Content-Type": "application/json",
            },
            signal: AbortSignal.timeout(90_000),
        });

        if (!response.ok) {
            return NextResponse.json({ error: `Render returned ${response.status}` }, { status: 502 });
        }

        const data = await response.json();
        return NextResponse.json({ ok: true, data });
    } catch (error) {
        return NextResponse.json({ error: "Failed to trigger Render", details: String(error) }, { status: 500 });
    }
}
