/**
 * Cliente Supabase para browser (client-side) — Fase 5.
 *
 * Usa @supabase/ssr para gerenciar sessão via cookies httpOnly.
 * Este cliente NÃO tem SERVICE_ROLE_KEY — apenas ANON_KEY.
 *
 * Auth flow: magic link por email (sem senha) ou OAuth (Google/GitHub).
 * Apenas o Fábio terá conta criada no Supabase Auth.
 */

import { createBrowserClient } from '@supabase/ssr';

export function createClient() {
    return createBrowserClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
}
