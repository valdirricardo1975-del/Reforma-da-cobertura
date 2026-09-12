# 07 — Roteiro por fases, com critérios de aceite

> Regra do projeto: **nenhuma fase avança sem critério de aceite verificado.**
> Cada fase entrega algo utilizável, não um pedaço de encanamento.

## Fase 0 — Arquitetura e alinhamento  ← *estamos aqui*

**Entrega:** docs 00 a 07 (pesquisa, tese, arquitetura, domínio, motores, fontes,
compliance, roteiro) + registro de decisões (ADR-0001 a 0010).

**Aceite:** sócios validam (a) a definição de oportunidade do doc 01, (b) os seis eixos
de diferenciação do doc 00, § 5, (c) a fronteira de autonomia (ADR-0008), (d) as
respostas às quatro perguntas de alinhamento; e decidem o escopo da fatia vertical.

## Fase 1 — Fatia vertical: de um edital a um dossiê

**Escopo consolidado pelas decisões de 12/09/2026** (ADR-0011 a 0014):

| Dimensão | Decisão |
|---|---|
| Adquirente | veículo próprio segregado; Portão 1 exige a base de processos do escritório |
| Classes de ativo | **todas** no funil; valuation escalonado por `maturidade_valuation`, com primazia do imóvel urbano |
| Geografia | eixo SP–RJ–MG–PR — coberto por 2 adaptadores nacionais, não por 4 raspadores de tribunal |
| Fontes | DataJud + DJEN apenas; documentos por ator (AJ e leiloeiro), não por sistema processual |

Objetivo: provar a arquitetura inteira ponta a ponta com **uma** classe calibrada
(imóvel urbano) e todas as demais em triagem catalogada.

**Entrega**
1. `core/` — entidades, `Evidencia`, `Money`, máquinas de estado, mapeamento TPU→evento;
2. adaptadores **DataJud** (movimentações/TPU) e **DJEN** (texto das publicações);
3. `extract/` — parser de edital + extrator LLM com citação obrigatória;
4. `score/` v0 — valor justo de imóvel urbano (`CALIBRADO`), blindagem por regras,
   checklist de vícios; TIR ajustada com p10/p50/p90; demais classes em `TRIAGEM`;
5. `compliance/` — Portões 1 e 2 funcionando (o 2 exige a base de processos do escritório);
6. `report/` — dossiê em PDF/HTML com procedência de cada número;
7. `tests/` — *fixtures* reais + golden files; suíte roda offline.

**Spikes de validação (bloqueantes, exigem ambiente com egresso liberado)**
- DataJud: profundidade histórica, presença dos códigos TPU de interesse, limites;
- DJEN: busca por termo livre é possível? (decide a estratégia de varredura);
- PNAJ: existe interface/feed? qual o vocabulário do Anexo I do Prov. 255/2026?
- amostragem: dos 30 maiores administradores judiciais, quantos publicam RMA/laudo/plano
  de forma estável?

**Aceite**
- 10 lotes reais de imóvel urbano processados ponta a ponta, com dossiê revisado por
  advogado do time; e ≥ 20 lotes de outras classes corretamente classificados e
  catalogados em `TRIAGEM`, sem valor estimado indevidamente;
- **100%** dos números com procedência rastreável (auditoria manual em 3 dossiês);
- zero falso-negativo no Portão 1 em conjunto de teste com processos do escritório;
- `hasta replay` reproduz resultado idêntico a partir do snapshot;
- as afirmações marcadas `⚠ verificar` nos docs 01, 03 e 04 conferidas em lei/jurisprudência
  e convertidas em regra ou removidas.

## Fase 2 — Originação a montante (o diferencial)

**Entrega:** Batedor com os detectores do mapa "sinal → fonte → antecipação" (doc 05, § 4);
linha do tempo concursal preenchida; **Mapa de Ativos por Devedor**; leitura de plano com
detecção de cláusula de UPI; grafo de atores processuais v1.

**Aceite**
- cobertura: ≥ 90% das RJs e falências ativas nas comarcas-alvo com procedimento
  cadastrado e estado correto (amostra auditada de 50 casos);
- **Índice de Antecipação mediano ≥ 90 dias** num conjunto retrospectivo de 30 leilões
  concursais já ocorridos (teríamos detectado com 90+ dias de antecedência?);
