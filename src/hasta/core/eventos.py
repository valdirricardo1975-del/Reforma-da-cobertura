"""Taxonomia de eventos e o funil de originação P0–P5 (doc 02, § 3).

Este módulo é a especificação executável do **Batedor**: para cada evento, em que
estágio do funil ele aparece e quanta antecipação ele oferece em relação ao edital.

O mapeamento ``código TPU → TipoEvento`` está deliberadamente vazio: os códigos da
Tabela Processual Unificada precisam ser conferidos na tabela vigente do CNJ
(spike da Fase 1, doc 07). Preencher de memória seria plantar erro silencioso na
base do funil — ``CODIGOS_TPU_PENDENTES`` existe para que isso apareça em teste,
e não em produção.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, unique


@unique
class EstagioFunil(StrEnum):
    P0_SINAL_FRACO = "P0_SINAL_FRACO"
    P1_PROCEDIMENTO = "P1_PROCEDIMENTO"
    P2_INVENTARIO = "P2_INVENTARIO"
    P3_AUTORIZACAO = "P3_AUTORIZACAO"
    P4_OFERTA_PUBLICA = "P4_OFERTA_PUBLICA"
    P5_RESULTADO = "P5_RESULTADO"

    @property
    def ordem(self) -> int:
        return int(self.value[1])

    @property
    def onde_o_mercado_acorda(self) -> bool:
        """P4 é onde os agregadores começam — e onde a nossa vantagem termina."""
        return self is EstagioFunil.P4_OFERTA_PUBLICA


@unique
class TipoEvento(StrEnum):
    PEDIDO_RJ_DISTRIBUIDO = "PEDIDO_RJ_DISTRIBUIDO"
    PEDIDO_FALENCIA_DISTRIBUIDO = "PEDIDO_FALENCIA_DISTRIBUIDO"
    DEFERIMENTO_PROCESSAMENTO = "DEFERIMENTO_PROCESSAMENTO"
    AJ_NOMEADO = "AJ_NOMEADO"
    RELACAO_CREDORES_PUBLICADA = "RELACAO_CREDORES_PUBLICADA"
    RMA_JUNTADO = "RMA_JUNTADO"
    AUTO_ARRECADACAO_JUNTADO = "AUTO_ARRECADACAO_JUNTADO"
    LAUDO_AVALIACAO_JUNTADO = "LAUDO_AVALIACAO_JUNTADO"
    PLANO_APRESENTADO = "PLANO_APRESENTADO"
    PLANO_COM_UPI = "PLANO_COM_UPI"
    AGC_CONVOCADA = "AGC_CONVOCADA"
    AGC_REALIZADA = "AGC_REALIZADA"
    PLANO_HOMOLOGADO = "PLANO_HOMOLOGADO"
    AUTORIZACAO_ART_66 = "AUTORIZACAO_ART_66"
    FALENCIA_DECRETADA = "FALENCIA_DECRETADA"
    CONVOLACAO_EM_FALENCIA = "CONVOLACAO_EM_FALENCIA"
    LEILOEIRO_NOMEADO = "LEILOEIRO_NOMEADO"
    LEILAO_DESIGNADO = "LEILAO_DESIGNADO"
    EDITAL_PUBLICADO = "EDITAL_PUBLICADO"
    EDITAL_RETIFICADO = "EDITAL_RETIFICADO"
    PRACA_SUSPENSA = "PRACA_SUSPENSA"
    PRACA_REALIZADA = "PRACA_REALIZADA"
    LOTE_DESERTO = "LOTE_DESERTO"
    ARREMATACAO_HOMOLOGADA = "ARREMATACAO_HOMOLOGADA"
    ARREMATACAO_ANULADA = "ARREMATACAO_ANULADA"


@dataclass(frozen=True, slots=True)
class MetaEvento:
    estagio: EstagioFunil
    lead_min_dias: int
    lead_max_dias: int
    descricao: str
    #: Códigos da Tabela Processual Unificada (CNJ) que sinalizam este evento.
    codigos_tpu: tuple[int, ...] = field(default_factory=tuple)
    #: Evento derivado de leitura de documento (LLM com citação), não de código de movimento.
    derivado_de_leitura: bool = False


_D = 1
_M = 30

CATALOGO: dict[TipoEvento, MetaEvento] = {
    TipoEvento.PEDIDO_RJ_DISTRIBUIDO: MetaEvento(
        EstagioFunil.P0_SINAL_FRACO, 12 * _M, 24 * _M, "Pedido de recuperação judicial distribuído"
    ),
    TipoEvento.PEDIDO_FALENCIA_DISTRIBUIDO: MetaEvento(
        EstagioFunil.P0_SINAL_FRACO, 9 * _M, 24 * _M, "Pedido de falência distribuído"
    ),
    TipoEvento.DEFERIMENTO_PROCESSAMENTO: MetaEvento(
        EstagioFunil.P1_PROCEDIMENTO, 6 * _M, 18 * _M, "Deferimento do processamento (art. 52)"
    ),
    TipoEvento.AJ_NOMEADO: MetaEvento(
        EstagioFunil.P1_PROCEDIMENTO, 6 * _M, 18 * _M, "Administrador judicial nomeado"
    ),
    TipoEvento.RELACAO_CREDORES_PUBLICADA: MetaEvento(
        EstagioFunil.P1_PROCEDIMENTO, 6 * _M, 18 * _M, "Relação de credores (art. 7º, § 2º)"
    ),
    TipoEvento.RMA_JUNTADO: MetaEvento(
        EstagioFunil.P1_PROCEDIMENTO, 1 * _M, 18 * _M, "Relatório mensal de atividades do AJ"
    ),
    TipoEvento.AUTO_ARRECADACAO_JUNTADO: MetaEvento(
        EstagioFunil.P2_INVENTARIO, 3 * _M, 12 * _M, "Auto de arrecadação — inventário de bens"
    ),
    TipoEvento.LAUDO_AVALIACAO_JUNTADO: MetaEvento(
        EstagioFunil.P2_INVENTARIO, 2 * _M, 9 * _M, "Laudo de avaliação juntado"
    ),
    TipoEvento.PLANO_APRESENTADO: MetaEvento(
        EstagioFunil.P3_AUTORIZACAO, 2 * _M, 8 * _M, "Plano de recuperação apresentado (art. 53)"
    ),
    TipoEvento.PLANO_COM_UPI: MetaEvento(
        EstagioFunil.P3_AUTORIZACAO,
        2 * _M,
        8 * _M,
        "Plano prevê alienação de UPI ou de ativos",
        derivado_de_leitura=True,
    ),
    TipoEvento.AGC_CONVOCADA: MetaEvento(
        EstagioFunil.P3_AUTORIZACAO, 1 * _M, 6 * _M, "Assembleia geral de credores convocada"
    ),
    TipoEvento.AGC_REALIZADA: MetaEvento(
        EstagioFunil.P3_AUTORIZACAO, 1 * _M, 6 * _M, "Assembleia geral de credores realizada"
    ),
    TipoEvento.PLANO_HOMOLOGADO: MetaEvento(
        EstagioFunil.P3_AUTORIZACAO, 1 * _M, 6 * _M, "Plano homologado (art. 58)"
    ),
    TipoEvento.AUTORIZACAO_ART_66: MetaEvento(
        EstagioFunil.P3_AUTORIZACAO, 1 * _M, 4 * _M, "Autorização de venda de ativo não circulante"
    ),
    TipoEvento.FALENCIA_DECRETADA: MetaEvento(
        EstagioFunil.P2_INVENTARIO, 3 * _M, 12 * _M, "Falência decretada"
    ),
    TipoEvento.CONVOLACAO_EM_FALENCIA: MetaEvento(
        EstagioFunil.P2_INVENTARIO, 3 * _M, 12 * _M, "Recuperação convolada em falência"
    ),
    TipoEvento.LEILOEIRO_NOMEADO: MetaEvento(
        EstagioFunil.P3_AUTORIZACAO, 1 * _M, 3 * _M, "Leiloeiro ou gestor judicial nomeado"
    ),
    TipoEvento.LEILAO_DESIGNADO: MetaEvento(
        EstagioFunil.P3_AUTORIZACAO, 15 * _D, 90 * _D, "Leilão designado por decisão"
    ),
    TipoEvento.EDITAL_PUBLICADO: MetaEvento(
        EstagioFunil.P4_OFERTA_PUBLICA, 15 * _D, 60 * _D, "Edital publicado — o mercado acorda"
    ),
    TipoEvento.EDITAL_RETIFICADO: MetaEvento(
        EstagioFunil.P4_OFERTA_PUBLICA, 5 * _D, 45 * _D, "Edital retificado — sinal de risco"
    ),
    TipoEvento.PRACA_SUSPENSA: MetaEvento(
        EstagioFunil.P4_OFERTA_PUBLICA, 0, 30 * _D, "Praça suspensa"
    ),
    TipoEvento.PRACA_REALIZADA: MetaEvento(EstagioFunil.P4_OFERTA_PUBLICA, 0, 0, "Praça realizada"),
    TipoEvento.LOTE_DESERTO: MetaEvento(
        EstagioFunil.P4_OFERTA_PUBLICA, 0, 30 * _D, "Lote deserto — reentrada em praça seguinte"
    ),
    TipoEvento.ARREMATACAO_HOMOLOGADA: MetaEvento(
        EstagioFunil.P5_RESULTADO, 0, 0, "Arrematação homologada"
    ),
    TipoEvento.ARREMATACAO_ANULADA: MetaEvento(
        EstagioFunil.P5_RESULTADO, 0, 0, "Arrematação anulada ou tornada ineficaz"
    ),
}

#: Eventos cujo detector ainda não tem código TPU confirmado (spike da Fase 1).
CODIGOS_TPU_PENDENTES: frozenset[TipoEvento] = frozenset(
    evento
    for evento, meta in CATALOGO.items()
    if not meta.codigos_tpu and not meta.derivado_de_leitura
)

#: Detectores com meta de recall explícita na Fase 2 (doc 07).
DETECTORES_CRITICOS: frozenset[TipoEvento] = frozenset(
    {
        TipoEvento.DEFERIMENTO_PROCESSAMENTO,
        TipoEvento.FALENCIA_DECRETADA,
        TipoEvento.PLANO_COM_UPI,
        TipoEvento.AUTORIZACAO_ART_66,
        TipoEvento.LEILAO_DESIGNADO,
        TipoEvento.EDITAL_PUBLICADO,
    }
)


def meta(evento: TipoEvento) -> MetaEvento:
    return CATALOGO[evento]


def mapear_codigo_tpu(codigo: int) -> TipoEvento | None:
    """Traduz código de movimento do DataJud em evento canônico."""
    for evento, m in CATALOGO.items():
        if codigo in m.codigos_tpu:
            return evento
    return None


def eventos_do_estagio(estagio: EstagioFunil) -> tuple[TipoEvento, ...]:
    return tuple(e for e, m in CATALOGO.items() if m.estagio is estagio)
