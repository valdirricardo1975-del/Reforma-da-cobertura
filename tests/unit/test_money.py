from datetime import date
from decimal import Decimal

import pytest

from hasta.core.money import (
    IndiceEmMemoria,
    MoedaIncompativel,
    Money,
    PrecisaoPerdida,
    ValorDatado,
)


def test_float_e_recusado_em_toda_a_api():
    with pytest.raises(PrecisaoPerdida):
        Money.de_reais(1234.56)
    with pytest.raises(PrecisaoPerdida):
        Money(100.0)  # type: ignore[arg-type]
    with pytest.raises(PrecisaoPerdida):
        Money(100) * 1.5


def test_construcao_e_arredondamento_meio_para_cima():
    assert Money.de_reais("10").centavos == 1000
    assert Money.de_reais("0.125").centavos == 13
    assert Money.de_reais(Decimal("-50.5")).centavos == -5050
    assert Money.de_reais("1000000").reais == Decimal(1000000)


def test_formatacao_brasileira():
    assert str(Money.de_reais("1234567.89")) == "R$ 1.234.567,89"
    assert str(Money.de_reais("-50.5")) == "-R$ 50,50"
    assert str(Money.zero()) == "R$ 0,00"


def test_aritmetica_e_moeda():
    assert Money(100) + Money(250) == Money(350)
    assert Money(100) - Money(250) == Money(-150)
    assert Money(1000) * Decimal("0.05") == Money(50)
    assert -Money(100) == Money(-100)
    with pytest.raises(MoedaIncompativel):
        Money(100, "BRL") + Money(100, "USD")


def test_razao_serve_para_desagio():
    lance = Money.de_reais("600000")
    avaliacao = Money.de_reais("1000000")
    assert lance.razao(avaliacao) == Decimal("0.6")
    with pytest.raises(ZeroDivisionError):
        lance.razao(Money.zero())


def test_ordenacao():
    assert sorted([Money(300), Money(100), Money(200)]) == [Money(100), Money(200), Money(300)]


@pytest.fixture
def ipca() -> IndiceEmMemoria:
    return IndiceEmMemoria(
        nome="IPCA",
        pontos={
            date(2019, 1, 1): Decimal("100"),
            date(2022, 1, 1): Decimal("130"),
            date(2026, 1, 1): Decimal("160"),
        },
    )


def test_laudo_antigo_corrigido_muda_o_desagio(ipca: IndiceEmMemoria):
    """O caso que o mercado erra: laudo de 2019 comparado a lance de 2026."""
    laudo = ValorDatado(Money.de_reais("1000000"), date(2019, 6, 1))
    lance = Money.de_reais("600000")

    desagio_ingenuo = 1 - lance.razao(laudo.quantia)
    corrigido = laudo.corrigir(ipca, date(2026, 6, 1))
    desagio_real = 1 - lance.razao(corrigido.quantia)

    assert desagio_ingenuo == Decimal("0.4")
    assert desagio_real > desagio_ingenuo
    assert corrigido.indice_aplicado == "IPCA"
    assert corrigido.data_base == date(2026, 6, 1)


def test_correcao_retroativa_exige_decisao_explicita(ipca: IndiceEmMemoria):
    valor = ValorDatado(Money.de_reais("100"), date(2026, 1, 1))
    with pytest.raises(ValueError, match="retroativa"):
        valor.corrigir(ipca, date(2019, 1, 1))


def test_serie_sem_cobertura_falha_alto(ipca: IndiceEmMemoria):
    valor = ValorDatado(Money.de_reais("100"), date(2010, 1, 1))
    with pytest.raises(ValueError, match="não cobre"):
        valor.corrigir(ipca, date(2026, 1, 1))


def test_idade_em_meses():
    valor = ValorDatado(Money.de_reais("100"), date(2024, 3, 1))
    assert valor.idade_em_meses(date(2026, 9, 1)) == 30
