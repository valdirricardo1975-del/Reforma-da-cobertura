"""Tipos comuns de explicação dos motores determinísticos.

Todo motor deste pacote devolve, junto com o número, a **conta que levou até ele**:
cada ajuste com a regra que o produziu, a base legal e o status de validação. É o
que permite um advogado do escritório revisar regra por regra — e discordar de uma
sem derrubar o resto (doc 04).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, unique
from typing import Protocol, runtime_checkable


@unique
class StatusRegra(StrEnum):
    """Estado de validação jurídica de uma regra."""

    #: Premissa conferida em fonte primária e revisada internamente.
    VIGENTE = "VIGENTE"
    #: Premissa plausível, marcada `⚠ verificar` nos docs: aguarda conferência em lei
    #: ou jurisprudência antes de valer em decisão de capital (doc 07, Fase 1).
    A_VALIDAR = "A_VALIDAR"
    #: Desativada por decisão interna, mas mantida no catálogo com o motivo.
    REVOGADA = "REVOGADA"

    @property
    def conta_no_score(self) -> bool:
        return self is not StatusRegra.REVOGADA


@dataclass(frozen=True, slots=True)
class Regra:
    """Item de catálogo: o que a regra afirma e de onde ela vem."""

    id: str
    titulo: str
    base_legal: str
    status: StatusRegra = StatusRegra.A_VALIDAR
    observacao: str | None = None


@runtime_checkable
class RegraValidavel(Protocol):
    """Superfície comum entre ``Regra`` e os itens do checklist de vícios.

    Existe para que o catálogo do doc 08 e os testes tratem as duas famílias de regra
    de forma uniforme: o que importa para validação é identificador, fundamento e status.
    """

    @property
    def id(self) -> str: ...

    @property
    def titulo(self) -> str: ...

    @property
    def base_legal(self) -> str: ...

    @property
    def status(self) -> StatusRegra: ...

    @property
    def observacao(self) -> str | None: ...


@dataclass(frozen=True, slots=True)
class Ajuste:
    """Uma parcela da conta, com a regra que a justifica."""

    regra_id: str
    motivo: str
    delta: int
    base_legal: str
    status: StatusRegra

    def __str__(self) -> str:
        sinal = "+" if self.delta >= 0 else ""
        return f"{self.regra_id} {sinal}{self.delta}: {self.motivo} ({self.base_legal})"


@dataclass(frozen=True, slots=True)
class Teto:
    """Limite superior imposto por lacuna de verificação.

    Teto é mais honesto que desconto: sem cadeia dominial verificada, o ativo não é
    "um pouco menos blindado" — ele não pode ser classificado como blindado.
    """

    regra_id: str
    valor: int
    motivo: str


@dataclass(frozen=True, slots=True)
class Explicacao:
    """Conta completa: base, ajustes, tetos e resultado."""

    base: int
    ajustes: tuple[Ajuste, ...] = ()
    tetos: tuple[Teto, ...] = ()
    minimo: int = 0
    maximo: int = 100

    @property
    def soma_ajustes(self) -> int:
        return sum(a.delta for a in self.ajustes if a.status.conta_no_score)

    @property
    def teto_aplicado(self) -> Teto | None:
        if not self.tetos:
            return None
        return min(self.tetos, key=lambda t: t.valor)

    @property
    def valor(self) -> int:
        bruto = self.base + self.soma_ajustes
        teto = self.teto_aplicado
        if teto is not None:
            bruto = min(bruto, teto.valor)
        return max(self.minimo, min(self.maximo, bruto))

    @property
    def regras_a_validar(self) -> tuple[str, ...]:
        """Regras que ainda dependem de conferência jurídica e já afetaram o número."""
        return tuple(
            dict.fromkeys(a.regra_id for a in self.ajustes if a.status is StatusRegra.A_VALIDAR)
        )

    def linhas(self) -> tuple[str, ...]:
        """Renderização textual para o dossiê."""
        saida = [f"base {self.base}"]
        saida += [str(a) for a in self.ajustes]
        teto = self.teto_aplicado
        if teto is not None and self.base + self.soma_ajustes > teto.valor:
            saida.append(f"{teto.regra_id} teto {teto.valor}: {teto.motivo}")
        saida.append(f"= {self.valor}")
        return tuple(saida)


@dataclass
class Acumulador:
    """Construtor incremental de uma ``Explicacao``."""

    base: int
    _ajustes: list[Ajuste] = field(default_factory=list)
    _tetos: list[Teto] = field(default_factory=list)

    def ajustar(self, regra: Regra, delta: int, motivo: str | None = None) -> Acumulador:
        self._ajustes.append(
            Ajuste(
                regra_id=regra.id,
                motivo=motivo or regra.titulo,
                delta=delta,
                base_legal=regra.base_legal,
                status=regra.status,
            )
        )
        return self

    def limitar(self, regra: Regra, valor: int, motivo: str | None = None) -> Acumulador:
        self._tetos.append(Teto(regra.id, valor, motivo or regra.titulo))
        return self

    def fechar(self) -> Explicacao:
        return Explicacao(self.base, tuple(self._ajustes), tuple(self._tetos))
