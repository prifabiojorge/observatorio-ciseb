"use client";

/**
 * Página de login — Fase 5 (Supabase Auth).
 *
 * Aceita magic link por email. Apenas o email do Fábio terá conta
 * ativa no Supabase (configurado via dashboard Supabase → Auth → Users).
 *
 * Após login, redireciona para /dashboard ou para ?redirect=...
 */

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";

function LoginForm() {
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);
    const router = useRouter();
    const searchParams = useSearchParams();
    const redirectTo = searchParams.get("redirect") || "/dashboard";
    const supabase = createClient();

    async function handleMagicLink(e: React.FormEvent) {
        e.preventDefault();
        if (!email) return;
        setLoading(true);
        setMessage(null);

        const { error } = await supabase.auth.signInWithOtp({
            email,
            options: {
                emailRedirectTo: `${window.location.origin}/auth/callback?redirect=${encodeURIComponent(redirectTo)}`,
            },
        });

        setLoading(false);
        if (error) {
            setMessage({ text: `Erro: ${error.message}`, type: "error" });
        } else {
            setMessage({
                text: "✅ Link de login enviado! Verifique seu email.",
                type: "success",
            });
        }
    }

    async function handleGoogleLogin() {
        setLoading(true);
        const { error } = await supabase.auth.signInWithOAuth({
            provider: "google",
            options: {
                redirectTo: `${window.location.origin}/auth/callback?redirect=${encodeURIComponent(redirectTo)}`,
            },
        });
        if (error) {
            setLoading(false);
            setMessage({ text: `Erro: ${error.message}`, type: "error" });
        }
    }

    return (
        <div style={styles.container}>
            <div style={styles.card}>
                <h1 style={styles.title}>🔐 Observatório CISEB</h1>
                <p style={styles.subtitle}>Login do revisor</p>

                <form onSubmit={handleMagicLink} style={styles.form}>
                    <input
                        type="email"
                        placeholder="seu@email.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        style={styles.input}
                        required
                        disabled={loading}
                    />
                    <button type="submit" style={styles.button} disabled={loading}>
                        {loading ? "Enviando..." : "Enviar link mágico"}
                    </button>
                </form>

                <div style={styles.divider}>ou</div>

                <button
                    onClick={handleGoogleLogin}
                    style={styles.googleButton}
                    disabled={loading}
                >
                    Continuar com Google
                </button>

                {message && (
                    <div
                        style={{
                            ...styles.message,
                            background: message.type === "success" ? "#d4edda" : "#f8d7da",
                            color: message.type === "success" ? "#155724" : "#721c24",
                        }}
                        role="alert"
                    >
                        {message.text}
                    </div>
                )}

                <p style={styles.help}>
                    Acesso restrito ao revisor autorizado. Se você não recebeu o email,
                    verifique o spam ou contate o administrador.
                </p>
            </div>
        </div>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={<div style={{ padding: 40 }}>Carregando...</div>}>
            <LoginForm />
        </Suspense>
    );
}

const styles: Record<string, React.CSSProperties> = {
    container: {
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f5f5f5",
        fontFamily: "system-ui, -apple-system, sans-serif",
    },
    card: {
        background: "#fff",
        padding: 40,
        borderRadius: 12,
        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
        width: "100%",
        maxWidth: 400,
    },
    title: { margin: "0 0 8px 0", fontSize: 24, fontWeight: 700 },
    subtitle: { margin: "0 0 24px 0", color: "#666", fontSize: 14 },
    form: { display: "flex", flexDirection: "column", gap: 12 },
    input: {
        padding: "12px 16px",
        border: "1px solid #ddd",
        borderRadius: 6,
        fontSize: 14,
        outline: "none",
    },
    button: {
        padding: "12px 16px",
        background: "#007bff",
        color: "#fff",
        border: "none",
        borderRadius: 6,
        cursor: "pointer",
        fontWeight: 600,
        fontSize: 14,
    },
    divider: {
        textAlign: "center",
        color: "#999",
        margin: "20px 0",
        fontSize: 12,
    },
    googleButton: {
        width: "100%",
        padding: "12px 16px",
        background: "#fff",
        color: "#333",
        border: "1px solid #ddd",
        borderRadius: 6,
        cursor: "pointer",
        fontWeight: 500,
        fontSize: 14,
    },
    message: {
        padding: "12px 16px",
        borderRadius: 6,
        marginTop: 16,
        fontSize: 14,
    },
    help: {
        marginTop: 24,
        fontSize: 12,
        color: "#999",
        lineHeight: 1.5,
    },
};
