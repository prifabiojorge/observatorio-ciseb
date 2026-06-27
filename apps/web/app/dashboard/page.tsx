"use client";

/**
 * Dashboard de Revisão Humana — Observatório CISEB (Fase 4)
 * 
 * Exibe os top 10 findings pendentes de revisão (status "scored"),
 * com scores por pilar e botões de aprovar/rejeitar.
 * 
 * Client-side rendering com chamadas fetch às API routes.
 * 
 * 🔒 AUTENTICAÇÃO: O token NEXT_PUBLIC_DASHBOARD_TOKEN é injetado no
 *    bundle client-side e enviado como Bearer nas chamadas às API
 *    routes. Isto NÃO é segurança real — é apenas uma barreira contra
 *    acesso casual. Para segurança real, migrar para Supabase Auth
 *    (Fase 5). Aceitável para MVP com revisor único (Fábio).
 * 
 * Rota: /dashboard
 */

import { useEffect, useState, useCallback } from "react";

// ─── Tipos ────────────────────────────────────────────────────────

/** Score individual de um pilar para um finding */
interface Score {
    finding_id: string;
    pillar_id: string;
    score_composite: number;
    confidence: number;
}

/** Finding pendente de revisão, com scores aninhados */
interface Finding {
    id: string;
    title: string;
    snippet: string;
    source_url: string;
    collected_at: string;
    scores: Score[];
}

/** Estados possíveis do feedback de ação */
type FeedbackType = "success" | "error" | "info";

interface ActionFeedback {
    message: string;
    type: FeedbackType;
}

// ─── Constantes ───────────────────────────────────────────────────

const API_PENDING = "/api/findings/pending";
const API_DECIDE = "/api/findings/decide";

/**
 * Token público injetado no client-side. Não é segurança real (qualquer
 * um pode inspecionar o bundle), mas previne acesso casual via URL.
 * Para segurança real: Supabase Auth (Fase 5).
 */
const DASHBOARD_TOKEN = process.env.NEXT_PUBLIC_DASHBOARD_TOKEN || "";

/** Monta headers com Authorization para chamadas autenticadas. */
function authHeaders(extra: Record<string, string> = {}): Record<string, string> {
    return {
        "Content-Type": "application/json",
        Authorization: `Bearer ${DASHBOARD_TOKEN}`,
        ...extra,
    };
}

/** Mapeamento de tipo de feedback para cores de fundo */
const FEEDBACK_COLORS: Record<FeedbackType, string> = {
    success: "#d4edda",
    error: "#f8d7da",
    info: "#fff3cd",
};

// ─── Componente Principal ─────────────────────────────────────────

export default function DashboardPage() {
    const [findings, setFindings] = useState<Finding[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionFeedback, setActionFeedback] = useState<ActionFeedback | null>(null);

    // ── Fetch: Buscar findings pendentes ────────────────────────────
    const fetchPending = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(API_PENDING, {
                headers: authHeaders(),
            });
            if (res.status === 401) {
                throw new Error("Token de acesso ausente ou inválido. Configure NEXT_PUBLIC_DASHBOARD_TOKEN.");
            }
            if (!res.ok) {
                const text = await res.text();
                throw new Error(text || `HTTP ${res.status}`);
            }
            const data: Finding[] = await res.json();
            setFindings(data);
        } catch (e: any) {
            setError(e.message || "Erro desconhecido ao carregar findings");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchPending();
    }, [fetchPending]);

    // ── Ação: Aprovar ou Rejeitar ───────────────────────────────────
    const decide = useCallback(async (id: string, decision: "approved" | "rejected") => {
        setActionFeedback(null);
        try {
            const res = await fetch(API_DECIDE, {
                method: "POST",
                headers: authHeaders(),
                body: JSON.stringify({ id, decision }),
            });

            if (res.status === 401) {
                throw new Error("Token de acesso inválido.");
            }
            if (!res.ok) {
                const text = await res.text();
                throw new Error(text || `HTTP ${res.status}`);
            }

            const label = decision === "approved" ? "✅ Aprovado" : "❌ Rejeitado";
            setActionFeedback({ message: label, type: "success" });

            // Remove o finding da lista local (otimista)
            setFindings((prev) => prev.filter((f) => f.id !== id));
        } catch (e: any) {
            setActionFeedback({
                message: `Erro: ${e.message || "Falha ao registrar decisão"}`,
                type: "error",
            });
        }
    }, []);

    // ── Render: Estados de loading / erro ───────────────────────────
    if (loading) {
        return (
            <div style={styles.container}>
                <div style={styles.loadingSpinner} />
                <p style={{ color: "#666", marginTop: 12 }}>Carregando achados pendentes...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div style={styles.container}>
                <div style={styles.errorBox}>
                    <h2>⚠️ Erro ao carregar</h2>
                    <p>{error}</p>
                    <button onClick={fetchPending} style={styles.retryButton}>
                        🔄 Tentar novamente
                    </button>
                </div>
            </div>
        );
    }

    // ── Render: Dashboard ───────────────────────────────────────────
    return (
        <div style={styles.pageWrapper}>
            <div style={styles.header}>
                <h1 style={styles.title}>📋 Observatório CISEB — Revisão</h1>
                <p style={styles.subtitle}>
                    {findings.length} achado{findings.length !== 1 ? "s" : ""} pendente
                    {findings.length !== 1 ? "s" : ""} de revisão
                </p>
            </div>

            {/* Feedback de ação */}
            {actionFeedback && (
                <div
                    style={{
                        ...styles.feedbackBanner,
                        background: FEEDBACK_COLORS[actionFeedback.type],
                    }}
                    role="alert"
                >
                    {actionFeedback.message}
                </div>
            )}

            {/* Lista de findings */}
            <div style={styles.cardList}>
                {findings.map((f) => (
                    <FindingCard key={f.id} finding={f} onDecide={decide} />
                ))}
            </div>

            {/* Estado vazio */}
            {findings.length === 0 && (
                <div style={styles.emptyState}>
                    <p style={{ fontSize: 48, margin: 0 }}>🎉</p>
                    <p style={{ color: "#999", marginTop: 8 }}>
                        Nenhum achado pendente. Tudo revisado!
                    </p>
                </div>
            )}
        </div>
    );
}

