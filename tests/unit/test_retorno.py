from decimal import Decimal

import pytest

from hasta.core.money import Money
from hasta.score.retorno import (
    Cenario,
    Custos,
    FaixaRetorno,
    Financiamento,
    RiscoExecucao,
    Veredito,
    _potencia,
    avaliar_faixa,
    avaliar_retorno,
    teto_de_lance,
)

VALOR_JUSTO = Money.de_reais("8000000")


def cenario(
    nome: str = "central",
    meses: int = 24,
    valor: str = "8000000",
    haircut: str = "0.15",
    **extra: object,
) -> Cenario:
    base: dict[str, object] = {
        "nome": nome,
        "valor_justo_saida": Money.de_reais(valor),
        "haircut_liquidez": Decimal(haircut),
        "meses_ate_posse": min(meses, 12),
        "meses_ate_venda": meses,
        "debitos_que_seguem": Money.de_reais("100000"),
        "custo_desocupacao": Money.de_reais("200000"),
        "custo_regularizacao": Money.de_reais("300000"),
    }
    return Cenario(**{**base, **extra})  # type: ignore[arg-type]


SEM_DIVIDA = Financiamento(participacao_divida=Decimal(0))


# -- fundamentos ------------------------------------------------------------


def test_potencia_exige_base_positiva():
    assert _potencia(Decimal(2), Decimal(3)).quantize(Decimal("1")) == Decimal(8)
    assert _potencia(Decimal(2), Decimal(0)) == Decimal(1)
    with pytest.raises(ValueError, match="base positiva"):
        _potencia(Decimal(-1), Decimal("0.5"))


def test_prazo_de_venda_nao_antecede_a_posse():
    with pytest.raises(ValueError, match="venda não pode anteceder"):
        Cenario(
            nome="x",
            valor_justo_saida=VALOR_JUSTO,
            meses_ate_posse=24,
            meses_ate_venda=12,
        )


# -- o que sai do bolso -----------------------------------------------------


def test_investimento_total_soma_todos_os_custos_de_entrada():
    """Lance não é preço. A conta tem de fechar centavo por centavo."""
    lance = Money.de_reais("1000000")
    r = avaliar_retorno(
        lance,
        cenario(
            debitos_que_seguem=Money.de_reais("50000"),
            custo_desocupacao=Money.de_reais("30000"),
            custo_regularizacao=Money.de_reais("20000"),
        ),
        Custos(
            comissao_leiloeiro=Decimal("0.05"),
            itbi=Decimal("0.03"),
            registro_e_emolumentos=Decimal("0.015"),
            custas_e_despesas=Money.de_reais("5000"),
        ),
    )
    # 1.000.000 + 50.000 + 30.000 + 15.000 + 5.000 + 100.000 de despesas do cenário
    assert r.investimento_total == Money.de_reais("1200000")


def test_divida_e_equity_seguem_a_participacao():
    r = avaliar_retorno(
        Money.de_reais("1000000"),
        cenario(),
        financiamento=Financiamento(participacao_divida=Decimal("0.75")),
    )
    assert r.divida + r.equity == r.investimento_total
    assert r.divida.razao(r.investimento_total) == Decimal("0.75")


def test_sem_divida_nao_ha_juros_nem_ponto_de_ruina():
    r = avaliar_retorno(Money.de_reais("2400000"), cenario(), financiamento=SEM_DIVIDA)
    assert r.juros_acumulados == Money.zero()
    assert r.ponto_de_ruina == Money.zero()
    assert r.margem_ate_a_ruina == Decimal(1)


# -- o tempo cobra ----------------------------------------------------------


def test_carrego_cresce_com_o_prazo_e_derruba_a_tir():
    """O ponto central do ADR-0016: prazo é variável de primeira ordem."""
    lance = Money.de_reais("2400000")
    resultados = [avaliar_retorno(lance, cenario(meses=m)) for m in (12, 24, 36, 48)]

    juros = [r.juros_acumulados for r in resultados]
    tirs = [r.tir_anual for r in resultados]

    assert juros == sorted(juros), "juros do funding devem crescer com o prazo"
    assert all(t is not None for t in tirs)
    assert tirs == sorted(tirs, reverse=True), "TIR deve cair com o prazo"


