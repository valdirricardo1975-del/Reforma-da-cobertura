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

## Estado atual

**Fase 0 — arquitetura e alinhamento.** Nenhum código de produção ainda: por decisão de
projeto (ADR-0001), o modelo de domínio e os critérios de aceite vêm antes dos coletores.
A Fase 1 entrega uma fatia vertical completa — de um edital real a um dossiê auditável.

Pendências que exigem decisão dos sócios estão listadas no doc 06, § 8, e no doc 07,
Fase 0.

---

*`reforma.html` na raiz é um arquivo legado, sem relação com este projeto.*
