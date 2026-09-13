"""Gera o catálogo de regras para validação jurídica (doc 08).

O documento é **gerado a partir do próprio motor**: pesos, bases legais e status de
validação saem da mesma fonte que o cálculo usa. Assim o que os sócios revisam é
necessariamente o que o sistema aplica — um teste de regressão impede divergência.
"""

from __future__ import annotations

from hasta.score.blindagem import (
    BASE_POR_REGIME,
    CATALOGO_BLINDAGEM,
    PESOS_BLINDAGEM,
    TETOS_BLINDAGEM,
    FaixaBlindagem,
)
from hasta.score.explicacao import RegraValidavel, StatusRegra
from hasta.score.vicios import (
    CHECKLIST_VICIOS,
    NOTAS_DE_REGIME,
    PESO_INDETERMINADO,
    PRIOR_NULIDADE_POR_SEVERIDADE,
)

CAMINHO_CATALOGO = "docs/08-catalogo-de-regras.md"

_MARCA_STATUS = {
    StatusRegra.VIGENTE: "✅ vigente",
    StatusRegra.A_VALIDAR: "⚠️ a validar",
    StatusRegra.REVOGADA: "⛔ revogada",
}

_FAIXAS = (
    (90, 100, FaixaBlindagem.BLINDADO_FORTE),
    (70, 89, FaixaBlindagem.BLINDADO_COM_RESIDUO),
    (45, 69, FaixaBlindagem.PARCIAL),
    (20, 44, FaixaBlindagem.FRAGIL),
    (0, 19, FaixaBlindagem.INDETERMINADO),
)


def _chaves_por_regra(mapa: dict[str, int]) -> dict[str, list[tuple[str, int]]]:
    agrupado: dict[str, list[tuple[str, int]]] = {}
    for chave, valor in mapa.items():
        agrupado.setdefault(chave.split(".", 1)[0], []).append((chave, valor))
    return agrupado