def test_desagio_de_quarenta_por_cento_reprova_ate_no_prazo_curto():
    """O achado que justifica o motor: deságio de vitrine não é oportunidade.

    Lance a 60% do valor justo — "40% de deságio" na linguagem dos agregadores — não
    supera um hurdle de 25% ao ano nem no melhor prazo, depois de comissão, ITBI,
    registro, débitos, desocupação, regularização, haircut e corretagem.
    """
    lance = Money.de_reais("4800000")  # 60% do valor justo
    curto = avaliar_retorno(lance, cenario(meses=12), financiamento=SEM_DIVIDA)
    longo = avaliar_retorno(lance, cenario(meses=60, haircut="0.25"), financiamento=SEM_DIVIDA)

    assert curto.desagio_sobre_valor_justo is not None
    assert curto.desagio_sobre_valor_justo > Decimal("0.29")  # "29% sobre o realizável"
    assert curto.veredito is Veredito.REPROVA
    assert longo.veredito is Veredito.REPROVA
    assert curto.tir_anual is not None and curto.tir_anual < curto.hurdle

    # No teto calculado, o mesmo ativo passa — e o teto é bem abaixo dos 60%.
    teto = teto_de_lance(cenario(meses=12), financiamento=SEM_DIVIDA)
    assert teto < lance
    assert avaliar_retorno(teto, cenario(meses=12), financiamento=SEM_DIVIDA).veredito in {
        Veredito.APROVA,
        Veredito.LIMITROFE,
    }


def test_juros_do_funding_entram_antes_do_equity():
    alavancado = avaliar_retorno(Money.de_reais("2400000"), cenario(meses=36))
    assert alavancado.divida_na_saida == alavancado.divida + alavancado.juros_acumulados
    assert alavancado.liquido_da_saida - alavancado.divida_na_saida == alavancado.caixa_ao_equity, (
        "a preferência nas retiradas paga o financiador primeiro"
    )


# -- alavancagem ------------------------------------------------------------


def test_alavancagem_infla_a_tir_e_encurta_a_margem_ate_a_ruina():
    """A troca que o comitê precisa ver: TIR alta com margem fina é aposta."""
    lance = Money.de_reais("2400000")
    alta = avaliar_retorno(
        lance, cenario(), financiamento=Financiamento(participacao_divida=Decimal("0.80"))
    )
    media = avaliar_retorno(
        lance, cenario(), financiamento=Financiamento(participacao_divida=Decimal("0.50"))
    )
    nenhuma = avaliar_retorno(lance, cenario(), financiamento=SEM_DIVIDA)

    assert alta.tir_anual is not None and media.tir_anual is not None
    assert nenhuma.tir_anual is not None
    assert alta.tir_anual > media.tir_anual > nenhuma.tir_anual

    assert alta.margem_ate_a_ruina is not None and media.margem_ate_a_ruina is not None
    assert alta.margem_ate_a_ruina < media.margem_ate_a_ruina


def test_saida_abaixo_do_ponto_de_ruina_zera_o_equity():
    lance = Money.de_reais("2400000")
    referencia = avaliar_retorno(lance, cenario())
    assert referencia.ponto_de_ruina.centavos > 0

    # Cenário cujo valor realizável fica logo abaixo do ponto de ruína.
    quase_nada = referencia.ponto_de_ruina * Decimal("0.9")
    valor_bruto = quase_nada * (Decimal(1) / (Decimal(1) - Decimal("0.15")))
    ruim = avaliar_retorno(
        lance,
        cenario(nome="ruína", valor=str(valor_bruto.reais)),
    )
    assert ruim.caixa_ao_equity.centavos <= 0
    assert ruim.tir_anual is None
    assert ruim.veredito is Veredito.INVIAVEL


# -- tributos e custos de saída --------------------------------------------


def test_tributo_so_incide_havendo_ganho():
    lance = Money.de_reais("2400000")
    custos = Custos(tributacao_do_ganho=Decimal("0.34"))
    com_ganho = avaliar_retorno(lance, cenario(), custos, SEM_DIVIDA)
    sem_tributo = avaliar_retorno(lance, cenario(), Custos(), SEM_DIVIDA)
    assert com_ganho.liquido_da_saida < sem_tributo.liquido_da_saida

    # Operação sem ganho: tributo não pode piorar o resultado.
    prejuizo = cenario(nome="prejuízo", valor="2000000")
    a = avaliar_retorno(lance, prejuizo, custos, SEM_DIVIDA)
    b = avaliar_retorno(lance, prejuizo, Custos(), SEM_DIVIDA)
    assert a.liquido_da_saida == b.liquido_da_saida


def test_haircut_de_liquidez_reduz_o_valor_realizavel():
    lance = Money.de_reais("2400000")
    liquido = avaliar_retorno(lance, cenario(haircut="0.00"), financiamento=SEM_DIVIDA)
    iliquido = avaliar_retorno(lance, cenario(haircut="0.30"), financiamento=SEM_DIVIDA)
    assert liquido.valor_realizavel == VALOR_JUSTO
    assert iliquido.valor_realizavel == VALOR_JUSTO * Decimal("0.70")


