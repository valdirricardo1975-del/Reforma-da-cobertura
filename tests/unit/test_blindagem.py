from uuid import uuid4

import pytest

from hasta.core.entidades import Ativo, Lote, Onus, Procedimento
from hasta.core.enums import ClasseAtivo, NaturezaProcedimento, RegimeTransmissao
from hasta.score.blindagem import (
    CATALOGO_BLINDAGEM,
    ContextoBlindagem,
    FaixaBlindagem,
    avaliar_blindagem,
)


def ctx(**kwargs: object) -> ContextoBlindagem:
    base: dict[str, object] = {
        "regime_declarado": RegimeTransmissao.LFR_141_II_FALENCIA,
        "natureza_procedimento": NaturezaProcedimento.FALENCIA,
        "classe_ativo_principal": ClasseAtivo.IMOVEL_URBANO,
        "clausula_nao_sucessao_no_edital": True,
        "decisao_autorizadora_identificada": True,
        "cadeia_dominial_verificada": True,
        "edital_silente_sobre_condominio": False,
    }
    return ContextoBlindagem(**{**base, **kwargs})  # type: ignore[arg-type]


# -- catálogo ---------------------------------------------------------------


def test_catalogo_nao_tem_id_duplicado_e_tem_base_legal():
    assert len(CATALOGO_BLINDAGEM) == len({r.id for r in CATALOGO_BLINDAGEM.values()})
    for regra in CATALOGO_BLINDAGEM.values():
        assert regra.base_legal
        assert regra.titulo


def test_regras_a_validar_estao_documentadas():
    """Premissa não conferida precisa dizer o que conferir."""
    for regra in CATALOGO_BLINDAGEM.values():
        if regra.status.name == "A_VALIDAR":
            assert regra.observacao, f"{regra.id} sem instrução de validação"


# -- faixas -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("grau", "faixa"),
    [
        (100, FaixaBlindagem.BLINDADO_FORTE),
        (90, FaixaBlindagem.BLINDADO_FORTE),
        (89, FaixaBlindagem.BLINDADO_COM_RESIDUO),
        (70, FaixaBlindagem.BLINDADO_COM_RESIDUO),
        (69, FaixaBlindagem.PARCIAL),
        (45, FaixaBlindagem.PARCIAL),
        (44, FaixaBlindagem.FRAGIL),
        (20, FaixaBlindagem.FRAGIL),
        (19, FaixaBlindagem.INDETERMINADO),
        (0, FaixaBlindagem.INDETERMINADO),
    ],
)
def test_faixas_seguem_o_doc_04(grau: int, faixa: FaixaBlindagem) -> None:
    assert FaixaBlindagem.de_grau(grau) is faixa


def test_indeterminado_nao_passa_da_triagem():
    assert not FaixaBlindagem.INDETERMINADO.passa_portao_de_triagem
    assert FaixaBlindagem.FRAGIL.passa_portao_de_triagem


# -- cenários ---------------------------------------------------------------


def test_falencia_com_clausula_e_matricula_verificada_e_blindagem_forte():
    r = avaliar_blindagem(ctx())
    assert r.grau == 92
    assert r.faixa is FaixaBlindagem.BLINDADO_FORTE
    assert not r.lacunas
    assert not r.impedimento_detectado


def test_sem_cadeia_dominial_verificada_nao_existe_blindagem_forte():
    """Teto, não desconto: sem registro conferido o ativo não é classificável como blindado."""
    r = avaliar_blindagem(ctx(cadeia_dominial_verificada=False))
    assert r.grau == 69
    assert r.faixa is FaixaBlindagem.PARCIAL
    assert any(lac.campo == "ativo.matricula" for lac in r.lacunas)


def test_upi_sem_plano_homologado_perde_a_base_da_blindagem():
    com_plano = avaliar_blindagem(
        ctx(regime_declarado=RegimeTransmissao.LFR_60_UPI, plano_homologado_juntado=True)
    )
    sem_plano = avaliar_blindagem(
        ctx(regime_declarado=RegimeTransmissao.LFR_60_UPI, plano_homologado_juntado=False)
    )
    assert com_plano.grau == 84
    assert com_plano.faixa is FaixaBlindagem.BLINDADO_COM_RESIDUO
    assert sem_plano.grau == 66
    assert "B12" in " ".join(sem_plano.explicacao.linhas())


def test_upi_com_homologacao_nao_verificada_recebe_teto_e_lacuna():
    r = avaliar_blindagem(
        ctx(regime_declarado=RegimeTransmissao.LFR_60_UPI, plano_homologado_juntado=None)
    )
    assert r.grau <= 69
    assert any("plano_homologado" in lac.campo for lac in r.lacunas)


def test_execucao_comum_de_imovel_e_fragil_mesmo_com_tributos_sub_rogados():
    r = avaliar_blindagem(
        ctx(
            regime_declarado=RegimeTransmissao.CPC_879_LEILAO,
            natureza_procedimento=NaturezaProcedimento.EXEC_TITULO,
            clausula_nao_sucessao_no_edital=False,
        )
    )
    assert r.faixa is FaixaBlindagem.FRAGIL
    assert "B19" in " ".join(r.explicacao.linhas())


