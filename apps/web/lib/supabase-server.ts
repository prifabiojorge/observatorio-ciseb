/**
 * Cliente Supabase para server-side (API routes, Server Components).
 *
 * Lê a sessão dos cookies httpOnly. NÃO usa SERVICE_ROLE_KEY — usa
 * ANON_KEY + sessão do usuário. RLS passa a governar acesso.
 */

import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';

/**
 * Cria cliente Supabase para uso em Server Components e Route Handlers.
 * Lê tokens de sessão dos cookies (gerenciados pelo @supabase/ssr).
 */
export async function createServerClientFromCookies() {
    const cookieStore = await cookies();
    return createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                getAll() {
                    return cookieStore.getAll();
                },
                setAll(cookiesToSet) {
                    try {
                        cookiesToSet.forEach(({ name, value, options }) =>
                            cookieStore.set(name, value, options)
                        );
                    } catch {
                        // Chamado de Server Component — cookies não pode ser setado.
                        // Pode ser ignorado se há middleware para refresh.
                    }
                },
            },
        }
    );
}

/**
 * Cria cliente Supabase para uso em middleware (Edge Runtime).
 * Recebe request/response para manipular cookies.
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
                setAll(cookiesToSet) {
                    cookiesToSet.forEach(({ name, value }) =>
                        request.cookies.set(name, value)
                    );
                    response.cookies.set({
                        name,
                        value,
                        httpOnly: true,
                        sameSite: 'lax',
                        secure: process.env.NODE_ENV === 'production',
                        path: '/',
                    });
                },
            },
        }
    );
}
