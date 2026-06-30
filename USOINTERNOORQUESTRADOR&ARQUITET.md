USO INTERNO ORQUESTRADOR & ARQUITETO

#### DOCUMENTO INTERNO · ARQUITETURA

# Observatório

# CISEB

Esqueleto Arquitetural — Imersões em Trilhas de

Aprendizagem

Sistema de monitoramento em tempo real de web, GitHub,

fóruns, redes sociais, literatura acadêmica e eventos/editais.

Curadoria por IA com revisão humana, entrega via newsletter

semanal e alertas instantâneos, organizada pelos seis pilares

CISEB.

PREPARADO POR

### Núcleo de Inovação CISEB

DATA

### Junho de 2026 · v 1. 0


## Sumário


- Capítulo 1 — Sumário Executivo
   - Princípios de desenho
- Capítulo 2 — Contexto, Justificativa e os 6 Pilares CISEB
   - Os seis pilares em detalhe
   - A lacuna que o Observatório preenche
- Capítulo 3 — Domínio Semântico: O Que Conta como Achado
- Capítulo 4 — Visão Arquitetural Macro
   - Princípios arquiteturais
- Capítulo 5 — Camada de Coletores: As 6 Fontes
   - Considerações sobre ToS e ética de coleta
- Capítulo 6 — Ingestão, Fila e Normalização
   - Schema de evento
   - Deduplicação e normalização
- Capítulo 7 — Classificação por Pilar CISEB e Scoring de Relevância
   - Classificador multi-rótulo por pilar
   - Fórmula de scoring composto
   - Thresholds de roteamento
- Capítulo 8 — Armazenamento e Busca Semântica
   - Esquema principal
   - Índices e estratégia de busca
- Capítulo 9 — Curadoria IA + Revisão Humana
   - Pipeline de curadoria
   - Interface de revisão
   - Feedback loop e recalibração
- Capítulo 10 — Camada de Entrega: Newsletter e Alertas
   - Alertas instantâneos
   - Newsletter semanal
   - Dashboard web (opcional, Fase 3)
- Capítulo 11 — Fluxo de Comunicação, Papéis e SLA
   - Tabela de SLAs
   - Tratamento de exceções
- Capítulo 12 — Stack Tecnológica Sugerida
- Capítulo 13 — Roadmap de Implementação
- Capítulo 14 — Governança, Ética e Riscos
   - Princípios éticos operacionais
- Capítulo 15 — Métricas de Sucesso (KPIs)
- Capítulo 16 — Próximos Passos e Decisões Pendentes


## Capítulo 1 — Sumário Executivo

Este documento apresenta o esqueleto arquitetural do **Observatório CISEB** , um
sistema de monitoramento em tempo real projetado para capturar, curar e entregar à
equipe do CISEB notícias, projetos, repositórios, artigos e oportunidades
relacionadas às **Imersões em Trilhas de Aprendizagem** e aos seis pilares de atuação
do Centro: Inteligência Artificial, Cultura Maker, Cultura Digital (Realidade Virtual e
Aumentada), Tecnologia e Arte, Fabricação Digital e Robótica Educacional. O
desenho aqui proposto combina a visão de **Orquestrador** — responsável pelo fluxo
de comunicação, papéis e SLAs — com a visão de **Arquiteto** — responsável pelos
componentes técnicos, pipelines e escolha de stack.

A motivação central é resolver a fragmentação informacional que hoje obriga a equipe a
buscar manualmente em dezenas de portais, redes sociais e repositórios. O Observatório
automatiza a coleta contínua em seis grandes famílias de fontes, submete o material a
um pipeline de classificação por pilar CISEB e scoring de relevância, e entrega o
resultado em dois canais complementares: **alertas instantâneos** via Telegram e
WhatsApp para achados de alto valor, e uma **newsletter semanal** curada em PDF para o
acompanhamento consolidado. Toda a curadoria é feita por IA, com um revisor humano
aprovando o top-N diário antes da publicação — modelo que chamamos de IA full +
revisão.

O documento responde, em ordem, às quatro perguntas que orientaram sua encomenda:
**o que precisa ser feito** (capítulos 4 a 9 — arquitetura e camadas técnicas), **como será
feito** (capítulos 5 a 13 — componentes, stack e roadmap), **como será o resultado**
(capítulos 10, 15 e 16 — entrega, KPIs e próximos passos) e **como será a comunicação**
(capítulo 11 — papéis, SLA e timeline). A leitura pode ser feita de forma linear para uma
compreensão completa, ou por seções, consultando o sumário para acesso direto ao
tópico de interesse.

**6**

```
Fontes monitoradas
em paralelo
```
**6**

```
Pilares CISEB
como taxonomia
```
**T+5min**

```
SLA alvo dos
alertas instantâneos
```
**7 dias**

```
Cadência da
newsletter curada
```
### Princípios de desenho

Cinco princípios orientam todas as decisões arquiteturais detalhadas adiante. Primeiro,
**streaming-first** : cada achado percorre o pipeline individualmente, sem esperar por
lotes, o que reduz a latência entre coleta e entrega. Segundo, **modularidade por camada** :
coletores, normalização, classificação, armazenamento, curadoria e entrega são


componentes independentes, comunicando-se por filas e schemas contratados,
permitindo substituir um sem afetar os outros. Terceiro, **idempotência** : todo evento é
deduplicado por hash criptográfico, garantindo que reprocessamentos não gerem
duplicatas no delivered. Quarto, **observabilidade nativa** : métricas, logs estruturados e
tracing estão presentes desde a primeira versão, não como complemento posterior.
Quinto, **curadoria humana no circuito crítico** : a IA faz o trabalho pesado, mas nenhum
achado é publicado em newsletter sem passar pela revisão do top-N diário — exceto
alertas de score máximo, que seguem regra à parte.

## Capítulo 2 — Contexto, Justificativa e os 6 Pilares CISEB

