from hasta.core.eventos import (
    CATALOGO,
    CODIGOS_TPU_PENDENTES,
    DETECTORES_CRITICOS,
    EstagioFunil,
    TipoEvento,
    eventos_do_estagio,
    mapear_codigo_tpu,
    meta,
)


def test_todo_evento_tem_metadados():
    assert set(CATALOGO) == set(TipoEvento)
    for evento in TipoEvento:
        m = meta(evento)
        assert m.descricao
        assert 0 <= m.lead_min_dias <= m.lead_max_dias


def test_funil_cobre_todos_os_estagios_exceto_o_derivado():
    estagios_usados = {m.estagio for m in CATALOGO.values()}
    assert estagios_usados == set(EstagioFunil)


def test_ordem_do_funil_e_ponto_onde_o_mercado_acorda():
    ordens = [e.ordem for e in EstagioFunil]
    assert ordens == sorted(ordens) == [0, 1, 2, 3, 4, 5]
    acordam = [e for e in EstagioFunil if e.onde_o_mercado_acorda]
    assert acordam == [EstagioFunil.P4_OFERTA_PUBLICA]


def test_antecipacao_decresce_ao_longo_do_funil():
    """Quanto mais avançado o estágio, menor a antecipação possível."""
    por_estagio: dict[EstagioFunil, int] = {}
    for m in CATALOGO.values():
        por_estagio[m.estagio] = max(por_estagio.get(m.estagio, 0), m.lead_max_dias)
    ordenados = [por_estagio[e] for e in EstagioFunil]
    assert ordenados == sorted(ordenados, reverse=True)


def test_codigos_tpu_pendentes_sao_visiveis_e_nao_silenciosos():
    """Spike da Fase 1: enquanto a tabela TPU não for conferida, isto fica evidente."""
    assert CODIGOS_TPU_PENDENTES, "se vazio, os códigos foram preenchidos — remover o marcador"
    assert TipoEvento.PLANO_COM_UPI not in CODIGOS_TPU_PENDENTES  # derivado de leitura
    assert meta(TipoEvento.PLANO_COM_UPI).derivado_de_leitura


def test_mapear_codigo_tpu_sem_tabela_nao_inventa():
    assert mapear_codigo_tpu(12345) is None


def test_detectores_criticos_estao_no_catalogo():
    assert set(CATALOGO) >= DETECTORES_CRITICOS
    assert TipoEvento.EDITAL_PUBLICADO in DETECTORES_CRITICOS


def test_eventos_do_estagio():
    p5 = eventos_do_estagio(EstagioFunil.P5_RESULTADO)
    assert TipoEvento.ARREMATACAO_HOMOLOGADA in p5
    assert TipoEvento.ARREMATACAO_ANULADA in p5
