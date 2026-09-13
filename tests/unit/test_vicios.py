from decimal import Decimal

import pytest

from hasta.core.enums import ClasseAtivo, NaturezaProcedimento, RegimeTransmissao
from hasta.core.money import Money
from hasta.score.explicacao import StatusRegra
from hasta.score.vicios import (
    CHECKLIST_VICIOS,
    NOTAS_DE_REGIME,
    PRIOR_NULIDADE_POR_SEVERIDADE,
    ContextoVicios,
    Escopo,
    ResultadoVicios,
    Severidade,
    Situacao,
    cacar_vicios,
)


def situacao_de(resultado: ResultadoVicios, item_id: str) -> Situacao:
    return next(c for c in resultado.constatacoes if c.item.id == item_id).situacao


FALENCIA = {
    "regime": RegimeTransmissao.LFR_141_II_FALENCIA,
    "natureza": NaturezaProcedimento.FALENCIA,
    "classe_ativo": ClasseAtivo.IMOVEL_URBANO,
}
EXECUCAO = {
    "regime": RegimeTransmissao.CPC_879_LEILAO,
    "natureza": NaturezaProcedimento.EXEC_TITULO,
    "classe_ativo": ClasseAtivo.IMOVEL_URBANO,
}

VERIFICADO_LIMPO: dict[str, object] = {
    "legitimados_art_889_pendentes": (),
    "dias_entre_publicacao_e_praca": 20,
    "laudo_existe": True,
    "laudo_idade_meses": 6,
    "avaliacao_impugnada": False,
    "penhora_averbada": True,
    "penhoras_concorrentes": 1,
    "lance_minimo": Money.de_reais("700000"),
    "avaliacao_atualizada": Money.de_reais("1000000"),
    "impenhorabilidade_alegada": False,
    "previsao_no_plano_ou_autorizacao": True,
    "recurso_suspensivo_pendente": False,
    "divergencia_descritiva": False,
    "edital_retificado_apos_publicidade": False,
}


# -- catálogo ---------------------------------------------------------------


def test_checklist_e_consistente():
    assert len(CHECKLIST_VICIOS) == len({i.id for i in CHECKLIST_VICIOS.values()})
    for item in CHECKLIST_VICIOS.values():
        assert item.base_legal and item.titulo and item.diligencia and item.por_que_importa
        assert item.falha, f"{item.id} sem rótulo de falha para o dossiê"
        assert isinstance(item.severidade, Severidade)


def test_itens_a_validar_dizem_o_que_conferir():
    for item in CHECKLIST_VICIOS.values():
        if item.status is StatusRegra.A_VALIDAR:
            assert item.observacao, f"{item.id} sem instrução de validação"


def test_prior_cresce_com_a_severidade():
    valores = [PRIOR_NULIDADE_POR_SEVERIDADE[s] for s in sorted(Severidade)]
    assert valores == sorted(valores)
    assert all(Decimal(0) < v < Decimal(1) for v in valores)


# -- semântica do desconhecido ---------------------------------------------


def test_nada_verificado_gera_incerteza_e_nenhum_risco_detectado():
    r = cacar_vicios(ContextoVicios(**FALENCIA))
    assert r.indice_risco_nulidade == Decimal("0.0000")
    assert r.indice_incerteza > Decimal("0.4")
    assert not r.checklist_completo
    assert len(r.lacunas) == len(r.indeterminados)


def test_checklist_verificado_e_limpo_zera_os_dois_indices():
    r = cacar_vicios(ContextoVicios(**FALENCIA, **VERIFICADO_LIMPO))
    assert r.indice_risco_nulidade == Decimal("0.0000")
    assert r.indice_incerteza == Decimal("0.0000")
    assert r.checklist_completo
    assert not r.lacunas
    assert r.severidade_maxima_constatada is None


def test_risco_pessimista_nunca_e_menor_que_os_componentes():
    for contexto in (
        ContextoVicios(**FALENCIA),
        ContextoVicios(**EXECUCAO, laudo_existe=False, laudo_idade_meses=60),
        ContextoVicios(**EXECUCAO, **VERIFICADO_LIMPO),
    ):
        r = cacar_vicios(contexto)
        assert r.risco_pessimista >= r.indice_risco_nulidade
        assert r.risco_pessimista >= r.indice_incerteza
        assert r.risco_pessimista <= Decimal(1)


def test_lacuna_traz_a_diligencia_do_item():
    r = cacar_vicios(ContextoVicios(**FALENCIA))
    lacuna = next(lac for lac in r.lacunas if lac.campo == "vicio.V01")
    assert "art. 889" in lacuna.diligencia_recomendada


# -- preço vil: a assimetria do nicho --------------------------------------


def test_preco_vil_se_aplica_na_execucao_comum():
    r = cacar_vicios(
        ContextoVicios(
            **EXECUCAO,
            lance_minimo=Money.de_reais("400000"),
            avaliacao_atualizada=Money.de_reais("1000000"),
        )
    )
    v08 = next(c for c in r.constatacoes if c.item.id == "V08")
    assert v08.situacao is Situacao.CONSTATADO
    assert "40%" in (v08.detalhe or "")


def test_preco_vil_nao_se_aplica_na_falencia_e_a_nota_explica_por_que():
    r = cacar_vicios(
        ContextoVicios(
            **FALENCIA,
            lance_minimo=Money.de_reais("300000"),
            avaliacao_atualizada=Money.de_reais("1000000"),
        )
    )
    v08 = next(c for c in r.constatacoes if c.item.id == "V08")
    assert v08.situacao is Situacao.NAO_APLICAVEL
    assert v08.peso == Decimal(0)
    assert "N01" in {n.id for n in r.notas}


