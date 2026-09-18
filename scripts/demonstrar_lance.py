#!/usr/bin/env python3
"""Mostra, em português, como o motor transforma avaliação em teto de lance.

Uso: python scripts/demonstrar_lance.py
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hasta.core.money import Money  # noqa: E402
from hasta.score.retorno import (  # noqa: E402
    Cenario,
    Financiamento,
    avaliar_faixa,
    avaliar_retorno,
    teto_de_lance,
)

LARGURA = 78
VALOR_JUSTO = Money.de_reais("8000000")


def titulo(texto: str) -> None:
    print()
    print("=" * LARGURA)
    print(texto)
    print("=" * LARGURA)


def cen(nome: str, meses: int, valor: str, haircut: str) -> Cenario:
    return Cenario(
        nome=nome,
        valor_justo_saida=Money.de_reais(valor),
        haircut_liquidez=Decimal(haircut),
        meses_ate_posse=min(meses, 12),
        meses_ate_venda=meses,
        debitos_que_seguem=Money.de_reais("100000"),
        custo_desocupacao=Money.de_reais("200000"),
        custo_regularizacao=Money.de_reais("300000"),
    )


PESSIMISTA = cen("pessimista", 36, "6500000", "0.25")
CENTRAL = cen("central", 24, "8000000", "0.15")
OTIMISTA = cen("otimista", 14, "9000000", "0.08")

titulo("O CASO")
print(
    "Galpao industrial arrematado em falencia. Avaliacao de mercado estimada por nos:\n"
    f"{VALOR_JUSTO} no cenario central. Despesas previstas: R$ 100 mil de debitos que\n"
    "seguem o bem, R$ 200 mil de desocupacao, R$ 300 mil de regularizacao.\n\n"
    "Parametros de capital (a confirmar pelo comite): 80% financiado a 15% ao ano,\n"
    "hurdle de 25% ao ano para o equity, comissao 5%, ITBI 3%, registro 1,5%,\n"
    "corretagem na saida 6%, tributacao do ganho ainda nao definida (zero no modelo)."
)

titulo("1. A CONTA DE UM LANCE DE R$ 2,4 MILHOES (30% DA AVALIACAO)")
print("\n".join(avaliar_retorno(Money.de_reais("2400000"), CENTRAL).linhas()))

titulo("2. TETO DE LANCE — o numero que vai para a praca")
for c in (OTIMISTA, CENTRAL, PESSIMISTA):
    teto = teto_de_lance(c)
    pct = teto.razao(c.valor_justo_saida)
    print(
        f"   cenario {c.nome:<11} ({c.meses_ate_venda} meses, haircut "
        f"{c.haircut_liquidez:.0%}): {teto}  =  {pct:.0%} da avaliacao"
    )
print()
print(f"   >>> TETO ADOTADO (pessimista): {teto_de_lance(PESSIMISTA)}")
print("       Acima disso nao se da lance. O teto e definido pelo cenario ruim de")
print("       proposito: teto calculado no cenario central e convite a pagar caro.")

titulo("3. O QUE O PRAZO FAZ COM O RETORNO")
print(f"   {'prazo':<10}{'juros do funding':>22}{'TIR do equity':>18}{'veredito':>14}")
for meses in (12, 24, 36, 48, 60):
    r = avaliar_retorno(Money.de_reais("2400000"), cen("p", meses, "8000000", "0.15"))
    tir = f"{r.tir_anual:.0%}" if r.tir_anual is not None else "—"
    print(f"   {meses:>2} meses{str(r.juros_acumulados):>24}{tir:>18}{r.veredito.value:>14}")
print()
print("   Mesmo lance, mesmo imovel, mesma avaliacao. So o tempo muda.")

titulo("4. O QUE A ALAVANCAGEM ESCONDE")
print(f"   {'financiado':<14}{'capital proprio':>20}{'TIR':>10}{'margem ate a ruina':>22}")
for part in ("0.00", "0.50", "0.80", "0.90"):
    r = avaliar_retorno(
        Money.de_reais("2400000"),
        CENTRAL,
        financiamento=Financiamento(participacao_divida=Decimal(part)),
    )
    tir = f"{r.tir_anual:.0%}" if r.tir_anual is not None else "—"
    margem = f"{r.margem_ate_a_ruina:.0%}" if r.margem_ate_a_ruina is not None else "—"
    print(f"   {Decimal(part):>9.0%}    {str(r.equity):>19}{tir:>10}{margem:>22}")
print()
print("   TIR alta com margem fina e aposta, nao investimento. A coluna da direita diz")
print("   quanto a venda pode frustrar antes de o equity zerar.")

titulo("5. O ACHADO QUE JUSTIFICA O MOTOR")
lance_vitrine = Money.de_reais("4800000")
r = avaliar_retorno(
    lance_vitrine, CENTRAL, financiamento=Financiamento(participacao_divida=Decimal(0))
)
print(
    f"   Um lance de {lance_vitrine} sobre avaliacao de {VALOR_JUSTO} e anunciado no\n"
    "   mercado como '40% de desagio'. Sem alavancagem, no cenario central:\n"
)
tir = f"{r.tir_anual:.1%} a.a." if r.tir_anual is not None else "indefinida"
print(f"      TIR do equity: {tir}   contra hurdle de {r.hurdle:.0%}   ->  {r.veredito.value}")
print()
print("   Desagio de vitrine nao e oportunidade. E por isso que o ranking usa TIR")
print("   liquida do carrego, e nao desconto sobre laudo.")

titulo("6. DECISAO CONSOLIDADA PARA O LANCE DE R$ 2,4 MILHOES")
f = avaliar_faixa(Money.de_reais("2400000"), PESSIMISTA, CENTRAL, OTIMISTA)
print(f"   TIR p10 / p50 / p90: {f.tir.p10:.0%}  /  {f.tir.p50:.0%}  /  {f.tir.p90:.0%}")
print(f"   Cenario que comanda a decisao: {f.decide_pelo_p10.cenario}")
print(f"   Veredito: {f.veredito.value} — {f.veredito.descricao}")
print(f"   Passa o hurdle? {'SIM' if f.passa_hurdle else 'NAO'}")
print()
