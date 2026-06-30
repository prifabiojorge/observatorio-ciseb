# Plano de Execução — Observatório CISEB
## Versão 1.0 · Para execução por IA autônoma · 2026-06-27

> **DOCUMENTO CANÔNICO.** Esta IA (executora) deve ler este arquivo do início ao fim antes de qualquer ação. Cada passo é auto-contido, cada comando é copy-paste, cada checkpoint tem critério objetivo. Se um checkpoint falhar, **PARE** e reporte — não tente contornar.

---

## 0. Como ler este documento (leia ANTES de executar)

### 0.1 Convenções tipográficas

| Convenção | Significado |
|-----------|-------------|
| `monospaced` | Comando de terminal, nome de arquivo, chave de config |
| **negrito** | Campo obrigatório, decisão tomada, palavra-chave de checkpoint |
| *itálico* | Variável a substituir pelo valor real |
| > citação | Aviso, nota de segurança, rascunho de prompt |
| ✅ / ❌ / ⚠️ | Aprovado / Bloqueante / Atenção |
| 🔴 / 🟠 / 🟡 / 🟢 | Crítica / Alta / Média / Baixa severidade |

### 0.2 Princípio anti-alucinação

Antes de executar qualquer passo, a IA executora deve se perguntar:
1. **Tenho todos os inputs listados na seção "Pré-requisitos"?** Se não, PARAR e pedir.
2. **O resultado esperado está definido objetivamente?** Se não, PARAR.
3. **Existe um comando de verificação?** Se não, PARAR.
4. **Estou criando algo que não está no plano?** Se sim, **NÃO FAÇA**.

### 0.3 Estrutura de cada passo

```
### Passo X.Y — Título
**Persona**: Arquiteto / Guardião / Orquestrador / Advogado / Harness
**Arquivos**: caminho/para/arquivo.ext
**Pré-requisitos**: ...
**Ação**: comando ou código copy-paste
**Verificação**: comando para validar
**Em caso de falha**: o que fazer
```

### 0.4 Estado de partida (snapshot auditado em 2026-06-27)