def test_patamar_de_preco_vil_e_parametro_revisavel():
    contexto = {
        **EXECUCAO,
        "lance_minimo": Money.de_reais("450000"),
        "avaliacao_atualizada": Money.de_reais("1000000"),
    }
    padrao = cacar_vicios(ContextoVicios(**contexto))
    exigente = cacar_vicios(ContextoVicios(**contexto, fracao_preco_vil=Decimal("0.4")))
    assert situacao_de(padrao, "V08") is Situacao.CONSTATADO
    assert situacao_de(exigente, "V08") is Situacao.AFASTADO


def test_notas_de_regime_tributario_aparecem_para_imovel():
    r = cacar_vicios(ContextoVicios(**EXECUCAO))
    assert "N02" in {n.id for n in r.notas}
    assert all(nota.base_legal for nota in r.notas)


def test_nota_de_nao_sucessao_tributaria_em_falencia():
    r = cacar_vicios(ContextoVicios(**FALENCIA))
    assert "N03" in {n.id for n in r.notas}


# -- escopos ---------------------------------------------------------------


def test_item_concursal_nao_se_aplica_em_execucao_comum():
    r = cacar_vicios(ContextoVicios(**EXECUCAO))
    v10 = next(c for c in r.constatacoes if c.item.id == "V10")
    assert v10.situacao is Situacao.NAO_APLICAVEL


def test_item_de_imovel_nao_se_aplica_a_maquina():
    r = cacar_vicios(
        ContextoVicios(
            regime=RegimeTransmissao.LFR_141_II_FALENCIA,
            natureza=NaturezaProcedimento.FALENCIA,
            classe_ativo=ClasseAtivo.MAQUINA_EQUIPAMENTO,
        )
    )
    v06 = next(c for c in r.constatacoes if c.item.id == "V06")
    assert v06.situacao is Situacao.NAO_APLICAVEL
    assert CHECKLIST_VICIOS["V06"].escopo is Escopo.IMOVEL


def test_nao_aplicavel_nao_gera_lacuna():
    r = cacar_vicios(ContextoVicios(**EXECUCAO))
    assert not any(lac.campo == "vicio.V10" for lac in r.lacunas)


# -- constatações ----------------------------------------------------------


@pytest.mark.parametrize(
    ("campo", "valor", "item_id"),
    [
        ("avaliacao_impugnada", True, "V05"),
        ("impenhorabilidade_alegada", True, "V09"),
        ("recurso_suspensivo_pendente", True, "V11"),
        ("divergencia_descritiva", True, "V12"),
        ("edital_retificado_apos_publicidade", True, "V14"),
    ],
)
def test_fatos_booleanos_viram_constatacao(campo: str, valor: bool, item_id: str) -> None:
    r = cacar_vicios(ContextoVicios(**FALENCIA, **{campo: valor}))
    assert next(c for c in r.constatacoes if c.item.id == item_id).situacao is Situacao.CONSTATADO


def test_segredo_de_justica_e_vicio_de_verificacao():
    r = cacar_vicios(ContextoVicios(**FALENCIA, segredo_justica=True))
    assert next(c for c in r.constatacoes if c.item.id == "V13").situacao is Situacao.CONSTATADO


def test_prazo_de_publicidade_usa_o_parametro_configurado():
    curto = cacar_vicios(ContextoVicios(**EXECUCAO, dias_entre_publicacao_e_praca=4))
    tolerante = cacar_vicios(
        ContextoVicios(**EXECUCAO, dias_entre_publicacao_e_praca=4, dias_minimos_publicidade=3)
    )
    assert next(c for c in curto.constatacoes if c.item.id == "V02").situacao is Situacao.CONSTATADO
    assert (
        next(c for c in tolerante.constatacoes if c.item.id == "V02").situacao is Situacao.AFASTADO
    )


def test_falha_nomeada_aparece_quando_constatado():
    r = cacar_vicios(ContextoVicios(**EXECUCAO, laudo_idade_meses=40))
    v04 = next(c for c in r.constatacoes if c.item.id == "V04")
    assert str(v04).startswith("V04 CONSTATADO: Laudo de avaliação defasado")


def test_itens_a_validar_excluem_os_nao_aplicaveis():
    """V01 e V02 dependem de conferência; itens fora de escopo não entram na lista."""
    r = cacar_vicios(ContextoVicios(**FALENCIA))
    assert set(r.itens_a_validar) == {"V01", "V02"}


def test_severidade_maxima_orienta_a_prioridade():
    r = cacar_vicios(
        ContextoVicios(**EXECUCAO, laudo_idade_meses=40, recurso_suspensivo_pendente=True)
    )
    assert r.severidade_maxima_constatada is Severidade.GRAVE


def test_todo_item_do_catalogo_tem_avaliador():
    """Se um item entrar no catálogo sem avaliador, isto falha em vez de sumir."""
    r = cacar_vicios(ContextoVicios(**FALENCIA, **VERIFICADO_LIMPO))
    assert {c.item.id for c in r.constatacoes} == set(CHECKLIST_VICIOS)


def test_notas_nao_repetem():
    r = cacar_vicios(ContextoVicios(**FALENCIA))
    ids = [n.id for n in r.notas]
    assert len(ids) == len(set(ids))
    assert set(ids) <= set(NOTAS_DE_REGIME)
