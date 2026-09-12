"""Número único de processo (Resolução CNJ 65/2008).

Formato ``NNNNNNN-DD.AAAA.J.TR.OOOO``. O dígito verificador usa Módulo 97
Base 10 (ISO 7064) sobre ``NNNNNNN + AAAA + J + TR + OOOO + "00"``.

Postura de projeto: número malformado levanta erro; dígito inconsistente é
**sinalizado, não rejeitado**. Dado real de tribunal contém erro de digitação, e
descartar silenciosamente um processo por causa disso custa uma oportunidade.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PADRAO = re.compile(r"^(\d{7})-?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})$")

SEGMENTOS: dict[str, str] = {
    "1": "Supremo Tribunal Federal",
    "2": "Conselho Nacional de Justiça",
    "3": "Superior Tribunal de Justiça",
    "4": "Justiça Federal",
    "5": "Justiça do Trabalho",
    "6": "Justiça Eleitoral",
    "7": "Justiça Militar da União",
    "8": "Justiça Estadual",
    "9": "Justiça Militar Estadual",
}

# Eixo-alvo da Fase 1 (ADR-0013).
EIXO_ALVO: dict[tuple[str, str], str] = {
    ("8", "26"): "TJSP",
    ("8", "19"): "TJRJ",
    ("8", "13"): "TJMG",
    ("8", "16"): "TJPR",
}


class NumeroCNJMalformado(ValueError):
    """String não corresponde ao formato do número único."""


@dataclass(frozen=True, slots=True)
class NumeroCNJ:
    sequencial: str
    digito: str
    ano: str
    segmento: str
    tribunal: str
    origem: str

    @classmethod
    def parse(cls, texto: str) -> NumeroCNJ:
        limpo = re.sub(r"\s", "", texto)
        casado = PADRAO.match(limpo)
        if not casado:
            raise NumeroCNJMalformado(f"não é número único CNJ: {texto!r}")
        return cls(*casado.groups())

    # -- dígito verificador -------------------------------------------------
    @property
    def digito_esperado(self) -> str:
        base = f"{self.sequencial}{self.ano}{self.segmento}{self.tribunal}{self.origem}00"
        return f"{98 - int(base) % 97:02d}"

    @property
    def digito_valido(self) -> bool:
        return self.digito == self.digito_esperado

    # -- leitura ------------------------------------------------------------
    @property
    def segmento_nome(self) -> str:
        return SEGMENTOS.get(self.segmento, "segmento desconhecido")

    @property
    def sigla_tribunal(self) -> str | None:
        return EIXO_ALVO.get((self.segmento, self.tribunal))

    @property
    def no_eixo_alvo(self) -> bool:
        return (self.segmento, self.tribunal) in EIXO_ALVO

    def formatado(self) -> str:
        return (
            f"{self.sequencial}-{self.digito}.{self.ano}."
            f"{self.segmento}.{self.tribunal}.{self.origem}"
        )

    @property
    def canonico(self) -> str:
        """20 dígitos sem pontuação — chave natural do ``Procedimento``."""
        return (
            f"{self.sequencial}{self.digito}{self.ano}{self.segmento}{self.tribunal}{self.origem}"
        )

    def __str__(self) -> str:
        return self.formatado()