- *recall* ≥ 0,85 nos detectores de `PLANO_COM_UPI`, `AUTORIZACAO_ART_66` e
  `LEILAO_DESIGNADO`, medido contra o histórico;
- Mapa de Ativos com ≥ 70% dos bens do auto de arrecadação capturados em 10 falências.

## Fase 3 — Motores calibrados e conjunto de ouro

**Entrega:** conjunto de ouro de 80–120 lotes resolvidos; calibração *out-of-time*;
motores de liquidez, risco processual e competição; Advogado do Diabo e Caçador de
Vícios em produção; `Confiança` operando a fila de diligência.

**Aceite**
- Avaliador: MAPE ≤ 20% (imóvel urbano) contra preço final realizado, sem viés > 5%;
- `P(anulado)` e `P(ocorre)` calibradas (erro de calibração ≤ 0,1);
- *precision@20* ≥ 0,6 no período de teste — dos 20 melhores do ranking, 12+ superariam
  o piso de retorno;
- Spearman entre ranking e retorno realizado ≥ 0,45;
- Advogado do Diabo: ≥ 70% dos riscos que se materializaram estavam listados.

## Fase 4 — Operação: feed, alertas, dossiê vivo, comitê

**Entrega:** feed ordenado por TIR p10; alertas por e-mail/WhatsApp com janela de ação;
dossiê vivo com *diff*; fluxo de comitê (aprovação, teto de lance, ata); "pergunte aos
autos" sobre o acervo da oportunidade.

**Aceite**
- ≤ 15 itens promovidos por dia (feed decidível, não mural);
- taxa de "isso não deveria estar aqui" pelos sócios < 20% em 4 semanas;
- 100% dos alertas com janela de ação correta (prazo de habilitação, caução, visita);
- tempo da detecção ao alerta < 6 horas para eventos de P4.

## Fase 5 — Multiclasse e rotas indiretas

**Entrega:** UPI (*going concern*), planta industrial, máquinas, carteira de crédito;
motor de rota de acesso completo; monitor de créditos concursais e de cessões.

**Aceite:** ao menos uma oportunidade por rota indireta levada ao comitê com tese
completa; MAPE ≤ 30% em máquinas/equipamentos.

## Fase 6 — Escala e aprendizado contínuo

**Entrega:** cobertura nacional priorizada por densidade de RJ/falência; adaptador da
PNAJ em produção; L9 recalibrando automaticamente; painel de desempenho do próprio agente.

**Aceite:** recalibração automática melhora *precision@20* em relação ao modelo congelado;
custo unitário de originação por oportunidade promovida medido e decrescente.

## Painel permanente de KPIs

| KPI | Por que importa |
|---|---|
| **Índice de Antecipação** (mediana de dias antes do edital) | mede o diferencial nº 1 |
| Cobertura de RJs/falências ativas nas comarcas-alvo | mede o funil |
| *Precision@20* e Spearman do ranking | mede se o score decide bem |
| MAPE do Avaliador por classe | mede se o valor justo é justo |
| Calibração de `P(anulado)` / `P(ocorre)` | mede honestidade do risco |
| Itens promovidos/dia e taxa de rejeição humana | mede utilidade real |
| % de números com procedência completa | mede auditabilidade |
| Bloqueios de compliance (e zero vazamentos de origem restrita) | mede segurança institucional |
| Custo unitário por oportunidade promovida | mede sustentabilidade |
| Taxa de conversão: promovida → comitê → lance → arremate → saída | mede o negócio |

## Riscos do projeto e resposta

| Risco | Resposta |
|---|---|
| PNAJ muda tudo no meio do caminho | adaptadores isolados + modelo canônico alinhado ao Prov. 255/2026 desde já |
| Provedor privado de dados encarece ou restringe | núcleo depende só de DataJud/DJEN; privado é acelerador |
| Ambiente sem egresso atrasa spikes | primeira tarefa de infra da Fase 1 é liberar ambiente de coleta |
| Escopo inflar (todas as classes, todo o Brasil) | ADR-0010: uma classe, uma comarca, ponta a ponta |
| Conjunto de ouro difícil de montar | começar com 30 casos das comarcas onde o escritório tem histórico |
| Score sobreajustado | validação *out-of-time* obrigatória e testes de regressão de decisão |
| Dependência de conhecimento tácito dos sócios | grafo de atores captura e versiona esse conhecimento |
