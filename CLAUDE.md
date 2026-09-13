# HASTA — memória do projeto

Agente de originação e análise de ativos em alienação judicial, com foco em recuperação
judicial e falência. Escritório de advocacia especializado em insolvência.

## Estado

**Desenvolvimento suspenso em 13/09/2026** para avaliação da proposta NEXUM Capital &
Recovery (veículo societário concebido em paralelo pelo provável sócio). Antes de retomar
código, leia **`docs/09-estado-e-retomada.md`** — traz decisões, pendências e a ordem de
retomada.

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
.venv/bin/python scripts/demonstrar.py      # demonstração em português
.venv/bin/python scripts/gerar_catalogo.py  # regenera docs/08 (teste falha se divergir)
```

`reforma.html` na raiz é legado, sem relação com este projeto.
