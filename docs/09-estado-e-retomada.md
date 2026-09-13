# 09 — Estado do projeto e ponto de retomada

> **Desenvolvimento suspenso em 13/09/2026**, a pedido, para avaliação da proposta
> NEXUM Capital & Recovery (concepção paralela do provável sócio). Este documento
> existe para que a retomada não perca contexto: o que foi decidido, o que está
> pronto, o que está pendente e em que ordem continuar.

## 1. O que é o projeto

**HASTA** — agente de originação e análise de oportunidades de aquisição de ativos em
alienação judicial, com foco em recuperação judicial e falência. Entra no funil no
deferimento do processamento (3 a 18 meses antes do edital), não na vitrine do edital
como fazem os agregadores do mercado.

Seis eixos de diferenciação (doc 00, § 5): originação a montante, blindagem sucessória
pontuada, risco processual modelado, valuation multiclasse, grafo de atores processuais,
rota de acesso calculada. Mais um sétimo obrigatório num escritório de advocacia:
muralha ética com trilha auditável da origem de cada informação.

## 2. Decisões tomadas (não reabrir sem motivo novo)

| ADR | Decisão |
|---|---|
| 0001 | Núcleo de domínio antes de coletores |
| 0002 | Fontes como adaptadores plugáveis; PNAJ como cidadã de primeira classe |
| 0003 | Procedência obrigatória: `Evidencia` como primitiva |
| 0004 | Determinismo onde vira número; LLM onde vira leitura |
| 0005 | Incerteza explícita em p10/p50/p90; ranking pelo p10 |
| 0006 | Desenvolvimento offline-first contra *fixtures* reais |
| 0007 | Postgres como fonte única da verdade; monólito modular |
| 0008 | Autonomia limitada a originação e análise — o agente nunca dá lance |
| 0009 | Muralha ética implementada em código |
| 0010 | Uma fatia vertical completa antes de ampliar |
| 0011 | **Veículo de aquisição próprio e segregado** (decisão dos sócios, 12/09/2026) |
| 0012 | Pipeline multiclasse desde o dia 1; valuation escalonado, primazia do imóvel urbano |
| 0013 | Cobertura SP–RJ–MG–PR sem construir três raspadores de tribunal |
| 0014 | Só fontes oficiais gratuitas (DataJud + DJEN) na Fase 1 |

**Atenção na retomada:** o ADR-0011 foi decidido antes de a proposta NEXUM entrar em
cena. Se a NEXUM (ou estrutura equivalente) virar o veículo de aquisição, o ADR-0011
precisa ser reescrito — e o Portão 1 de compliance (doc 06, § 1) passa a ter de cruzar
não só a base de processos do escritório, mas também o pipeline e a carteira da NEXUM.

## 3. O que está pronto e funcionando

Código em `src/hasta/`, 141 testes passando offline, `ruff` e `mypy strict` sem erros.

| Módulo | Entrega |
|---|---|
| `core/money.py` | dinheiro exato em centavos; `float` recusado; correção por índice declarado obrigatória |
| `core/intervalo.py` | `Faixa` p10/p50/p90; soma de quantis recusada |
| `core/cnj.py` | número único CNJ: malformado levanta erro, dígito inconsistente é sinalizado |
| `core/enums.py` | vocabulário controlado + `MaturidadeValuation` |
| `core/eventos.py` | taxonomia de eventos e funil P0–P5 com antecipação por estágio |
| `core/estados.py` | máquinas de estado do procedimento concursal e da oportunidade |
| `core/evidencia.py` | procedência e muralha ética: origem pegajosa, portão que levanta exceção |
| `core/entidades.py` | entidades canônicas do doc 03 |
| `score/explicacao.py` | conta aberta; teto vence soma de ajustes |
| `score/blindagem.py` | Grau de Blindagem 0–100, 23 regras catalogadas |
| `score/vicios.py` | checklist de 14 nulidades; risco detectado e incerteza reportados separadamente |
| `report/catalogo.py` | doc 08 gerado do motor, com teste anti-divergência |
| `scripts/demonstrar.py` | demonstração em português de três lotes de exemplo |

## 4. Pendências herdadas

### 4.1 Sete premissas jurídicas a validar (doc 08, § 8)

Já influenciam número e estão marcadas no catálogo. Em ordem de impacto:

| Regra | Pergunta |
|---|---|
| **N01** | O art. 142, § 2º, da Lei 11.101/2005 permite alienação pelo maior valor ofertado ainda que inferior à avaliação? (é metade da tese do nicho) |
| **B03** | A não sucessão do art. 141 alcança as modalidades alternativas dos arts. 144 e 145? |
| **B15** | Bem em alienação fiduciária ou arrendamento: lote arriscado ou impróprio? |
| **B17** | Exposição real à tese de sucessão trabalhista com consolidação substancial |
| **B20** | Débito condominial anterior com edital silente: segue o arrematante ou sub-roga no preço? |
| **V01** | A lista de intimações obrigatórias do art. 889 do CPC utilizada está completa? |
| **V02** | Prazo mínimo entre publicação do edital e a praça (adotados 5 dias) |

### 4.2 Bloqueios de ambiente

O ambiente de desenvolvimento remoto bloqueia, por política de egresso, todos os
domínios `*.jus.br`, sites de leiloeiros e portais imobiliários. Consequências:

- os *spikes* de DataJud, DJEN e PNAJ precisam rodar em ambiente do escritório;
- o mapeamento `código TPU → evento` está vazio e marcado em `CODIGOS_TPU_PENDENTES`,
  com teste que o mantém visível — preencher de memória plantaria erro silencioso;
- as sete premissas acima não puderam ser conferidas em fonte primária.

### 4.3 Insumos que dependem do escritório

1. Base de processos do escritório (todas as OABs, sócios e associados) — é o insumo do
   Portão 1; sem ela a verificação de impedimento do advogado da causa não funciona.
2. Três a cinco editais reais de leilão em falência ou RJ, em PDF, para servirem de
   *fixture* do extrator de editais.
3. Parecer interno sobre aquisição de ativos concursais por estrutura ligada ao
   escritório (doc 06, § 8) — agora entrelaçado com a análise da NEXUM.

## 5. Ordem de retomada sugerida

1. **Decidir o veículo** (NEXUM, estrutura própria ou ambos) — porque isso define o
   Portão 1, o desenho da muralha e quem é o destinatário do dossiê.
2. Validar as sete premissas jurídicas e aplicar no catálogo.
3. Rodar os *spikes* de DataJud, DJEN e PNAJ em ambiente com egresso liberado.
4. Escriba: extrator de edital com citação obrigatória, contra *fixtures* reais.
5. Adaptadores DataJud e DJEN; preencher o mapeamento TPU.
6. Motor de valor justo para imóvel urbano; promover a classe a `CALIBRADO`.
7. Dossiê e fluxo de comitê.

Detalhamento de fases e critérios de aceite: doc 07.

## 6. Como reproduzir o ambiente

```bash
uv venv && uv pip install -e ".[dev]"
.venv/bin/python -m pytest -q          # 141 testes, sem rede
.venv/bin/python scripts/demonstrar.py # vê os motores rodando em português
.venv/bin/python scripts/gerar_catalogo.py
```
