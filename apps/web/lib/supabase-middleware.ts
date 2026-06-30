/**
 * Cliente Supabase para Middleware (Edge Runtime).
 *
 * Fase 7.5 fix (auditoria Harness 2026-06-27):
 * MIDDLEWARE_INVOCATION_FAILED (500) no /dashboard. Causa: middleware.ts
 * importava de lib/supabase-server.ts que importa next/headers no topo.
 * next/headers NÃO está disponível no Edge Runtime — só no Node.js runtime.
 *
 * Solução: módulo separado, sem next/headers, apenas NextRequest/NextResponse
 * (que SÃO suportados no Edge).
 *
 * Docs: https://supabase.com/docs/guides/auth/server-side/nextjs
 */

import { createServerClient } from '@supabase/ssr';
import { NextRequest, NextResponse } from 'next/server';

/**
 * Tipo para o parâmetro cookiesToSet do @supabase/ssr.
 */
type CookieToSet = {
    name: string;
    value: string;
    options?: {
        domain?: string;
        path?: string;
        sameSite?: 'strict' | 'lax' | 'none';
        secure?: boolean;
        httpOnly?: boolean;
        maxAge?: number;
        expires?: Date;
    };
};

/**
 * Cria cliente Supabase para uso em middleware (Edge Runtime).
 * Recebe request/response para manipular cookies.
 *
 * ATENÇÃO: Cada cookie do array deve ser aplicado tanto a `request.cookies`
 * quanto a `response.cookies` para que a sessão persista no ciclo de vida
 * completo da requisição Edge.
 */
export function createMiddlewareClient(request: NextRequest, response: NextResponse) {
    return createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                getAll() {
                    return request.cookies.getAll();
                },
                setAll(cookiesToSet: CookieToSet[]) {
                    // Aplica cada cookie em request E response, preservando
                    // opções de segurança (httpOnly, sameSite, secure, path).
                    // As opções do Supabase (se houver) são mergeadas via spread.
                    cookiesToSet.forEach(({ name, value, options }) => {
                        request.cookies.set(name, value);
                        response.cookies.set(name, value, {
                            httpOnly: true,
                            sameSite: 'lax',
                            secure: process.env.NODE_ENV === 'production',
                            path: '/',
                            ...options, // sobrescreve defaults se Supabase especificar
                        });
                    });
                },
            },
        }
    );
}
