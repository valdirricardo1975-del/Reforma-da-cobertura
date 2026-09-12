# 02 — Arquitetura do HASTA

> **HASTA** — nome de trabalho. Em Roma, as vendas públicas eram feitas *sub hasta*, sob
> a lança fincada no solo; daí "hasta pública" e, em espanhol, *subasta*. Nome curto,
> pronunciável, aderente ao domínio e sem colisão com os concorrentes. Sujeito a troca.

## 1. Princípio arquitetural central

> **Determinismo onde vira número; LLM onde vira leitura.**

Todo valor que entra numa decisão de capital é produzido por código determinístico,
testável e versionado. LLMs são usados onde são insuperáveis — ler documentos jurídicos
heterogêneos, extrair estrutura de prosa, gerar hipóteses e redigir dossiês — e **sempre**
com: (a) esquema de saída obrigatório, (b) citação obrigatória do trecho de origem,
(c) validação cruzada determinística, (d) registro de prompt/modelo/versão.

Corolário: a "nota de oportunidade" nunca é gerada por um LLM. Ela é calculada. O LLM
explica a conta; não a faz.

## 2. Visão em camadas

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ L8  INTERFACES        feed · dossiê · alertas · API · "pergunte aos autos"   │
├──────────────────────────────────────────────────────────────────────────────┤
│ L7  DECISÃO           tese · teto de lance · cronograma · checklist de DD    │
│                       fluxo de comitê (humano no circuito)                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ L6  COMPLIANCE GATE   conflito · muralha ética · impedimentos · LGPD         │◄── bloqueia
├──────────────────────────────────────────────────────────────────────────────┤
│ L5  MOTORES           valor justo · blindagem · risco processual · liquidez   │
│                       competição · rota de acesso  →  TIR ajustada + score    │
├──────────────────────────────────────────────────────────────────────────────┤
│ L4  ENRIQUECIMENTO    comparáveis · geo · ônus/gravames · mercado · histórico │
├──────────────────────────────────────────────────────────────────────────────┤
│ L3  DOMÍNIO           entidades canônicas · resolução de identidade           │
│                       linha do tempo concursal · máquinas de estado          │
├──────────────────────────────────────────────────────────────────────────────┤
│ L2  EXTRAÇÃO          parsers determinísticos · OCR · tabelas                 │
│                       extração LLM com esquema + citação obrigatória          │
├──────────────────────────────────────────────────────────────────────────────┤
│ L1  INGESTÃO          agendador · polidez/limites · snapshot WORM · dedupe    │
├──────────────────────────────────────────────────────────────────────────────┤
│ L0  FONTES            DataJud · DJEN · PNAJ · PJe/eSAJ/eproc · leiloeiros     │
│                       sites de AJs · diários · cadastros · mercados           │
└──────────────────────────────────────────────────────────────────────────────┘
        ┌──────────────────────────────────────────────────────────────┐
        │ L9 APRENDIZADO   resultado real → recalibração → backtesting │
        └──────────────────────────────────────────────────────────────┘
Transversais: procedência · auditoria · observabilidade · custo por fonte · segredos
```

### O que cada camada garante

| Camada | Garantia (invariante) |
|---|---|
| L0/L1 | Nada entra sem **snapshot imutável** e metadados de coleta (URL, hash, timestamp, agente) |
| L2 | Toda afirmação estruturada é uma `Evidência` com ponteiro para trecho do documento |
| L3 | Uma entidade do mundo real = um registro canônico; conflitos ficam explícitos, não são sobrescritos |
| L4 | Todo enriquecimento declara fonte, data-base e incerteza |
| L5 | Todo número é reproduzível a partir das evidências + versão do modelo |
| L6 | Nenhuma oportunidade é exibida sem passar pelos portões |
| L7 | Nenhuma ação externa sem autorização humana registrada |
| L9 | Todo resultado real volta para o modelo que o previu |

## 3. O funil de originação (a diferença de verdade)

Os concorrentes entram em P4. Nós entramos em P0.

```
P0  SINAL FRACO       distribuição de pedido de RJ/falência · protesto/execução em massa
                      CNAE intensivo em ativos · dívida com garantia real
      │  lead time típico: 12–24 meses
