"""Máquinas de estado do procedimento concursal e da oportunidade (doc 03, §§ 4 e 5).

Transição ilegal é erro de execução, não aviso. A máquina do procedimento é o que
permite ao Batedor saber **o que esperar em seguida** e priorizar a coleta.
"""

from __future__ import annotations

from enum import StrEnum, unique


class TransicaoInvalida(ValueError):
    """Tentativa de transição não prevista na máquina de estados."""

    def __init__(self, de: StrEnum, para: StrEnum) -> None:
        super().__init__(f"transição inválida: {de.value} → {para.value}")
        self.de = de
        self.para = para


@unique
class EstadoProcedimento(StrEnum):
    PEDIDO = "PEDIDO"
    PROCESSAMENTO_DEFERIDO = "PROCESSAMENTO_DEFERIDO"
    RELACAO_CREDORES = "RELACAO_CREDORES"
    PLANO_APRESENTADO = "PLANO_APRESENTADO"
    AGC = "AGC"
    PLANO_APROVADO = "PLANO_APROVADO"
    PLANO_REJEITADO = "PLANO_REJEITADO"
    EM_CUMPRIMENTO = "EM_CUMPRIMENTO"
    ALIENACAO_UPI = "ALIENACAO_UPI"
    DESCUMPRIMENTO = "DESCUMPRIMENTO"
    FALENCIA = "FALENCIA"
    ARRECADACAO = "ARRECADACAO"
    ALIENACAO_FALIMENTAR = "ALIENACAO_FALIMENTAR"
    ENCERRADA = "ENCERRADA"
    ARQUIVADO = "ARQUIVADO"


TRANSICOES_PROCEDIMENTO: dict[EstadoProcedimento, frozenset[EstadoProcedimento]] = {
    EstadoProcedimento.PEDIDO: frozenset(
        {
            EstadoProcedimento.PROCESSAMENTO_DEFERIDO,
            EstadoProcedimento.FALENCIA,
            EstadoProcedimento.ARQUIVADO,
        }
    ),
    EstadoProcedimento.PROCESSAMENTO_DEFERIDO: frozenset(
        {
            EstadoProcedimento.RELACAO_CREDORES,
            EstadoProcedimento.PLANO_APRESENTADO,
            EstadoProcedimento.FALENCIA,
            EstadoProcedimento.ARQUIVADO,
        }
    ),
    EstadoProcedimento.RELACAO_CREDORES: frozenset(
        {EstadoProcedimento.PLANO_APRESENTADO, EstadoProcedimento.FALENCIA}
    ),
    EstadoProcedimento.PLANO_APRESENTADO: frozenset(
        {EstadoProcedimento.AGC, EstadoProcedimento.FALENCIA}
    ),
    EstadoProcedimento.AGC: frozenset(
        {
            EstadoProcedimento.PLANO_APROVADO,
            EstadoProcedimento.PLANO_REJEITADO,
            EstadoProcedimento.FALENCIA,
        }
    ),
    EstadoProcedimento.PLANO_APROVADO: frozenset({EstadoProcedimento.EM_CUMPRIMENTO}),
    EstadoProcedimento.PLANO_REJEITADO: frozenset({EstadoProcedimento.FALENCIA}),
    EstadoProcedimento.EM_CUMPRIMENTO: frozenset(
        {
            EstadoProcedimento.ALIENACAO_UPI,
            EstadoProcedimento.DESCUMPRIMENTO,
            EstadoProcedimento.ENCERRADA,
        }
    ),
    # A alienação de UPI não encerra o cumprimento: pode haver mais de uma.
    EstadoProcedimento.ALIENACAO_UPI: frozenset(
        {
            EstadoProcedimento.EM_CUMPRIMENTO,
            EstadoProcedimento.DESCUMPRIMENTO,
            EstadoProcedimento.ENCERRADA,
        }
    ),
    EstadoProcedimento.DESCUMPRIMENTO: frozenset(
        {EstadoProcedimento.FALENCIA, EstadoProcedimento.EM_CUMPRIMENTO}
    ),
    EstadoProcedimento.FALENCIA: frozenset({EstadoProcedimento.ARRECADACAO}),
    EstadoProcedimento.ARRECADACAO: frozenset(
        {EstadoProcedimento.ALIENACAO_FALIMENTAR, EstadoProcedimento.ENCERRADA}
    ),
    # Também aqui há repetição: vários lotes, várias praças.
    EstadoProcedimento.ALIENACAO_FALIMENTAR: frozenset(
        {EstadoProcedimento.ARRECADACAO, EstadoProcedimento.ENCERRADA}
    ),
    EstadoProcedimento.ENCERRADA: frozenset(),
    EstadoProcedimento.ARQUIVADO: frozenset(),
}

