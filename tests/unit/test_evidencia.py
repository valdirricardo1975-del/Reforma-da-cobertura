from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from hasta.core.evidencia import (
    PRECEDENCIA_FONTE,
    Documento,
    Evidencia,
    Origem,
    OrigemRestritaError,
    assert_origem_publica,
    origem_mais_restritiva,
    valor_efetivo,
)

AGORA = datetime(2026, 9, 12, 10, 0, tzinfo=UTC)


def doc(fonte: str = "djen") -> Documento:
    return Documento(
        uri_origem=f"https://exemplo.invalid/{fonte}",
        caminho_snapshot=f"raw/2026/09/{fonte}.pdf",
        sha256=Documento.calcular_sha256(fonte.encode()),
        coletado_em=AGORA,
        fonte=fonte,
    )


def ev(origem: Origem = Origem.PUBLICA, *, documento_id=None, confianca=0.9) -> Evidencia:
    return Evidencia(
        documento_id=documento_id or uuid4(),
        campo="lote.lance_minimo",
        valor=600000,
        localizador="p.3, §2",
        trecho="lance mínimo de R$ 600.000,00",
        extrator="parser:edital@1.0",
        confianca=confianca,
        origem=origem,
        coletado_em=AGORA,
    )


def test_hash_de_snapshot_e_validado():
    with pytest.raises(ValueError, match="sha256"):
        Documento(
            uri_origem="x",
            caminho_snapshot="y",
            sha256="curto",
            coletado_em=AGORA,
            fonte="djen",
        )


def test_documento_e_evidencia_sao_imutaveis():
    d = doc()
    with pytest.raises(ValidationError):
        d.fonte = "outro"  # type: ignore[misc]


def test_evidencia_exige_trecho_e_localizador():
    """Sem citação não há procedência — ADR-0003."""
    with pytest.raises(ValueError):
        Evidencia(
            documento_id=uuid4(),
            campo="lote.lance_minimo",
            valor=1,
            localizador="",
            trecho="",
            extrator="llm:escriba",
            confianca=0.5,
            origem=Origem.PUBLICA,
            coletado_em=AGORA,
        )


def test_rotulo_de_origem_e_pegajoso():
    assert origem_mais_restritiva([Origem.PUBLICA, Origem.INTERNA]) is Origem.INTERNA
    assert origem_mais_restritiva([Origem.PUBLICA, Origem.CLIENTE]) is Origem.CLIENTE
    assert origem_mais_restritiva([Origem.RELACIONAMENTO, Origem.INTERNA]) is Origem.RELACIONAMENTO
    assert origem_mais_restritiva([]) is Origem.PUBLICA


def test_so_publica_e_interna_alimentam_investimento():
    assert Origem.PUBLICA.pode_investir
    assert Origem.INTERNA.pode_investir
    assert not Origem.CLIENTE.pode_investir
    assert not Origem.RELACIONAMENTO.pode_investir


def test_portao_bloqueia_informacao_de_cliente():
    publicas = [ev(), ev()]
    assert_origem_publica(publicas)  # não levanta

    com_cliente = [*publicas, ev(Origem.CLIENTE)]
    with pytest.raises(OrigemRestritaError) as exc:
        assert_origem_publica(com_cliente)
    assert exc.value.origem is Origem.CLIENTE
    assert len(exc.value.ofensoras) == 1


def test_portao_bloqueia_informacao_de_relacionamento():
    with pytest.raises(OrigemRestritaError):
        assert_origem_publica([ev(Origem.RELACIONAMENTO)])


def test_precedencia_de_fonte_resolve_conflito_sem_apagar_divergencia():
    d_leiloeiro, d_djen = doc("leiloeiro"), doc("djen")
    e_leiloeiro = ev(documento_id=d_leiloeiro.id, confianca=0.99)
    e_djen = ev(documento_id=d_djen.id, confianca=0.7)
    fontes = {d_leiloeiro.id: "leiloeiro", d_djen.id: "djen"}

    escolhida = valor_efetivo([e_leiloeiro, e_djen], fontes)
    assert escolhida is e_djen, "fonte oficial vence confiança maior de fonte secundária"
    assert PRECEDENCIA_FONTE["djen"] > PRECEDENCIA_FONTE["leiloeiro"]


def test_pnaj_tem_a_maior_precedencia():
    """Prov. CN-CNJ 255/2026: quando a PNAJ existir, ela é a fonte de referência."""
    assert PRECEDENCIA_FONTE["pnaj"] == max(PRECEDENCIA_FONTE.values())


def test_valor_efetivo_sem_candidatos():
    assert valor_efetivo([], {}) is None


def test_conflito_e_registrado_na_evidencia():
    a = ev()
    b = Evidencia(**{**a.model_dump(exclude={"id", "conflita_com"}), "conflita_com": (a.id,)})
    assert a.id in b.conflita_com
