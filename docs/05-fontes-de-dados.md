# 05 — Registro de fontes de dados

> Cada fonte é um adaptador isolado (ADR-0002) com: método de acesso, cobertura,
> latência, custo, postura jurídica e amostras em `tests/fixtures/`.
> Semáforo de postura: 🟢 fonte oficial/API pública · 🟡 público com termos a checar ·
> 🔴 raspagem sensível ou termos restritivos (evitar; usar só com parecer interno).

## 1. Fontes de origem processual (o funil P0–P3)

| Fonte | O que entrega | Acesso | Latência | Postura |
|---|---|---|---|---|
| **DataJud (API Pública CNJ)** | metadados de capa + movimentações codificadas (TPU) de todos os tribunais e instâncias; base nacional (Res. CNJ 331/2020) | REST em `api-publica.datajud.cnj.jus.br/<alias-do-tribunal>`, requer API key | D+1 a D+30 (varia por tribunal) | 🟢 |
| **DJEN (Diário de Justiça Eletrônico Nacional)** | **texto** das publicações/comunicações; concentra os diários dos tribunais (Res. CNJ 455/2022) | API de comunicações | D+0/D+1 | 🟢 |
| **PNAJ** (Prov. CN-CNJ 255/2026) | ambiente único das alienações judiciais eletrônicas; editais e autos gerados automaticamente | a definir (ainda pendente de homologação) | D+0 | 🟢 (prioridade máxima quando existir) |
| **Sistemas de tribunal** (eSAJ, PJe, eproc, Projudi) | autos públicos, peças, laudos, planos | consulta pública / raspagem controlada | D+0 | 🟡 (respeitar limites e segredo de justiça) |
| **Sites de administradores judiciais** | RMAs, editais, planos, listas de credores, laudos — **a fonte mais rica e menos explorada** | HTTP + PDF/OCR | D+0 | 🟡 |
| **Diários oficiais estaduais/União** | editais e atos não capturados no DJEN | API/raspagem | D+0/D+1 | 🟢/🟡 |
| **Juntas comerciais / CNPJ (Receita)** | atos societários, sócios, CNAE, situação cadastral | dados abertos CNPJ + API | mensal | 🟢 |
| **Provedores privados** (Escavador, JUDIT, Digesto, Predictus, Kurier) | monitoramento normalizado, captura antecipada, webhooks | API paga | minutos | 🟢 contratual |

**Decisão de projeto:** começar por DataJud + DJEN (gratuitos, oficiais, cobertura
nacional) e usar provedor privado como **acelerador seletivo** — só para as comarcas e
carteiras prioritárias, onde a latência paga a si mesma. O modelo canônico não deve
depender do formato de nenhum provedor privado.

### Pontos a validar na Fase 1 (spikes técnicos)
- `⚠` DataJud: profundidade histórica real por tribunal, presença dos códigos TPU de
  interesse (deferimento de RJ, decretação de falência, designação de leilão) e limites
  de requisição.
- `⚠` DJEN: é possível busca por termo livre (ex.: "unidade produtiva isolada",
  "designo leilão") ou só por processo/parte/OAB? Isso muda a estratégia de varredura.
- `⚠` PNAJ: interface, existência de API ou feed, e o vocabulário do checklist do Anexo I.
- `⚠` Cobertura de sites de AJs: quantos publicam documentos de forma estável e
  raspável (amostra dos 30 maiores AJs do eixo-alvo).

## 2. Fontes da oferta pública (P4)

| Fonte | Nota |
|---|---|
| **Leiloeiros credenciados** (Sodré Santoro, Superbid Exchange, Zukerman, Mega, Frazão, Biasi e os credenciados por tribunal) | fonte primária de lote; HTML heterogêneo; muitos exigem cadastro. Prioridade: leiloeiros com histórico em falência/RJ nas comarcas-alvo, não "todos" |
| **Agregadores** (LeilôAI, Radar Leilão, Núcleo, Zuk) | 🔴 **não raspar.** Usar apenas como *benchmark* manual de cobertura e como verificação de que não perdemos lote relevante |
| **Editais em jornal de grande circulação** | ainda exigidos em certas hipóteses; capturáveis via diários e por OCR |

## 3. Fontes de valoração e verificação de ativo

