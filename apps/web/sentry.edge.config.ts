import * as Sentry from "@sentry/nextjs";

/**
 * Configuração Sentry — Edge Runtime (middleware).
 *
 * Fase 7 (auditoria Harness 2026-06-27): captura erros no middleware.ts
 * (autenticação Supabase). Edge runtime é mais restrito que Node.js.
 */

Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,

    tracesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 1.0,

    environment: process.env.NODE_ENV || "development",

    sendDefaultPii: false,
});
