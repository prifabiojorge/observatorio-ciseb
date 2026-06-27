# Guia: Configuração do Sentry em Produção

## Para: professor Fábio Jorge
## De: Agente do Harness
## Data: 2026-06-27
## Tempo estimado: 20 minutos

---

## 0. Por que isto importa

Hoje, se um erro acontecer em produção (ex: o `/run` falha no Render, ou `/api/findings/decide` quebra na Vercel), o erro aparece **apenas no log do dashboard** — você precisa abrir o Render/Vercel e procurar manualmente. Se não olhar, o erro fica silencioso.

Com o Sentry (que já está integrado no código, falta só a conta), você passa a receber:
- **Email** quando um erro novo acontece
- **Agrupamento** de erros repetidos (não spamma)
- **Stack trace** completo com linha exata do código
- **Performance monitoring** (qual endpoint está lento)
- **Release tracking** (qual deploy introduziu o bug)

**Plano gratuito**: 5.000 eventos/mês + 50 replays — suficiente para o observatório.

---

## 1. Criar conta no Sentry (3 min)

1. Acesse: https://sentry.io/signup/
2. Clique em **"Sign up for free"**
3. Escolha **"Continue with GitHub"** (mais fácil — usa sua conta GitHub)
4. Autorize o Sentry a acessar seu perfil GitHub
5. Preencha:
   - **Name**: Fábio Jorge
   - **Role**: Developer
   - **Company**: CISEB (ou UFAM)
6. Clique em **"Continue"**

---

## 2. Criar organização (1 min)

1. Na tela "Create Organization":
   - **Name**: `observatorio-ciseb`
   - **Plan**: Free (5k events/month)
   - **Region**: US (mesma região do Supabase)
2. Clique em **"Create Organization"**

---

## 3. Criar projeto para o Web (Next.js) (3 min)

1. Na tela "Create Project":
   - **Platform**: escolha **Next.js**
   - **Project Name**: `observatorio-web`
   - **Set Alert Rules**: deixe padrão (email on new issue)
2. Clique em **"Create Project"**
3. **IMPORTANTE**: você verá uma tela com o **DSN** (Data Source Name).
   Tem formato:
   ```
   https://<chave-secreta>@o<org-id>.ingest.sentry.io/<project-id>
   ```
4. **Copie este DSN** — você vai precisar em 2 lugares

---

## 4. Criar projeto para o Worker (Python) (2 min)

1. No menu lateral do Sentry, clique em **"Projects"**
2. Clique em **"Create Project"** (canto superior direito)
3. **Platform**: escolha **Python** (ou FastAPI)
4. **Project Name**: `observatorio-worker`
5. Clique em **"Create Project"**
6. Copie o **DSN** deste projeto também (será parecido, mas com project-id diferente)

> **Dica**: se você quer todos os erros no mesmo painel, pode usar o MESMO DSN para web e worker. Sentry separa por `environment` (production/development). Mas criar projetos separados é mais organizado.

---

## 5. Configurar variáveis no Render (Worker Python) (3 min)

1. Acesse: https://dashboard.render.com/web → clique em `observatorio-ciseb`
2. Menu lateral: **Environment**
3. Adicione/atualize:

| Key | Value |
|-----|-------|
| `SENTRY_DSN` | *(cole o DSN do projeto Python — passo 4)* |

4. Clique em **"Save Changes"**
5. Render pergunta se quer redeploy → **"Yes, deploy"**

---

## 6. Configurar variáveis na Vercel (Web Next.js) (3 min)

1. Acesse: https://vercel.com/observatorio-ciseb → **Settings** → **Environment Variables**
2. Adicione (marque "Production" e "Preview"):

| Key | Value |
|-----|-------|
| `SENTRY_DSN_WEB` | *(cole o DSN do projeto Next.js — passo 3)* |
| `NEXT_PUBLIC_SENTRY_DSN` | *(MESMO DSN do passo acima — este é público, vai pro browser)* |
| `SENTRY_ORG` | `observatorio-ciseb` *(nome da org que você criou no passo 2)* |
| `SENTRY_PROJECT` | `observatorio-web` *(nome do projeto criado no passo 3)* |

> **Sobre o `SENTRY_AUTH_TOKEN`**: opcional — só é necessário para upload de source maps no build. Para MVP, pode pular. Source maps ajudam a debugar, mas não são obrigatórios.

3. Clique em **"Save"** para cada variável
4. **Trigger redeploy**: Deployments → clique no último → "Redeploy"

---

## 7. Validar que está funcionando (3 min)

### 7.1 Validar Worker (Render)