// ─── Sub-componente: Card de Finding ──────────────────────────────

interface FindingCardProps {
    finding: Finding;
    onDecide: (id: string, decision: "approved" | "rejected") => void;
}

function FindingCard({ finding, onDecide }: FindingCardProps) {
    const { id, title, snippet, source_url, scores } = finding;

    return (
        <div style={styles.card}>
            <h3 style={styles.cardTitle}>{title}</h3>
            <p style={styles.cardSnippet}>{snippet}</p>

            {/* Scores badges */}
            {scores.length > 0 && (
                <div style={styles.badgeRow}>
                    {scores.map((s, i) => (
                        <span
                            key={i}
                            style={{
                                ...styles.badge,
                                background: s.score_composite >= 75 ? "#d4edda" : "#e2e3e5",
                            }}
                            title={`Pilar ${s.pillar_id}: confiança ${(s.confidence * 100).toFixed(0)}%`}
                        >
                            🏷️ {s.score_composite}/100
                        </span>
                    ))}
                </div>
            )}

            {/* Link para fonte */}
            <a
                href={source_url}
                target="_blank"
                rel="noopener noreferrer"
                style={styles.sourceLink}
            >
                🔗 Fonte original
            </a>

            {/* Botões de ação */}
            <div style={styles.actionRow}>
                <button
                    onClick={() => onDecide(id, "approved")}
                    style={styles.approveButton}
                    aria-label={`Aprovar finding: ${title}`}
                >
                    ✅ Aprovar
                </button>
                <button
                    onClick={() => onDecide(id, "rejected")}
                    style={styles.rejectButton}
                    aria-label={`Rejeitar finding: ${title}`}
                >
                    ❌ Rejeitar
                </button>
            </div>
        </div>
    );
}

// ─── Estilos inline (zero dependências CSS) ───────────────────────

const styles: Record<string, React.CSSProperties> = {
    pageWrapper: {
        maxWidth: 800,
        margin: "0 auto",
        padding: 20,
        fontFamily: "system-ui, -apple-system, sans-serif",
    },
    container: {
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "60vh",
        fontFamily: "system-ui, -apple-system, sans-serif",
    },
    header: {
        marginBottom: 20,
    },
    title: {
        fontSize: 24,
        fontWeight: 700,
        margin: "0 0 4px 0",
    },
    subtitle: {
        color: "#666",
        fontSize: 14,
        margin: 0,
    },
    feedbackBanner: {
        padding: "12px 16px",
        margin: "10px 0 16px 0",
        borderRadius: 6,
        fontSize: 14,
        fontWeight: 500,
    },
    cardList: {
        display: "flex",
        flexDirection: "column",
        gap: 12,
    },
    card: {
        border: "1px solid #e0e0e0",
        borderRadius: 8,
        padding: 16,
        background: "#fff",
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
    },
    cardTitle: {
        margin: "0 0 8px 0",
        fontSize: 16,
        fontWeight: 600,
    },
    cardSnippet: {
        color: "#555",
        fontSize: 14,
        lineHeight: 1.5,
        margin: "0 0 8px 0",
    },
    badgeRow: {
        margin: "8px 0",
        display: "flex",
        gap: 6,
        flexWrap: "wrap",
    },
    badge: {
        padding: "2px 10px",
        borderRadius: 4,
        fontSize: 12,
        fontWeight: 500,
    },
    sourceLink: {
        fontSize: 12,
        color: "#007bff",
        textDecoration: "none",
        display: "inline-block",
        marginBottom: 4,
    },
    actionRow: {
        marginTop: 12,
        display: "flex",
        gap: 8,
    },
    approveButton: {
        padding: "8px 20px",
        background: "#28a745",
        color: "#fff",
        border: "none",
        borderRadius: 6,
        cursor: "pointer",
        fontWeight: 600,
        fontSize: 14,
    },
    rejectButton: {
        padding: "8px 20px",
        background: "#dc3545",
        color: "#fff",
        border: "none",
        borderRadius: 6,
        cursor: "pointer",
        fontWeight: 600,
        fontSize: 14,
    },
    emptyState: {
        textAlign: "center",
        marginTop: 60,
    },
    loadingSpinner: {
        width: 32,
        height: 32,
        border: "3px solid #e0e0e0",
        borderTopColor: "#007bff",
        borderRadius: "50%",
        animation: "spin 1s linear infinite",
    },
    errorBox: {
        textAlign: "center",
        padding: 24,
        border: "1px solid #f5c6cb",
        borderRadius: 8,
        background: "#f8d7da",
    },
    retryButton: {
        marginTop: 12,
        padding: "8px 16px",
        background: "#6c757d",
        color: "#fff",
        border: "none",
        borderRadius: 6,
        cursor: "pointer",
        fontSize: 14,
    },
};
