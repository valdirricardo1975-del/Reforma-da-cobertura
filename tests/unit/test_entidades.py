from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from hasta.core.entidades import (
    Ativo,
    AtorProcessual,
    AvaliacaoOficial,
    Devedor,
    EventoProcessual,
    Lote,
    Oportunidade,
    Praca,
    Procedimento,
)
from hasta.core.enums import (
    ClasseAtivo,
    MaturidadeValuation,
    NaturezaProcedimento,
    RegimeTransmissao,
    TipoAtor,
)
from hasta.core.estados import EstadoOportunidade
from hasta.core.eventos import EstagioFunil, TipoEvento
from hasta.core.money import Money

NUMERO = "1234567-13.2024.8.26.0100"


def test_procedimento_normaliza_numero_para_forma_canonica():
    p = Procedimento(numero_cnj=NUMERO, natureza=NaturezaProcedimento.RJ, tribunal="TJSP")
    assert p.numero_cnj == "12345671320248260100"
    assert p.numero.formatado() == NUMERO
    assert p.numero.sigla_tribunal == "TJSP"


def test_numero_invalido_recusado_na_entidade():
    with pytest.raises(ValueError):
        Procedimento(numero_cnj="nao-e-numero", natureza=NaturezaProcedimento.RJ, tribunal="TJSP")


def test_natureza_concursal_identifica_o_nosso_foco():
    for natureza in (
        NaturezaProcedimento.RJ,
        NaturezaProcedimento.FALENCIA,
        NaturezaProcedimento.RE_EXTRAJUDICIAL,
    ):
        assert natureza.concursal
    assert not NaturezaProcedimento.EXEC_FISCAL.concursal


def test_segredo_de_justica_torna_procedimento_nao_coletavel():
    p = Procedimento(
        numero_cnj=NUMERO,
        natureza=NaturezaProcedimento.FALENCIA,
        tribunal="TJSP",
        segredo_justica=True,
    )
    assert not p.coletavel


def test_devedor_exige_identificador():
    Devedor(razao_social="Indústria Exemplo S.A.", cnpj="00000000000191")
    with pytest.raises(ValueError):
        Devedor(razao_social="")


def test_toda_classe_de_ativo_nasce_em_triagem():
    """ADR-0012: nenhuma classe recebe recomendação antes de ter erro medido."""
    for classe in ClasseAtivo:
        ativo = Ativo(classe=classe, descricao="teste")
        assert ativo.maturidade_valuation is MaturidadeValuation.TRIAGEM
        assert not ativo.maturidade_valuation.pode_recomendar


def test_maturidade_limita_confianca():
    assert MaturidadeValuation.CALIBRADO.teto_confianca == 1.0
    assert MaturidadeValuation.ESTIMADO.teto_confianca == 0.75
    assert MaturidadeValuation.TRIAGEM.teto_confianca == 0.4


def test_regime_concursal_marca_blindagem_potencial():
    assert RegimeTransmissao.LFR_141_II_FALENCIA.concursal
    assert RegimeTransmissao.LFR_60_UPI.concursal
    assert not RegimeTransmissao.CPC_879_LEILAO.concursal
    assert not RegimeTransmissao.INDETERMINADO.concursal


def test_blindagem_declarada_exige_regime_concursal_e_clausula():
    base = {"procedimento_id": uuid4(), "ativos": (uuid4(),)}
    sem_clausula = Lote(**base, regime_transmissao=RegimeTransmissao.LFR_141_II_FALENCIA)
    assert not sem_clausula.blindagem_declarada

    com_clausula_em_execucao = Lote(
        **base,
        regime_transmissao=RegimeTransmissao.CPC_879_LEILAO,
        clausula_nao_sucessao="o arrematante não responde por débitos anteriores",
    )
    assert not com_clausula_em_execucao.blindagem_declarada

    blindado = Lote(
        **base,
        regime_transmissao=RegimeTransmissao.LFR_141_II_FALENCIA,
        clausula_nao_sucessao="objeto da alienação livre de ônus, sem sucessão (art. 141, II)",
    )
    assert blindado.blindagem_declarada


def test_lote_exige_ao_menos_um_ativo():
    with pytest.raises(ValueError):
        Lote(procedimento_id=uuid4(), ativos=())


def test_praca_recusa_janela_invertida():
    with pytest.raises(ValueError, match="anterior"):
        Praca(
            ordem=1,
            data_inicio=datetime(2026, 10, 10, tzinfo=UTC),
            data_fim=datetime(2026, 10, 1, tzinfo=UTC),
            lance_minimo=Money.de_reais("600000"),
        )


def test_idade_do_laudo_alimenta_penalizacao():
    laudo = AvaliacaoOficial(valor=Money.de_reais("1000000"), data_base=date(2019, 6, 1))
    assert laudo.idade_em_meses(date(2026, 9, 1)) == 87


def test_evento_conhece_seu_estagio_no_funil():
    e = EventoProcessual(
        tipo=TipoEvento.PLANO_COM_UPI,
        ocorrido_em=date(2026, 3, 1),
        detectado_em=datetime(2026, 3, 2, tzinfo=UTC),
        fonte="administrador_judicial",
    )
    assert e.estagio is EstagioFunil.P3_AUTORIZACAO


def test_indice_de_antecipacao_e_a_kpi_assinatura():
    o = Oportunidade(
        lote_id=uuid4(),
        detectada_em=datetime(2026, 1, 10, tzinfo=UTC),
        edital_publicado_em=date(2026, 7, 10),
    )
    assert o.indice_antecipacao_dias == 181


def test_indice_de_antecipacao_indefinido_sem_edital():
    assert Oportunidade(lote_id=uuid4()).indice_antecipacao_dias is None


def test_descarte_e_bloqueio_exigem_motivo_visivel():
    with pytest.raises(ValueError, match="motivo"):
        Oportunidade(lote_id=uuid4(), estado=EstadoOportunidade.DESCARTADA)
    with pytest.raises(ValueError, match="motivo"):
        Oportunidade(lote_id=uuid4(), estado=EstadoOportunidade.BLOQUEADA_COMPLIANCE)

    ok = Oportunidade(
        lote_id=uuid4(),
        estado=EstadoOportunidade.BLOQUEADA_COMPLIANCE,
        motivo_bloqueio="escritório atua no processo — impedimento do advogado da causa",
    )
    assert ok.motivo_bloqueio


def test_ator_guarda_metricas_do_grafo():
    aj = AtorProcessual(
        tipo=TipoAtor.ADMINISTRADOR_JUDICIAL,
        nome="AJ Exemplo",
        qualidade_documental=0.92,
        casos_observados=37,
    )
    assert aj.qualidade_documental == 0.92
    with pytest.raises(ValueError):
        AtorProcessual(tipo=TipoAtor.LEILOEIRO, nome="X", taxa_anulacao=Decimal("1.5"))