def test_clausula_de_edital_nao_cria_blindagem_fora_do_regime_concursal():
    concursal = avaliar_blindagem(ctx())
    execucao = avaliar_blindagem(
        ctx(
            regime_declarado=RegimeTransmissao.CPC_879_LEILAO,
            natureza_procedimento=NaturezaProcedimento.EXEC_TITULO,
        )
    )
    ganho_concursal = concursal.explicacao.soma_ajustes
    ganho_execucao = execucao.explicacao.soma_ajustes
    assert ganho_concursal > ganho_execucao
    assert "B11" in " ".join(execucao.explicacao.linhas())


def test_regime_de_falencia_e_inferido_com_teto_porque_inferencia_nao_e_evidencia():
    r = avaliar_blindagem(
        ctx(regime_declarado=RegimeTransmissao.INDETERMINADO, clausula_nao_sucessao_no_edital=False)
    )
    assert r.regime_efetivo is RegimeTransmissao.LFR_141_II_FALENCIA
    assert r.regime_foi_inferido
    assert r.grau <= 69


def test_em_recuperacao_judicial_o_regime_nao_e_deduzido():
    """Venda em RJ pode ser UPI do art. 60 ou alienação do art. 66: deduzir seria inventar."""
    r = avaliar_blindagem(
        ctx(
            regime_declarado=RegimeTransmissao.INDETERMINADO,
            natureza_procedimento=NaturezaProcedimento.RJ,
            clausula_nao_sucessao_no_edital=False,
        )
    )
    assert r.regime_efetivo is RegimeTransmissao.INDETERMINADO
    assert not r.regime_foi_inferido
    assert r.faixa is FaixaBlindagem.INDETERMINADO


def test_adquirente_ligado_ao_devedor_gera_impedimento_nao_desconto():
    r = avaliar_blindagem(ctx(adquirente_pode_ser_socio_parente_agente=True))
    assert r.impedimento_detectado
    assert r.grau <= 44
    assert "B16" in " ".join(r.explicacao.linhas())


def test_bem_de_terceiro_derruba_a_blindagem():
    r = avaliar_blindagem(ctx(onus_de_terceiro_detectado=True))
    assert r.grau == 67
    assert "B15" in " ".join(r.explicacao.linhas())


def test_segredo_de_justica_limita_a_40_e_pede_exclusao():
    r = avaliar_blindagem(ctx(segredo_justica=True))
    assert r.grau <= 40
    assert any("segredo" in lac.campo for lac in r.lacunas)


def test_condominio_desconhecido_gera_lacuna_sem_penalizar():
    desconhecido = avaliar_blindagem(ctx(edital_silente_sobre_condominio=None))
    tratado = avaliar_blindagem(ctx(edital_silente_sobre_condominio=False))
    assert desconhecido.grau == tratado.grau
    assert any("condominiais" in lac.campo for lac in desconhecido.lacunas)


def test_exposicao_trabalhista_so_pesa_com_consolidacao_substancial():
    isolado = avaliar_blindagem(ctx(passivo_trabalhista_relevante=True))
    combinado = avaliar_blindagem(
        ctx(passivo_trabalhista_relevante=True, consolidacao_substancial=True)
    )
    assert isolado.grau > combinado.grau


def test_resumo_e_legivel_para_o_dossie():
    r = avaliar_blindagem(ctx())
    assert r.resumo().startswith("BLINDADO_FORTE (92/100)")
    assert "art. 141, II" in r.resumo()


# -- integração com o núcleo de domínio -------------------------------------


def test_contexto_se_monta_a_partir_das_entidades():
    procedimento = Procedimento(
        numero_cnj="1234567-13.2024.8.26.0100",
        natureza=NaturezaProcedimento.FALENCIA,
        tribunal="TJSP",
    )
    ativo = Ativo(
        classe=ClasseAtivo.IMOVEL_URBANO,
        descricao="galpão",
        onus=(Onus(tipo="Alienação fiduciária em favor de terceiro"),),
    )
    lote = Lote(
        procedimento_id=procedimento.id,
        ativos=(ativo.id,),
        regime_transmissao=RegimeTransmissao.LFR_141_II_FALENCIA,
        clausula_nao_sucessao="sem sucessão, art. 141, II",
    )
    contexto = ContextoBlindagem.de_entidades(
        lote, procedimento, (ativo,), cadeia_dominial_verificada=True
    )
    assert contexto.clausula_nao_sucessao_no_edital
    assert contexto.onus_de_terceiro_detectado
    assert contexto.classe_ativo_principal is ClasseAtivo.IMOVEL_URBANO

    r = avaliar_blindagem(contexto)
    assert "B15" in " ".join(r.explicacao.linhas())


def test_lote_sem_ativo_nao_e_avaliavel():
    procedimento = Procedimento(
        numero_cnj="1234567-13.2024.8.26.0100",
        natureza=NaturezaProcedimento.FALENCIA,
        tribunal="TJSP",
    )
    lote = Lote(procedimento_id=procedimento.id, ativos=(uuid4(),))
    with pytest.raises(ValueError, match="sem ativos"):
        ContextoBlindagem.de_entidades(lote, procedimento, ())