- **Commit atual**: `a7fc34f` (F4.1 concluída)
- **Branch**: `main`
- **Patch pronto**: `0001-fase-5-seguranca-testes-auth-cron.patch` (2 commits: `819da65` + `bdb2e54`)
- **Testes**: 37/40 passam (3 falham por falta do patch #1 — esperado)
- **Lógica**: ✅ válida (hashing, scoring, parser, dedup)
- **Memória**: ✅ schema correto, RLS impecável, pgmq definido mas não usado
- **Motor**: ✅ funcional, com gaps documentados (sem retry, sem transacionalidade)

### 0.5 Gaps identificados na auditoria (corrigidos no Plano)

| # | Gap | Severidade | Corrigido no Passo |
|---|-----|------------|-------------------|
| G1 | `CRON_SECRET` com fallback hardcoded em 3 arquivos | 🔴 Crítica | 3.1 |
| G2 | Rotas `/api/findings/*` sem autenticação | 🔴 Crítica | 3.2 + 5.x |
| G3 | Alerta Telegram usa `confidence*100` em vez de `score_composite` | 🔴 Crítica | 3.3 |
| G4 | Zero testes automatizados | 🟠 Alta | 4.x |
| G5 | Dashboard sem auth real (apenas token client-side) | 🟠 Alta | 5.x |
| G6 | Cron de coleta removido (Vercel Hobby limita 1/dia) | 🟠 Alta | 6.1 |
| G7 | `dim_alignment` não é truncado individualmente (pode exceder 100) | 🟡 Média | 7.1 |
| G8 | `scholar.py` sem rate limiting entre queries (risco de ban) | 🟡 Média | 7.2 |
| G9 | Sem retry para findings `status='new'` stale (>24h sem enrich) | 🟡 Média | 7.3 |
| G10 | `pgmq` definido mas nunca usado (fila órfã) | 🟢 Baixa | 7.4 (opcional) |
| G11 | `print()` em vez de logging estruturado | 🟡 Média | 7.5 |
| G12 | CRLF line endings no zip (quebra diff e shells Linux) | 🟠 Alta | 2.1 |

---

## FASE 1 — Pré-requisitos (ANTES de tudo)

### ✅ CHECKPOINT F1.0 — Ambiente de execução

**Persona**: Harness
**Pré-requisitos**: acesso a terminal bash com git, python 3.11+, node 20+, npm.

**Ação** — verifique cada item:

```bash
# 1. Git instalado
git --version  # Esperado: git version 2.40+

# 2. Python 3.11+ (necessário para o worker)
python3 --version  # Esperado: Python 3.11+

# 3. Node 20+ (necessário para web)
node --version  # Esperado: v20+

# 4. npm
npm --version  # Esperado: 10+

# 5. openssl (para gerar CRON_SECRET)
openssl version  # Esperado: OpenSSL 3.0+

# 6. Acesso ao repositório local
cd /caminho/do/observatorio-ciseb
git status  # Esperado: "On branch main" + "nothing to commit"
```

**Verificação**: todos os 6 comandos executam sem erro.

**Em caso de falha**: instalar a ferramenta faltante antes de prosseguir.

---

### ✅ CHECKPOINT F1.1 — Credenciais e contas

**Persona**: Guardião
**Pré-requisitos**: o professor Fábio Jorge deve ter configurado previamente:

| Serviço | Conta | Como verificar |
|---------|-------|----------------|
| GitHub | repo `prifabiojorge/observatorio-ciseb` | `git remote -v` |
| Supabase | projeto `yefudgudlpjctmdjkkio` | Dashboard Supabase acessível |
| Vercel | projeto `observatorio-ciseb` | Dashboard Vercel acessível |
| Render | service `observatorio-ciseb` | Dashboard Render acessível |
| DeepSeek | API key válida + US$ 5 crédito | `curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" https://api.deepseek.com/v1/models` |
| Telegram | bot + chat_id do Fábio | Enviar msg de teste ao bot |
| HuggingFace | token HF (free tier) | `curl -H "Authorization: Bearer $HF_API_KEY" https://huggingface.co/api/whoami-v2` |

**Verificação**: todos os 7 serviços respondem.

**Em caso de falha**: PARAR. Sem estas contas, o deploy é impossível.

---

### ✅ CHECKPOINT F1.2 — Snapshot do estado atual

**Persona**: Harness
**Ação**: registre o ponto de partida para rollback.

```bash
cd /caminho/do/observatorio-ciseb

# 1. Backup do estado atual
git stash push -m "backup-pre-fase5-$(date +%Y%m%d)" 2>/dev/null || echo "nada para stashar"

# 2. Registre o commit atual
git log --oneline -1 > /tmp/obs-commit-antes.txt
cat /tmp/obs-commit-antes.txt
# Esperado: a7fc34f docs: CHECKPOINT F4.1 ATINGIDO — dashboard, alertas, digest

# 3. Crie branch de trabalho
git checkout -b fix/fase5-execucao
git log --oneline -1
```

**Verificação**: branch `fix/fase5-execucao` criada, HEAD em `a7fc34f`.

**Em caso de falha**: se `git stash` falhar (nada para stashar), ignore. Se `git checkout -b` falhar, há alterações não commitadas — faça commit ou reset antes.

---

## FASE 2 — Sanitização do código (CRLF + limpeza)

### Passo 2.1 — Converter CRLF para LF

**Persona**: Harness
**Arquivos**: todos os `.py`, `.ts`, `.tsx`, `.sql`, `.md`, `.yml`, `.json`, `.toml`
**Pré-requisitos**: F1.2 concluído.

**Contexto**: o zip original veio com line endings CRLF (Windows), que poluem diffs e podem quebrar shells Linux. Precisamos normalizar para LF antes de aplicar patches.

**Ação**:

```bash
cd /caminho/do/observatorio-ciseb

# 1. Criar .gitattributes para prevenir reincidência
cat > .gitattributes << 'EOF'
* text=auto eol=lf

# Arquivos de texto sempre LF
*.py text eol=lf
*.ts text eol=lf
*.tsx text eol=lf
*.js text eol=lf
*.mjs text eol=lf
*.sql text eol=lf
*.md text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
*.toml text eol=lf
*.sh text eol=lf
*.env text eol=lf
*.env.example text eol=lf

# Arquivos binários
*.pdf binary
*.png binary
*.jpg binary
*.gif binary
*.ico binary
EOF

# 2. Converter CRLF → LF em todos os arquivos de texto
find . -type f \( \
    -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.mjs" \
    -o -name "*.sql" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" \
    -o -name "*.json" -o -name "*.toml" -o -name "*.sh" \
    -o -name ".env" -o -name ".env.example" -o -name ".gitignore" -o -name ".gitattributes" \
  \) -not -path "*/.git/*" -not -path "*/node_modules/*" -not -path "*/.venv/*" \
  -exec sed -i 's/\r$//' {} \;

# 3. Renormalizar com git
git add --renormalize .

# 4. Commit
git add -A
git commit -m "chore: normalizar line endings para LF + adicionar .gitattributes"
```

**Verificação**:

```bash
# Não deve haver arquivos com CRLF
find . -type f -name "*.py" -not -path "*/.git/*" -not -path "*/.venv/*" \
    -exec file {} \; | grep -i crlf | head -5
# Esperado: vazio (nenhum arquivo com CRLF)

# Diff stat deve estar limpo agora
git diff --stat HEAD~1
# Esperado: apenas .gitattributes novo + arquivos renormalizados
```

**Em caso de falha**: se `sed` não estiver disponível (macOS usa BSD sed), usar `perl -pi -e 's/\r\n/\n/g'` no lugar.

---

### Passo 2.2 — Remover artefatos que não devem ir para produção

**Persona**: Guardião
**Arquivos**: `repomix-output.xml`, `.env` (se presente no working tree)

**Ação**:

```bash
cd /caminho/do/observatorio-ciseb

# 1. Remover repomix-output.xml (dump para IA, não deve ir para produção)
rm -f repomix-output.xml

# 2. Garantir que .env NÃO está tracked
git ls-files | grep -E "^\.env$" && echo "⚠️ .env está tracked! Removendo..." && git rm --cached .env || echo "✅ .env não está tracked"

# 3. Verificar .gitignore inclui .env
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore

# 4. Commit
git add -A
git commit -m "chore: remover repomix-output.xml e garantir .env no .gitignore" || echo "nada para commitar"
```

**Verificação**:

```bash
git ls-files | grep -E "repomix-output|^\.env$"
# Esperado: vazio
```

---

## FASE 3 — Aplicar correções críticas de segurança (Patch #1, #2, #4)

### Passo 3.1 — Aplicar patch consolidado

**Persona**: Harness
**Pré-requisitos**: FASE 2 concluída.
**Arquivo de patch**: `/home/z/my-project/download/0001-fase-5-seguranca-testes-auth-cron.patch`

> ⚠️ Este patch contém 2 commits: `819da65` (correções F4) e `bdb2e54` (Fase 5: testes + Supabase Auth + cron). Aplicar com `git am` preserva a história.

**Ação**:

```bash
cd /caminho/do/observatorio-ciseb

# 1. Copiar o patch para o diretório do repo
cp /home/z/my-project/download/0001-fase-5-seguranca-testes-auth-cron.patch /tmp/

# 2. Aplicar com git am
git am < /tmp/0001-fase-5-seguranca-testes-auth-cron.patch

# 3. Verificar
git log --oneline -5
```

**Verificação**:

```bash
# Esperado: ver os 2 commits novos no topo
git log --oneline -3
# bdb2e54 feat(fase-5): testes, Supabase Auth, GitHub Actions cron
# 819da65 fix(seguranca): correções críticas F4 — auth fail-closed, score_composite real
# a7fc34f docs: CHECKPOINT F4.1 ATINGIDO — dashboard, alertas, digest

# Confirmar que fallback hardcoded foi removido
grep -r "observatorio-ciseb-f1-2026" apps/ 2>/dev/null
# Esperado: vazio
```

**Em caso de conflito**:

```bash
# Se git am falhar com conflito:
git am --abort
git am --3way < /tmp/0001-fase-5-seguranca-testes-auth-cron.patch

# Resolver conflitos manualmente (marcar com <<< === >>>)
# Priorizar sempre a versão do patch (código novo)
# Após resolver:
git add <arquivos-resolvidos>
git am --continue
```

---

### Passo 3.2 — Validar testes automatizados

**Persona**: Harness
**Pré-requisitos**: Passo 3.1 concluído.

**Ação**:

```bash
cd /caminho/do/observatorio-ciseb/apps/worker

# 1. Criar venv se não existir
python3 -m venv .venv
source .venv/bin/activate

# 2. Instalar dependências
pip install -e ".[dev]"
pip install pytest-asyncio scholarly

# 3. Rodar testes do worker (Python)
PYTHONPATH=src python -m pytest tests/ -v
```

**Verificação**:

```bash
# Esperado: 40 passed, 0 failed
PYTHONPATH=src python -m pytest tests/ -q | tail -3
# 40 passed in 2.0s
```

**Em caso de falha**:

- Se `ModuleNotFoundError: No module named 'scholarly'`: `pip install scholarly`
- Se `ModuleNotFoundError: No module named 'pytest-asyncio'`: `pip install pytest-asyncio`
- Se `ImportError: cannot import name 'createBrowserClient'`: instalar `pip install` do `@supabase/ssr` no web (não afeta worker)
- Se 3 testes `test_verify_cron` falharem: o patch #1 NÃO foi aplicado corretamente. Voltar ao Passo 3.1.

---

### ✅ CHECKPOINT F3.1 — Patch aplicado e testes passando

**Critério objetivo**:
1. `git log --oneline -1` mostra commit `bdb2e54` no topo
2. `grep -r "observatorio-ciseb-f1-2026" apps/` retorna vazio
3. `PYTHONPATH=src python -m pytest tests/ -q` mostra `40 passed`
4. `ls apps/web/middleware.ts apps/web/lib/supabase-browser.ts apps/web/app/login/page.tsx` retorna os 3 arquivos
5. `ls .github/workflows/cron-coleta.yml` retorna o arquivo
6. `ls supabase/migrations/004_rls_auth.sql` retorna o arquivo

**Se falhar**: NÃO AVANCE. Voltar ao Passo 3.1 e diagnosticar.

---

## FASE 4 — Configurar Supabase Auth

### Passo 4.1 — Criar conta do Fábio no Supabase Auth

**Persona**: Guardião
**Pré-requisitos**: acesso ao Dashboard Supabase.

**Ação (manual, no Dashboard)**:

1. Acessar https://supabase.com/dashboard/project/yefudgudlpjctmdjkkio/auth/users
2. Clicar em **"Add user"** → **"Create new user"**
3. Preencher:
   - Email: `fabio.jorge@ciseb.edu.br` (ou email real do Fábio)
   - Password: deixar vazio (magic link) OU definir senha
   - **Auto Confirm User**: ✅ marcar (pula verificação por email)
4. Clicar em **"Create user"**
5. **Copiar o `User UID`** exibido (UUID v4, formato `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

**Verificação**:

```bash
# O UID copiado deve ter este formato (36 chars, 4 hífens):
echo "<UID_COPIADO>" | grep -E "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
# Esperado: ecoa o UID de volta (sem erro)
```

**Salvar o UID**: anotar em local seguro. Será usado no Passo 4.3.

---

### Passo 4.2 — Configurar URLs de redirect no Supabase Auth

**Persona**: Guardião
**Ação (manual, no Dashboard)**:

1. Acessar https://supabase.com/dashboard/project/yefudgudlpjctmdjkkio/auth/url-configuration
2. **Site URL**: `https://observatorio-ciseb.vercel.app`
3. **Redirect URLs** (adicionar uma por linha):
   - `https://observatorio-ciseb.vercel.app/auth/callback`
   - `http://localhost:3000/auth/callback` (para dev local)
4. Clicar em **"Save"**

**Verificação**: ao recarregar a página, as URLs aparecem salvas.

---

### Passo 4.3 — Aplicar migração 004_rls_auth.sql

**Persona**: Arquiteto
**Pré-requisitos**: UID do Fábio (Passo 4.1).

**Ação**:

```bash
cd /caminho/do/observatorio-ciseb

# 1. Substituir placeholder <FABIO_AUTH_UID> pelo UID real
# Use o UID copiado no Passo 4.1
FABIO_UID="<cole-o-uid-aqui>"

sed -i "s/<FABIO_AUTH_UID>/${FABIO_UID}/g" supabase/migrations/004_rls_auth.sql

# 2. Verificar substituição
grep "reviewer_auth_uid" supabase/migrations/004_rls_auth.sql
# Esperado: INSERT INTO app_config (key, value) VALUES ('reviewer_auth_uid', '<UID-real>')
```

**Ação (manual, no Dashboard Supabase)**:

1. Acessar https://supabase.com/dashboard/project/yefudgudlpjctmdjkkio/sql/new
2. Abrir o arquivo `supabase/migrations/004_rls_auth.sql` localmente
3. Copiar TODO o conteúdo
4. Colar no SQL Editor do Supabase
5. Clicar em **"Run"** (ou Ctrl+Enter)

**Verificação**:

```sql
-- No SQL Editor do Supabase, executar:

-- 1. Função is_reviewer existe?
SELECT proname FROM pg_proc WHERE proname = 'is_reviewer';
-- Esperado: 1 linha

-- 2. Policies authenticated criadas?
SELECT tablename, policyname, roles
FROM pg_policies
WHERE schemaname = 'public' AND roles @> ARRAY['authenticated']::name[]
ORDER BY tablename;
-- Esperado: ≥ 8 linhas (findings x2, scores, reviews x2, deliveries x2, sources, pillars)

-- 3. UID do Fábio salvo?
SELECT value FROM app_config WHERE key = 'reviewer_auth_uid';
-- Esperado: o UID copiado no Passo 4.1
```

**Em caso de falha**:

- Se `ERROR: function is_reviewer already exists`: a função já foi criada. Usar `CREATE OR REPLACE FUNCTION` (já é o que o script usa). Re-executar é seguro.
- Se `ERROR: policy already exists`: fazer `DROP POLICY IF EXISTS "<nome>" ON <tabela>` antes de re-executar. Ou executar linha por linha.

---

### ✅ CHECKPOINT F4.1 — Supabase Auth configurado

**Critério objetivo**:
1. Conta do Fábio aparece em Auth → Users com `Confirmed: yes`
2. `SELECT value FROM app_config WHERE key = 'reviewer_auth_uid'` retorna o UID
3. `SELECT count(*) FROM pg_policies WHERE roles @> ARRAY['authenticated']::name[]` retorna `≥ 8`

**Se falhar**: NÃO AVANCE. O dashboard não conseguirá ler findings sem RLS configurada.

---

## FASE 5 — Configurar variáveis de ambiente

### Passo 5.1 — Gerar novos segredos

**Persona**: Guardião
**Ação**:

```bash
# 1. Gerar novo CRON_SECRET (forte, 64 chars hex)
NEW_CRON_SECRET=$(openssl rand -hex 32)
echo "NOVO CRON_SECRET: ${NEW_CRON_SECRET}"

# 2. Gerar NEXT_PUBLIC_DASHBOARD_TOKEN (não é mais usado após Supabase Auth,
#    mas manter por compatibilidade)
NEW_DASHBOARD_TOKEN=$(openssl rand -hex 16)
echo "NOVO DASHBOARD_TOKEN: ${NEW_DASHBOARD_TOKEN}"

# 3. Salvar em local seguro (NÃO commitar)
cat > /tmp/obs-segredos-novos.txt << EOF
CRON_SECRET=${NEW_CRON_SECRET}
NEXT_PUBLIC_DASHBOARD_TOKEN=${NEW_DASHBOARD_TOKEN}
EOF
echo "Segredos salvos em /tmp/obs-segredos-novos.txt (NÃO commitar este arquivo)"
```

**Verificação**: `cat /tmp/obs-segredos-novos.txt` mostra os 2 valores.

---

### Passo 5.2 — Configurar variáveis no Render

**Persona**: Orquestrador
**Ação (manual, no Dashboard Render)**:

1. Acessar https://dashboard.render.com/web → clicar em `observatorio-ciseb`
2. No menu lateral: **Environment** → **Add Environment Variable**
3. Adicionar/atualizar:

| Key | Value |
|-----|-------|
| `CRON_SECRET` | *(valor de /tmp/obs-segredos-novos.txt)* |
| `SUPABASE_URL` | `https://yefudgudlpjctmdjkkio.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | *(manter o atual — worker precisa de write)* |
| `SUPABASE_ANON_KEY` | *(manter o atual)* |
| `DEEPSEEK_API_KEY` | *(manter o atual)* |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | `deepseek-chat` |
| `HF_API_KEY` | *(manter o atual)* |
| `TELEGRAM_BOT_TOKEN` | *(manter o atual)* |
| `TELEGRAM_CHAT_ID_FABIO` | `1158904776` |

4. Clicar em **"Save Changes"**
5. Render pergunta se quer fazer redeploy → **"Yes, deploy"**

**Verificação**:

```bash
# Após deploy (~2-3 min), testar health
curl -s https://observatorio-ciseb.onrender.com/health
# Esperado: {"status":"ok","service":"observatorio-ciseb-worker"}

# Testar /run SEM auth (deve dar 401)
curl -s -o /dev/null -w "%{http_code}" -X POST https://observatorio-ciseb.onrender.com/run
# Esperado: 401

# Testar /run COM auth (deve dar 200 e disparar pipeline)
CRON_SECRET=$(grep CRON_SECRET /tmp/obs-segredos-novos.txt | cut -d= -f2)
curl -s -X POST -H "Authorization: Bearer ${CRON_SECRET}" https://observatorio-ciseb.onrender.com/run
# Esperado: {"status":"ok","message":"Pipeline executado com sucesso"}
```

**Em caso de falha**:

- Se health retornar 502/503: Render Free tier pode estar em cold start. Aguardar 30s e tentar novamente.
- Se `/run` sem auth retornar 200: o deploy NÃO pegou a nova versão. Verificar se `CRON_SECRET` foi salvo corretamente.
- Se `/run` com auth retornar 500: ver logs em https://dashboard.render.com/web/srv-d8usrhurnols73flq750/logs

---

### Passo 5.3 — Configurar variáveis na Vercel

**Persona**: Orquestrador
**Ação (manual, no Dashboard Vercel)**:

1. Acessar https://vercel.com/observatorio-ciseb → **Settings** → **Environment Variables**
2. Adicionar/atualizar (marcar "Production" e "Preview" para todas):

| Key | Value |
|-----|-------|
| `CRON_SECRET` | *(mesmo valor do Render)* |
| `RENDER_RUN_URL` | `https://observatorio-ciseb.onrender.com/run` |
| `RENDER_DIGEST_URL` | `https://observatorio-ciseb.onrender.com/digest` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://yefudgudlpjctmdjkkio.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | *(anon key do Supabase)* |
| `NEXT_PUBLIC_DASHBOARD_TOKEN` | *(valor de /tmp/obs-segredos-novos.txt)* |

3. **REMOVER** (se existir): `SUPABASE_SERVICE_ROLE_KEY` — não é mais necessária na Vercel após Supabase Auth. RLS governa acesso.

4. Clicar em **"Save"** para cada variável.

**Verificação**:

```bash
# Trigger deploy manual na Vercel (push de qualquer commit, ou via Dashboard)
# Após deploy (~1-2 min):

# 1. Dashboard sem sessão deve redirecionar para /login
curl -s -o /dev/null -w "%{http_code}\n%{redirect_url}" https://observatorio-ciseb.vercel.app/dashboard
# Esperado: 307 + redirect para /login?redirect=/dashboard

# 2. API sem sessão deve dar 401
curl -s -o /dev/null -w "%{http_code}" https://observatorio-ciseb.vercel.app/api/findings/pending
# Esperado: 401

# 3. Página de login deve carregar
curl -s -o /dev/null -w "%{http_code}" https://observatorio-ciseb.vercel.app/login
# Esperado: 200
```

---

### Passo 5.4 — Configurar GitHub Secrets para cron

**Persona**: Orquestrador
**Ação (manual, no GitHub)**:

1. Acessar https://github.com/prifabiojorge/observatorio-ciseb/settings/secrets/actions
2. Clicar em **"New repository secret"** para cada:

| Name | Value |
|------|-------|
| `VERCEL_CRON_URL` | `https://observatorio-ciseb.vercel.app/api/cron/collect` |
| `CRON_SECRET` | *(mesmo valor do Render/Vercel)* |
| `RENDER_HEALTH_URL` | `https://observatorio-ciseb.onrender.com/health` |
| `TELEGRAM_BOT_TOKEN` | *(token do bot)* |
| `TELEGRAM_CHAT_ID` | `1158904776` |

**Verificação**:

```bash
# Disparar workflow manualmente
# Acessar: https://github.com/prifabiojorge/observatorio-ciseb/actions
# Workflow: "Cron Coleta Observatório" → "Run workflow" → "Run workflow"

# Após 2-3 min, verificar logs do workflow:
# - Step "Wake-up Render": deve mostrar "HTTP 200"
# - Step "Aguardar cold start": deve mostrar "Sleep 30s"
# - Step "Disparar coleta": deve mostrar "HTTP 200" + "Coleta disparada com sucesso"
```

---

### ✅ CHECKPOINT F5.1 — Variáveis configuradas e deploy validado

**Critério objetivo**:
1. `curl https://observatorio-ciseb.onrender.com/health` → 200
2. `curl -X POST https://observatorio-ciseb.onrender.com/run` (sem auth) → 401
3. `curl -X POST -H "Authorization: Bearer $CRON_SECRET" https://observatorio-ciseb.onrender.com/run` → 200
4. `curl https://observatorio-ciseb.vercel.app/dashboard` → 307 redirect para `/login`
5. `curl https://observatorio-ciseb.vercel.app/api/findings/pending` → 401
6. GitHub Actions workflow "Cron Coleta Observatório" executou com sucesso (green)

**Se falhar**: NÃO AVANCE. Verificar logs do serviço que falhou.

---

## FASE 6 — Deploy final e validação ponta-a-ponta

### Passo 6.1 — Merge do branch para main

**Persona**: Orquestrador
**Pré-requisitos**: F5.1 concluído.

**Ação**:

```bash
cd /caminho/do/observatorio-ciseb

# 1. Voltar para main
git checkout main

# 2. Merge do branch de trabalho
git merge fix/fase5-execucao --no-ff -m "merge: Fase 5 — segurança, testes, Supabase Auth, cron GitHub Actions"

# 3. Push para origin
git push origin main

# 4. Verificar
git log --oneline -5
```

**Verificação**: `git log --oneline -1` mostra o merge commit no topo.

---

### Passo 6.2 — Aguardar deploy automático

**Persona**: Harness
**Ação**: aguardar 3-5 minutos. Render e Vercel detectam o push e fazem redeploy.

**Verificação**:

```bash
# 1. Render deploy status
curl -s https://observatorio-ciseb.onrender.com/health
# Esperado: {"status":"ok",...}

# 2. Vercel deploy status
curl -s -o /dev/null -w "%{http_code}" https://observatorio-ciseb.vercel.app/login
# Esperado: 200
```

---

### Passo 6.3 — Validação ponta-a-ponta (teste de aceitação)

**Persona**: Advogado do Usuário
**Ação**: simular o fluxo completo do Fábio.

#### 6.3.1 — Login no dashboard

1. Abrir `https://observatorio-ciseb.vercel.app/login` no navegador
2. Digitar o email do Fábio (`fabio.jorge@ciseb.edu.br` ou o email cadastrado)
3. Clicar em **"Enviar link mágico"**
4. Verificar email do Fábio — deve ter chegado link do Supabase
5. Clicar no link → redireciona para `/dashboard`

**Verificação**: dashboard mostra "X achados pendentes de revisão" com cards.

#### 6.3.2 — Revisar um finding

1. No dashboard, clicar em **"✅ Aprovar"** em um finding
2. **Verificação imediata**: banner verde "✅ Aprovado" aparece
3. **Verificação no banco** (SQL Editor Supabase):

```sql
SELECT f.id, f.title, f.status, r.decision, r.reviewer_id, r.reviewed_at
FROM findings f
JOIN reviews r ON r.finding_id = f.id
ORDER BY r.reviewed_at DESC
LIMIT 1;
-- Esperado: 1 linha com status='reviewed', decision='approved', reviewer_id=<UID do Fábio>
```

#### 6.3.3 — Disparar coleta manualmente

```bash
CRON_SECRET=$(grep CRON_SECRET /tmp/obs-segredos-novos.txt | cut -d= -f2)
curl -s -X POST -H "Authorization: Bearer ${CRON_SECRET}" \
  https://observatorio-ciseb.onrender.com/run | jq .
# Esperado: {"status":"ok","message":"Pipeline executado com sucesso"}
```

#### 6.3.4 — Verificar alertas Telegram

Após a coleta, se houver findings com `score_composite >= 75`:

1. Verificar Telegram do Fábio — deve ter recebido cards com:
   - 🚨 **Alerta — score X/100** (X é o score_composite REAL, não confidence*100)
   - Título do finding
   - 📁 pilar (slug)
   - 📝 resumo
   - 💡 **Aplicação:** *(sugestão do LLM)*
   - 🔗 URL da fonte

2. **Verificação no banco**:

```sql
SELECT f.title, s.score_composite, d.sent_at
FROM deliveries d
JOIN findings f ON f.id = d.finding_id
JOIN scores s ON s.finding_id = f.id
WHERE d.channel = 'telegram'
ORDER BY d.sent_at DESC
LIMIT 5;
-- Esperado: linhas com score_composite >= 75
```

#### 6.3.5 — Verificar digest diário

```bash
# Disparar digest manualmente
CRON_SECRET=$(grep CRON_SECRET /tmp/obs-segredos-novos.txt | cut -d= -f2)
curl -s -X POST -H "Authorization: Bearer ${CRON_SECRET}" \
  https://observatorio-ciseb.onrender.com/digest | jq .
# Esperado: {"status":"ok","message":"Digest enviado com N achados"}

# Verificar Telegram do Fábio — deve ter recebido:
# 📬 Digest YYYY-MM-DD — N achados
# 1. [score] Título
#    🔗 URL
# 2. ...
```

---

### ✅ CHECKPOINT F6.1 — Sistema em produção validado

**Critério objetivo** (todos devem passar):
1. ✅ Login via magic link funciona
2. ✅ Dashboard lista findings pendentes (após login)
3. ✅ Aprovar/Rejeitar grava em `reviews` com `reviewer_id = <UID Fábio>`
4. ✅ Coleta manual via `/run` com auth retorna 200
5. ✅ Alertas Telegram recebidos com `score_composite` real (≥ 75)
6. ✅ Digest manual via `/digest` envia top 10 ao Telegram
7. ✅ GitHub Actions cron executou com sucesso (green)

**Se falhar**: ver logs do serviço específico. NÃO AVANÇAR para FASE 7 sem sistema estável.

---

## FASE 7 — Correções de gaps identificados (pós-deploy)

> Esta fase é **opcional mas recomendada**. Pode ser feita após o sistema estar estável em produção por alguns dias.

### Passo 7.1 — Corrigir bug `dim_alignment` não truncado

**Persona**: Arquiteto
**Severidade**: 🟡 Média
**Arquivo**: `apps/worker/src/llm/classifier.py`

**Problema**: `dim_alignment = int(alignment * 100)` pode exceder 100 se `confidence > 1.0` (anômala, mas possível em alucinação do LLM). Apenas `score_composite` é truncado.

**Ação**:

```python
# Em classifier.py, função compute_score, substituir:
dim_alignment = int(alignment * 100)

# Por:
dim_alignment = max(0, min(100, int(alignment * 100)))
```

**Verificação**:

```bash
cd /caminho/do/observatorio-ciseb/apps/worker
PYTHONPATH=src python -m pytest tests/test_classifier.py::TestComputeScore::test_score_sempre_entre_0_e_100 -v
# Esperado: PASSED (o teste foi escrito para documentar este bug — após correção, atualizar o teste)
```

**Atualizar o teste** (remover o "bug conhecido"):

```python
# Em test_classifier.py, função test_score_sempre_entre_0_e_100, substituir o docstring e asserts:
def test_score_sempre_entre_0_e_100(self):
    """Score composto E dim_alignment nunca devem sair do intervalo [0, 100]."""
    enriched = {
        "pillars": [{"slug": "ia", "confidence": 5.0}],
        "geo_br": True, "replicable": True, "practical_project": True,
        "audience": "basica", "_dim_novelty": 100,
    }
    sc = compute_score(enriched, {})
    assert 0 <= sc["score_composite"] <= 100
    assert 0 <= sc["dim_alignment"] <= 100  # agora sim, truncado
```

---

### Passo 7.2 — Adicionar rate limiting ao coletor Scholar

**Persona**: Arquiteto
**Severidade**: 🟡 Média
**Arquivo**: `apps/worker/src/collectors/scholar.py`

**Problema**: `scholarly` faz scraping do Google Scholar. Sem delay entre queries, pode levar a banimento por IP.

**Ação**: adicionar `asyncio.sleep(5)` entre queries (não entre publicações).

```python
# Em scholar.py, função collect, substituir o loop:
async def collect(self) -> list[RawFinding]:
    findings: list[RawFinding] = []
    for query in QUERIES:
        try:
            items = await self._search(query)
            findings.extend(items)
            # Rate limiting: 5s entre queries para evitar ban do Google Scholar
            await asyncio.sleep(5)
        except Exception as exc:
            print(f"[scholar] Erro na query '{query}': {exc}")
    return findings
```

**Verificação**:

```bash
cd /caminho/do/observatorio-ciseb/apps/worker
PYTHONPATH=src python -c "
import asyncio
from collectors.scholar import ScholarCollector
async def test():
    c = ScholarCollector()
    # Apenas verifica que carrega sem erro (não roda coleta real)
    assert c.source_slug == 'scholar'
    print('✅ Scholar import OK')
asyncio.run(test())
"
```

---

### Passo 7.3 — Adicionar retry para findings stale

**Persona**: Arquiteto
**Severidade**: 🟡 Média
**Arquivo**: `apps/worker/src/main.py`

**Problema**: se `enrich()` falha para um finding (ex: DeepSeek offline), ele fica `status='new'` para sempre. Não há reprocessamento.

**Ação**: modificar `run_enrich_and_score` para incluir findings `new` com mais de 1h de idade (não apenas os mais recentes).

```python
# Em main.py, função run_enrich_and_score, substituir a query:
new_findings = (
    supabase.table("findings").select("*").eq("status", "new")
    .order("collected_at", desc=False).limit(batch_size).execute().data
)

# Por:
# Busca findings new, priorizando os mais antigos (FIFO) — stale primeiro
from datetime import datetime, timezone, timedelta
stale_threshold = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

new_findings = (
    supabase.table("findings")
    .select("*")
    .eq("status", "new")
    .or_(f"collected_at.lte.{stale_threshold}")  # stale (>1h) primeiro
    .order("collected_at", desc=False)
    .limit(batch_size)
    .execute().data
)

# Se não há stale, pega os mais recentes
if not new_findings:
    new_findings = (
        supabase.table("findings").select("*").eq("status", "new")
        .order("collected_at", desc=False).limit(batch_size).execute().data
    )
```

**Verificação**:

```bash
cd /caminho/do/observatorio-ciseb/apps/worker
PYTHONPATH=src python -m pytest tests/ -q | tail -3
# Esperado: 40 passed (não deve quebrar testes existentes)
```

---

### Passo 7.4 — Implementar logging estruturado (substituir print)

**Persona**: Harness
**Severidade**: 🟡 Média
**Arquivo**: todos os `*.py` do worker

**Problema**: `print()` não é capturado por ferramentas de observabilidade (Sentry, Logflare).

**Ação**: substituir todos `print(` por `log.info(` / `log.warning(` / `log.error(`.

```python
# No topo de cada arquivo, já existe:
import logging
log = logging.getLogger(__name__)

# Substituir em main.py:
# print(f"[main] ...") → log.info("...")
# print(f"[main] Erro...") → log.error("...")
# print(f"[main] ⚠️ ...") → log.warning("...")

# Configurar logging no entry point (main.py, função main):
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

**Verificação**:

```bash
# Após deploy, logs do Render devem mostrar formato estruturado:
# 2026-06-27 12:00:00 [main] INFO: Observatório CISEB — Fase Coleta
# 2026-06-27 12:00:01 [main] INFO: Coletores ativos: 6
```

---

### Passo 7.5 — (Opcional) Usar pgmq para fila assíncrona

**Persona**: Arquiteto
**Severidade**: 🟢 Baixa (já funciona sem isto)
**Arquivos**: `apps/worker/src/main.py`, `supabase/migrations/002_pgmq.sql`

**Problema**: `pgmq` e a função `enqueue_finding` estão definidos mas NUNCA são usados. O pipeline é síncrono: coleta → enrich → score → alerta, tudo na mesma execução.

**Justificativa para NÃO implementar agora**: o sistema funciona em MVP síncrono. Migrar para fila adiciona complexidade (consumer loop, dead letter queue, monitoring) que não é necessária para 50-300 findings/dia.

**Quando implementar**: se o volume crescer para >1000 findings/dia, ou se DeepSeek ficar instável e precisar de retry assíncrono.

**Ação (referência futura)**:

1. Após `insert_finding` em `main.py`, chamar `enqueue_finding(finding_id)`:
   ```python
   supabase.rpc('enqueue_finding', {'finding_id': fid}).execute()
   ```

2. Criar consumer separado (`apps/worker/src/consumer.py`) que faz polling:
   ```python
   while True:
       msgs = supabase.rpc('pgmq_read', {
           'queue_name': 'findings_queue',
           'vt': 60,
           'qty': 5
       }).execute().data
       for msg in msgs:
           process_finding(msg['message']['finding_id'])
           supabase.rpc('pgmq_delete', {
               'queue_name': 'findings_queue',
               'msg_id': msg['msg_id']
           }).execute()
       asyncio.sleep(10)
   ```

3. Deployar como serviço separado no Render.

---

### ✅ CHECKPOINT F7.1 — Correções opcionais aplicadas

**Critério objetivo** (apenas se FASE 7 foi executada):
1. `test_classifier.py::test_score_sempre_entre_0_e_100` passa com `dim_alignment <= 100`
2. `scholar.py` tem `asyncio.sleep(5)` entre queries
3. `main.py` busca findings stale (>1h) primeiro
4. Logs do Render mostram formato `YYYY-MM-DD HH:MM:SS [module] LEVEL: message`

---

## FASE 8 — Documentação e handoff

### Passo 8.1 — Atualizar memoria/08_LOG_EXECUCAO.md

**Persona**: Harness
**Ação**: adicionar entrada no log de execução.

```bash
cd /caminho/do/observatorio-ciseb

cat >> memoria/08_LOG_EXECUCAO.md << 'EOF'

### 2026-06-27 — Fase 5: Segurança + Testes + Auth + Cron

```
[2026-06-27 HH:MM] [HARNESS] Patch consolidado aplicado: 819da65 + bdb2e54
[2026-06-27 HH:MM] [GUARDIÃO] CRON_SECRET fail-closed em 3 arquivos
[2026-06-27 HH:MM] [GUARDIÃO] Rotas /api/findings/* com Supabase Auth
[2026-06-27 HH:MM] [ARQUITETO] Score do alerta Telegram usa score_composite real
[2026-06-27 HH:MM] [HARNESS] 40 testes pytest passando
[2026-06-27 HH:MM] [ARQUITETO] Supabase Auth + RLS 004 aplicada
[2026-06-27 HH:MM] [ORQUESTRADOR] GitHub Actions cron 3x/dia configurado
[2026-06-27 HH:MM] [ADVOGADO] Login magic link + Google funcionando
[2026-06-27 HH:MM] [HARNESS] 🎉 CHECKPOINT F5.1 ATINGIDO — Sistema em produção com auth real
```

EOF

git add memoria/08_LOG_EXECUCAO.md
git commit -m "docs: log Fase 5 — segurança, testes, auth, cron"
git push origin main
```

---

### Passo 8.2 — Atualizar README.md

**Persona**: Advogado do Usuário
**Ação**: refletir o novo estado do projeto.

```bash
cd /caminho/do/observatorio-ciseb

cat > README.md << 'EOF'
# Observatório CISEB

Sistema de monitoramento em tempo real que captura, cura e entrega conteúdos de 6 famílias de fontes classificados pelos 6 pilares CISEB.

## Fases

| Fase | Status |
|------|--------|
| F0 — Fundação | ✅ COMPLETO |
| F1 — Bootstrap | ✅ COMPLETO |
| F2 — Coleta Real | ✅ COMPLETO (123 findings, 4 famílias) |
| F3 — LLM + Score | ✅ COMPLETO (30 scored, custo US$0.015) |
| F4 — Entrega | ✅ COMPLETO (dashboard, alertas, digest) |
| F5 — Segurança + Auth | ✅ COMPLETO (Supabase Auth, 40 testes, cron GitHub Actions) |

## Stack

- **Banco**: Supabase (Postgres 15 + pgvector + pgmq)
- **Web/API**: Next.js 14 (Vercel) — com Supabase Auth
- **Worker**: Python 3.11 + FastAPI (Render)
- **LLM**: DeepSeek API
- **Embeddings**: HuggingFace Inference API (BGE-M3)
- **Mensageria**: Telegram Bot
- **Cron**: GitHub Actions (3x/dia)

## Acesso

- **Dashboard**: https://observatorio-ciseb.vercel.app/dashboard (login via magic link)
- **API health**: https://observatorio-ciseb.onrender.com/health

## Desenvolvimento

```bash
# Worker (Python)
cd apps/worker
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
PYTHONPATH=src python -m pytest tests/ -v

# Web (Next.js)
cd apps/web
npm install
npm run dev
```

## Estrutura

```
apps/
├── web/          # Next.js 14 (Vercel) — com Supabase Auth
└── worker/       # Python 3.11 (Render)
supabase/
└── migrations/   # 001-004 SQL migrations
memoria/          # Documentação e memória da IA
```
EOF

git add README.md
git commit -m "docs: atualizar README pós-Fase 5"
git push origin main
```

---

### ✅ CHECKPOINT F8.1 — Documentação atualizada

**Critério objetivo**:
1. `memoria/08_LOG_EXECUCAO.md` tem entrada de 2026-06-27 com Fase 5
2. `README.md` mostra F5 ✅ COMPLETO
3. `git push origin main` retorna sucesso

---

## Apêndice A — Comandos de rollback

### A.1 — Rollback do patch (se FASE 3 falhar)

```bash
cd /caminho/do/observatorio-ciseb
git checkout main
git reset --hard a7fc34f  # volta ao commit pré-patch
git branch -D fix/fase5-execucao
```

### A.2 — Rollback da migração RLS (se FASE 4 falhar)

```sql
-- No SQL Editor do Supabase:
DROP POLICY IF EXISTS "reviewer_read_findings" ON findings;
DROP POLICY IF EXISTS "reviewer_read_scores" ON scores;
DROP POLICY IF EXISTS "reviewer_read_reviews" ON reviews;
DROP POLICY IF EXISTS "reviewer_insert_reviews" ON reviews;
DROP POLICY IF EXISTS "reviewer_update_findings_status" ON findings;
DROP POLICY IF EXISTS "reviewer_read_deliveries" ON deliveries;
DROP POLICY IF EXISTS "reviewer_insert_deliveries" ON deliveries;
DROP POLICY IF EXISTS "authenticated_read_sources" ON sources;
DROP POLICY IF EXISTS "authenticated_read_pillars" ON pillars;
DROP FUNCTION IF EXISTS is_reviewer();
DROP TABLE IF EXISTS app_config;
```

### A.3 — Rollback das env vars (se FASE 5 falhar)

Restaurar `CRON_SECRET=observatorio-ciseb-f1-2026` em Render e Vercel (valor antigo, ainda hardcoded no código pré-patch).

---

## Apêndice B — Troubleshooting

### B.1 — Render: `RuntimeError: CRON_SECRET não configurado`

**Causa**: variável `CRON_SECRET` não foi salva no Render Environment.
**Solução**: https://dashboard.render.com/web → `observatorio-ciseb` → Environment → adicionar `CRON_SECRET` → Save → redeploy.

### B.2 — Vercel: build falha com `Cannot find module '@supabase/ssr'`

**Causa**: `npm install` não rodou após adicionar dependência.
**Solução**: localmente, `cd apps/web && npm install && git add package.json package-lock.json && git commit -m "deps: @supabase/ssr" && git push`. Vercel reinstala automaticamente.

### B.3 — Dashboard: "Token de acesso ausente ou inválido"

**Causa**: `NEXT_PUBLIC_DASHBOARD_TOKEN` não configurada OU middleware redirecionando em loop.
**Solução**: verificar Vercel env vars. Após Supabase Auth, este token não é mais usado — mas o middleware deve estar presente.

### B.4 — Login magic link não chega no email

**Causa**: Supabase Auth não tem SMTP configurado OU email do Fábio não confirmado.
**Solução**:
1. https://supabase.com/dashboard/project/yefudgudlpjctmdjkkio/auth/users → verificar se usuário está "Confirmed"
2. Auth → Settings → SMTP → configurar (ou usar Resend, já no .env)
3. Como fallback: usar OAuth Google (botão na página de login)

### B.5 — GitHub Actions cron falha com `HTTP 401`

**Causa**: `CRON_SECRET` no GitHub Secrets diferente do Render/Vercel.
**Solução**: https://github.com/prifabiojorge/observatorio-ciseb/settings/secrets/actions → atualizar `CRON_SECRET` com mesmo valor.

### B.6 — Alertas Telegram não chegam

**Causa possível**:
1. Não há findings com `score_composite >= 75` (verificar: `SELECT count(*) FROM scores WHERE score_composite >= 75`)
2. Bot token inválido (verificar: `curl https://api.telegram.org/bot<TOKEN>/getMe`)
3. `chat_id` errado (verificar: `curl https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=1158904776&text=teste`)

### B.7 — Dim alignment excede 100 (bug conhecido)

**Sintoma**: `SELECT max(dim_alignment) FROM scores` retorna > 100.
**Causa**: LLM retornou `confidence > 1.0` (anômala).
**Solução**: aplicar Passo 7.1 (correção do truncamento).

---

## Apêndice C — Critérios de "pronto para produção"

O sistema está pronto para produção quando TODOS os checkpoints abaixo passam:

| Checkpoint | Critério | Como verificar |
|------------|----------|----------------|
| F1.0 | Ambiente OK | `git --version && python3 --version && node --version` |
| F1.1 | Credenciais OK | 7 serviços respondem |
| F1.2 | Branch criada | `git branch --show-current` = `fix/fase5-execucao` |
| F3.1 | Patch aplicado | `git log --oneline -1` = `bdb2e54` + 40 testes passam |
| F4.1 | Supabase Auth | `is_reviewer()` existe + 8 policies authenticated |
| F5.1 | Env vars | 6 critérios de curl passam |
| F6.1 | Validação E2E | 7 critérios de aceitação passam |
| F8.1 | Docs atualizadas | README mostra F5 ✅ + log atualizado |

**Nota**: FASE 7 (gaps opcionais) NÃO é bloqueante para produção. Pode ser feita após estabilização.

---

## Apêndice D — Decisões tomadas durante este Plano

| # | Decisão | Persona | Justificativa |
|---|---------|---------|---------------|
| 1 | Usar `git am` em vez de `git apply` | Harness | Preserva commits e autoría |
| 2 | Sanitizar CRLF antes do patch | Harness | Evita conflitos de merge |
| 3 | Manter `SERVICE_ROLE_KEY` no Render | Guardião | Worker precisa de write (bypass RLS para insert/update) |
| 4 | Remover `SERVICE_ROLE_KEY` da Vercel | Guardião | Após Supabase Auth, RLS governa acesso no web |
| 5 | GitHub Actions em vez de Vercel cron | Orquestrador | Free para repo público, sem limite de crons |
| 6 | Magic link em vez de senha | Advogado | UX sem senha — Fábio não precisa decorar |
| 7 | pgmq não implementado (G10) | Arquiteto | MVP síncrono funciona; fila adiciona complexidade desnecessária |
| 8 | FASE 7 opcional | Harness | Gaps são melhorias, não bloqueantes |

---

> **Fim do Plano.** Próxima ação: executar FASE 1 e seguir os checkpoints em ordem. Se qualquer checkpoint falhar, PARAR e reportar — não tentar contornar.
>
> **Auditado por**: Agente do Harness (ciclo de 5 personas), 2026-06-27
> **Baseado em**: auditoria de lógica/memória/motor do commit `a7fc34f`
> **Patch de referência**: `0001-fase-5-seguranca-testes-auth-cron.patch`
