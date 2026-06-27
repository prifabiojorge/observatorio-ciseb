/**
 * Callback OAuth/Magic Link — Fase 5.
 *
 * Supabase redireciona para cá após autenticação. Troca o code por
 * sessão, salva cookies, e redireciona para ?redirect= ou /dashboard.
 */

import { NextResponse, NextRequest } from 'next/server';
import { createMiddlewareClient } from '@/lib/supabase-server';

export async function GET(request: NextRequest) {
    const { searchParams, origin } = request.nextUrl;
    const code = searchParams.get('code');
    const redirect = searchParams.get('redirect') || '/dashboard';

    if (code) {
        const response = NextResponse.redirect(`${origin}${redirect}`);
        const supabase = createMiddlewareClient(request, response);
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) {
            // Falha na troca do code — redireciona para login com erro
            const loginUrl = request.nextUrl.clone();
            loginUrl.pathname = '/login';
            loginUrl.search = `redirect=${encodeURIComponent(redirect)}&error=auth_failed`;
            return NextResponse.redirect(loginUrl);
        }
        return response;
    }

    // Sem code — volta para login
    return NextResponse.redirect(`${origin}/login`);
}
