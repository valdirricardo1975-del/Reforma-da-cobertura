"""Valores monetários e correção por índice.

Duas invariantes do domínio (doc 03, § 7):

1. Dinheiro nunca é ``float``. Um centavo perdido em arredondamento binário
   invalida um dossiê que um advogado vai assinar.
2. Valor histórico não se compara a valor presente sem correção **declarada**.
   Comparar R$ de 2019 com R$ de 2026 é o erro silencioso mais comum deste
   domínio: o laudo é antigo, o lance é de hoje, e o deságio aparente mente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol, Self

CENTAVOS_POR_UNIDADE = 100


class MoedaIncompativel(ValueError):
    """Operação entre moedas diferentes."""


class PrecisaoPerdida(TypeError):
    """Tentativa de construir dinheiro a partir de ``float``."""


@dataclass(frozen=True, slots=True, order=True)
class Money:
    """Quantia exata, em centavos."""

    centavos: int
    moeda: str = "BRL"

    def __post_init__(self) -> None:
        if not isinstance(self.centavos, int) or isinstance(self.centavos, bool):
            raise PrecisaoPerdida(f"centavos deve ser int, recebido {type(self.centavos).__name__}")
        if not self.moeda.isalpha() or len(self.moeda) != 3:
            raise ValueError(f"moeda deve ser código ISO de 3 letras, recebido {self.moeda!r}")

    # -- construção ---------------------------------------------------------
    @classmethod
    def de_reais(cls, valor: str | int | Decimal, moeda: str = "BRL") -> Self:
        """Constrói a partir de unidades monetárias. ``float`` é recusado de propósito."""
        if isinstance(valor, float):
            raise PrecisaoPerdida("use str ou Decimal; float não representa dinheiro com exatidão")
        quantia = Decimal(valor) if not isinstance(valor, Decimal) else valor
        centavos = (quantia * CENTAVOS_POR_UNIDADE).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        return cls(int(centavos), moeda)

    @classmethod
    def zero(cls, moeda: str = "BRL") -> Self:
        return cls(0, moeda)

    # -- leitura ------------------------------------------------------------
    @property
    def reais(self) -> Decimal:
        return Decimal(self.centavos) / CENTAVOS_POR_UNIDADE

    def __str__(self) -> str:
        sinal = "-" if self.centavos < 0 else ""
        inteiro, cents = divmod(abs(self.centavos), CENTAVOS_POR_UNIDADE)
        simbolo = "R$" if self.moeda == "BRL" else self.moeda
        return f"{sinal}{simbolo} {inteiro:,.0f}".replace(",", ".") + f",{cents:02d}"

    # -- aritmética ---------------------------------------------------------
    def _mesma_moeda(self, outro: Money) -> None:
        if self.moeda != outro.moeda:
            raise MoedaIncompativel(f"{self.moeda} e {outro.moeda}")

    def __add__(self, outro: Money) -> Money:
        self._mesma_moeda(outro)
        return Money(self.centavos + outro.centavos, self.moeda)

    def __sub__(self, outro: Money) -> Money:
        self._mesma_moeda(outro)
        return Money(self.centavos - outro.centavos, self.moeda)

    def __neg__(self) -> Money:
        return Money(-self.centavos, self.moeda)

    def __mul__(self, fator: int | Decimal | str) -> Money:
        if isinstance(fator, float):
            raise PrecisaoPerdida("multiplique por Decimal ou str, não por float")
        produto = Decimal(self.centavos) * (fator if isinstance(fator, Decimal) else Decimal(fator))
        return Money(int(produto.quantize(Decimal(1), rounding=ROUND_HALF_UP)), self.moeda)

    __rmul__ = __mul__

    def razao(self, outro: Money) -> Decimal:
        """Proporção entre duas quantias (ex.: lance / avaliação)."""
        self._mesma_moeda(outro)
        if outro.centavos == 0:
            raise ZeroDivisionError("divisão por quantia nula")
        return Decimal(self.centavos) / Decimal(outro.centavos)


# -- correção monetária -----------------------------------------------------


class SerieIndice(Protocol):
    """Série de índice capaz de informar o fator de correção entre duas datas."""

    nome: str

    def fator(self, de: date, para: date) -> Decimal: ...


@dataclass(frozen=True, slots=True)
class IndiceEmMemoria:
    """Série declarada ponto a ponto — suficiente para testes e para IPCA/INCC mensais."""

    nome: str
    pontos: dict[date, Decimal]

    def fator(self, de: date, para: date) -> Decimal:
        base = self._ponto(de)
        destino = self._ponto(para)
        return destino / base

    def _ponto(self, quando: date) -> Decimal:
        anteriores = [d for d in self.pontos if d <= quando]
        if not anteriores:
            raise ValueError(f"série {self.nome} não cobre {quando.isoformat()}")
        return self.pontos[max(anteriores)]


@dataclass(frozen=True, slots=True)
class ValorDatado:
    """Quantia com data-base. Só se compara a outra depois de corrigida."""

    quantia: Money
    data_base: date
    indice_aplicado: str | None = None

    def corrigir(self, indice: SerieIndice, para: date) -> ValorDatado:
        if para < self.data_base:
            raise ValueError("correção retroativa exige decisão explícita; use fator inverso")
        fator = indice.fator(self.data_base, para)
        origem = self.indice_aplicado or indice.nome
        return ValorDatado(self.quantia * fator, para, indice_aplicado=origem)

    @property
    def idade_em_meses_ate(self) -> object:
        raise NotImplementedError  # pragma: no cover - use idade_em_meses(quando)

    def idade_em_meses(self, quando: date) -> int:
        return (quando.year - self.data_base.year) * 12 + (quando.month - self.data_base.month)