O CISEB atua como um centro de inovação educacional cuja oferta pedagógica se
organiza em torno de seis pilares tecnológicos e metodológicos complementares.
Cada pilar representa não apenas um conjunto de ferramentas, mas uma **filosofia de
aprendizagem ativa** que coloca o aluno como protagonista da construção do
conhecimento. A edição de 2026 do programa reforçou a ênfase em **Imersões em
Trilhas de Aprendizagem** — percursos estruturados que combinam dois ou mais
pilares ao longo de semanas, culminando em entregáveis concretos (protótipos,
jogos, instalações, projetos de robótica). Compreender o ecossistema de cada pilar —
quem produz conhecimento, quem aplica, quem publica — é condição para que o
Observatório filtre corretamente o sinal do ruído.

### Os seis pilares em detalhe

A **Inteligência Artificial** é aplicada para personalizar o aprendizado, automatizar
processos e criar soluções tecnológicas que ajudam a preparar os alunos para os desafios
do futuro digital. No CISEB, isso se traduz em trilhas que introduzem conceitos de
machine learning, prompts engineering, ética em IA e criação de assistentes
educacionais. O Observatório deve capturar tanto ferramentas novas (modelos, SDKs,
plataformas de ensino) quanto experiências pedagógicas relatadas por professores em
sala de aula, planos de aula abertos e estudos de caso publicados em congressos
brasileiros e internacionais.

A **Cultura Maker** fomenta a criação prática, incentivando estudantes e educadores a
desenvolverem projetos e soluções com tecnologia e criatividade, promovendo a
aprendizagem ativa. Achados relevantes incluem repos em GitHub com projetos de baixo
custo, tutoriais de construção de ferramentas didáticas, relatos de feiras maker escolares
e metodologias de prototipagem rápida adaptadas ao contexto brasileiro de restrição de
recursos.


A **Cultura Digital** explora tecnologias como Realidade Virtual e Realidade Aumentada,
oferecendo experiências imersivas que enriquecem o processo de ensino e
aprendizagem, conectando o mundo físico ao digital. Aqui o Observatório busca
aplicações pedagógicas de RV/RA, plataformas acessíveis (incluindo soluções baseadas
em smartphone + cardboard), kits de desenvolvimento e avaliações de impacto cognitivo
publicadas em literatura acadêmica.

A integração de **Tecnologia e Arte** permite que alunos e educadores criem jogos,
animações e projetos inovadores, desenvolvendo habilidades de pensamento
computacional. Este é um pilar particularmente fértil em projetos abertos: Scratch, p5.js,
Processing, Godot, GDevelop e pixi.js têm comunidades ativas que publicam tutoriais,
plans de aula e jams educacionais. O Observatório deve priorizar recursos replicáveis —
ou seja, com código, assets e roteiros disponíveis para download.

A **Fabricação Digital** com uso de ferramentas como impressoras 3D e cortadoras a laser
promove a prototipagem, transformando ideias em produtos reais e incentivando a
inovação e o empreendedorismo. Achados de valor incluem repositórios de modelos STL
pedagógicos (Thingiverse, Printables, Cults), configurações de impressora otimizadas
para uso escolar, estudos de segurança em makerspace escolar e cases de fabricação de
material didático acessível para alunos com deficiência.

A **Robótica Educacional** oferece um espaço para o aprendizado prático de engenharia,
programação e resolução de problemas, utilizando kits modernos de robótica. Os alunos
desenvolvem habilidades tecnológicas, criatividade e trabalho em equipe. O
Observatório deve monitorar o ecossistema de kits (Arduino, micro:bit, Raspberry Pi
Pico, LEGO Spike, Mbot, RoboRemo), competições (OBR, RoboCup Junior, First Lego
League), bibliotecas de controle (MicroPython, ROS2 educacional) e relatos de
implementação em escolas públicas brasileiras.

### A lacuna que o Observatório preenche

Hoje, a descoberta de iniciativas relevantes depende do esforço individual de professores
e coordenadores que, esparsamente, navegam portais institucionais, grupos de
WhatsApp, canais do YouTube e repositórios acadêmicos. O resultado é desigual: alguns
professores reproduzem projetos excelentes, outros reinventam a roda por
desconhecerem materiais disponíveis. Há três lacunas concretas que o Observatório
endereça. Primeira, **fragmentação** : a informação está espalhada em pelo menos seis
famílias de fontes com padrões de publicação distintos. Segunda, **ausência de curadoria
pedagógica** : mesmo quando algo é encontrado, falta uma avaliação de aderência aos
pilares CISEB e de viabilidade de replicação no contexto do Centro. Terceira, **baixa
replicabilidade** : a maior parte do que se publica é notícia institucional sem artefatos
reproduzíveis, e o Observatório prioriza justamente o oposto — projetos com código,
STLs, planos de aula e tutoriais.


## Capítulo 3 — Domínio Semântico: O Que Conta como Achado

Nem tudo que o pipeline coleta constitui um "achado" no sentido usado por este
documento. Para que um item seja aceito, enriquecido e eventualmente entregue, ele
precisa satisfazer dois critérios: **aderência temática** a pelo menos um dos seis
pilares CISEB e **conteúdo substantivo** suficiente para gerar um resumo útil e uma
sugestão de aplicação. Itens meramente institucionais (como comunicados
administrativos) ou puramente promocionais (como anúncios de cursos pagos sem
material aberto) são descartados já na fase de normalização. A tabela a seguir define
os sete tipos de achado que o sistema reconhece, com exemplos concretos, pilares
típicos e prioridade relativa.

```
Tipo de
Achado
```
```
Exemplo Concreto Pilares Típico
s
```
```
Replicabilidade Prioridade
```
```
Notícia de
projeto
```
```
Matéria do portal Porvir
sobre escola pública que
montou makerspace
```
```
Maker, Fabrica
ção Digital
```
```
Baixa (relato) Média
```
```
Repositório
de código
```
```
Repo GitHub com jogo
educacional em p5.js sobre
frações
```
```
Tecnologia e
Arte, IA
```
```
Alta (código
aberto)
```
```
Alta
```
```
Plano de aula
aberto
```
```
PDF no site da OBI com
sequência didática de 4
aulas usando micro:bit
```
```
Robótica, IA Alta (roteiro
completo)
```
```
Alta
```
```
Modelo 3D /
STL
```
```
STL no Printables de braço
robótico impresso para
ensino de cinemática
```
```
Fabricação
Digital, Robótic
a
```
```
Alta (arte-fato) Alta
```
```
Paper acadê
mico
```
```
Artigo SciELO sobre uso de
RV no ensino de biologia
celular
```
```
Cultura Digital Média (metodolog
ia)
```
```
Média
```
```
Edital /
oportunidade
```
```
Chamada FAPESP de apoio
a projetos de IA na
educação básica
```
```
IA (transversal) N/A (oportunidad
e)
```
```
Crítica
```
```
Evento /
chamada
```
```
Inscrições abertas para a
OBR 2026 — regional São
Paulo
```
```
Robótica N/A (evento) Alta
```
```
Tabela 3.1 — Tipos de achado reconhecidos pelo Observatório CISEB.
```
A coluna **replicabilidade** merece destaque porque ela é o principal filtro de qualidade do
sistema: achados com artefatos reproduzíveis (código, STL, plano de aula, dataset)
recebem um bônus significativo no scoring descrito no capítulo 7. Achados puramente
descritivos (notícias, releases institucionais) são mantidos no acervo mas raramente


