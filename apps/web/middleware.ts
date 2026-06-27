/**
 * Middleware de autenticação — protege rotas /dashboard e /api/findings/*.
 *
 * Redireciona usuários não autenticados para /login.
 * Atualiza sessão expirada automaticamente (refresh token).
 *
 * Executa em Edge Runtime (antes de qualquer Server Component).
 *
 * Fase 7.5 fix (auditoria Harness 2026-06-27):
 * MIDDLEWARE_INVOCATION_FAILED (500) no /dashboard.
 *
 * Causa 1: middleware.ts importava de lib/supabase-server.ts que importa
 * next/headers no topo — não disponível no Edge Runtime. Corrigido com
 * módulo separado lib/supabase-middleware.ts.
 *
 * Causa 2 (esta correção): @supabase/ssr createServerClient pode falhar
 * se NEXT_PUBLIC_SUPABASE_URL ou NEXT_PUBLIC_SUPABASE_ANON_KEY não estiverem
 * configuradas na Vercel. Adicionado try/catch com fallback gracioso.
 *
 * Docs: https://supabase.com/docs/guides/auth/server-side/nextjs
 */

import { NextResponse, NextRequest } from 'next/server';
import { createMiddlewareClient } from '@/lib/supabase-middleware';

// Rotas que exigem autenticação
const PROTECTED_PATHS = ['/dashboard'];
const PROTECTED_API_PREFIXES = ['/api/findings'];

export async function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Verifica se a rota é protegida
    const isProtectedPage = PROTECTED_PATHS.some(p => pathname.startsWith(p));
    const isProtectedApi = PROTECTED_API_PREFIXES.some(p => pathname.startsWith(p));

    if (!isProtectedPage && !isProtectedApi) {
        return NextResponse.next();
    }

    // Fase 7.5: verificar se env vars estão configuradas antes de tentar
    // criar cliente Supabase. Se faltar, redireciona para /login com aviso.
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseAnonKey) {
        console.error('[middleware] NEXT_PUBLIC_SUPABASE_URL ou NEXT_PUBLIC_SUPABASE_ANON_KEY não configuradas');
        if (isProtectedPage) {
            const loginUrl = request.nextUrl.clone();
            loginUrl.pathname = '/login';
            loginUrl.searchParams.set('redirect', pathname);
            loginUrl.searchParams.set('error', 'config_missing');
            return NextResponse.redirect(loginUrl);
        }
        return NextResponse.json(
            { error: 'Server configuration error — Supabase env vars missing' },
            { status: 500 }
        );
    }

    try {
        // Cria resposta e cliente Supabase que lê/define cookies
        const response = NextResponse.next();
        const supabase = createMiddlewareClient(request, response);

        // Verifica sessão (refresh automático se expirada)
        const { data: { session }, error } = await supabase.auth.getSession();

        if (error || !session) {
            // Para páginas HTML: redireciona para /login
            if (isProtectedPage) {
                const loginUrl = request.nextUrl.clone();
                loginUrl.pathname = '/login';
                loginUrl.searchParams.set('redirect', pathname);
                return NextResponse.redirect(loginUrl);
            }
            // Para API: retorna 401 JSON
            if (isProtectedApi) {
                return NextResponse.json(
                    { error: 'Unauthorized — login required' },
                    { status: 401 }
                );
            }
        }

        return response;
    } catch (err) {
        // Fase 7.5: capturar qualquer erro no Edge Runtime
        // Em vez de 500 (MIDDLEWARE_INVOCATION_FAILED), redireciona para /login
        console.error('[middleware] Erro inesperado:', err);
        if (isProtectedPage) {
            const loginUrl = request.nextUrl.clone();
            loginUrl.pathname = '/login';
            loginUrl.searchParams.set('redirect', pathname);
            loginUrl.searchParams.set('error', 'middleware_failed');
            return NextResponse.redirect(loginUrl);
        }
        return NextResponse.json(
            { error: 'Middleware error', details: String(err) },
            { status: 500 }
        );
    }
}

export const config = {
    matcher: [
        // Protege dashboard e rotas de findings
        '/dashboard/:path*',
        '/api/findings/:path*',
    ],
};
