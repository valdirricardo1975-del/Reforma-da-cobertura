"""Vocabulário controlado do domínio (doc 03)."""

from __future__ import annotations

from enum import StrEnum, unique


@unique
class NaturezaProcedimento(StrEnum):
    RJ = "RJ"
    FALENCIA = "FALENCIA"
    RE_EXTRAJUDICIAL = "RE_EXTRAJUDICIAL"
    EXEC_TITULO = "EXEC_TITULO"
    EXEC_FISCAL = "EXEC_FISCAL"
    EXEC_TRABALHISTA = "EXEC_TRABALHISTA"
    INSOLVENCIA_CIVIL = "INSOLVENCIA_CIVIL"
    OUTRO = "OUTRO"

    @property
    def concursal(self) -> bool:
        """Procedimentos onde vale o regime da Lei 11.101/2005 — o nosso foco."""
        return self in {
            NaturezaProcedimento.RJ,
            NaturezaProcedimento.FALENCIA,
            NaturezaProcedimento.RE_EXTRAJUDICIAL,
        }


@unique
class ClasseAtivo(StrEnum):
    IMOVEL_URBANO = "IMOVEL_URBANO"
    IMOVEL_RURAL = "IMOVEL_RURAL"
    PLANTA_INDUSTRIAL = "PLANTA_INDUSTRIAL"
    MAQUINA_EQUIPAMENTO = "MAQUINA_EQUIPAMENTO"
    VEICULO = "VEICULO"
    FROTA = "FROTA"
    ESTOQUE = "ESTOQUE"
    MARCA_IP = "MARCA_IP"
    PARTICIPACAO_SOCIETARIA = "PARTICIPACAO_SOCIETARIA"
    CARTEIRA_CREDITO = "CARTEIRA_CREDITO"
    PRECATORIO = "PRECATORIO"
    CREDITO_FISCAL = "CREDITO_FISCAL"
    DIREITO_LITIGIOSO = "DIREITO_LITIGIOSO"
    UPI = "UPI"
    OUTRO = "OUTRO"


@unique
class MaturidadeValuation(StrEnum):
    """ADR-0012: profundidade do valuation por classe, declarada e visível."""

    CALIBRADO = "CALIBRADO"
    ESTIMADO = "ESTIMADO"
    TRIAGEM = "TRIAGEM"

    @property
    def pode_recomendar(self) -> bool:
        return self is not MaturidadeValuation.TRIAGEM

    @property
    def teto_confianca(self) -> float:
        return {"CALIBRADO": 1.0, "ESTIMADO": 0.75, "TRIAGEM": 0.4}[self.value]


#: Estado atual da escada de maturidade. Muda conforme o backtesting promove classes
#: (doc 04, § 9). Toda classe nasce em TRIAGEM: nenhuma classe recebe recomendação
#: antes de ter erro medido.
MATURIDADE_POR_CLASSE: dict[ClasseAtivo, MaturidadeValuation] = {
    classe: MaturidadeValuation.TRIAGEM for classe in ClasseAtivo
}

#: Ordem de promoção decidida em 12/09/2026 (ADR-0012): primazia do imóvel urbano.
ORDEM_PROMOCAO: tuple[ClasseAtivo, ...] = (
    ClasseAtivo.IMOVEL_URBANO,
    ClasseAtivo.PLANTA_INDUSTRIAL,
    ClasseAtivo.MAQUINA_EQUIPAMENTO,
    ClasseAtivo.VEICULO,
    ClasseAtivo.IMOVEL_RURAL,
    ClasseAtivo.UPI,
    ClasseAtivo.CARTEIRA_CREDITO,
    ClasseAtivo.PRECATORIO,
)


def maturidade(classe: ClasseAtivo) -> MaturidadeValuation:
    return MATURIDADE_POR_CLASSE.get(classe, MaturidadeValuation.TRIAGEM)


