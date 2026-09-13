"""Motor 2 — Grau de Blindagem (doc 04, § 2).

A diferença estrutural que nenhum agregador modela: ativo alienado em falência
(art. 141, II, da Lei 11.101/2005) e unidade produtiva isolada em recuperação
judicial (art. 60) transferem-se **sem sucessão do arrematante nas obrigações do
devedor, inclusive tributárias e trabalhistas** — constitucionalidade reconhecida
pelo STF na ADI 3.934. Um leilão de execução comum não oferece isso.

O motor é um catálogo de regras explicáveis. Cada regra tem identificador, base
legal e **status de validação**: ``A_VALIDAR`` marca a premissa que ainda depende de
conferência em fonte primária (doc 07, Fase 1). O resultado informa quais regras
ainda não validadas influenciaram o número — para que ninguém decida sem saber.

Duas escolhas de projeto que evitam otimismo:

* **Teto em vez de desconto** para lacuna de verificação. Sem cadeia dominial
  conferida, o ativo não é "um pouco menos blindado": ele não pode ser classificado
  como blindado.
* **Inferência não vale como evidência.** Regime deduzido da natureza do
  procedimento também impõe teto.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from hasta.core.entidades import Ativo, Lacuna, Lote, Procedimento
from hasta.core.enums import ClasseAtivo, NaturezaProcedimento, RegimeTransmissao
from hasta.score.explicacao import Acumulador, Explicacao, Regra, StatusRegra

# ---------------------------------------------------------------------------
# Catálogo de regras
# ---------------------------------------------------------------------------

_LFR = "Lei 11.101/2005"

CATALOGO_BLINDAGEM: dict[str, Regra] = {
    r.id: r
    for r in (
        # -- bases por regime de transmissão -------------------------------
        Regra(
            "B01",
            "Falência: alienação sem sucessão nas obrigações do devedor",
            f"art. 141, II, da {_LFR}; STF, ADI 3.934",
            StatusRegra.VIGENTE,
        ),
        Regra(
            "B02",
            "UPI em recuperação judicial: alienação livre de ônus e sem sucessão",
            f"art. 60 c/c art. 141, II, da {_LFR}; STF, ADI 3.934",
            StatusRegra.VIGENTE,
        ),
        Regra(
            "B03",
            "Modalidade alternativa de alienação em procedimento concursal",
            f"arts. 144 e 145 da {_LFR}",
            StatusRegra.A_VALIDAR,
            "Conferir se a não sucessão do art. 141 alcança as modalidades alternativas.",
        ),
        Regra("B04", "Leilão judicial comum", "arts. 879 e ss. do CPC", StatusRegra.VIGENTE),
        Regra("B05", "Alienação por iniciativa particular", "art. 880 do CPC", StatusRegra.VIGENTE),
        Regra(
            "B06",
            "Leilão extrajudicial de bem em alienação fiduciária",
            "art. 27 da Lei 9.514/1997",
            StatusRegra.VIGENTE,
        ),
        Regra("B07", "Regime de transmissão indeterminado", "—", StatusRegra.VIGENTE),
        # -- ajustes -------------------------------------------------------
        Regra(
            "B10",
            "Edital traz cláusula expressa de não sucessão em alienação concursal",
            f"art. 141, II, e art. 60 da {_LFR}",
            StatusRegra.VIGENTE,
        ),
        Regra(
            "B11",
            "Cláusula de não sucessão fora de regime concursal tem valor de advertência",
            "art. 141, II, da Lei 11.101/2005 (inaplicável); art. 130 do CTN",
            StatusRegra.VIGENTE,
            "Edital não cria imunidade que a lei não dá: o efeito é probatório, não translativo.",
        ),
        Regra(
            "B12",
            "UPI sem plano homologado juntado",
            f"art. 60 da {_LFR}",
            StatusRegra.VIGENTE,
            "A blindagem da UPI pressupõe alienação prevista em plano aprovado e homologado.",
        ),
        Regra(
            "B13",
            "Alienação concursal sem decisão judicial autorizadora identificada",
            f"arts. 66, 142 e 145 da {_LFR}",
            StatusRegra.VIGENTE,
        ),
        Regra(
            "B14",
            "Cadeia dominial não verificada em registro competente",
            "política interna de diligência",
            StatusRegra.VIGENTE,
        ),
        Regra(
            "B15",
            "Ativo gravado por propriedade de terceiro (fiduciária, arrendamento)",
            f"art. 49, § 3º, da {_LFR}; art. 108 da {_LFR}",
            StatusRegra.A_VALIDAR,
            "Bem de terceiro não integra a massa; o lote pode ser impróprio, não só arriscado.",
        ),
        Regra(
            "B16",
            "Adquirente potencialmente sócio, parente ou agente do devedor",
            f"art. 141, § 1º, da {_LFR}",
            StatusRegra.VIGENTE,
            "Exceção legal à não sucessão e indício de fraude: caso de bloqueio, não de desconto.",
        ),
        Regra(
            "B17",
            "Consolidação substancial com passivo trabalhista relevante",
            f"art. 69-J da {_LFR}; teses de grupo econômico e sucessão trabalhista",
            StatusRegra.A_VALIDAR,
            "Medir a exposição real à tese de sucessão trabalhista na jurisprudência atual.",
        ),
        Regra(
            "B18",
            "Impugnação ou recurso pendente contra o plano ou a decisão autorizadora",
            "art. 1.015 do CPC; art. 59, § 2º, da Lei 11.101/2005",
            StatusRegra.VIGENTE,
        ),
        Regra(
            "B19",
            "Tributos do imóvel sub-rogam-se no preço na arrematação em hasta pública",
            "art. 130, parágrafo único, do CTN",
            StatusRegra.VIGENTE,
        ),
        Regra(
            "B20",
            "Débitos condominiais anteriores com edital silente",
            "natureza propter rem; jurisprudência do STJ",
            StatusRegra.A_VALIDAR,
            "Jurisprudência nuançada entre sub-rogação no preço e responsabilidade do arrematante.",
        ),
        Regra(
            "B21",
            "Edital retificado mais de uma vez",
            "política interna: instabilidade do instrumento",
            StatusRegra.VIGENTE,
        ),
        Regra(
            "B22",
            "Segredo de justiça impede verificação documental",
            "política interna de diligência",
            StatusRegra.VIGENTE,
        ),
        Regra(
            "B23",
            "Regime de transmissão inferido, não declarado",
            "política interna: inferência não é evidência",
            StatusRegra.VIGENTE,
        ),
    )
}

BASE_POR_REGIME: dict[RegimeTransmissao, tuple[str, int]] = {
    RegimeTransmissao.LFR_141_II_FALENCIA: ("B01", 80),
    RegimeTransmissao.LFR_60_UPI: ("B02", 72),
    RegimeTransmissao.LFR_144_145_ALTERNATIVA: ("B03", 55),
    RegimeTransmissao.CPC_879_LEILAO: ("B04", 32),
    RegimeTransmissao.CPC_880_INICIATIVA_PARTICULAR: ("B05", 30),
    RegimeTransmissao.LEI_9514_EXTRAJUDICIAL: ("B06", 25),
    RegimeTransmissao.INDETERMINADO: ("B07", 10),
}

_IMOVEIS = frozenset({ClasseAtivo.IMOVEL_URBANO, ClasseAtivo.IMOVEL_RURAL})

#: Pesos e tetos como **dados**, não como números soltos no motor: é o que permite
#: revisá-los em comitê, versioná-los e gerar a tabela de validação do doc 08 a partir
#: da mesma fonte que o cálculo usa.
PESOS_BLINDAGEM: dict[str, int] = {
    "B10.clausula_concursal": 12,
    "B11.clausula_fora_do_concursal": 2,
    "B12.plano_ausente": -18,
    "B12.plano_nao_verificado": -9,
    "B13.autorizacao_ausente": -12,
    "B13.autorizacao_nao_verificada": -6,
    "B15.bem_de_terceiro": -25,
    "B16.adquirente_ligado_ao_devedor": -60,
    "B17.sucessao_trabalhista": -8,
    "B18.impugnacao_pendente": -10,
    "B19.tributos_sub_rogados": 6,
    "B20.condominio_edital_silente": -5,
    "B21.edital_instavel": -3,
}

TETOS_BLINDAGEM: dict[str, int] = {
    "B12.plano_nao_verificado": 69,
    "B14.cadeia_dominial_nao_verificada": 69,
    "B22.segredo_de_justica": 40,
    "B23.regime_inferido": 69,
}


def _peso(chave: str) -> int:
    return PESOS_BLINDAGEM[chave]


def _teto(chave: str) -> int:
    return TETOS_BLINDAGEM[chave]


@unique
class FaixaBlindagem(StrEnum):
    """Faixas do doc 04, § 2."""

    BLINDADO_FORTE = "BLINDADO_FORTE"
    BLINDADO_COM_RESIDUO = "BLINDADO_COM_RESIDUO"
    PARCIAL = "PARCIAL"
    FRAGIL = "FRAGIL"
    INDETERMINADO = "INDETERMINADO"

    @classmethod
    def de_grau(cls, grau: int) -> FaixaBlindagem:
        if grau >= 90:
            return cls.BLINDADO_FORTE
        if grau >= 70:
            return cls.BLINDADO_COM_RESIDUO
        if grau >= 45:
            return cls.PARCIAL
        if grau >= 20:
            return cls.FRAGIL
        return cls.INDETERMINADO

    @property
    def passa_portao_de_triagem(self) -> bool:
        """Doc 01, § 2.2: regime indeterminado não passa da triagem."""
        return self is not FaixaBlindagem.INDETERMINADO


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------


class ContextoBlindagem(BaseModel):
    """Fatos necessários ao motor — e, por isso, especificação do que o Escriba extrai.

    ``None`` significa **desconhecido**, e desconhecido não é o mesmo que ausente:
    gera lacuna e, quando o fato é decisivo, teto no grau.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    regime_declarado: RegimeTransmissao
    natureza_procedimento: NaturezaProcedimento
    classe_ativo_principal: ClasseAtivo
    clausula_nao_sucessao_no_edital: bool = False
    plano_homologado_juntado: bool | None = None
    decisao_autorizadora_identificada: bool | None = None
    cadeia_dominial_verificada: bool = False
    onus_de_terceiro_detectado: bool = False
    adquirente_pode_ser_socio_parente_agente: bool = False
    consolidacao_substancial: bool = False
    passivo_trabalhista_relevante: bool = False
    impugnacao_pendente: bool = False
    edital_silente_sobre_condominio: bool | None = None
    retificacoes_do_edital: int = Field(default=0, ge=0)
    segredo_justica: bool = False

    @classmethod
    def de_entidades(
        cls,
        lote: Lote,
        procedimento: Procedimento,
        ativos: tuple[Ativo, ...],
        **fatos: object,
    ) -> ContextoBlindagem:
        """Preenche o que as entidades já sabem; o resto vem da extração ou da diligência."""
        if not ativos:
            raise ValueError("lote sem ativos não é avaliável")
        edital_retificacoes = fatos.pop("retificacoes_do_edital", None)
        conhecido: dict[str, object] = {
            "regime_declarado": lote.regime_transmissao,
            "natureza_procedimento": procedimento.natureza,
            "classe_ativo_principal": ativos[0].classe,
            "clausula_nao_sucessao_no_edital": bool(lote.clausula_nao_sucessao),
            "onus_de_terceiro_detectado": any(
                o.tipo.lower().startswith(("alienação fiduciária", "arrendamento"))
                for a in ativos
                for o in a.onus
            ),
            "segredo_justica": procedimento.segredo_justica,
        }
        if edital_retificacoes is not None:
            conhecido["retificacoes_do_edital"] = edital_retificacoes
        return cls(**{**conhecido, **fatos})  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Saída
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResultadoBlindagem:
    grau: int
    faixa: FaixaBlindagem
    regime_efetivo: RegimeTransmissao
    regime_foi_inferido: bool
    explicacao: Explicacao
    lacunas: tuple[Lacuna, ...]
    impedimento_detectado: bool
    evidencias: tuple[UUID, ...] = ()

    @property
    def regras_a_validar(self) -> tuple[str, ...]:
        return self.explicacao.regras_a_validar

    def resumo(self) -> str:
        linhas = " · ".join(self.explicacao.linhas())
        return f"{self.faixa.value} ({self.grau}/100) — {linhas}"


