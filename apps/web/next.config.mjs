/**
 * Next.js config com integração Sentry (Fase 7).
 *
 * Fase 7 (auditoria Harness 2026-06-27): wrap do config com withSentryConfig
 * para habilitar source maps upload + tree-shaking do bundle Sentry.
 *
 * Docs: https://docs.sentry.io/platforms/javascript/guides/nextjs/
 */

import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const nextConfig = {
    // Linha adicionada para silenciar warning sobre instrumentation.ts
    // (necessário para Sentry funcionar em Next.js 14)
    experimental: {
        instrumentationHook: true,
    },
};

export default withSentryConfig(nextConfig, {
    // Org e project name no Sentry — necessários para source map upload.
    // Preenchidos via env vars para não hardcodear.
    org: process.env.SENTRY_ORG || "observatorio-ciseb",
    project: process.env.SENTRY_PROJECT || "observatorio-web",

    // Só fazer upload de source maps em produção (não em dev)
    silent: process.env.NODE_ENV !== "production",

    // Não falhar o build se Sentry auth faltar (dev/staging)
    errorHandler: (err) => {
        if (process.env.NODE_ENV === "production") {
            console.warn("[Sentry] Source map upload skipped:", err.message);
        }
    },

    // Tree-shaking do código Sentry em browser bundle
    hideSourceMaps: true,
    disableLogger: true,
});