chegam aos canais de entrega, a menos que traguem uma ideia metodológica
particularmente transferível. Essa escolha reflete a prioridade do CISEB por **projetos
práticos vindos de metodologias ativas** , conforme definição do próprio programa —
criação de professores, alunos ou ambos.

## Capítulo 4 — Visão Arquitetural Macro

A arquitetura do Observatório segue um padrão de **pipeline em camadas** com fluxo
unidirecional: cada camada consome a saída da anterior e produz uma saída
normalizada para a próxima. Não há chamadas reversas entre camadas durante o
fluxo normal — feedback loops (como a recalibração mensal do classificador)
acontecem fora do caminho crítico, em jobs batch agendados. Essa restrição
simplifica a resiliência: se a camada de curadoria fica indisponível, a camada de
armazenamento continua recebendo e indexando achados; quando a curadoria volta,
ela processa o backlog sem perda. O diagrama a seguir apresenta as seis camadas e
os dois canais de entrega.

```
Figura 4.1 — Arquitetura macro do Observatório CISEB, das seis fontes aos dois canais de entrega.
```
### Princípios arquiteturais

A escolha por **streaming-first** em vez de batch noturno responde à necessidade de
alertas em tempo real para achados críticos (editais, eventos com prazo curto). Cada
coletor publica eventos individuais em uma fila Redis Streams assim que detecta


novidade, e o processamento semântico (LLM + embeddings) consome esses eventos em
paralelo. A latência ponta-a-ponta alvo é de cinco minutos entre a publicação da fonte
original e o disparo do alerta, em condições normais de operação.

A **modularidade por camada** permite que o time substitua componentes sem rewirar
todo o sistema. Por exemplo: a camada de enriquecimento pode mudar de GLM-4 para
Claude ou para um modelo local sem que coletores ou entrega precisem ser tocados —
basta respeitar o schema JSON de entrada e saída da camada. Da mesma forma, novos
coletores podem ser adicionados sem modificar o restante do pipeline, desde que
publiquem no formato de evento contratado.

A **idempotência** é garantida por hash SHA-256 do conteúdo normalizado de cada item
(título + corpo canônico + URL). Antes de um coletor publicar um evento, ele consulta
um índice de hashes recentes no Redis; se o hash já existe, o evento é descartado
silenciosamente. Esse mecanismo tolera reprocessamentos, re-execuções de cron e até
redeploys sem gerar duplicatas na entrega — problema clássico de sistemas de
monitoramento menos cuidadosos.

A **observabilidade nativa** é implementada com Prometheus (métricas), Loki (logs
estruturados) e Grafana (dashboards), todos containers no mesmo docker-compose do
MVP. Cada camada expõe métricas de吞吐 (throughput), latência por estágio, taxa de erro
e tamanho de fila. Alertas operacionais (não confundir com alertas de achados) são
disparados para o mesmo canal Telegram usado pela entrega, mas com prefixo [OPS]
para distinguir.

## Capítulo 5 — Camada de Coletores: As 6 Fontes

A camada de coletores é a única que conversa com o mundo exterior. Cada coletor é
um processo independente, responsável por uma família de fontes, com seu próprio
cronograma, tratamento de erros e mecanismo de checkpoint. A escolha por separar
coletores por família — e não por fonte individual — reduz a complexidade
operacional: o coletor de "literatura acadêmica" abstrai as particularidades de Google
Scholar, SciELO, CAPES e arXiv por trás de uma interface comum. A tabela a seguir
resume as seis famílias, com a stack sugerida para cada uma, frequência de coleta,
tipo de dado predominante e principais desafios técnicos.

```
Fonte Ferramenta / API Frequên
cia
```
```
Tipo de Dado Desafio Técnico
```
```
Web / Blogs Scrapy + feedparser +
trafilatura; RSS/Atom;
Common Crawl index
```
```
15-30 min HTML, artigos,
posts
```
```
Boilerplate removal;
sites sem RSS;
rate-limit
```

```
Fonte Ferramenta / API Frequên
cia
```
```
Tipo de Dado Desafio Técnico
```
```
GitHub GitHub GraphQL API +
PyGithub; tópicos:
education, maker, robotics
```
```
30 min Repositórios,
READMEs, releas
es
```
```
Rate-limit 5k req/h;
distinguir edu de
hobby
Fóruns /
Comunidade
s
```
```
Reddit API (PRAW); bridges
Telegram/WhatsApp; Stack
Exchange API
```
```
10-20 min Threads, comentá
rios, links
```
```
ToS de WhatsApp;
comunidades
privadas; ruído
Redes Sociai
s
```
```
YouTube Data API v3;
LinkedIn scraping limitado;
hashtags IG via API Graph
```
```
30-
min
```
```
Vídeos, posts,
descrições
```
```
APIs pagas;
shadow-banning;
metadados escassos
Literatura
Acadêmica
```
```
scholarly (Google Scholar);
SciELO OAI-PMH; CAPES;
arXiv API
```
```
Diária PDFs, abstracts,
metadados
```
```
Captcha do Scholar;
PDFs pesados;
paywall
Eventos /
Editais
```
```
Scrapy em sites
MEC/FAPESP/CAPES;
newsletters institucionais
```
```
Diária +
gatilho
```
```
Editais, chamadas,
inscrições
```
```
Datas críticas;
formatos heterogêne
os
Tabela 5.1 — As seis famílias de fontes monitoradas pelo Observatório.
```
### Considerações sobre ToS e ética de coleta

