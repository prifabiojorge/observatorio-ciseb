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
 * Tipo para o parâmetro cookiesToSet do @supabase/ssr.
 * Compatível com `CookieOptions` da biblioteca — mantido inline para evitar
 * dependência de importação de tipos internos.
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
                setAll(cookiesToSet: CookieToSet[]) {
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
