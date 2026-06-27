/**
 * Next.js config com integração Sentry (Fase 7) + redirect raiz (Fase 7.4).
 *
 * Fase 7 (auditoria Harness 2026-06-27): wrap do config com withSentryConfig
 * para habilitar source maps upload + tree-shaking do bundle Sentry.
 *
 * Fase 7.4 (auditoria Harness 2026-06-27): redirect 301 da raiz (/) para
 * /dashboard. Antes, acessar observatorio-ciseb.vercel.app retornava 404.
 * Agora redireciona automaticamente para o dashboard (que por sua vez
 * redireciona para /login se não houver sessão).
 *
 * Docs:
 * - Sentry: https://docs.sentry.io/platforms/javascript/guides/nextjs/
 * - Redirects: https://nextjs.org/docs/app/api-reference/next-config-js/redirects
 */

import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const nextConfig = {
    // Necessário para Sentry funcionar em Next.js 14 (instrumentation.ts)
    experimental: {
        instrumentationHook: true,
    },

    // Fase 7.4: redirect 301 da raiz para /dashboard
    // 301 = permanent (SEO friendly, browser cacheia)
    // Fluxo: / → /dashboard → (sem sessão) → /login
    async redirects() {
        return [
            {
                source: "/",
                destination: "/dashboard",
                permanent: true,
            },
        ];
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
