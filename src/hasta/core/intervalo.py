"""Estimativas com incerteza explícita (ADR-0005).

Todo motor devolve ``Faixa`` — p10/p50/p90 — e o ranking usa o p10, para que a
margem de segurança seja estrutural e não opinada.

Decisão deliberada: **quantis não somam**. ``Faixa(a) + Faixa(b)`` não é
``Faixa(a+b)`` salvo independência perfeita, e tratar como se fosse é o jeito
mais elegante de produzir um intervalo estreito e falso. Por isso a soma é
recusada; a composição de faixas correlacionadas entra na Fase 3, por simulação.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Generic, TypeVar

T = TypeVar("T")


def _como_numero(valor: object) -> float | None:
    """Extrai magnitude para razões, sem expor ``__float__`` em ``Money``.

    Dinheiro não deve ser convertível em ``float`` implicitamente (doc 03, § 7), mas
    o cálculo de uma razão adimensional é legítimo.
    """
    centavos = getattr(valor, "centavos", None)
    if centavos is not None:
        return float(centavos)
    if isinstance(valor, int | float | Decimal):
        return float(valor)
    return None


class QuantisNaoSomam(TypeError):
    """Tentativa de aritmética inválida entre faixas."""


@dataclass(frozen=True, slots=True)
class Faixa(Generic[T]):
    """Estimativa em três quantis, monotonicamente ordenados."""

    p10: T
    p50: T
    p90: T

    def __post_init__(self) -> None:
        if not (self.p10 <= self.p50 <= self.p90):  # type: ignore[operator]
            raise ValueError(f"quantis fora de ordem: {self.p10}, {self.p50}, {self.p90}")

    @classmethod
    def certa(cls, valor: T) -> Faixa[T]:
        """Faixa degenerada — use só quando o valor é fato, não estimativa."""
        return cls(valor, valor, valor)

    @property
    def amplitude_relativa(self) -> float | None:
        """(p90 − p10) / p50 — proxy de incerteza. ``None`` quando não é numérico."""
        baixo, meio, alto = (_como_numero(v) for v in (self.p10, self.p50, self.p90))
        if baixo is None or meio is None or alto is None or meio == 0:
            return None
        return (alto - baixo) / meio

    def mapear(self, fn: Callable[[T], object]) -> Faixa[object]:
        """Aplica transformação **monótona crescente** — válida quantil a quantil."""
        return Faixa(fn(self.p10), fn(self.p50), fn(self.p90))

    def mapear_decrescente(self, fn: Callable[[T], object]) -> Faixa[object]:
        """Transformação monótona decrescente: inverte os quantis (p10 vira p90)."""
        return Faixa(fn(self.p90), fn(self.p50), fn(self.p10))

    def __add__(self, outro: object) -> Faixa[T]:
        raise QuantisNaoSomam(
            "quantis não somam; composição de faixas exige simulação (doc 04, § 9)"
        )

    __radd__ = __add__
