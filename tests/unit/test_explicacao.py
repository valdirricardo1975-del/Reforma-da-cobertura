from hasta.score.explicacao import Acumulador, Regra, StatusRegra

VIGENTE = Regra("X01", "regra conferida", "art. 1º", StatusRegra.VIGENTE)
A_VALIDAR = Regra("X02", "premissa a conferir", "art. 2º", StatusRegra.A_VALIDAR)
REVOGADA = Regra("X03", "regra desativada", "art. 3º", StatusRegra.REVOGADA)


def test_conta_e_aberta_e_ordenada():
    e = Acumulador(base=50).ajustar(VIGENTE, 10).ajustar(A_VALIDAR, -5).fechar()
    assert e.valor == 55
    assert e.linhas() == (
        "base 50",
        "X01 +10: regra conferida (art. 1º)",
        "X02 -5: premissa a conferir (art. 2º)",
        "= 55",
    )


def test_regra_revogada_fica_no_registro_mas_nao_conta():
    e = Acumulador(base=50).ajustar(REVOGADA, 30).fechar()
    assert e.valor == 50
    assert len(e.ajustes) == 1


def test_regras_a_validar_sao_expostas_sem_repeticao():
    e = Acumulador(base=0).ajustar(A_VALIDAR, 1).ajustar(A_VALIDAR, 2).ajustar(VIGENTE, 3).fechar()
    assert e.regras_a_validar == ("X02",)


def test_teto_vence_a_soma_de_ajustes():
    e = Acumulador(base=80).ajustar(VIGENTE, 15).limitar(VIGENTE, 69, "sem verificação").fechar()
    assert e.valor == 69
    assert "teto 69" in " ".join(e.linhas())


def test_teto_mais_restritivo_prevalece():
    e = (
        Acumulador(base=90)
        .limitar(VIGENTE, 69, "lacuna A")
        .limitar(A_VALIDAR, 40, "lacuna B")
        .fechar()
    )
    assert e.valor == 40
    assert e.teto_aplicado is not None
    assert e.teto_aplicado.valor == 40


def test_teto_nao_eleva_valor_baixo():
    e = Acumulador(base=30).limitar(VIGENTE, 69, "teto folgado").fechar()
    assert e.valor == 30
    assert "teto" not in " ".join(e.linhas())


def test_resultado_fica_dentro_dos_limites():
    assert Acumulador(base=10).ajustar(VIGENTE, -99).fechar().valor == 0
    assert Acumulador(base=95).ajustar(VIGENTE, 99).fechar().valor == 100