# ---------------------------------------------------------------------------
# Motor
# ---------------------------------------------------------------------------


def _regra(id_: str) -> Regra:
    return CATALOGO_BLINDAGEM[id_]


def _inferir_regime(ctx: ContextoBlindagem) -> tuple[RegimeTransmissao, bool]:
    """Inferência conservadora: só a falência tem regime único e previsível.

    Em recuperação judicial, a venda pode ser UPI do art. 60 ou alienação do art. 66,
    com blindagens diferentes — deduzir seria inventar.
    """
    if ctx.regime_declarado is not RegimeTransmissao.INDETERMINADO:
        return ctx.regime_declarado, False
    if ctx.natureza_procedimento is NaturezaProcedimento.FALENCIA:
        return RegimeTransmissao.LFR_141_II_FALENCIA, True
    return RegimeTransmissao.INDETERMINADO, False


def avaliar_blindagem(ctx: ContextoBlindagem) -> ResultadoBlindagem:
    """Calcula o Grau de Blindagem com a conta aberta."""
    regime, inferido = _inferir_regime(ctx)
    regra_base, base = BASE_POR_REGIME[regime]
    acc = Acumulador(base=base)
    acc.ajustar(_regra(regra_base), 0, f"regime {regime.value}")
    lacunas: list[Lacuna] = []
    impedimento = False

    if inferido:
        acc.limitar(
            _regra("B23"),
            _teto("B23.regime_inferido"),
            "regime deduzido da natureza do procedimento",
        )

    # Cláusula de não sucessão
    if ctx.clausula_nao_sucessao_no_edital:
        if regime.concursal:
            acc.ajustar(_regra("B10"), _peso("B10.clausula_concursal"))
        else:
            acc.ajustar(_regra("B11"), _peso("B11.clausula_fora_do_concursal"))

    # UPI exige plano homologado
    if regime is RegimeTransmissao.LFR_60_UPI:
        if ctx.plano_homologado_juntado is False:
            acc.ajustar(_regra("B12"), _peso("B12.plano_ausente"), "plano homologado ausente")
        elif ctx.plano_homologado_juntado is None:
            acc.ajustar(
                _regra("B12"),
                _peso("B12.plano_nao_verificado"),
                "homologação do plano não verificada",
            )
            acc.limitar(
                _regra("B12"), _teto("B12.plano_nao_verificado"), "UPI sem homologação verificada"
            )
            lacunas.append(
                Lacuna(
                    campo="procedimento.plano_homologado",
                    por_que_importa="A blindagem da UPI pressupõe previsão em plano homologado.",
                    diligencia_recomendada=(
                        "Localizar a decisão de homologação do plano (art. 58) nos autos."
                    ),
                )
            )

    # Autorização judicial da venda
    if regime.concursal:
        if ctx.decisao_autorizadora_identificada is False:
            acc.ajustar(
                _regra("B13"),
                _peso("B13.autorizacao_ausente"),
                "venda sem autorização judicial identificada",
            )
        elif ctx.decisao_autorizadora_identificada is None:
            acc.ajustar(
                _regra("B13"),
                _peso("B13.autorizacao_nao_verificada"),
                "autorização judicial não verificada",
            )
            lacunas.append(
                Lacuna(
                    campo="lote.decisao_autorizadora",
                    por_que_importa="Alienação concursal sem autorização é atacável.",
                    diligencia_recomendada="Identificar a decisão que autorizou a alienação.",
                )
            )

    # Cadeia dominial
    if not ctx.cadeia_dominial_verificada:
        acc.limitar(
            _regra("B14"),
            _teto("B14.cadeia_dominial_nao_verificada"),
            "cadeia dominial não verificada em registro",
        )
        lacunas.append(
            Lacuna(
                campo="ativo.matricula",
                por_que_importa=(
                    "Ônus, indisponibilidade e titularidade só se conferem no registro."
                ),
                diligencia_recomendada="Obter certidão atualizada de matrícula e de ônus.",
            )
        )

    # Bem de terceiro
    if ctx.onus_de_terceiro_detectado:
        acc.ajustar(_regra("B15"), _peso("B15.bem_de_terceiro"), "ativo pode não integrar a massa")

    # Exceção do art. 141, § 1º — bloqueio, não desconto
    if ctx.adquirente_pode_ser_socio_parente_agente:
        acc.ajustar(
            _regra("B16"),
            _peso("B16.adquirente_ligado_ao_devedor"),
            "exceção legal à não sucessão pode incidir",
        )
        impedimento = True

    if ctx.consolidacao_substancial and ctx.passivo_trabalhista_relevante:
        acc.ajustar(
            _regra("B17"),
            _peso("B17.sucessao_trabalhista"),
            "exposição a tese de sucessão trabalhista",
        )

    if ctx.impugnacao_pendente:
        acc.ajustar(_regra("B18"), _peso("B18.impugnacao_pendente"))

    # Tributos do imóvel em hasta pública
    if ctx.classe_ativo_principal in _IMOVEIS and not regime.concursal:
        acc.ajustar(
            _regra("B19"), _peso("B19.tributos_sub_rogados"), "tributos sub-rogam-se no preço"
        )

    # Condomínio
    if ctx.classe_ativo_principal is ClasseAtivo.IMOVEL_URBANO:
        if ctx.edital_silente_sobre_condominio is True:
            acc.ajustar(
                _regra("B20"),
                _peso("B20.condominio_edital_silente"),
                "edital silente sobre débito condominial",
            )
        elif ctx.edital_silente_sobre_condominio is None:
            lacunas.append(
                Lacuna(
                    campo="edital.debitos_condominiais",
                    por_que_importa="Débito condominial pode acompanhar o bem.",
                    diligencia_recomendada=(
                        "Ler o edital e pedir declaração de débitos ao condomínio."
                    ),
                )
            )

    if ctx.retificacoes_do_edital > 1:
        acc.ajustar(
            _regra("B21"),
            _peso("B21.edital_instavel"),
            f"{ctx.retificacoes_do_edital} retificações",
        )

    if ctx.segredo_justica:
        acc.limitar(_regra("B22"), _teto("B22.segredo_de_justica"), "autos sob segredo de justiça")
        lacunas.append(
            Lacuna(
                campo="procedimento.segredo_justica",
                por_que_importa="Sem acesso aos autos não há verificação possível.",
                diligencia_recomendada="Excluir do pipeline até que haja acesso regular.",
            )
        )

    explicacao = acc.fechar()
    return ResultadoBlindagem(
        grau=explicacao.valor,
        faixa=FaixaBlindagem.de_grau(explicacao.valor),
        regime_efetivo=regime,
        regime_foi_inferido=inferido,
        explicacao=explicacao,
        lacunas=tuple(lacunas),
        impedimento_detectado=impedimento,
    )
