import * as Sentry from "@sentry/nextjs";

/**
 * Configuração Sentry — lado cliente (browser).
 *
 * Fase 7 (auditoria Harness 2026-06-27): captura erros de runtime no
 * browser (React errors, fetch failures, etc.) e envia para o Sentry.
 *
 * DSN vem de NEXT_PUBLIC_SENTRY_DSN. Sem DSN, Sentry fica inativo
 * (não quebra o build — fail-safe).
 */

Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,

    // Sampling: 100% em dev, 10% em produção (conta free tier tem limite)
    tracesSampleRate: process.env.NODE_ENV === "production" ? 0.1 : 1.0,

    // Environment (production, preview, development)
    environment: process.env.NODE_ENV || "development",

    // Release version (para identificar deploy que introduziu bug)
    release: process.env.NEXT_PUBLIC_VERCEL_GIT_COMMIT_SHA || "dev",

    // Ignorar erros conhecidos e barulho
    ignoreErrors: [
        // Hydra/Chrome extensions
        "top.GLOBALS",
        // Cancelamento de fetch (não é erro real)
        "AbortError",
    ],

    // Não enviar PII (LGPD)
    sendDefaultPii: false,
});