def gerar_catalogo_markdown() -> str:
    """Produz o conteúdo integral do doc 08."""
    todas: list[RegraValidavel] = [
        *CATALOGO_BLINDAGEM.values(),
        *NOTAS_DE_REGIME.values(),
        *CHECKLIST_VICIOS.values(),
    ]
    a_validar = [r for r in todas if r.status is StatusRegra.A_VALIDAR]
    pesos = _chaves_por_regra(PESOS_BLINDAGEM)
    tetos = _chaves_por_regra(TETOS_BLINDAGEM)

    linhas: list[str] = []
    add = linhas.append

    add("# 08 — Catálogo de regras para validação jurídica")
    add("")
    add("> **Documento gerado automaticamente** a partir de `src/hasta/score/`.")
    add("> Não editar à mão: rode `python scripts/gerar_catalogo.py`.")
    add("> Um teste de regressão falha se o documento divergir do motor.")
    add("")
    add("## Como usar este catálogo")
    add("")
    add("Cada regra tem identificador, base legal, efeito numérico e status. O trabalho de")
    add("validação é percorrer as regras marcadas `⚠️ a validar`, conferir a premissa em")
    add("fonte primária e decidir entre três destinos:")
    add("")
    add("1. **confirmar** — a premissa se sustenta: muda o status para `VIGENTE`;")
    add("2. **corrigir** — a premissa está imprecisa: ajusta-se o texto, a base legal ou o peso;")
    add("3. **revogar** — a premissa não se sustenta: status `REVOGADA`, e a regra deixa de")
    add("   contar no score sem desaparecer do histórico.")
    add("")
    add("Enquanto houver regra `⚠️ a validar` influenciando um número, o resultado do motor")
    add("expõe quais foram, em `regras_a_validar` e `itens_a_validar` — para que ninguém")
    add("decida sem saber.")
    add("")
    add(f"**Situação atual:** {len(todas)} regras, das quais {len(a_validar)} a validar.")
    add("")

    add("## 1. Blindagem — base por regime de transmissão")
    add("")
    add("| Regra | Regime | Base | Fundamento | Status |")
    add("|---|---|---:|---|---|")
    for regime, (regra_id, base) in BASE_POR_REGIME.items():
        regra = CATALOGO_BLINDAGEM[regra_id]
        add(
            f"| {regra_id} | `{regime.value}` | {base} | {regra.base_legal} | "
            f"{_MARCA_STATUS[regra.status]} |"
        )
    add("")

    add("## 2. Blindagem — ajustes")
    add("")
    add("| Regra | Condição | Efeito | Fundamento | Status |")
    add("|---|---|---:|---|---|")
    for regra_id in sorted(pesos):
        regra = CATALOGO_BLINDAGEM[regra_id]
        for chave, valor in pesos[regra_id]:
            condicao = chave.split(".", 1)[1].replace("_", " ")
            sinal = "+" if valor >= 0 else ""
            add(
                f"| {regra_id} | {condicao} | {sinal}{valor} | {regra.base_legal} | "
                f"{_MARCA_STATUS[regra.status]} |"
            )
    add("")

    add("## 3. Blindagem — tetos")
    add("")
    add("Teto é mais honesto que desconto: sem o fato verificado, o ativo não é *um pouco*")
    add("menos blindado — ele não pode ser classificado como blindado.")
    add("")
    add("| Regra | Condição | Teto | Fundamento |")
    add("|---|---|---:|---|")
    for regra_id in sorted(tetos):
        regra = CATALOGO_BLINDAGEM[regra_id]
        for chave, valor in tetos[regra_id]:
            condicao = chave.split(".", 1)[1].replace("_", " ")
            add(f"| {regra_id} | {condicao} | {valor} | {regra.base_legal} |")
    add("")

    add("## 4. Blindagem — faixas do grau")
    add("")
    add("| Faixa | Grau | Leitura |")
    add("|---|---|---|")
    leitura = {
        FaixaBlindagem.BLINDADO_FORTE: "falência com não sucessão expressa e registro conferido",
        FaixaBlindagem.BLINDADO_COM_RESIDUO: "UPI homologada; risco residual de tese de sucessão",
        FaixaBlindagem.PARCIAL: "alienação concursal com lacuna de verificação",
        FaixaBlindagem.FRAGIL: "execução comum",
        FaixaBlindagem.INDETERMINADO: "regime não identificado — não passa da triagem",
    }
    for minimo, maximo, faixa in _FAIXAS:
        add(f"| `{faixa.value}` | {minimo}–{maximo} | {leitura[faixa]} |")
    add("")

    add("## 5. Caçador de Vícios — checklist")
    add("")
    add("| Item | Verificação | Falha correspondente | Severidade | Escopo | Fundamento | Status |")
    add("|---|---|---|---|---|---|---|")
    for item in CHECKLIST_VICIOS.values():
        add(
            f"| {item.id} | {item.titulo} | {item.falha} | {item.severidade.name} | "
            f"`{item.escopo.value}` | {item.base_legal} | {_MARCA_STATUS[item.status]} |"
        )
    add("")

    add("## 6. Notas de regime")
    add("")
    add("Não são vícios: são consequências do regime que o dossiê precisa registrar.")
    add("")
    add("| Nota | Conteúdo | Fundamento | Status |")
    add("|---|---|---|---|")
    for nota in NOTAS_DE_REGIME.values():
        add(f"| {nota.id} | {nota.titulo} | {nota.base_legal} | {_MARCA_STATUS[nota.status]} |")
    add("")

    add("## 7. Priors de agregação de risco")
    add("")
    add("Pesos **declarados por julgamento, não medidos**. Servem para ordenar diligência,")
    add("não para decidir capital; a calibração contra casos reais de anulação é entrega da")
    add("Fase 3 (doc 04, § 9).")
    add("")
    add("| Severidade | Probabilidade atribuída quando constatado |")
    add("|---|---:|")
    for severidade, prior in sorted(PRIOR_NULIDADE_POR_SEVERIDADE.items()):
        add(f"| {severidade.name} ({severidade.value}) | {prior} |")
    add("")
    add(f"Item apenas suspeito (não verificado) entra com peso {PESO_INDETERMINADO} do valor")
    add("acima, e compõe o **índice de incerteza**, que é reportado separadamente do risco")
    add("detectado — misturar os dois esconderia se o problema é o ativo ou a diligência.")
    add("")

    add("## 8. Pendências de validação")
    add("")
    if not a_validar:
        add("Nenhuma. Todas as regras foram conferidas em fonte primária.")
    else:
        for pendente in a_validar:
            add(f"### {pendente.id} — {pendente.titulo}")
            add("")
            add(f"- **Fundamento invocado:** {pendente.base_legal}")
            add(f"- **O que conferir:** {pendente.observacao or 'a definir'}")
            add("")
    return "\n".join(linhas).rstrip() + "\n"
