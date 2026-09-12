from decimal import Decimal

import pytest

from hasta.core.intervalo import Faixa, QuantisNaoSomam
from hasta.core.money import Money


def test_quantis_precisam_estar_ordenados():
    Faixa(Money(100), Money(200), Money(300))
    with pytest.raises(ValueError, match="fora de ordem"):
        Faixa(Money(300), Money(200), Money(100))


def test_faixa_certa_para_fato_nao_estimativa():
    f = Faixa.certa(Money(500))
    assert f.p10 == f.p50 == f.p90 == Money(500)
    assert f.amplitude_relativa == 0.0


def test_amplitude_relativa_mede_incerteza():
    f = Faixa(Decimal(80), Decimal(100), Decimal(140))
    assert f.amplitude_relativa == pytest.approx(0.6)


def test_soma_de_faixas_e_recusada():
    """Quantis não somam — recusar evita intervalo estreito e falso."""
    a = Faixa(Decimal(1), Decimal(2), Decimal(3))
    with pytest.raises(QuantisNaoSomam):
        a + a
    with pytest.raises(QuantisNaoSomam):
        sum([a, a])


def test_mapear_preserva_ordem_em_transformacao_crescente():
    f = Faixa(Money(100), Money(200), Money(300))
    dobrado = f.mapear(lambda m: m * 2)
    assert (dobrado.p10, dobrado.p90) == (Money(200), Money(600))


def test_mapear_decrescente_inverte_quantis():
    """Deságio é decrescente no valor: p10 do valor gera p90 do deságio."""
    valor = Faixa(Decimal(80), Decimal(100), Decimal(120))
    desagio = valor.mapear_decrescente(lambda v: Decimal(200) - v)
    assert desagio.p10 == Decimal(80)
    assert desagio.p90 == Decimal(120)
