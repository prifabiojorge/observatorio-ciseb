/**
 * Cliente Supabase para server-side (API routes, Server Components).
 *
 * NÃO usar em middleware — Edge Runtime não suporta next/headers.
 * Para middleware, usar createMiddlewareClient de lib/supabase-middleware.ts.
 *
 * Lê a sessão dos cookies httpOnly. NÃO usa SERVICE_ROLE_KEY — usa
 * ANON_KEY + sessão do usuário. RLS passa a governar acesso.
 */

import { createServerClient } from '@supabase/ssr';
import { cookies } from 'next/headers';

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
