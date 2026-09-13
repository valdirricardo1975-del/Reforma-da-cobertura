"""Motores determinísticos de avaliação e risco (doc 04).

Nenhum LLM produz número aqui: o que um LLM faz, nas camadas anteriores, é ler
documento e devolver fato citado. O cálculo é código testável e versionado (ADR-0004).
"""

from hasta.score.blindagem import (
    BASE_POR_REGIME,
    CATALOGO_BLINDAGEM,
    PESOS_BLINDAGEM,
    TETOS_BLINDAGEM,
    ContextoBlindagem,
    FaixaBlindagem,
    ResultadoBlindagem,
    avaliar_blindagem,
)
from hasta.score.explicacao import (
    Acumulador,
    Ajuste,
    Explicacao,
    Regra,
    RegraValidavel,
    StatusRegra,
    Teto,
)
from hasta.score.vicios import (
    CHECKLIST_VICIOS,
    NOTAS_DE_REGIME,
    PESO_INDETERMINADO,
    PRIOR_NULIDADE_POR_SEVERIDADE,
    Constatacao,
    ContextoVicios,
    Escopo,
    ItemVicio,
    ResultadoVicios,
    Severidade,
    Situacao,
    cacar_vicios,
)

__all__ = [
    "BASE_POR_REGIME",
    "CATALOGO_BLINDAGEM",
    "CHECKLIST_VICIOS",
    "NOTAS_DE_REGIME",
    "PESOS_BLINDAGEM",
    "PESO_INDETERMINADO",
    "PRIOR_NULIDADE_POR_SEVERIDADE",
    "TETOS_BLINDAGEM",
    "Acumulador",
    "Ajuste",
    "Constatacao",
    "ContextoBlindagem",
    "ContextoVicios",
    "Escopo",
    "Explicacao",
    "FaixaBlindagem",
    "ItemVicio",
    "Regra",
    "RegraValidavel",
    "ResultadoBlindagem",
    "ResultadoVicios",
    "Severidade",
    "Situacao",
    "StatusRegra",
    "Teto",
    "avaliar_blindagem",
    "cacar_vicios",
]
