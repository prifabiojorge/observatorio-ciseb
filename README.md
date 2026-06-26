# Observatório CISEB

Sistema de monitoramento em tempo real que captura, cura e entrega conteúdos de 6 famílias de fontes classificados pelos 6 pilares CISEB.

## Fases

| Fase | Status |
|------|--------|
| F0 — Fundação | ✅ CHECKPOINT F0.1 completo (6/6) |
| F1 — Bootstrap | 🔄 Em andamento |
| F2 — Coleta Real | ⬜ Pendente |
| F3 — LLM + Score | ⬜ Pendente |
| F4 — Entrega | ⬜ Pendente |
| F5 — Operação | ⬜ Pendente |

## Stack

- **Banco**: Supabase (Postgres 15 + pgvector)
- **Web/API**: Next.js 14 (Vercel)
- **Worker**: Python 3.11 + FastAPI + Celery (Render)
- **LLM**: DeepSeek API
- **Mensageria**: Telegram Bot

## Estrutura

```
apps/
├── web/          # Next.js 14 (Vercel)
└── worker/       # Python 3.11 (Render)
supabase/
└── migrations/   # SQL migrations
memoria/          # Documentação e memória da IA
```