@unique
class RegimeTransmissao(StrEnum):
    """Chave da dimensão *blindagem* (doc 04, § 2)."""

    LFR_141_II_FALENCIA = "LFR_141_II_FALENCIA"
    LFR_60_UPI = "LFR_60_UPI"
    LFR_144_145_ALTERNATIVA = "LFR_144_145_ALTERNATIVA"
    CPC_879_LEILAO = "CPC_879_LEILAO"
    CPC_880_INICIATIVA_PARTICULAR = "CPC_880_INICIATIVA_PARTICULAR"
    LEI_9514_EXTRAJUDICIAL = "LEI_9514_EXTRAJUDICIAL"
    INDETERMINADO = "INDETERMINADO"

    @property
    def concursal(self) -> bool:
        return self in {
            RegimeTransmissao.LFR_141_II_FALENCIA,
            RegimeTransmissao.LFR_60_UPI,
            RegimeTransmissao.LFR_144_145_ALTERNATIVA,
        }


@unique
class Modalidade(StrEnum):
    LEILAO_ELETRONICO = "LEILAO_ELETRONICO"
    LEILAO_PRESENCIAL = "LEILAO_PRESENCIAL"
    LEILAO_HIBRIDO = "LEILAO_HIBRIDO"
    PROPOSTA_FECHADA = "PROPOSTA_FECHADA"
    PREGAO = "PREGAO"
    VENDA_DIRETA = "VENDA_DIRETA"


@unique
class Ocupacao(StrEnum):
    DESOCUPADO = "DESOCUPADO"
    OCUPADO_TERCEIRO = "OCUPADO_TERCEIRO"
    OCUPADO_DEVEDOR = "OCUPADO_DEVEDOR"
    INVADIDO = "INVADIDO"
    LOCADO = "LOCADO"
    DESCONHECIDO = "DESCONHECIDO"


@unique
class StatusPraca(StrEnum):
    DESIGNADA = "DESIGNADA"
    SUSPENSA = "SUSPENSA"
    REALIZADA = "REALIZADA"
    DESERTA = "DESERTA"
    CANCELADA = "CANCELADA"


@unique
class ClasseCredito(StrEnum):
    I_TRABALHISTA = "I_TRABALHISTA"
    II_GARANTIA_REAL = "II_GARANTIA_REAL"
    III_QUIROGRAFARIO = "III_QUIROGRAFARIO"
    IV_ME_EPP = "IV_ME_EPP"
    EXTRACONCURSAL = "EXTRACONCURSAL"


@unique
class TipoAtor(StrEnum):
    ADMINISTRADOR_JUDICIAL = "ADMINISTRADOR_JUDICIAL"
    JUIZ = "JUIZ"
    LEILOEIRO = "LEILOEIRO"
    GESTOR_JUDICIAL = "GESTOR_JUDICIAL"
    ADVOGADO = "ADVOGADO"
    CREDOR = "CREDOR"
    FUNDO = "FUNDO"
    PERITO = "PERITO"


@unique
class RotaAcesso(StrEnum):
    """Doc 04, § 6 — a rota é calculada, não presumida."""

    LANCE_EM_PRACA = "LANCE_EM_PRACA"
    COMPRA_DE_CREDITO = "COMPRA_DE_CREDITO"
    DIP = "DIP"
    STALKING_HORSE_UPI = "STALKING_HORSE_UPI"
    VENDA_DIRETA = "VENDA_DIRETA"
    ADJUDICACAO = "ADJUDICACAO"


@unique
class TipoOportunidade(StrEnum):
    """Os cinco padrões do doc 01, § 4."""

    T1_DESAGIO_POR_COMPLEXIDADE = "T1_DESAGIO_POR_COMPLEXIDADE"
    T2_BLINDAGEM_SUBPRECIFICADA = "T2_BLINDAGEM_SUBPRECIFICADA"
    T3_LAUDO_DEFASADO = "T3_LAUDO_DEFASADO"
    T4_UPI_GOING_CONCERN = "T4_UPI_GOING_CONCERN"
    T5_ROTA_INDIRETA = "T5_ROTA_INDIRETA"