P1  PROCEDIMENTO      deferimento do processamento (art. 52) · nomeação do AJ
      │               relação de credores (art. 7º, § 2º) · RMAs
      │  lead time típico: 6–18 meses
P2  INVENTÁRIO        auto de arrecadação (falência) · relação de bens
      │               laudos de avaliação juntados · matrículas · frota
      │  lead time típico: 3–12 meses
P3  AUTORIZAÇÃO       plano com cláusula de UPI/alienação · AGC · homologação (art. 58)
      │               autorização do art. 66 · decisão "designe-se leilão"
      │  lead time típico: 1–6 meses
P4  OFERTA PÚBLICA    edital publicado · praças designadas · PNAJ  ◄── onde o mercado acorda
      │  lead time típico: 15–60 dias
P5  RESULTADO         arrematação · auto · carta · desdobramentos → aprendizado (L9)
```

**Métrica-assinatura do produto: `Índice de Antecipação`** = dias entre a nossa
detecção qualificada e a publicação do edital. É a KPI que prova o diferencial.

Dois artefatos vivem nesse funil:

- **Mapa de Ativos por Devedor** — inventário acumulativo por devedor/grupo, construído
  desde P1, muito antes de existir lote. Quando o edital sai, o dossiê já existe.
- **Dossiê Vivo** — documento por oportunidade que se atualiza com *diff* auditável
  ("laudo substituído em 12/03; valor caiu 18%").

## 4. Agentes especialistas (L2–L7)

Não um agente monolítico "autônomo", mas um **enxame com trilhos**, cada um com entrada,
saída tipada e critério de sucesso avaliável:

| Agente | Função | Entrada → Saída | Como é avaliado |
|---|---|---|---|
| **Batedor** | vigia fontes, detecta novidade relevante | fonte → `EventoCandidato` | recall de eventos-alvo em conjunto histórico |
| **Escriba** | transforma documento em fatos estruturados | PDF/HTML → `Evidência[]` | exatidão campo a campo vs. gabarito anotado |
| **Cartógrafo** | resolve identidade, monta linha do tempo e inventário | `Evidência[]` → `Procedimento`, `Ativo[]` | taxa de fusão correta/incorreta de entidades |
| **Avaliador** | valor justo por classe, com comparáveis | `Ativo` → `Avaliação(p10,p50,p90)` | MAPE contra preços realizados |
| **Advogado do Diabo** | ataca a tese; lista o que a mataria e o que falta | `Oportunidade` → `Riscos[]`, `Lacunas[]` | % de riscos materializados que havia previsto |
| **Caçador de Vícios** | varre nulidades (art. 889, laudo, publicidade, penhora) | autos/edital → `Vícios[]` | detecção em casos de anulação conhecidos |
| **Estrategista** | escolhe rota de acesso e escada de lances | `Oportunidade` → `Estratégia` | aderência à decisão do comitê |
| **Auditor** | portões de compliance | tudo → `permitido/bloqueado + motivo` | zero falso-negativo tolerado |
| **Relator** | dossiê e alerta em linguagem de decisão | tudo → dossiê | legibilidade e ausência de alegação sem evidência |

O **Advogado do Diabo é obrigatório**: nenhuma oportunidade é ranqueada sem sobreviver ao
ataque adversarial, e o resultado do ataque é parte do dossiê. É um diferencial de
projeto, não um enfeite — inverte o viés natural de um sistema que "procura achar coisa".

## 5. Fluxo de um lote, ponta a ponta

```
 Fonte           Snapshot      Evidências        Domínio          Motores         Portões        Saída
