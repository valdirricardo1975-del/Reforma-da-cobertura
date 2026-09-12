import pytest

from hasta.core.cnj import EIXO_ALVO, NumeroCNJ, NumeroCNJMalformado


def digito_de(base_sem_digito: str) -> str:
    """Recalcula o DD pela regra do módulo 97 base 10 para montar casos válidos."""
    seq, ano, seg, trib, orig = (
        base_sem_digito[:7],
        base_sem_digito[7:11],
        base_sem_digito[11],
        base_sem_digito[12:14],
        base_sem_digito[14:18],
    )
    return f"{98 - int(f'{seq}{ano}{seg}{trib}{orig}00') % 97:02d}"


@pytest.mark.parametrize("base", ["1234567202482601000", "0000001201981900010"])
def test_digito_calculado_valida(base: str) -> None:
    corpo = base[:18]
    dd = digito_de(corpo)
    texto = f"{corpo[:7]}-{dd}.{corpo[7:11]}.{corpo[11]}.{corpo[12:14]}.{corpo[14:18]}"
    numero = NumeroCNJ.parse(texto)
    assert numero.digito_valido
    assert numero.digito_esperado == dd


def test_digito_errado_e_sinalizado_nao_rejeitado():
    """Dado real de tribunal tem erro de digitação; descartar custa oportunidade."""
    numero = NumeroCNJ.parse("1234567-99.2024.8.26.0100")
    assert not numero.digito_valido
    assert numero.sigla_tribunal == "TJSP"


def test_aceita_com_e_sem_pontuacao_e_normaliza():
    a = NumeroCNJ.parse("1234567-13.2024.8.26.0100")
    b = NumeroCNJ.parse("12345671320248260100")
    assert a == b
    assert a.canonico == "12345671320248260100"
    assert a.formatado() == "1234567-13.2024.8.26.0100"
    assert len(a.canonico) == 20


@pytest.mark.parametrize("ruim", ["", "123", "abcdefg-13.2024.8.26.0100", "12345671320248260"])
def test_malformado_levanta(ruim: str) -> None:
    with pytest.raises(NumeroCNJMalformado):
        NumeroCNJ.parse(ruim)


def test_segmento_e_eixo_alvo():
    assert NumeroCNJ.parse("1234567-13.2024.8.26.0100").segmento_nome == "Justiça Estadual"
    assert NumeroCNJ.parse("1234567-13.2024.5.02.0100").segmento_nome == "Justiça do Trabalho"
    assert NumeroCNJ.parse("1234567-13.2024.8.26.0100").no_eixo_alvo
    assert not NumeroCNJ.parse("1234567-13.2024.8.05.0100").no_eixo_alvo


def test_eixo_alvo_tem_os_quatro_tribunais_decididos():
    assert set(EIXO_ALVO.values()) == {"TJSP", "TJRJ", "TJMG", "TJPR"}
