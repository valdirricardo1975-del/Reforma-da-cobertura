# HASTA — agente de originação de ativos em alienação judicial

Agente autônomo de **originação e análise** de oportunidades de aquisição de ativos em
leilões judiciais e procedimentos assemelhados, com foco em **recuperação judicial e
falência**.

> *Sub hasta* — em Roma, as vendas públicas eram feitas sob a lança fincada no solo.
> Daí "hasta pública". Nome de trabalho, sujeito a troca.

## O que este agente faz de diferente

O mercado brasileiro de agregadores de leilão (LeilôAI, Radar Leilão, Núcleo, Zuk)
começa a trabalhar **quando o edital é publicado** e mede deságio **contra o laudo de
avaliação**. Nós começamos no **deferimento do processamento da recuperação judicial** —
3 a 18 meses antes — e medimos retorno **ajustado a risco, líquido e com procedência
verificável**.

Seis eixos de diferenciação (doc [00](docs/00-pesquisa-de-mercado.md), § 5):

1. **Originação a montante** — funil P0→P5 do ciclo concursal, não a vitrine do edital.
2. **Blindagem sucessória pontuada** — art. 141, II, da LFR e art. 60, § 1º (UPI) criam
   um perfil de risco que nenhum agregador distingue.
3. **Motor de risco processual** — P(leilão ocorre), P(arrematação anulada), T(posse).
4. **Valuation multiclasse** — inclusive UPI como *going concern*, não só imóvel.
5. **Grafo de atores processuais** — converte o conhecimento do escritório sobre AJs,
   varas e leiloeiros em ativo de dados que compõe com o tempo.
6. **Rota de acesso ótima** — lance, crédito concursal, DIP, *stalking horse*, venda direta.

E um sétimo, obrigatório num escritório de advocacia: **muralha ética em código**, com
trilha auditável da origem de cada informação (doc [06](docs/06-compliance-etica-e-seguranca.md)).

## Princípios

- **Determinismo onde vira número; LLM onde vira leitura.** Nenhum score é gerado por LLM.
- **Nenhum número sem evidência** (documento + trecho + hash + data).
- **Incerteza explícita** — tudo em p10/p50/p90; ranking pelo p10.
- **Autonomia em descobrir e analisar; nunca em dar lance.**

## Documentação

| Doc | Conteúdo |
|---|---|
| [00 — Pesquisa de mercado](docs/00-pesquisa-de-mercado.md) | Quem já faz, como faz, as 7 lacunas, o impacto do Provimento CN-CNJ 255/2026 e da PNAJ |
| [01 — Tese e definição de oportunidade](docs/01-tese-e-definicao-de-oportunidade.md) | A equação de retorno ajustado, portões rígidos, os 5 tipos de oportunidade |
| [02 — Arquitetura](docs/02-arquitetura.md) | Camadas L0–L9, funil de originação, agentes especialistas, ADR-0001 a 0010, pilha técnica |
| [03 — Modelo de domínio](docs/03-modelo-de-dominio.md) | Entidades canônicas, `Evidencia`, máquinas de estado, taxonomia de eventos |
| [04 — Motores e score](docs/04-motor-de-avaliacao-e-score.md) | Valor justo por classe, blindagem, risco processual, liquidez, competição, backtesting |
| [05 — Fontes de dados](docs/05-fontes-de-dados.md) | Registro de fontes com postura jurídica, mapa sinal→fonte→antecipação, regras de coleta |
| [06 — Compliance e ética](docs/06-compliance-etica-e-seguranca.md) | Impedimentos, muralha ética, LGPD/ANPD, segurança, limites de autonomia |
| [07 — Roteiro e validação](docs/07-roadmap-e-validacao.md) | Fases 0–6 com critérios de aceite mensuráveis e painel de KPIs |
| [08 — Catálogo de regras](docs/08-catalogo-de-regras.md) | **Gerado do código.** Cada regra de blindagem e de vícios com fundamento, efeito e status de validação jurídica |
| [09 — Estado e retomada](docs/09-estado-e-retomada.md) | Onde o projeto parou, pendências herdadas e ordem de retomada |