──────────────────────────────────────────────────────────────────────────────────────────────────────
 DJEN/PNAJ  →   raw/2026/…  →  {campo,trecho} →  Lote+Ativos  →  valor justo  →  conflito?  →  alerta
 leiloeiro      hash+meta      + citação          Procedimento     blindagem       muralha?      dossiê
 site do AJ                                      Atores           risco proc.     mandato?      fila do
 DataJud                                         Créditos         liquidez                      comitê
                                                 linha do tempo   competição
                                                                  rota  →  TIR(p10,p50,p90)
                                                                            + score 7D
                                            ┌──────────────────────────────────────┐
                                            │ Advogado do Diabo + Caçador de Vícios│
                                            └──────────────────────────────────────┘
```

Idempotência: reprocessar o mesmo snapshot produz exatamente o mesmo resultado
(mesma versão de modelo). Reexecução é sempre segura — requisito para auditoria e
para backtesting.

## 6. Registro de decisões (ADRs)

### ADR-0001 — Núcleo de domínio antes de coletores
Construímos primeiro o modelo canônico e a máquina de estados concursal; adaptadores de
fonte são periféricos substituíveis.
*Por quê:* o ativo durável é o modelo; fontes mudam (e a PNAJ vai mudar todas de uma vez).
*Custo aceito:* demora um pouco mais para ver o primeiro dado na tela.

### ADR-0002 — Fontes como adaptadores plugáveis, com a PNAJ como cidadã de primeira classe
Interface única `Fonte` (descobrir → buscar → snapshot → parsear). PNAJ entra como um
adaptador entre outros, mas o modelo canônico é desenhado para o vocabulário do
checklist do Provimento 255/2026.
*Por quê:* concentração nacional da oferta é questão de quando, não de se.

### ADR-0003 — Procedência obrigatória (`Evidência` como primitiva)
Nenhum campo existe "solto": todo valor carrega `(documento, página, trecho, hash,
coletado_em, extrator, confiança)`.
*Por quê:* é o que permite um advogado assinar embaixo. E é pré-requisito de auditoria,
de depuração e do aprendizado (L9).
*Custo aceito:* ~2–3× mais escrita de dados; vale.

### ADR-0004 — Determinismo no cálculo, LLM na leitura
Ver §1. LLM nunca produz score nem valor final.
*Por quê:* reprodutibilidade, custo, auditabilidade e defesa em comitê.

### ADR-0005 — Incerteza explícita (p10/p50/p90), não ponto único
Todos os motores retornam distribuição; ranking usa p10 (margem de segurança).
*Por quê:* decisão de capital sob incerteza; ponto único mente por omissão.

### ADR-0006 — Desenvolvimento contra *fixtures* reais, offline-first
Cada fonte tem amostras reais salvas em `tests/fixtures/`, com testes de regressão
(golden files). A suíte roda sem rede.
*Por quê:* (a) o sandbox atual bloqueia `*.jus.br`; (b) coletores quebram silenciosamente
quando HTML muda — golden files detectam; (c) CI barata e determinística.

### ADR-0007 — Postgres como fonte única da verdade; objetos brutos fora do banco
Postgres (JSONB + pgvector) para domínio, evidências e vetores; *object storage* para
snapshots imutáveis. Sem microsserviços na fase inicial: um monólito modular.
*Por quê:* simplicidade operacional para um escritório; complexidade distribuída não
resolve nenhum problema que temos agora.

### ADR-0008 — Autonomia limitada a originação e análise
O sistema não executa atos externos. Teto de lance é decisão de comitê, registrada.
*Por quê:* ética profissional, risco patrimonial e responsabilidade civil.

### ADR-0009 — Muralha ética implementada em código, não em política
Toda evidência carrega `origem ∈ {pública, cliente, relacionamento, interna}`. Só
`pública` alimenta o pipeline de investimento. Tentativa de vazamento é erro de
execução, não advertência.
*Por quê:* somos um escritório de advocacia; ver doc 06.

### ADR-0010 — Uma classe de ativo de cada vez, com fatia vertical completa
Fase 1 entrega uma classe do edital ao dossiê, ponta a ponta, antes de ampliar.
*Por quê:* prova a arquitetura inteira com risco mínimo; evita o clássico "muitos
coletores, nenhuma decisão".

### ADR-0011 — Veículo de aquisição próprio e segregado
*Decisão dos sócios em 12/09/2026.* A aquisição se dará por estrutura própria
(holding/fundo/clube) formalmente separada da atividade advocatícia; o escritório não
arremata em nome próprio.
*Consequências arquiteturais:* (a) o Portão 1 depende da base de processos do escritório
para cruzamento automático — insumo obrigatório, não opcional; (b) as pessoas vinculadas
ao veículo entram numa lista verificada contra o art. 497, III, do Código Civil; (c) o
dossiê precisa ser apresentável a um comitê de governança do veículo, com procedência
completa; (d) o parecer interno do doc 06, § 8.2, é pré-requisito da **primeira
aquisição**, não do desenvolvimento.

### ADR-0012 — Pipeline multiclasse desde o dia 1, profundidade de valuation escalonada
*Decisão dos sócios em 12/09/2026: "todos, com primazia aos imóveis urbanos".*
Refina o ADR-0010: o **funil não é filtrado por classe** — todo ativo concursal é
detectado, classificado e catalogado desde a Fase 1, qualquer que seja a classe. O que é
escalonado é a **profundidade do valuation**, controlada por um atributo explícito:

| `maturidade_valuation` | Significado | Efeito |
|---|---|---|
| `CALIBRADO` | modelo validado contra preços realizados (MAPE medido) | pode ser promovido ao feed com confiança plena |
| `ESTIMADO` | método defensável, ainda sem calibração local | entra no feed com teto de confiança e rótulo visível |
| `TRIAGEM` | apenas catalogado e monitorado; valor não estimável ainda | aparece na fila de diligência, nunca como recomendação |

Ordem de promoção a `CALIBRADO`: `IMOVEL_URBANO` → `PLANTA_INDUSTRIAL`/galpão →
`MAQUINA_EQUIPAMENTO`/`VEICULO` → `UPI` → `CARTEIRA_CREDITO`/`PRECATORIO` → demais.
*Por quê:* atende à primazia do imóvel urbano sem perder nenhuma oportunidade das outras
classes por omissão de cobertura — e mantém a honestidade do sistema, porque a incerteza
fica rotulada em vez de disfarçada.

### ADR-0013 — Cobertura SP–RJ–MG–PR sem construir três raspadores de tribunal
*Decisão dos sócios em 12/09/2026.* Comarcas-alvo: eixo SP–RJ–MG–PR.
Combinada com o ADR-0014, a consequência é favorável: **DataJud e DJEN são nacionais**,
logo os quatro tribunais são cobertos por dois adaptadores, não por quatro. A coleta
documental (RMA, plano, laudo, edital) é organizada **por ator** — administrador judicial
e leiloeiro — e não por sistema processual (eSAJ/PJe/eproc/Projudi). Isso evita a
multiplicação de raspadores de tribunal na Fase 1 e concentra o esforço onde o documento
realmente está.
*Consequência:* o ranking de esforço da Fase 1 é dado pelos **30 maiores AJs e
leiloeiros com histórico concursal no eixo**, não pela geografia.

### ADR-0014 — Só fontes oficiais gratuitas na Fase 1
*Decisão dos sócios em 12/09/2026.* Núcleo apoiado exclusivamente em DataJud e DJEN.
Provedor pago (Escavador, JUDIT, Digesto, Kurier) é reavaliado na Fase 2, com decisão
baseada em número medido: custo por oportunidade promovida e ganho real de latência.
*Por quê:* nossa vantagem é antecipação de meses, não de minutos — pagar por latência de
minutos antes de provar o funil seria otimizar a variável errada. Efeito colateral
desejado: o modelo canônico não nasce acoplado ao formato de nenhum fornecedor.

## 7. Pilha tecnológica proposta

| Camada | Escolha | Justificativa |
|---|---|---|
| Linguagem | Python 3.11+, `uv`, `ruff`, `mypy`, `pytest` | ecossistema de dados/PDF/ML; contratação fácil |
| Domínio | Pydantic v2 + SQLAlchemy 2 + Alembic | validação e migração sérias |
| Banco | PostgreSQL 16 (JSONB, `pgvector`) | um banco resolve relacional, documento e vetor |
| Snapshots | *object storage* S3-compatível (MinIO local) | imutabilidade e custo |
| Orquestração | fase 1: CLI + cron; fase 3+: Prefect | não pagar complexidade antes da hora |
| Coleta | `httpx` + `selectolax`; Playwright só quando indispensável | leveza e polidez |
| Documentos | `pypdfium2`/`pdfplumber` + OCR (`ocrmypdf`/Tesseract) | autos e laudos são PDF escaneado |
| LLM | Claude (Opus/Sonnet) com *structured outputs* | leitura jurídica e extração citada |
| API/UI | FastAPI + HTMX/Jinja (fase 4) | UI é consequência, não ponto de partida |
| Alertas | e-mail + WhatsApp/Telegram (fase 4) | onde a decisão acontece |
| Infra | Docker Compose (fase 1–3) | roda no escritório e na nuvem |

## 8. Layout do repositório (proposto)

```
docs/                      # este conjunto de decisões (vive e é versionado)
src/hasta/
  core/                    # entidades, máquinas de estado, Evidência, tipos monetários
  sources/                 # um módulo por fonte: datajud, djen, pnaj, esaj, leiloeiros/*, aj/*
  ingest/                  # agendador, fetcher polido, snapshot store, dedupe
  extract/                 # parsers, OCR, tabelas, extratores LLM + validadores
  resolve/                 # resolução de entidades, construtor de linha do tempo
  enrich/                  # comparáveis, geo, ônus, dados de mercado
  score/                   # valor justo, blindagem, risco processual, liquidez, competição
  compliance/              # portões, muralha, registro de auditoria
  agents/                  # prompts + esquemas + evals de cada agente especialista
  report/                  # dossiê, alertas
  api/  cli.py
