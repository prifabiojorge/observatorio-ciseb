# Manifesto da IA — Observatório CISEB
### Arquivo de Persistência · Gerado em 2026-06-25 · v1.0

---

## Propósito deste diretório

A pasta `memoria/` é o **diretório de persistência cognitiva** do projeto Observatório CISEB.
Qualquer IA que interaja com este projeto deve:

1. **Ler todos os arquivos desta pasta ANTES** de executar qualquer ação.
2. **Nunca contradizer decisões documentadas aqui** sem autorização explícita do professor Fábio Jorge.
3. **Atualizar os arquivos quando fizer progresso**, marcando timestamps e status.

---

## Quem é o stakeholder

- **Nome**: Fábio Jorge (professor formador, único revisor humano)
- **Canal**: Telegram @fabiojorgebr / +55 91 985140988
- **Papel**: Único tomador de decisão. SLA de revisão: até 24h.

## O que é o Observatório CISEB

Sistema de monitoramento em tempo real que captura, cura e entrega conteúdos de 6 famílias de fontes (web, GitHub, fóruns, redes sociais, academia, eventos/editais) classificados pelos **6 pilares CISEB**:

| Pilar | Slug | Descrição curta |
|-------|------|----------------|
| Inteligência Artificial | `ia` | Personalização, automação, IA em educação |
| Cultura Maker | `maker` | Projetos práticos, construção, criatividade |
| Cultura Digital | `digital` | RV, RA, experiências imersivas |
| Tecnologia e Arte | `tech_art` | Jogos, animações, pensamento computacional |
| Fabricação Digital | `fabrication` | Impressão 3D, cortadora a laser, prototipagem |
| Robótica Educacional | `robotics` | Kits, competições, programação de robôs |

## Ciclo de 5 Personas (obrigatório a cada passo)

```
[1] ARQUITETO → projeta a solução
[2] GUARDIÃO DE SEGURANÇA → audita em tempo real
[3] ORQUESTRADOR → define ordem e dependências
[4] ADVOGADO DO USUÁRIO → valida UX e simplicidade
[5] AGENTE DO HARNESS → executa + testa + registra evidências
```

## Índice dos arquivos de memória

| Arquivo | Conteúdo |
|---------|----------|
| `00_MANIFESTO_IA.md` | Este arquivo. Leitura obrigatória. |
| `01_DECISOES_TOMADAS.md` | As 8 decisões do Fábio (imutáveis) |
| `02_STACK_TECNOLOGICA.md` | Stack pinada com versões exatas |
| `03_SCHEMA_BANCO.md` | Contratos das 6 tabelas SQL |
| `04_MAPA_FASES.md` | Roadmap de 5 fases com checkpoints |
| `05_SEGURANCA_DESDE_DESENHO.md` | Decisões de segurança incorporadas desde o design |
| `06_CONTRATOS_E_SCHEMAS.md` | Contratos de evento e API |
| `07_CONTEXTO_PEDAGOGICO.md` | Contexto educacional do CISEB |
| `08_LOG_EXECUCAO.md` | Log vivo de progresso (atualizar!) |
| `09_ESTRUTURA_ARQUIVOS.md` | Estrutura planejada de arquivos do monorepo |

## Regras anti-alucinação

> Antes de executar qualquer passo, a IA executora deve se perguntar:
> 1. **Tenho todos os inputs?** Se não, PARAR e pedir.
> 2. **O resultado esperado está definido objetivamente?** Se não, PARAR.
> 3. **Existe um comando de verificação?** Se não, PARAR.
> 4. **Estou criando algo que não está no plano?** Se sim, **NÃO FAÇA**.

---

> **Última atualização**: 2026-06-29T11:00:00-03:00
> **Atualizado por**: Agente do Harness (CHECKPOINT F8.1+F8.2+F8.3 — Freshness + YouTube + Cobertura IA. 84 testes. Queries diversificadas incl. Gemini/AI Studio.)
