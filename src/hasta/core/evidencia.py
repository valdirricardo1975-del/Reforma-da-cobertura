"""Procedência (ADR-0003) e muralha ética em código (ADR-0009).

Nenhum campo relevante existe solto: todo valor carrega documento, trecho, hash e
data de coleta. E toda evidência carrega a **origem** da informação — é o que
permite provar que uma decisão de investimento se apoiou apenas em fonte pública,
requisito de um escritório que atua na mesma matéria (doc 06).

O rótulo de origem é *pegajoso*: qualquer derivação herda a origem mais restritiva
das suas entradas.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from datetime import date, datetime
from enum import StrEnum, unique
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


@unique
class Origem(StrEnum):
    """Ordem de restritividade crescente: PUBLICA < RELACIONAMENTO < CLIENTE."""

    PUBLICA = "PUBLICA"
    INTERNA = "INTERNA"
    RELACIONAMENTO = "RELACIONAMENTO"
    CLIENTE = "CLIENTE"

    @property
    def restritividade(self) -> int:
        return {"PUBLICA": 0, "INTERNA": 1, "RELACIONAMENTO": 2, "CLIENTE": 3}[self.value]

    @property
    def pode_investir(self) -> bool:
        """Só informação pública (e derivação dela) alimenta decisão de aquisição."""
        return self in {Origem.PUBLICA, Origem.INTERNA}


class OrigemRestritaError(PermissionError):
    """Evidência de origem não pública tentou alimentar o pipeline de investimento."""

    def __init__(self, ofensoras: tuple[UUID, ...], origem: Origem) -> None:
        super().__init__(
            f"{len(ofensoras)} evidência(s) de origem {origem.value} não podem alimentar "
            "cálculo de oportunidade (doc 06, § 2). Lote vai para quarentena."
        )
        self.ofensoras = ofensoras
        self.origem = origem


def origem_mais_restritiva(origens: Iterable[Origem]) -> Origem:
    """Rótulo pegajoso: a derivação nunca é menos restrita que sua entrada."""
    candidatas = list(origens)
    if not candidatas:
        return Origem.PUBLICA
    return max(candidatas, key=lambda o: o.restritividade)


class Documento(BaseModel):
    """Snapshot imutável do que foi visto — base de toda reprodutibilidade."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    uri_origem: str
    caminho_snapshot: str
    sha256: str
    tipo_midia: str = "application/pdf"
    coletado_em: datetime
    fonte: str
    origem: Origem = Origem.PUBLICA
    titulo: str | None = None
    data_documento: date | None = None

    @field_validator("sha256")
    @classmethod
    def _hash_valido(cls, v: str) -> str:
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("sha256 deve ter 64 dígitos hexadecimais")
        return v.lower()

    @staticmethod
    def calcular_sha256(conteudo: bytes) -> str:
        return hashlib.sha256(conteudo).hexdigest()


class Evidencia(BaseModel):
    """Unidade atômica de procedência: um campo, um valor, um trecho que o sustenta."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    documento_id: UUID
    campo: str = Field(min_length=1, description="caminho canônico, ex.: lote.lance_minimo")
    valor: Any
    localizador: str = Field(min_length=1, description='"p.14, §3" | seletor | offset')
    trecho: str = Field(min_length=1, description="texto literal que sustenta a afirmação")
    extrator: str = Field(min_length=1, description="parser:esaj_edital@2.1 | llm:escriba@2026-09")
    confianca: float = Field(ge=0.0, le=1.0)
    origem: Origem
    coletado_em: datetime
    conflita_com: tuple[UUID, ...] = ()

    @property
    def pode_investir(self) -> bool:
        return self.origem.pode_investir


def assert_origem_publica(evidencias: Iterable[Evidencia]) -> None:
    """Portão 2 (doc 06). Violação levanta exceção — não registra aviso e segue."""
    ofensoras = tuple(e.id for e in evidencias if not e.pode_investir)
    if ofensoras:
        restritas = [e.origem for e in evidencias if not e.pode_investir]
        raise OrigemRestritaError(ofensoras, origem_mais_restritiva(restritas))


#: Precedência entre fontes divergentes (doc 03, § 1): conflito não se resolve por
#: sobrescrita — escolhe-se o valor efetivo e a divergência continua visível.
PRECEDENCIA_FONTE: dict[str, int] = {
    "pnaj": 100,
    "djen": 95,
    "datajud": 90,
    "tribunal": 85,
    "administrador_judicial": 80,
    "leiloeiro": 70,
    "diario_oficial": 65,
    "cadastro_publico": 60,
    "noticia": 20,
}


def valor_efetivo(evidencias: Iterable[Evidencia], fonte_de: dict[UUID, str]) -> Evidencia | None:
    """Escolhe a evidência prevalente por precedência de fonte, depois confiança, depois data."""
    candidatas = list(evidencias)
    if not candidatas:
        return None
    return max(
        candidatas,
        key=lambda e: (
            PRECEDENCIA_FONTE.get(fonte_de.get(e.documento_id, ""), 0),
            e.confianca,
            e.coletado_em,
        ),
    )