Toda coleta respeita os Termos de Serviço das plataformas e os arquivos robots.txt dos
sites. Para APIs pagas ou com rate-limit restritivo (YouTube, LinkedIn), priorizamos
acesso via APIs oficiais com quotas documentadas; quando insuficiente, recurremos a
scraping respeitoso (com User-Agent identificável, delays entre requisições e cache local
agressivo). WhatsApp e Telegram são acessados via bots em grupos onde o CISEB tenha
participação explícita — nunca por scraping de grupos públicos sem autorização. Os
detalhes de governança estão no capítulo 14.

## Capítulo 6 — Ingestão, Fila e Normalização

A camada de ingestão recebe eventos publicados pelos coletores e os prepara para o
processamento semântico. A escolha de **Redis Streams** como fila em vez de Kafka ou
RabbitMQ é deliberada para o MVP: Redis é mais leve de operar, tem latência
submilissegundo para nosso volume (estimado em 1k-5k eventos/dia), e oferece
grupos de consumidores nativos para paralelismo. A migração para Kafka fica
reservada para a Fase 4 (scale), se o volume cruzar 50k eventos/dia — patamar em
que Redis começa a perder vantagem.

### Schema de evento

Todo evento publicado na fila segue o mesmo schema JSON canônico. A obrigatoriedade
de campos é o contrato entre coletores e processadores:


{
"event_id": "uuid v4",
"source": "github" | "web" | "scielo" | ...,
"source_url": "https://...",
"collected_at": "2026-06-25T10:30:00Z",
"content_hash": "sha256(...)",
"raw_payload": { ... fonte-específico ... },
"raw_text": "texto extraído do conteúdo",
"language": "pt" | "en" | "es",
"metadata": { ... metadados estruturados ... }
}

### Deduplicação e normalização

A deduplicação ocorre em duas fases. A primeira, **sintática** , é feita pelo hash SHA-256 do
campo content_hash, que combina URL canonicalizada + título normalizado + corpo sem
whitespace. Se dois coletores publicam o mesmo item (por exemplo, um post que
aparece tanto no RSS quanto no scraper HTML), apenas o primeiro evento é aceito; o
segundo é descartado e logado. A segunda fase, **semântica** , é feita após enriquecimento
LLM: se dois achados têm embeddings com similaridade cosseno acima de 0,93, o de
maior score é mantido e o outro é marcado como duplicata semântica e arquivado.

A normalização converte o payload cru em um formato canônico: extração de texto
principal com trafilatura (que lida bem com boilerplate), limpeza de caracteres
invisíveis, identificação de idioma com langdetect, corte para um máximo de 5.
tokens (preservando o início e o fim do texto, que concentram a maior densidade
informacional) e geração de um snippet de 200 caracteres. O resultado é o que a próxima
camada consome.

## Capítulo 7 — Classificação por Pilar CISEB e Scoring de Relevância

Esta é a camada que diferencia o Observatório de um mero agregador de RSS. Ela
atribui a cada achado: (a) um ou mais **pilares CISEB** (classificação multi-rótulo), (b)
um conjunto de **atributos enriquecidos** (público-alvo, geografia, recursos citados,
nível educacional, replicabilidade) e (c) um **score composto** de 0 a 100 que
determina o roteamento. A combinação desses três elementos permite que a próxima
camada (curadoria) decida com baixa ambiguidade o que fazer com cada item.

### Classificador multi-rótulo por pilar


Um achado pode tocar múltiplos pilares simultaneamente — um repositório de robótica
educacional com interface web em p5.js que usa um modelo de IA para visão
computacional toca três pilares (Robótica, Tecnologia e Arte, IA). O classificador opera
em duas etapas. Primeiro, computa embeddings do conteúdo normalizado e calcula a
similaridade cosseno contra descrições canônicas dos seis pilares (previamente
embedadas). Segundo, submete o top-3 candidatos a um LLM (GLM-4) com prompt
few-shot que retorna, para cada pilar, uma confiança entre 0 e 1. Pilares com confiança
≥ 0,55 são aceitos; abaixo disso são descartados. Esse desenho híbrido (embeddings +
LLM) combina velocidade (embeddings são baratos) com precisão (LLM resolve casos
ambíguos).

### Fórmula de scoring composto

O score composto combina cinco dimensões, cada uma normalizada para 0-100 antes de
ser ponderada. A fórmula reflete explicitamente as prioridades definidas pelo CISEB no
briefing original — Brasil/Lusofonia, replicabilidade, projetos práticos e nível
educacional são fatores de primeira classe, não apenas filtros binários.

```
Dimensão Peso Como é Calculado Justificativa
Alinhamento
ao pilar
```
```
30% Média das confianças do classificador
multi-rótulo
```
```
Pilar é a unidade
organizacional do CISEB
Brasil / Lusofon
ia
```
```
20% Heurística: idioma pt, domínio .br,
menção a estados/cidades, autor
brasileiro
```
```
Prioridade explícita do
briefing
```
```
Replicabilidade 20% Presença de artefatos: código, STL, plano
de aula, dataset, tutorial
```
```
Filtro de qualidade central do
sistema
Projeto prático 15% LLM detecta: é criação de
professor/aluno? Tem implementação?
```
```
Briefing: "não apenas notícias"
```
```
Nível educacion
al
```
```
10% Classificação: básica, técnico, superior,
form. continuada
```
```
Permite filtrar por público
```
```
Novidade
temporal
```
```
5% Decaimento exponencial: 100 se ≤7d; 80
se ≤30d; 50 se ≤90d; 30 caso contrário
```
```
Recompensa achados recentes
```
```
Tabela 7.1 — Pesos e cálculo do score composto (0-100).
```
### Thresholds de roteamento

O score composto determina o destino do achado em regras claras e auditáveis. Achados
com **score ≥ 75** disparam alerta instantâneo via Telegram/WhatsApp imediatamente
após a revisão humana do top-N diário (ver capítulo 9). Achados com **score 50-74** entram
na fila de candidatos à newsletter semanal. Achados com **score 30-49** são arquivados e
ficam acessíveis via busca no dashboard, mas não chegam aos canais push. Achados com
**score < 30** são descartados do índice ativo após 7 dias, mantendo apenas metadados para


