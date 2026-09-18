# HASTA — memória do projeto

Agente de originação e análise de ativos em alienação judicial, com foco em recuperação
judicial e falência. Escritório de advocacia especializado em insolvência.

## Estado

**Desenvolvimento retomado em 18/09/2026**, com escopo e estrutura definidos
(ADR-0015 a 0017):

- **Escopo:** apenas busca, análise, compra e venda de **ativos estressados,
  principalmente imóveis**. Fomento/recebíveis e recuperação tributária ficaram fora.
- **Sociedade:** três partes iguais — Schmitti; Castor e Analice (Delivar e Mattos);
  DCVM (Valdir, Daniel e Rosana) — R$ 2,5 milhões de subscrição cada.
- **Funding:** R$ 100 milhões do sócio financiador, remunerados pelo CDI, com
  preferência nas retiradas até a quitação dos aportes.
- **Prioridade declarada:** o agente de busca e avaliação de ativos.

Contexto e pendências: **`docs/09-estado-e-retomada.md`**.

## Leituras obrigatórias antes de mexer

| Doc | Para quê |
|---|---|
| `docs/09-estado-e-retomada.md` | estado atual, pendências, ordem de retomada |
| `docs/02-arquitetura.md` § 6 | ADR-0001 a 0014 — decisões que não se reabrem sem motivo novo |
| `docs/01-tese-e-definicao-de-oportunidade.md` | o que conta como oportunidade e por quê |
| `docs/06-compliance-etica-e-seguranca.md` | portões que bloqueiam; muralha ética |
| `docs/08-catalogo-de-regras.md` | **gerado do código** — não editar à mão |

## Invariantes que não se negociam

- **Determinismo onde vira número; LLM onde vira leitura.** Nenhum score sai de um LLM.
- **Nenhum número sem evidência** (documento + trecho + hash + data de coleta).
- **Incerteza explícita** em p10/p50/p90; ranking pelo p10.
- **Teto em vez de desconto** para lacuna de verificação.
- **Risco detectado ≠ incerteza de verificação** — dois números, nunca um.
- **Deságio não é retorno.** Ranking é por TIR líquida do carrego, nunca por desconto
  sobre laudo. Prazo é variável de primeira ordem.
- **Teto de lance sai do cenário pessimista**, não do central.
- **Margem até a ruína andando junto com a TIR** em qualquer operação alavancada.
- **Origem da informação é pegajosa**: derivação herda a mais restritiva. Só origem
  pública alimenta decisão de investimento; violação levanta exceção, não aviso.
- **O agente nunca dá lance.** Autonomia é originar e analisar.

## Interlocutor

Não é programador. Explicar em linguagem de negócio e de direito, com exemplos
concretos; mostrar saída do sistema em vez de descrever código. Preferência declarada:
fazer perguntas de esclarecimento e alinhamento antes de decidir.

## Comandos

```bash
uv venv && uv pip install -e ".[dev]"
.venv/bin/ruff check . && .venv/bin/mypy && .venv/bin/python -m pytest -q
.venv/bin/python scripts/demonstrar.py        # blindagem e vícios, em português
.venv/bin/python scripts/demonstrar_lance.py  # retorno, carrego e teto de lance
.venv/bin/python scripts/gerar_catalogo.py  # regenera docs/08 (teste falha se divergir)
```

`reforma.html` na raiz é legado, sem relação com este projeto.
