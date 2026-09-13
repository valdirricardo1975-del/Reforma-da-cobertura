"""O catálogo do doc 08 é gerado do motor; este teste impede que ele divirja."""

from pathlib import Path

from hasta.core.enums import RegimeTransmissao
from hasta.report.catalogo import CAMINHO_CATALOGO, gerar_catalogo_markdown
from hasta.score.blindagem import (
    BASE_POR_REGIME,
    CATALOGO_BLINDAGEM,
    PESOS_BLINDAGEM,
    TETOS_BLINDAGEM,
)
from hasta.score.explicacao import StatusRegra
from hasta.score.vicios import CHECKLIST_VICIOS

RAIZ = Path(__file__).resolve().parents[2]


def test_documento_esta_sincronizado_com_o_motor():
    """Se falhar: rode `python scripts/gerar_catalogo.py` e revise o diff."""
    destino = RAIZ / CAMINHO_CATALOGO
    assert destino.exists(), "catálogo não gerado"
    assert destino.read_text(encoding="utf-8") == gerar_catalogo_markdown()


def test_todo_regime_tem_base_declarada():
    assert set(BASE_POR_REGIME) == set(RegimeTransmissao)
    for regra_id, base in BASE_POR_REGIME.values():
        assert regra_id in CATALOGO_BLINDAGEM
        assert 0 <= base <= 100


def test_regime_concursal_tem_base_maior_que_execucao_comum():
    """A assimetria que justifica o foco do escritório precisa estar no número."""
    concursais = [base for regime, (_, base) in BASE_POR_REGIME.items() if regime.concursal]
    comuns = [
        base
        for regime, (_, base) in BASE_POR_REGIME.items()
        if not regime.concursal and regime is not RegimeTransmissao.INDETERMINADO
    ]
    assert min(concursais) > max(comuns)


def test_toda_chave_de_peso_e_teto_aponta_para_regra_existente():
    for mapa in (PESOS_BLINDAGEM, TETOS_BLINDAGEM):
        for chave in mapa:
            assert chave.split(".", 1)[0] in CATALOGO_BLINDAGEM, chave
            assert "." in chave, f"{chave} deve ter a forma REGRA.condicao"


def test_tetos_estao_no_intervalo_valido():
    for valor in TETOS_BLINDAGEM.values():
        assert 0 < valor < 100


def test_catalogo_lista_todas_as_pendencias_de_validacao():
    texto = gerar_catalogo_markdown()
    pendentes = [
        r.id
        for r in (*CATALOGO_BLINDAGEM.values(), *CHECKLIST_VICIOS.values())
        if r.status is StatusRegra.A_VALIDAR
    ]
    assert pendentes, "se vazio, todas as premissas foram conferidas — atualizar o teste"
    for regra_id in pendentes:
        assert f"### {regra_id} —" in texto
