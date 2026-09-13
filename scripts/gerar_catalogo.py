#!/usr/bin/env python3
"""Regenera `docs/08-catalogo-de-regras.md` a partir do motor de regras."""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from hasta.report.catalogo import CAMINHO_CATALOGO, gerar_catalogo_markdown  # noqa: E402


def main() -> int:
    destino = RAIZ / CAMINHO_CATALOGO
    destino.write_text(gerar_catalogo_markdown(), encoding="utf-8")
    print(f"gerado: {destino.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