fins de auditoria. Os thresholds são parâmetros de configuração e podem ser ajustados
mensalmente com base no feedback dos revisores humanos.

## Capítulo 8 — Armazenamento e Busca Semântica

O armazenamento central é um **PostgreSQL 16** com a extensão **pgvector** para índice
de embeddings. A escolha por Postgres em vez de um banco orientado a documentos
(MongoDB) ou um search engine dedicado (Elasticsearch) é pragmática: Postgres
cobre os três requisitos do sistema — armazenamento relacional metadados, busca
textual full-text (TSVECTOR) e busca vetorial (pgvector) — em um único processo
operável, reduzindo a superfície de manutenção no MVP. Para volumes acima de 1
milhão de achados, uma migração para Elasticsearch como camada de busca
secundária pode ser avaliada na Fase 4.

### Esquema principal

O esquema é deliberadamente simples, com seis tabelas principais:

findings (id, source, url, title, content_text, snippet, language,
collected_at, content_hash, embedding vector(768), status)
sources (id, name, type, last_polled_at, healthy)
pillars (id, slug, name, description, canonical_embedding vector(768))
scores (finding_id, pillar_id, confidence, score_composite,
dim_alignment, dim_br_luso, dim_replicable, dim_practical,
dim_level, dim_novelty, computed_at)
reviews (finding_id, reviewer_id, decision, edited_summary,
feedback_tags, reviewed_at)
deliveries (finding_id, channel, sent_at, opened_at)

### Índices e estratégia de busca

Três índices cobrem os padrões de acesso esperados. Um **GIN** sobre metadados JSONB
permite filtrar por atributos como nível educacional ou geografia com latência
submilissegundo. Um **IVFFlat** sobre a coluna embedding dos findings habilita busca por
similaridade vetorial (k-NN) com bom trade-off entre precisão e velocidade. Um
**TSVECTOR** sobre título + snippet habilita busca full-text tradicional. A combinação de
busca BM25 (TSVECTOR) com busca vetorial (pgvector) é chamada de **busca híbrida** e é
o padrão para queries complexas no dashboard: o usuário pode, por exemplo, buscar "
robótica microbit escola pública" e receber resultados que combinam matching textual
com similaridade semântica ao conceito.

A política de retenção é **24 meses quente** no Postgres, com migração para **arquivo frio
em S3** (ou equivalente on-prem) após esse período. Achados descartados pelo scoring


(score < 30) têm seus textos removidos após 7 dias, mas mantêm metadados por 12 meses
para fins de auditoria do próprio sistema. Essa política equilibra custo de
armazenamento (texto é o maior consumidor de espaço) com a necessidade de
rastreabilidade.

## Capítulo 9 — Curadoria IA + Revisão Humana

A camada de curadoria é onde o sistema deixa de ser puramente automático e
incorpora o julgamento humano no circuito crítico. O modelo operacional escolhido
é o que chamamos de **IA full + revisão** : a IA faz todo o trabalho pesado (classificação,
scoring, ranking, geração de resumo, sugestão de aplicação), e um revisor humano
aprova, edita ou rejeita o top-N diário antes que qualquer item chegue à newsletter.
Alertas instantâneos (score ≥ 75) seguem regra à parte: são enviados imediatamente,
mas o revisor recebe notificação simultânea e pode cancelar/recuperar a publicação
em até 5 minutos se julgar inadequada.

### Pipeline de curadoria

O pipeline de curadoria consiste em seis etapas sequenciais, executadas sobre cada novo
achado ou em batch diário para o top-N:

**1 Dedup final:** remove duplicatas semânticas detectadas por similaridade de
embeddings.

**2 Classificação:** atribui pilares CISEB via embeddings + LLM few-shot.

**3 Scoring:** calcula score composto 0-100 com a fórmula do capítulo 7.

**4 Ranking:** ordena achados do dia por score composto.

**5 Geração de card:** LLM produz título editado, resumo executivo (2-3 linhas) e "
como aplicar no CISEB".

**6 Fila de revisão:** top-N diário (default: top 10 score ≥ 75) é enviado para a interface
do revisor humano.

### Interface de revisão

