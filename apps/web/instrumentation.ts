/**
 * Instrumentação Next.js — registra Sentry no Node.js runtime.
 *
 * Fase 7 (auditoria Harness 2026-06-27): Next.js 14 exige este arquivo
 * para que Sentry capture erros de API routes e Server Components.
 * Sem ele, sentry.server.config.ts não é carregado.
 *
 * Docs: https://docs.sentry.io/platforms/javascript/guides/nextjs/
 */

export async function register() {
    if (process.env.NEXT_RUNTIME === "nodejs") {
        await import("./sentry.server.config");
    }

    if (process.env.NEXT_RUNTIME === "edge") {
        await import("./sentry.server.config");
    }
}