```bash
# Disparar /run com auth (vai rodar pipeline e pode gerar erro se algo falhar)
curl -X POST -H "Authorization: Bearer $CRON_SECRET" https://observatorio-ciseb.onrender.com/run
```

Acesse: https://sentry.io → organização `observatorio-ciseb` → projeto `observatorio-worker`

Se houver erros durante o pipeline, eles devem aparecer aqui em até 30 segundos.

### 7.2 Validar Web (Vercel)

Acesse: https://observatorio-ciseb.vercel.app/dashboard

Tente aprovar/rejeitar um finding. Se houver erro, deve chegar no Sentry.

Acesse: https://sentry.io → organização `observatorio-ciseb` → projeto `observatorio-web`

### 7.3 Forçar um erro de teste (opcional)

Se quiser confirmar que Sentry está capturando, force um erro:

```bash
# No Sentry (browser), abra o console do dashboard e digite:
# (após logar)
throw new Error("Teste Sentry - Fase 7");
```

Deve aparecer no Sentry em < 30 segundos com stack trace.

---

## 8. Configurar alertas (2 min)

Por padrão, Sentry envia email quando:
- Novo erro acontece
- Erro resolvido reaparece

Para ajustar:

1. Sentry → Settings → Notifications
2. Configure seu email
3. (Opcional) Configure Slack/Discord se tiver

Para o observatório, recomendo:
- ✅ Email on new issue
- ✅ Email on regression (erro resolvido volta)
- ❌ Email on every event (seria spam)

---

## 9. O que esperar nos primeiros dias

Após configurar, você verá:

1. **"No events yet"** nos primeiros dias se tudo estiver funcionando bem
2. Eventos começam a aparecer quando:
   - Cron GitHub Actions falha (ex: Render em cold start)
   - LLM (DeepSeek) retorna JSON inválido
   - Rate limiting do GitHub/Scholar é disparado
   - Supabase Auth expira sessão

Isto é **normal** — Sentry é para capturar quando algo dá errado, não quando dá certo.

---

## 10. Custo e limites

| Plano | Eventos/mês | Replays/mês | Preço |
|-------|-------------|-------------|-------|
| **Free** | 5.000 | 50 | R$ 0 |
| Team | 50.000 | 500 | US$ 26/mês |

Para o observatório (50-300 findings/dia, ~5 endpoints), o plano free é mais que suficiente. Se você começar a ver "quota exceeded", considere aumentar sampling rate (de 0.2 para 0.1) em `sentry.server.config.ts`.

---

## 11. Troubleshooting

### "Não vejo eventos no Sentry"

**Causa provável**: DSN não configurado ou errado.

**Verificar**:
```bash
# Render — ver logs do worker
# Deve aparecer: "[sentry] SDK inicializado com sucesso"
# Se aparecer warning, DSN está faltando.

# Vercel — ver logs da Function
# Vercel Dashboard → projeto → Logs
```

### "Erros estão chegando mas sem stack trace"

**Causa**: source maps não estão sendo enviados.

**Solução** (opcional): configurar `SENTRY_AUTH_TOKEN`:
1. Sentry → Settings → Auth Tokens → "Create new token"
2. Permissões: `project:releases` e `project:write`
3. Vercel → Settings → Environment Variables → `SENTRY_AUTH_TOKEN`

### "Quota excedida"

**Solução**: reduzir sampling rate:
- `apps/web/sentry.server.config.ts`: mudar `tracesSampleRate` de `0.2` para `0.1`
- `apps/worker/src/sentry_init.py`: mudar `traces_sample_rate` de `0.2` para `0.1`

---

## 12. Após configurar — me avise!

Quando você terminar os passos 5 e 6 (configurar env vars no Render e Vercel), me mande uma mensagem "ok sentry configurado". Eu vou:

1. Disparar um `/run` de teste
2. Verificar se eventos chegam ao Sentry
3. Confirmar que o projeto chegou em **10/10 na auditoria Harness**

---

## Resumo executivo (1 linha por etapa)

1. Criar conta Sentry com GitHub → https://sentry.io/signup
2. Criar organização `observatorio-ciseb`
3. Criar projeto Next.js `observatorio-web` → copiar DSN
4. Criar projeto Python `observatorio-worker` → copiar DSN
5. Render → Environment → adicionar `SENTRY_DSN` (DSN Python)
6. Vercel → Settings → Environment Variables → adicionar `SENTRY_DSN_WEB`, `NEXT_PUBLIC_SENTRY_DSN`, `SENTRY_ORG`, `SENTRY_PROJECT`
7. Redeploy Render + Vercel
8. Validar em https://sentry.io

**Total**: ~20 minutos. Após isto, projeto está em 10/10.