A interface de revisão é uma aplicação web leve (Next.js ou Streamlit) que apresenta cada
candidato como um **card** contendo: título editado pela IA, pilar(es) atribuído(s) com
confiança, score composto com breakdown das cinco dimensões, resumo executivo,
sugestão de aplicação no CISEB, link original, screenshot automática da página (quando
aplicável) e três botões: **Aprovar** , **Editar** (abre formulário para corrigir título, resumo,
pilar, aplicação) e **Rejeitar** (com tags de feedback: "off-topic", "duplicata", "baixa
qualidade", "fora de escopo pedagógico"). O revisor pode processar o top-N diário em
10-15 minutos.


### Feedback loop e recalibração

Toda decisão do revisor (aprovar, editar, rejeitar com tag) é registrada na tabela reviews e
alimenta dois processos mensais de recalibração. O primeiro recalibra o **classificador de
pilares** : o conjunto de achados revisados vira dataset de fine-tuning (ou few-shot
enrichment) para o próximo mês. O segundo recalibra os **pesos do scoring** : se, por
exemplo, o revisor rejeita sistematicamente achados com alta novidade temporal mas
baixa replicabilidade, o peso da replicabilidade pode ser aumentado em 5 pontos e o da
novidade reduzido em 5. Esse loop é a garantia de que o sistema aprende com a equipe
em vez de petrificar as suposições iniciais.

## Capítulo 10 — Camada de Entrega: Newsletter e Alertas

A entrega é o que torna o Observatório útil no dia a dia do CISEB. Foram escolhidos
dois canais complementares, com características opostas: **alertas instantâneos** via
Telegram e WhatsApp para achados críticos (baixa latência, baixo volume, alta
urgência) e uma **newsletter semanal** em PDF e HTML para o acompanhamento
consolidado (alta latência, alto volume, baixa urgência). Um terceiro canal opcional
— um dashboard web leve — pode ser adicionado na Fase 3 para consultas ad-hoc.

### Alertas instantâneos

Os alertas são disparados para um canal Telegram e um grupo WhatsApp dedicados do
CISEB. O formato do alerta é um **card visual** com cinco elementos: (1) título editado
(máximo 80 caracteres), (2) pilar CISEB principal como tag colorida, (3) link original com
preview, (4) resumo executivo de 2 linhas, (5) sugestão de aplicação no CISEB em 1 linha
precedida do rótulo "Aplicação sugerida". O disparo é feito por um bot via
python-telegram-bot e whatsapp-web.js (este último requer um número de WhatsApp
Business dedicado). O SLA alvo é de 5 minutos entre a coleta e o disparo do alerta. Alertas
podem ser cancelados pelo revisor humano em até 5 minutos após o disparo, com uma
mensagem de retratação automática no mesmo canal.

### Newsletter semanal

A newsletter é gerada toda segunda-feira às 7h e enviada via **Postmark** ou **Amazon SES**
para uma lista gerida pelo CISEB. Ela contém entre 20 e 30 achados selecionados (top
score da semana após revisão humana), organizados por pilar CISEB, com a seguinte
estrutura por item: título, pilar, score, resumo de 3-4 linhas, "como aplicar no CISEB" em
2 linhas, e link original. A newsletter é gerada em dois formatos: HTML responsivo (para
leitura em email clients) e PDF anexo (para arquivo e consulta offline). A geração do PDF
reutiliza o mesmo motor ReportLab + paleta do presente documento, garantindo


identidade visual consistente entre o esqueleto arquitetural e as publicações
operacionais do Observatório.

### Dashboard web (opcional, Fase 3)

Um dashboard Next.js leve pode ser adicionado a partir da Fase 3. Ele oferece: busca
híbrida (textual + semântica) sobre o acervo, filtros por pilar / período / nível educacional
/ fonte, favoritos pessoais, exportação para BibTeX/CSV, e um modo "explorar" que
recomenda achados similares a um item selecionado. O dashboard não substitui os
canais push — é complementar para consultas deliberadas. A audiência natural são
professores que queiram pesquisar materiais antes de uma aula.

## Capítulo 11 — Fluxo de Comunicação, Papéis e SLA

A clareza sobre papéis e SLAs é o que evita que o Observatório se torne um sistema
técnico correto mas operacionalmente inútil. Quatro papéis orbitam o sistema, cada
um com responsabilidade distinta: o **Orquestrador** define prioridades, fonte de
prioridades e SLAs; o **Arquiteto** mantém o pipeline saudável e evolui componentes; o
**Curador IA** é o autômato que executa o trabalho pesado de classificação, scoring e
geração de cards; o **Revisor Humano** aprova, edita ou rejeita o top-N diário. A figura
a seguir mostra a timeline de um achado atravessando essas quatro
responsabilidades, do momento da coleta até a entrega final.

```
Figura 11.1 — Timeline de um achado, dos 4 papéis aos 2 canais de entrega.
```
### Tabela de SLAs

```
Etapa / Canal SLA Alvo Janela de Operação Responsável
Coleta de fonte 15-60 min (por
fonte)
```
```
24/7 automático Coletores (autôma
to)
```

```
Etapa / Canal SLA Alvo Janela de Operação Responsável
Classificação + score T+3 min após coleta 24/7 automático Curador IA
Alerta para score ≥ 75 T+5 min após coleta 24/7 (com notificação ao
revisor)
```
```
Curador IA
```
```
Revisão humana do top-N 30 min após card
gerado
```
```
Dia útil, 9h-19h Revisor Humano
```
```
Newsletter semanal Segundas 7h-8h Automático após revisão Curador IA +
Orquestrador
Recalibração do modelo Mensal, primeira
semana
```
```
Janela de manutenção Arquiteto +
Revisor
Recuperação de falha 15 min para
detectar; 1h para
restaurar
```
```
24/7 monitorado Arquiteto
```
```
Tabela 11.1 — SLAs operacionais por etapa do pipeline.
```
### Tratamento de exceções

A operação normal é desenhada para ser silenciosa: o revisor humano interage apenas
com o top-N diário e o Orquestrador recebe apenas o digest semanal mais alertas
operacionais. As exceções seguem três caminhos. Primeiro, **falhas de coletor** : se um
coletor falha três vezes consecutivas, um alerta [OPS] é disparado no Telegram para o
Arquiteto, que tem 1h para restaurar. Segundo, **explosão de volume** : se a fila excede
1.000 eventos pendentes, o sistema ativa processamento paralelo adicional e notifica o
Arquiteto. Terceiro, **degradação de qualidade da IA** : se a taxa de aprovação do revisor
cai abaixo de 60% por duas semanas consecutivas, o Arquiteto inicia uma recalibração
extraordinária do classificador. Nenhum desses caminhos exige intervenção do
Orquestrador no dia a dia — apenas comunicação estruturada.

## Capítulo 12 — Stack Tecnológica Sugerida

A stack abaixo é uma **recomendação de partida** , não um contrato. Foi montada
priorizando três critérios: (a) **operabilidade por equipe pequena** (preferência por
tecnologias conhecidas e com boa documentação em português), (b) **custo baixo no
MVP** (preferência por open-source e serviços com free tier generoso), e (c) **caminho
de saída claro** (cada componente tem uma alternativa identificada para a fase de
scale). Substituições são esperadas e bem-vindas conforme a equipe amadurece e os
volumes crescem.


**Cama
da**

```
Componente Ferramenta Sugerida Justificativa / Alternativa
```
Coleta Web scraper Scrapy 2.11+ Maduro, escalável; alt: Playwright para
JS-heavy

Coleta RSS/Atom feedparser Padrão de facto Python

Coleta Extração de
texto

```
trafilatura Melhor boilerplate removal para PT-BR
```
Coleta GitHub PyGithub + GraphQL API oficial; alt: gh CLI para ad-hoc

Coleta YouTube youtube-transcript-api Acesso a transcrições (ricas em
conteúdo)

Coleta Acadêmico scholarly + arxiv API Alt: Semantic Scholar API (gratuita)

Fila Message broker Redis Streams Leve; alt Fase 4: Kafka

Proces
so

```
Workers Celery 5 + Redis broker Padrão Python; alt: Dramatiq
```
IA LLM (classif+re
sumo)

```
GLM-4 via z-ai-web-dev-sdk Custo/qualidade; alt: Claude Haiku,
Llama 3.1 70B local
```
IA Embeddings sentence-transformers
(BGE-M3)

```
Multilíngue (PT+EN+ES); alt: OpenAI
text-embedding-
```
Armaz. Banco relaciona
l

```
PostgreSQL 16 + pgvector Único processo cobre 3 requisitos
```
Armaz. Arquivo frio MinIO (S3-compatible
on-prem)

```
Alt: AWS S3, Cloudflare R
```
Entreg
a

```
E-mail Amazon SES Custo baixo; alt: Postmark (melhor
deliverability)
```
Entreg
a

```
Telegram bot python-telegram-bot API oficial estável
```
Entreg
a

```
WhatsApp whatsapp-web.js (Node) Requer número Business; alt: API
oficial Meta
```
Obs. Métricas/logs Prometheus + Loki + Grafana Stack CNCF padrão; alt: Datadog pago

Infra Orquestração Docker Compose (MVP) → k8s
(Fase 4)

```
Progressão natural de complexidade
```
```
Tabela 12.1 — Stack tecnológica sugerida por camada.
```

## Capítulo 13 — Roadmap de Implementação

O roadmap é organizado em cinco fases sequenciais, com duração total estimada de
20 semanas (5 meses) até a operação em cobertura completa, mais uma fase contínua
de scale e evolução. Cada fase tem um critério de saída objetivo — não se avança para
a próxima fase sem atender o critério, evitando acúmulo de débito técnico. A fase 0 é
de decisão e setup, sem código de produção; a fase 4 é operação contínua com
melhorias incrementais.

```
Fase Objetivo Entregáveis Principais Dur
ação
```
```
Critério de Saída
```
```
0 — Decisão e
Setup
```
```
Alinhar decisões
pendentes (cap.
16) e provisionar
infra
```
```
Conta cloud; repositório Git;
docker-compose base; lista
de revisor humano
```
```
2 se
m
```
```
Decisões do cap. 16
fechadas; ambiente
roda "hello world"
```
```
1 — MVP Provar o circuito
ponta-a-ponta
com 1 fonte e 1
pilar
```
```
Coletor GitHub +
normalização + classificador
1 pilar + alerta Telegram
```
```
4 se
m
```
```
5+ alertas reais
enviados e revisados em
uma semana
```
```
2 — Piloto Expandir para 3
fontes e 3 pilares;
ativar newsletter
```
```
+ coletores Web e
Acadêmico; + pilares Maker,
Robótica, IA; newsletter
HTML semanal
```
```
6 se
m
```
```
Newsletter enviada por
4 semanas seguidas;
taxa de aprovação ≥
70%
3 — Cobertur
a Completa
```
```
6 fontes + 6
pilares + dashboa
rd opcional
```
```
+ Fóruns, Redes Sociais,
Eventos; + pilares restantes;
dashboard Next.js
```
```
8 se
m
```
```
Cobertura 6/6 pilares;
dashboard com busca
híbrida funcional
4 — Scale e
Evolução
```
```
Operação contínu
a; observabilidad
e; multicanal;
feedback loop
```
```
Migração para k8s (se vol >
50k/dia); recalibração
mensal automatizada;
métricas de impacto
```
```
Contí
nuo
```
```
KPIs do cap. 15 medidos
mensalmente; roadmap
trimestral
```
```
Tabela 13.1 — Roadmap de implementação em cinco fases.
```
A duração de cada fase inclui uma margem de 20% para imprevistos — padrão razoável
para projetos com componentes de IA cujo comportamento em produção é parcialmente
imprevisível. Fases paralelas (por exemplo, começar o dashboard na Fase 2) são possíveis
se a equipe tiver capacidade, mas não devem comprometer o caminho crítico do pipeline
principal. A recomendação é manter foco linear até a Fase 3 e só depois paralelizar
evoluções.


## Capítulo 14 — Governança, Ética e Riscos

Todo sistema que coleta, classifica e republica informação de terceiros carrega riscos
éticos e legais que precisam ser endereçados explicitamente, não varridos para baixo
do tapete. Este capítulo identifica os cinco riscos mais relevantes para o Observatório
CISEB, com probabilidade, impacto e mitigação concreta. A regra ética fundamental
do sistema é simples: **sempre citar a fonte original, nunca republicar conteúdo
integral, optar por links + resumos curtos**. Respeitar essa regra resolve a maior
parte dos riscos jurídicos e mantém a relação saudável com a comunidade
educacional que produz o conteúdo que o Observatório curadoria.

```
Risco Probabili
dade
```
```
Impac
to
```
```
Mitigação
```
```
Viés do LLM na
classificação de pilares
```
```
Média Médio Few-shot com exemplos revisados; recalibração
mensal; auditoria de paridade por pilar
Direitos autorais de
materiais replicados
```
```
Alta Alto Republicar apenas resumos + links; nunca o
conteúdo integral; respeitar licenças (CC BY, MIT,
etc.)
LGPD (dados pessoais de
educadores)
```
```
Média Alto Não coletar dados pessoais além do necessário;
anonimizar em estatísticas; DPO consultado na
Fase 0
ToS de redes sociais
(risco de banimento)
```
```
Média Médio Preferir APIs oficiais; respeitar rate-limits;
User-Agent identificável; fallback para fontes
alternativas
Degradação de qualidade
por auto-loop
```
```
Baixa Médio Revisão humana obrigatória no top-N; alertas de
taxa de aprovação; refresh periódico do conjunto
de few-shot
Tabela 14.1 — Riscos identificados e mitigações.
```
### Princípios éticos operacionais

Cinco princípios éticos orientam decisões operacionais do dia a dia. Primeiro,
**transparência de curadoria** : todo achado entregue tem link para a fonte original e
atribuição clara ao autor, sem exceção. Segundo, **não republicação integral** : resumos
são sempre produções originais do LLM sob revisão humana, com extensão máxima de 4
linhas; o leitor interessado deve clicar no link para o conteúdo completo. Terceiro,
**diversidade de fontes** : o sistema monitora ativamente se algum pilar está sendo coberto
majoritariamente por uma única fonte e gera alerta se isso ocorrer, evitando captura
editorial. Quarto, **direito ao esquecimento** : qualquer autor pode solicitar a remoção de
seus conteúdos do acervo do Observatório, com prazo de 7 dias para atendimento.
Quinto, **auditoria aberta** : métricas agregadas (volume por fonte, taxa de aprovação,
cobertura por pilar) são publicadas mensalmente em um relatório de transparência
acessível a toda equipe CISEB.


## Capítulo 15 — Métricas de Sucesso (KPIs)

KPIs traduzem a intenção do Observatório em números verificáveis e permitem que a
equipe avalie, mês a mês, se o sistema está entregando valor. Os oito KPIs abaixo
estão organizados em três grupos — **cobertura** (o sistema está vendo o ecossistema?),
**qualidade** (o que chega ao usuário é relevante?) e **impacto** (o que chega ao usuario
muda a prática pedagógica?). Os dois primeiros grupos são medidos
automaticamente; o terceiro requer pesquisa qualitativa trimestral com a equipe do
CISEB.

```
KPI Grupo Definição Operacional Meta Frequênci
a
Fontes ativas Cobertura Coletores saudáveis / total
configurado
```
```
≥ 90% Diária
```
```
Achados por dia Cobertura Média móvel 7d de eventos
únicos coletados
```
```
50-500/dia Diária
```
```
Cobertura por pilar Cobertura Pilares com ≥ 5 achados/dia na
média semanal
```
```
6 de 6 Semanal
```
```
Precisão da
curadoria
```
```
Qualidade Achados aprovados / achados no
top-N revisado
```
```
≥ 75% Semanal
```
```
Recall estimado Qualidade Achados relevantes capturados /
amostra manual
```
```
≥ 80% Mensal
```
```
Taxa de falso
positivo
```
```
Qualidade Alertas cancelados pelo revisor /
alertas enviados
```
```
≤ 10% Semanal
```
```
Taxa de abertura
(newsletter)
```
```
Impacto Opens únicos / entregas ≥ 45% Semanal
```
```
Achados replicados
no CISEB
```
```
Impacto Achados citados em relatórios
pedagógicos trimestrais
```
```
≥ 3/trimestre Trimestral
```
```
Tabela 15.1 — KPIs do Observatório CISEB, com metas e frequência de medição.
```
Os KPIs de impacto são os mais difíceis de medir mas os mais importantes para justificar
a continuidade do sistema. "Achados replicados no CISEB" exige que a equipe pedagógica
cite explicitamente, em relatórios trimestrais de atividades, quais projetos ou materiais
foram inspirados por achados do Observatório. Esse dado pode ser coletado por meio de
um campo estruturado no relatório ("Origem: Observatório CISEB, achado de DD/MM") e
alimenta de volta o sistema, permitindo fechar o loop entre descoberta e aplicação. A
meta inicial de três replicações por trimestre é deliberadamente modesta — o objetivo no
primeiro ano é estabelecer o hábito de citar a fonte; a meta pode ser revista para cima a
partir do segundo ano.


## Capítulo 16 — Próximos Passos e Decisões Pendentes

Este documento entrega um esqueleto arquitetural completo, mas o início da
implementação depende de oito decisões que precisam ser tomadas pelo CISEB antes
da Fase 0 terminar. Cada decisão tem uma pergunta-guia e um prazo sugerido dentro
das 2 semanas da Fase 0. As respostas determinam configurações, custos e escolhas
de stack que só fazem sentido serem ajustadas uma vez — refazer depois é caro. A
recomendação é que o Orquestrador convoque uma reunião de kickoff com o
Arquiteto e o futuro Revisor Humano para fechar todas as oito em uma única sessão
estruturada de 90 minutos.

**1 Orçamento de LLM (decisão financeira).** Qual teto mensal de gasto com
chamadas de LLM (GLM-4, Claude, etc.) o CISEB consegue absorver? Estimativa
inicial: US$ 50-150/mês para volume MVP. Prazo: semana 1 da Fase 0.

**2 Revisor Humano (papel operacional).** Quem da equipe do CISEB assumirá a
revisão diária do top-N (10-15 min/dia)? É um professor? Um coordenador?
Rotativo? Definir antes de iniciar. Prazo: semana 1.

**3 Canais Telegram e WhatsApp (infraestrutura de entrega).** Qual número de
WhatsApp Business será usado? Qual canal/grupo Telegram receberá os alertas?
Quem é admin? Prazo: semana 1.

**4 Hospedagem (cloud vs on-prem).** O sistema roda em cloud (AWS, GCP,
Cloudflare) ou on-prem CISEB? Para volumes MVP, cloud custa US$ 30-80/mês;
on-prem exige uma máquina com 16GB RAM. Prazo: semana 2.

**5 Lista inicial de fontes prioritárias (escopo Fase 1-2).** Dentre as 6 famílias, quais
fontes específicas são absolutamente prioritárias no contexto do CISEB? (Ex.:
Porvir, Nova Escola, OBR, Printables, github.com/topics/educational-robotics).
Prazo: semana 2.

**6 Política de retenção (conformidade).** Confirmar 24 meses quente + S3 frio, ou
ajustar? Há requisitos legais do CISEB ou da instituição mantenedora que mudam
esses números? Prazo: semana 2.

**7 Frequência da newsletter (cadência editorial).** Semanal (segundas 7h) é o
padrão sugerido. Quinzenal reduz volume mas perde oportunidade. Diária é
inviável sem expandir o time editorial. Prazo: semana 2.

**8 Definição operacional de "replicável" (critério de qualidade).** O que conta como
replicável para o CISEB? Apenas código aberto? Inclui planos de aula em PDF?
Vídeos tutoriais? Definir para calibrar o scorer. Prazo: semana 2.

Com as oito decisões fechadas e a Fase 0 concluída, o Observatório CISEB está pronto
para entrar na Fase 1 (MVP) e começar a provar o circuito ponta-a-ponta em quatro
semanas. A partir da primeira newsletter enviada e dos primeiros alertas reais revisados,


o sistema entra em regime de melhoria contínua orientado pelos KPIs do capítulo 15
epelo feedback estruturado do Revisor Humano, que mensalmente realimenta
oclassificador e o scorer. O esqueleto aqui proposto não é um fim em si mesmo — é
oponto de partida para um Observatório que amadurece junto com a prática
pedagógicado CISEB.


