import pytest

from hasta.core.estados import (
    ESTADOS_FERTEIS,
    TERMINAIS_OPORTUNIDADE,
    TRANSICOES_OPORTUNIDADE,
    TRANSICOES_PROCEDIMENTO,
    EstadoOportunidade,
    EstadoProcedimento,
    TransicaoInvalida,
    aplicar_oportunidade,
    aplicar_procedimento,
    transicoes_oportunidade,
)


def test_toda_transicao_declarada_aponta_para_estado_conhecido():
    for mapa, enum in (
        (TRANSICOES_PROCEDIMENTO, EstadoProcedimento),
        (TRANSICOES_OPORTUNIDADE, EstadoOportunidade),
    ):
        assert set(mapa) == set(enum)
        for destinos in mapa.values():
            assert destinos <= set(enum)


def test_caminho_tipico_de_recuperacao_judicial():
    estado = EstadoProcedimento.PEDIDO
    for proximo in (
        EstadoProcedimento.PROCESSAMENTO_DEFERIDO,
        EstadoProcedimento.RELACAO_CREDORES,
        EstadoProcedimento.PLANO_APRESENTADO,
        EstadoProcedimento.AGC,
        EstadoProcedimento.PLANO_APROVADO,
        EstadoProcedimento.EM_CUMPRIMENTO,
        EstadoProcedimento.ALIENACAO_UPI,
    ):
        estado = aplicar_procedimento(estado, proximo)
    assert estado is EstadoProcedimento.ALIENACAO_UPI


def test_caminho_de_convolacao_em_falencia_e_alienacao():
    estado = aplicar_procedimento(
        EstadoProcedimento.EM_CUMPRIMENTO, EstadoProcedimento.DESCUMPRIMENTO
    )
    estado = aplicar_procedimento(estado, EstadoProcedimento.FALENCIA)
    estado = aplicar_procedimento(estado, EstadoProcedimento.ARRECADACAO)
    estado = aplicar_procedimento(estado, EstadoProcedimento.ALIENACAO_FALIMENTAR)
    # Mais de um lote: volta à arrecadação e aliena de novo.
    estado = aplicar_procedimento(estado, EstadoProcedimento.ARRECADACAO)
    assert estado is EstadoProcedimento.ARRECADACAO


def test_transicao_ilegal_falha_alto():
    with pytest.raises(TransicaoInvalida) as exc:
        aplicar_procedimento(EstadoProcedimento.PEDIDO, EstadoProcedimento.EM_CUMPRIMENTO)
    assert "PEDIDO → EM_CUMPRIMENTO" in str(exc.value)


def test_encerrada_e_arquivado_sao_terminais():
    assert TRANSICOES_PROCEDIMENTO[EstadoProcedimento.ENCERRADA] == frozenset()
    assert TRANSICOES_PROCEDIMENTO[EstadoProcedimento.ARQUIVADO] == frozenset()


def test_estados_ferteis_podem_gerar_lote():
    assert EstadoProcedimento.ARRECADACAO in ESTADOS_FERTEIS
    assert EstadoProcedimento.ALIENACAO_UPI in ESTADOS_FERTEIS
    assert EstadoProcedimento.PEDIDO not in ESTADOS_FERTEIS


def test_descarte_e_bloqueio_sao_possiveis_de_qualquer_estado_ativo():
    for estado in EstadoOportunidade:
        saidas = transicoes_oportunidade(estado)
        if estado in TERMINAIS_OPORTUNIDADE:
            assert saidas == frozenset()
        else:
            assert EstadoOportunidade.DESCARTADA in saidas
            assert EstadoOportunidade.BLOQUEADA_COMPLIANCE in saidas


def test_lote_deserto_volta_ao_ciclo_de_precificacao():
    """Padrão T1: deserto na 1ª praça é justamente onde o deságio aparece."""
    estado = aplicar_oportunidade(EstadoOportunidade.DESERTA, EstadoOportunidade.PRECIFICADA)
    assert estado is EstadoOportunidade.PRECIFICADA


def test_nao_se_pula_o_comite():
    with pytest.raises(TransicaoInvalida):
        aplicar_oportunidade(EstadoOportunidade.EM_DD, EstadoOportunidade.LANCE_AUTORIZADO)


def test_terminais_nao_tem_saida():
    for estado in TERMINAIS_OPORTUNIDADE:
        assert TRANSICOES_OPORTUNIDADE[estado] == frozenset()