| Fonte | Uso | Postura |
|---|---|---|
| Índice FipeZAP / DataZAP | correção e sanidade de valores de imóvel | 🟢 índice público / 🟡 dados granulares |
| AVMs comerciais (Urbit e similares) | *check* independente de valor de apartamento | 🟢 contratual |
| Dados abertos municipais (IPTU/valor venal, ITBI) | piso e comparável fiscal; São Paulo e capitais publicam | 🟢 |
| Registro de imóveis eletrônico (SREI/ONR) | matrícula, ônus, cadeia dominial — **verificação decisiva** | 🟡 pago por certidão |
| Tabela FIPE | veículos | 🟢 |
| Mercado secundário de máquinas | comparáveis industriais | 🟡 |
| INCRA/SIGEF, CAR, IBGE/SIDRA, INPE/MapBiomas | imóvel rural: georreferenciamento, reserva, uso do solo | 🟢 |
| INPI | marcas e patentes | 🟢 |
| IBGE, RAIS/CAGED, ANTT e setoriais | profundidade de mercado regional, contexto setorial | 🟢 |
| Notícias e mídia especializada | contexto, disputa, sinais de grupo econômico | 🟡 (nunca como única evidência de número) |

## 4. Mapa "sinal → fonte → antecipação"

| Sinal (o que queremos saber primeiro) | Onde aparece primeiro | Antecipação vs. edital |
|---|---|---|
| Empresa com ativos relevantes entrou em RJ | DataJud (movimento) + DJEN (publicação do deferimento) | 12–24 meses |
| Quem é o AJ e qual a qualidade documental esperada | DJEN + site do AJ | 12–18 meses |
| Quais ativos existem e quanto valem no laudo | auto de arrecadação / RMA / laudo no site do AJ ou nos autos | 3–12 meses |
| Plano prevê venda de UPI | plano no site do AJ ou nos autos (leitura LLM com citação) | 2–8 meses |
| Venda autorizada (art. 66 / homologação) | DJEN + autos | 1–6 meses |
| Leiloeiro nomeado e praça designada | DJEN + site do leiloeiro | 15–90 dias |
| Edital com lance mínimo e condições | leiloeiro / DJEN / PNAJ | 0 (o mercado acorda aqui) |

Este mapa é a especificação funcional do **Batedor**: para cada linha, um detector com
meta de *recall* medida contra histórico (doc 07).

## 5. Regras de coleta (invioláveis)

1. **Fonte oficial antes de raspagem.** Se existe API pública, raspar é bug.
2. **Polidez:** limite por domínio, `robots.txt` respeitado, *user-agent* identificável
   com contato, janelas de baixa carga, *backoff* exponencial.
3. **Sem burlar proteção:** não contornamos captcha, *paywall*, login ou bloqueio
   técnico. Bloqueio técnico é decisão do titular do site e se respeita.
4. **Segredo de justiça:** processo sigiloso é excluído da coleta e do pipeline; se
   entrar por engano, é expurgado com registro.
5. **Minimização (LGPD):** coleta-se o necessário ao propósito; dado de pessoa física é
   pseudonimizado no armazenamento analítico (doc 06).
6. **Snapshot imutável:** guarda-se o que se viu, com hash — é o que sustenta o dossiê
   perante o comitê e, se preciso, perante um juízo.
7. **Custo medido:** toda fonte paga tem orçamento e alerta de consumo.

## 6. Situação do ambiente de desenvolvimento

O sandbox atual bloqueia por política de egresso todos os domínios `*.jus.br`, sites de
leiloeiros e portais imobiliários (verificado em 12/09/2026: retorno `000` para
`api-publica.datajud.cnj.jus.br`, `cnj.jus.br`, `sodresantoro.com.br`, `portalzuk.com.br`;
apenas repositórios de pacotes e GitHub acessíveis). Consequências práticas:

- os **spikes de validação de API** (DataJud, DJEN, PNAJ) precisam rodar no ambiente do
  escritório ou num ambiente com liberação de egresso — é a primeira tarefa de
  infraestrutura da Fase 1;
- aqui, desenvolvemos e testamos contra `tests/fixtures/` com amostras reais coletadas
  no ambiente liberado (ADR-0006);
- vantagem colateral: a suíte de testes fica rápida, determinística e barata.