# -- risco processual -------------------------------------------------------


def test_risco_de_anulacao_reduz_o_vpl_ajustado():
    lance = Money.de_reais("2400000")
    seguro = avaliar_retorno(lance, cenario(), risco=RiscoExecucao())
    arriscado = avaliar_retorno(
        lance,
        cenario(),
        risco=RiscoExecucao(p_anulacao=Decimal("0.3"), custo_desfazimento=Money.de_reais("200000")),
    )
    assert arriscado.vpl_ajustado_a_risco < seguro.vpl_ajustado_a_risco
    assert arriscado.vpl_ao_hurdle == seguro.vpl_ao_hurdle, "o VPL bruto não muda"


def test_leilao_que_nao_ocorre_zera_o_valor_esperado():
    r = avaliar_retorno(
        Money.de_reais("2400000"),
        cenario(),
        risco=RiscoExecucao(p_leilao_ocorre=Decimal(0)),
    )
    assert r.vpl_ajustado_a_risco == Money.zero()


# -- faixa de cenários ------------------------------------------------------


def faixa_padrao(lance: Money) -> FaixaRetorno:
    return avaliar_faixa(
        lance,
        pessimista=cenario("pessimista", meses=36, valor="6500000", haircut="0.25"),
        central=cenario("central", meses=24, valor="8000000", haircut="0.15"),
        otimista=cenario("otimista", meses=14, valor="9000000", haircut="0.08"),
    )


def test_faixa_ordena_quantis_e_decide_pelo_p10():
    f = faixa_padrao(Money.de_reais("2400000"))
    assert f.tir.p10 <= f.tir.p50 <= f.tir.p90
    assert f.decide_pelo_p10 is f.pessimista
    assert f.veredito is f.pessimista.veredito


def test_lance_alto_reprova_no_p10_mesmo_aprovando_no_otimista():
    """A margem de segurança é estrutural: quem manda é o cenário ruim."""
    f = faixa_padrao(Money.de_reais("4200000"))
    assert f.otimista.veredito in {Veredito.APROVA, Veredito.LIMITROFE}
    assert f.pessimista.veredito in {Veredito.REPROVA, Veredito.INVIAVEL}
    assert not f.passa_hurdle


# -- teto de lance ----------------------------------------------------------


def test_no_teto_a_tir_encosta_no_hurdle_e_acima_dele_reprova():
    pess = cenario("pessimista", meses=30, valor="8000000", haircut="0.20")
    teto = teto_de_lance(pess)

    no_teto = avaliar_retorno(teto, pess)
    assert no_teto.tir_anual is not None
    assert no_teto.tir_anual >= no_teto.hurdle

    acima = avaliar_retorno(teto + Money.de_reais("50000"), pess)
    assert acima.tir_anual is not None
    assert acima.tir_anual < acima.hurdle


def test_teto_do_cenario_pessimista_e_menor_que_o_do_central():
    pess = cenario("pessimista", meses=36, valor="6500000", haircut="0.25")
    central = cenario("central", meses=24, valor="8000000", haircut="0.15")
    assert teto_de_lance(pess) < teto_de_lance(central)


def test_hurdle_mais_exigente_reduz_o_teto():
    pess = cenario("pessimista", meses=30, haircut="0.20")
    brando = teto_de_lance(pess, tir_minima=Decimal("0.20"))
    exigente = teto_de_lance(pess, tir_minima=Decimal("0.45"))
    assert exigente < brando


def test_prazo_mais_longo_reduz_o_teto():
    curto = teto_de_lance(cenario("curto", meses=18))
    longo = teto_de_lance(cenario("longo", meses=48))
    assert longo < curto


def test_teto_zero_quando_nada_supera_a_exigencia():
    inviavel = cenario("inviável", meses=60, valor="900000", haircut="0.40")
    assert teto_de_lance(inviavel, tir_minima=Decimal("0.60")) == Money.zero()


def test_veredito_limitrofe_fica_entre_hurdle_e_vinte_por_cento_acima():
    pess = cenario("pessimista", meses=30, haircut="0.20")
    teto = teto_de_lance(pess)
    assert avaliar_retorno(teto, pess).veredito is Veredito.LIMITROFE


def test_linhas_do_dossie_mostram_a_conta_na_ordem_do_dinheiro():
    r = avaliar_retorno(Money.de_reais("2400000"), cenario())
    texto = "\n".join(r.linhas())
    for esperado in (
        "lance",
        "investimento total",
        "juros do funding",
        "quitação do financiador",
        "caixa ao equity",
        "TIR do equity",
        "equity zera se a saída cair",
    ):
        assert esperado in texto
