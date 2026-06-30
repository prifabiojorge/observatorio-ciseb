# Decisões Tomadas — NÃO REABRIR
### Registro imutável · Observatório CISEB

---

> ⚠️ **ESTAS DECISÕES FORAM FECHADAS PELO PROFESSOR FÁBIO JORGE.**
> Nenhuma IA pode alterá-las sem autorização explícita.

---

## As 8 decisões finais

| # | Decisão | Valor definido | Implicações diretas |
|---|---------|----------------|---------------------|
| 1 | **Orçamento LLM** | DeepSeek (`deepseek-chat` / `deepseek-reasoner`) | Custo ~US$ 0,27/M input, US$ 1,10/M output. API OpenAI-compatible. |
| 2 | **Revisor Humano** | Fábio Jorge (professor formador, único) | SLA de revisão: até 24h. Notificação por Telegram. |
| 3 | **Canal de entrega** | Telegram @fabiojorgebr / +55 91 985140988 | Apenas Telegram. Sem WhatsApp no MVP. |
| 4 | **Hospedagem** | Supabase (DB) + Vercel (cron+dashboard) + Render (worker) | Stack 100% free-tier inicial. |
| 5 | **Fontes prioritárias** | Nenhuma pré-definida | Coletor padrão cobre 6 famílias; Fábio ajusta após 2 semanas. |
| 6 | **Política de retenção** | Ignorada no MVP | Soft-delete após 90 dias (delete lógico, sem purge). |
| 7 | **Frequência newsletter** | Diária (início) → reavaliar após 30 dias | Digest enviado às 7h BRT, dias úteis. |
| 8 | **Definição de "replicável"** | Híbrido: código aberto + plano de aula em PDF + vídeo tutorial | Qualquer um dos três basta; tag `replicable=true`. |

---

## Decisões derivadas (tomadas pelo ciclo de 5 personas)

| Decisão | Persona | Justificativa |
|---------|---------|---------------|
| RLS habilitada desde migração 001 | Guardião | Zero tolerância a acesso não autorizado |
| `service_role_key` NUNCA na Vercel | Guardião | Reduz superfície de ataque |
| Telegram usa `chat_id` numérico | Guardião | Não logar telefone pessoal |
| LLM nunca recebe dado pessoal | Guardião | Apenas texto de artigos públicos |
| Máx 5 alertas Telegram/dia | Advogado do Usuário | Evitar fadiga de notificação |
| Dashboard é 1 tela, sem filtros | Advogado do Usuário | 10-15 min/dia para Fábio |
| 4 KPIs apenas no MVP | Advogado do Usuário | Mais que isso vira ruído |
| Fila via pgmq, NÃO Redis | Arquiteto | 1 componente a menos para operar |
| Embeddings BGE-M3 (1024 dims) | Arquiteto | Multilíngue PT+EN+ES |
| Score 0-100 com 6 dimensões ponderadas | Arquiteto | Fórmula auditável e ajustável |

---

> **Registrado em**: 2026-06-25
> **Fonte**: Plano_Observatorio_CISEB_v2.md, §0.4 e ciclo de personas
