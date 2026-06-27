/**
 * Middleware de autenticação — protege rotas /dashboard e /api/findings/*.
 *
 * Redireciona usuários não autenticados para /login.
 * Atualiza sessão expirada automaticamente (refresh token).
 *
 * Executa em Edge Runtime (antes de qualquer Server Component).
 *
 * Fase 7.5 fix (auditoria Harness 2026-06-27):
 * MIDDLEWARE_INVOCATION_FAILED (500) no /dashboard. Causa: importava de
 * lib/supabase-server.ts que importa next/headers no topo — não disponível
 * no Edge Runtime. Corrigido: importar de lib/supabase-middleware.ts (sem
 * next/headers).
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
}

export const config = {
    matcher: [
        // Protege dashboard e rotas de findings
        '/dashboard/:path*',
        '/api/findings/:path*',
    ],
};