tests/
  fixtures/                # amostras reais (anonimizadas quando necessário)
  unit/ integration/ evals/  golden/
infra/                     # docker-compose, migrações, seeds
```

## 9. Requisitos não funcionais

- **Reprodutibilidade:** `hasta replay <snapshot_id>` reproduz o resultado bit a bit.
- **Polidez de coleta:** limite por domínio, `robots.txt`, *backoff*, identificação de
  agente, janelas de horário. Fonte oficial sempre preferida a raspagem (doc 06).
- **Custo por fonte instrumentado:** cada chamada paga (API, LLM, OCR) é medida e
  atribuída à oportunidade — para saber o custo unitário de originação.
- **Degradação graciosa:** fonte indisponível reduz `Confiança`, não derruba pipeline.
- **Auditoria:** log append-only de quem/o quê/quando, incluindo decisões de portão.
- **Segurança:** segredos fora do repositório; dados de devedores PF pseudonimizados;
  acesso por papel; banco cifrado em repouso.

## 10. Modos de falha previstos e resposta

| Falha | Sintoma | Mitigação desenhada |
|---|---|---|
| Coletor quebra com mudança de HTML | queda silenciosa de volume | golden files + alerta de variação de volume por fonte |
| Extração LLM alucina valor | número sem lastro | citação obrigatória + validação cruzada + reconciliação aritmética |
| Fusão indevida de entidades | dois devedores viram um | *blocking* por CNPJ/matrícula + revisão humana de fusões de baixa confiança |
| Laudo defasado tratado como verdade | deságio ilusório | idade do laudo é *feature* penalizadora explícita |
| Excesso de candidatos (ruído) | comitê ignora o feed | portões + ranking por p10 + limite diário de itens promovidos |
| Sobreajuste do score | backtest ótimo, prática ruim | validação temporal (*out-of-time*), não aleatória (doc 07) |
| Bloqueio de fonte / mudança regulatória | perda de cobertura | adaptadores isolados; PNAJ já prevista |
