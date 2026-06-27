import * as Sentry from "@sentry/nextjs";

/**
 * Configuração Sentry — lado servidor (API routes, Server Components).
 *
 * Fase 7 (auditoria Harness 2026-06-27): captura erros em:
 * - API routes (/api/findings/*, /api/cron/*)
 * - Server Components
 * - Edge middleware
 *
 * DSN vem de SENTRY_DSN (server-side, NÃO público).
 */

Sentry.init({
    dsn: process.env.SENTRY_DSN,

    // Sampling: 100% em dev, 20% em produção (server errors são mais raros)
    tracesSampleRate: process.env.NODE_ENV === "production" ? 0.2 : 1.0,

    environment: process.env.NODE_ENV || "development",

    release: process.env.VERCEL_GIT_COMMIT_SHA || "dev",

    // Erros a ignorar (barulho comum)
    ignoreErrors: [
        "AbortError",
        // Supabase Auth: sessão expirada não é erro real
        "AuthSessionMissingError",
        // Vercel: timeout de função em cold start
        "FunctionExecutionTimeout",
    ],

    sendDefaultPii: false,
});