## Estado atual

> **Retomado em 18/09/2026** com escopo definido: apenas ativos estressados,
> principalmente imóveis. Estrutura de capital e parâmetros no
> [doc 09](docs/09-estado-e-retomada.md).

**Fase 1 — núcleo de domínio, motores jurídicos e motor de retorno implementados.** Por decisão de projeto
(ADR-0001), o modelo canônico vem antes dos coletores.

Pronto e coberto por testes (`src/hasta/core/`):

| Módulo | O que garante |
|---|---|
| `money.py` | dinheiro em centavos, `float` recusado; valor histórico só se compara depois de corrigido por índice **declarado** |
| `intervalo.py` | `Faixa` p10/p50/p90; soma de quantis é recusada, porque quantis não somam |
| `cnj.py` | número único CNJ: malformado levanta erro, dígito inconsistente é sinalizado e não descartado |
| `enums.py` | vocabulário controlado, incluindo `MaturidadeValuation` (ADR-0012) |
| `eventos.py` | taxonomia de eventos e funil P0–P5 com antecipação por estágio |
| `estados.py` | máquinas de estado do procedimento concursal e da oportunidade |
| `evidencia.py` | procedência obrigatória e muralha ética: origem pegajosa e portão que levanta exceção |
| `entidades.py` | entidades canônicas do doc 03 |

Motores determinísticos (`src/hasta/score/`):

| Módulo | O que entrega |
|---|---|
| `explicacao.py` | conta aberta: cada ajuste com regra, fundamento e status; teto vence soma de ajustes |
| `blindagem.py` | Grau de Blindagem 0–100 por regime de transmissão, com 23 regras catalogadas |
| `vicios.py` | checklist de 14 nulidades, com risco detectado e incerteza de verificação reportados **separadamente** |
| `retorno.py` | preço total, carrego ao CDI, TIR do equity, margem até a ruína e **teto de lance** |

Duas escolhas que evitam otimismo silencioso:

* **Teto em vez de desconto** para lacuna de verificação — sem certidão de matrícula
  conferida, um ativo de falência não chega a `BLINDADO_FORTE`, mesmo com cláusula
  expressa de não sucessão no edital.
* **Risco detectado ≠ incerteza de verificação.** Um dossiê que diz "risco 5%,
  incerteza 48%, resolva estas 12 diligências" é acionável; um índice único de 53%
  esconde se o problema é o ativo ou a nossa diligência.
* **Deságio não é retorno.** Um lance a 60% da avaliação — "40% de deságio" na linguagem
  dos agregadores — entrega 4,5% ao ano depois de comissão, ITBI, registro, débitos,
  desocupação, regularização, haircut e corretagem. Contra *hurdle* de 25%, reprova.

O catálogo do doc 08 é **gerado a partir do motor** (`python scripts/gerar_catalogo.py`),
e um teste falha se divergir: o que os sócios revisam é necessariamente o que o sistema
aplica. Hoje são 38 regras, 7 marcadas `⚠️ a validar` — inclusive a assimetria central do
nicho (art. 142, § 2º, da Lei 11.101/2005: na falência não há piso de preço vil).

Decisões de escopo tomadas em 12/09/2026: ADR-0011 a 0014 (doc 02, § 6).

**Escolha deliberada:** o mapeamento `código TPU → evento` está vazio e marcado como
pendente (`CODIGOS_TPU_PENDENTES`), com teste que o mantém visível. Preencher de memória
plantaria erro silencioso na base do funil — depende do spike de validação do DataJud.

Pendências que exigem decisão dos sócios: doc 06, § 8.

## Desenvolvimento

```bash
uv venv && uv pip install -e ".[dev]"
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/mypy                 # strict, sem erros
.venv/bin/python -m pytest -q  # roda offline, sem rede (ADR-0006)
```

---

*`reforma.html` na raiz é um arquivo legado, sem relação com este projeto.*
