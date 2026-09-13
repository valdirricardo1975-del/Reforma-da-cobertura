#!/usr/bin/env python3
"""Roda os motores em dois lotes de exemplo e imprime o resultado em português claro.

Serve para mostrar, sem ler código, o que o sistema já faz hoje.
Uso: python scripts/demonstrar.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hasta.core.enums import ClasseAtivo, NaturezaProcedimento, RegimeTransmissao  # noqa: E402
from hasta.core.money import Money  # noqa: E402
from hasta.score import (  # noqa: E402
    ContextoBlindagem,
    ContextoVicios,
    Situacao,
    avaliar_blindagem,
    cacar_vicios,
)

LARGURA = 78


def titulo(texto: str) -> None:
    print()
    print("=" * LARGURA)
    print(texto)
    print("=" * LARGURA)


def ficha(
    nome: str,
    descricao: str,
    blindagem: ContextoBlindagem,
    vicios: ContextoVicios,
) -> None:
    titulo(nome)
    print(descricao)

    b = avaliar_blindagem(blindagem)
    print()
    print(f"BLINDAGEM JURIDICA: {b.grau}/100 — {b.faixa.value}")
    print("Como o sistema chegou nesse numero:")
    for linha in b.explicacao.linhas():
        print(f"   {linha}")
    if b.regime_foi_inferido:
        print("   (o regime nao estava declarado; foi deduzido, e por isso limitado)")
    if b.impedimento_detectado:
        print("   ATENCAO: impedimento legal detectado — vai para bloqueio, nao para o feed")

    v = cacar_vicios(vicios)
    print()
    print(f"RISCO DE DESFAZIMENTO (vicios constatados): {v.indice_risco_nulidade:.1%}")
    print(f"INCERTEZA (parte do checklist nao verificada): {v.indice_incerteza:.1%}")
    print(f"VISAO PESSIMISTA (os dois somados): {v.risco_pessimista:.1%}")

    if v.constatados:
        print()
        print("Vicios encontrados:")
        for c in v.constatados:
            detalhe = f" — {c.detalhe}" if c.detalhe else ""
            print(f"   [{c.item.severidade.name}] {c.item.falha}{detalhe}")

    nao_aplicaveis = [c for c in v.constatacoes if c.situacao is Situacao.NAO_APLICAVEL]
    if nao_aplicaveis:
        print()
        print("Itens que NAO se aplicam a este regime:")
        for c in nao_aplicaveis:
            print(f"   {c.item.id} — {c.item.titulo}")

    if v.notas:
        print()
        print("Notas de regime (consequencias juridicas a registrar no dossie):")
        for nota in v.notas:
            print(f"   {nota.titulo} ({nota.base_legal})")

    pendencias = [*b.lacunas, *v.lacunas]
    if pendencias:
        print()
        print(f"DILIGENCIAS PENDENTES ({len(pendencias)}):")
        for lac in pendencias[:6]:
            print(f"   - {lac.diligencia_recomendada}")
        if len(pendencias) > 6:
            print(f"   ... e outras {len(pendencias) - 6}")

    a_validar = [*b.regras_a_validar, *v.itens_a_validar]
    if a_validar:
        print()
        lista = ", ".join(a_validar)
        print(f"REGRAS AINDA NAO VALIDADAS que influenciaram este resultado: {lista}")


# ---------------------------------------------------------------------------
# Lote 1 — galpao em falencia, tudo conferido
# ---------------------------------------------------------------------------

ficha(
    "LOTE 1 — Galpao industrial em falencia, diligencia completa",
    "Falencia decretada. Edital com clausula expressa de nao sucessao. Matricula\n"
    "conferida em registro. Autorizacao judicial localizada. Checklist todo verificado.",
    ContextoBlindagem(
        regime_declarado=RegimeTransmissao.LFR_141_II_FALENCIA,
        natureza_procedimento=NaturezaProcedimento.FALENCIA,
        classe_ativo_principal=ClasseAtivo.IMOVEL_URBANO,
        clausula_nao_sucessao_no_edital=True,
        decisao_autorizadora_identificada=True,
        cadeia_dominial_verificada=True,
        edital_silente_sobre_condominio=False,
    ),
    ContextoVicios(
        regime=RegimeTransmissao.LFR_141_II_FALENCIA,
        natureza=NaturezaProcedimento.FALENCIA,
        classe_ativo=ClasseAtivo.IMOVEL_URBANO,
        legitimados_art_889_pendentes=(),
        dias_entre_publicacao_e_praca=25,
        laudo_existe=True,
        laudo_idade_meses=8,
        avaliacao_impugnada=False,
        penhora_averbada=True,
        penhoras_concorrentes=1,
        lance_minimo=Money.de_reais("2400000"),
        avaliacao_atualizada=Money.de_reais("8000000"),
        impenhorabilidade_alegada=False,
        previsao_no_plano_ou_autorizacao=True,
        recurso_suspensivo_pendente=False,
        divergencia_descritiva=False,
        edital_retificado_apos_publicidade=False,
    ),
)

# ---------------------------------------------------------------------------
# Lote 2 — mesmo galpao, nada conferido
# ---------------------------------------------------------------------------

ficha(
    "LOTE 2 — O MESMO galpao, antes de qualquer diligencia",
    "Identico ao lote 1 no edital. A unica diferenca: ninguem conferiu nada ainda.",
    ContextoBlindagem(
        regime_declarado=RegimeTransmissao.LFR_141_II_FALENCIA,
        natureza_procedimento=NaturezaProcedimento.FALENCIA,
        classe_ativo_principal=ClasseAtivo.IMOVEL_URBANO,
        clausula_nao_sucessao_no_edital=True,
    ),
    ContextoVicios(
        regime=RegimeTransmissao.LFR_141_II_FALENCIA,
        natureza=NaturezaProcedimento.FALENCIA,
        classe_ativo=ClasseAtivo.IMOVEL_URBANO,
    ),
)

# ---------------------------------------------------------------------------
# Lote 3 — apartamento em execucao comum, com problemas
# ---------------------------------------------------------------------------

ficha(
    "LOTE 3 — Apartamento em execucao comum, com vicios",
    "Execucao de titulo. Sem regime concursal. Credor hipotecario sem intimacao\n"
    "comprovada, publicidade de 3 dias, laudo de 2019, lance minimo em 40% da avaliacao.",
    ContextoBlindagem(
        regime_declarado=RegimeTransmissao.CPC_879_LEILAO,
        natureza_procedimento=NaturezaProcedimento.EXEC_TITULO,
        classe_ativo_principal=ClasseAtivo.IMOVEL_URBANO,
        cadeia_dominial_verificada=True,
        decisao_autorizadora_identificada=True,
        edital_silente_sobre_condominio=True,
    ),
    ContextoVicios(
        regime=RegimeTransmissao.CPC_879_LEILAO,
        natureza=NaturezaProcedimento.EXEC_TITULO,
        classe_ativo=ClasseAtivo.IMOVEL_URBANO,
        legitimados_art_889_pendentes=("credor hipotecario",),
        dias_entre_publicacao_e_praca=3,
        laudo_existe=True,
        laudo_idade_meses=80,
        avaliacao_impugnada=False,
        penhora_averbada=True,
        penhoras_concorrentes=1,
        lance_minimo=Money.de_reais("400000"),
        avaliacao_atualizada=Money.de_reais("1000000"),
        impenhorabilidade_alegada=False,
        recurso_suspensivo_pendente=False,
        divergencia_descritiva=False,
        edital_retificado_apos_publicidade=False,
    ),
)
print()
