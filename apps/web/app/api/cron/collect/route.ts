import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "crypto";

/**
 * URL do endpoint /run no Render Web Service.
 *
 * R1+R2 (auditoria Harness 2026-06-27):
 * - Se RENDER_RUN_URL faltar, usamos fallback da URL pública conhecida.
 *   Não é segredo (URL é pública no .env.example), mas logamos warning
 *   para que o diagnóstico de "cron falhando" seja claro nos logs Vercel.
 * - Alternativa: throw em build time. Rejeitada porque Vercel Hobby
 *   às vezes demora a propagar env vars após mudança, e quebrar o build
 *   por isso é pior que logar warning em runtime.
 */
const RENDER_RUN_URL = process.env.RENDER_RUN_URL || "https://observatorio-ciseb.onrender.com/run";
if (!process.env.RENDER_RUN_URL) {
    // eslint-disable-next-line no-console
    console.warn("[cron/collect] RENDER_RUN_URL não configurada — usando fallback público.");
}

/**
 * Segredo compartilhado entre Vercel cron e Render.
 *
 * R2 (auditoria Harness 2026-06-27):
 * - Se CRON_SECRET faltar, TODAS as requisições serão rejeitadas como 401
 *   (fail-closed em runtime, já que throw em build time quebraria o deploy
 *   se a env var fosse acidentalmente removida).
 * - Logamos erro em runtime para diagnóstico — sem isto, cron falharia
 *   silenciosamente com 401 repetido.
 * - Type cast `as string` satisfaz TypeScript sem sacrificar fail-closed.
 */
const CRON_SECRET = process.env.CRON_SECRET || "";
if (!process.env.CRON_SECRET) {
    // eslint-disable-next-line no-console
    console.error("[FATAL] [cron/collect] CRON_SECRET não configurado — todas as requisições serão 401.");
}

export async function GET(request: NextRequest) {
    // ── Verificação de autorização ──────────────────────────────────
    const authHeader = request.headers.get("authorization");
    if (!authHeader?.startsWith("Bearer ")) {
        return NextResponse.json({ error: "Unauthorized — missing Bearer token" }, { status: 401 });
    }

    const token = authHeader.slice("Bearer ".length);
    if (!token || !CRON_SECRET) {
        // R2: log explícito para diagnóstico — sem isto, 401 silencioso.
        // eslint-disable-next-line no-console
        console.error("[cron/collect] Requisição rejeitada: token ou CRON_SECRET ausente.");
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