#: Estados em que o procedimento pode gerar lote a qualquer momento — prioridade de coleta.
ESTADOS_FERTEIS: frozenset[EstadoProcedimento] = frozenset(
    {
        EstadoProcedimento.EM_CUMPRIMENTO,
        EstadoProcedimento.ALIENACAO_UPI,
        EstadoProcedimento.ARRECADACAO,
        EstadoProcedimento.ALIENACAO_FALIMENTAR,
    }
)


@unique
class EstadoOportunidade(StrEnum):
    DETECTADA = "DETECTADA"
    QUALIFICADA = "QUALIFICADA"
    PRECIFICADA = "PRECIFICADA"
    PROMOVIDA = "PROMOVIDA"
    EM_DD = "EM_DD"
    APROVADA_COMITE = "APROVADA_COMITE"
    LANCE_AUTORIZADO = "LANCE_AUTORIZADO"
    ARREMATADA = "ARREMATADA"
    PERDIDA = "PERDIDA"
    DESERTA = "DESERTA"
    POS_ARREMATACAO = "POS_ARREMATACAO"
    SAIDA_REALIZADA = "SAIDA_REALIZADA"
    DESCARTADA = "DESCARTADA"
    BLOQUEADA_COMPLIANCE = "BLOQUEADA_COMPLIANCE"


_SAIDAS_SEMPRE_POSSIVEIS = frozenset(
    {EstadoOportunidade.DESCARTADA, EstadoOportunidade.BLOQUEADA_COMPLIANCE}
)

TRANSICOES_OPORTUNIDADE: dict[EstadoOportunidade, frozenset[EstadoOportunidade]] = {
    EstadoOportunidade.DETECTADA: frozenset({EstadoOportunidade.QUALIFICADA}),
    EstadoOportunidade.QUALIFICADA: frozenset({EstadoOportunidade.PRECIFICADA}),
    EstadoOportunidade.PRECIFICADA: frozenset({EstadoOportunidade.PROMOVIDA}),
    EstadoOportunidade.PROMOVIDA: frozenset({EstadoOportunidade.EM_DD}),
    EstadoOportunidade.EM_DD: frozenset({EstadoOportunidade.APROVADA_COMITE}),
    EstadoOportunidade.APROVADA_COMITE: frozenset({EstadoOportunidade.LANCE_AUTORIZADO}),
    EstadoOportunidade.LANCE_AUTORIZADO: frozenset(
        {
            EstadoOportunidade.ARREMATADA,
            EstadoOportunidade.PERDIDA,
            EstadoOportunidade.DESERTA,
        }
    ),
    EstadoOportunidade.ARREMATADA: frozenset({EstadoOportunidade.POS_ARREMATACAO}),
    # Lote deserto volta ao ciclo: nova praça, lance mínimo menor (padrão T1).
    EstadoOportunidade.DESERTA: frozenset({EstadoOportunidade.PRECIFICADA}),
    EstadoOportunidade.PERDIDA: frozenset(),
    EstadoOportunidade.POS_ARREMATACAO: frozenset({EstadoOportunidade.SAIDA_REALIZADA}),
    EstadoOportunidade.SAIDA_REALIZADA: frozenset(),
    EstadoOportunidade.DESCARTADA: frozenset(),
    EstadoOportunidade.BLOQUEADA_COMPLIANCE: frozenset(),
}

#: Estados terminais — nenhuma transição de saída.
TERMINAIS_OPORTUNIDADE: frozenset[EstadoOportunidade] = frozenset(
    {
        EstadoOportunidade.PERDIDA,
        EstadoOportunidade.SAIDA_REALIZADA,
        EstadoOportunidade.DESCARTADA,
        EstadoOportunidade.BLOQUEADA_COMPLIANCE,
    }
)


def transicoes_procedimento(de: EstadoProcedimento) -> frozenset[EstadoProcedimento]:
    return TRANSICOES_PROCEDIMENTO[de]


def transicoes_oportunidade(de: EstadoOportunidade) -> frozenset[EstadoOportunidade]:
    """Descarte e bloqueio são possíveis de qualquer estado não terminal."""
    saidas = TRANSICOES_OPORTUNIDADE[de]
    if de in TERMINAIS_OPORTUNIDADE:
        return saidas
    return saidas | _SAIDAS_SEMPRE_POSSIVEIS


def aplicar_procedimento(de: EstadoProcedimento, para: EstadoProcedimento) -> EstadoProcedimento:
    if para not in transicoes_procedimento(de):
        raise TransicaoInvalida(de, para)
    return para


def aplicar_oportunidade(de: EstadoOportunidade, para: EstadoOportunidade) -> EstadoOportunidade:
    if para not in transicoes_oportunidade(de):
        raise TransicaoInvalida(de, para)
    return para
