"""Caçador de Vícios — checklist executável de nulidades (doc 04, § 3).

Princípio: **item ausente não vira nota baixa silenciosa**. Se o fato não foi
verificado, a situação é ``INDETERMINADO``, gera ``Lacuna`` com a diligência
recomendada e entra no risco com peso reduzido. O contrário — tratar não verificado
como afastado — é como o mercado produz surpresa em imissão na posse.

Dois números, não um: **risco detectado** (vícios efetivamente constatados) e
**incerteza de verificação** (itens que ninguém checou). Somá-los num único índice
esconde justamente a informação que decide o próximo passo — se o problema é o ativo
ou a nossa diligência. O ``risco_pessimista`` combina os dois e serve de margem de
segurança no ranking.

Os pesos desta versão são **priors declarados, não medidos**: servem para ordenar
diligência, não para decidir capital. A calibração contra casos reais de anulação é
entrega da Fase 3 (doc 04, § 9, e doc 07).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import IntEnum, StrEnum, unique

from pydantic import BaseModel, ConfigDict, Field

from hasta.core.entidades import Lacuna
from hasta.core.enums import ClasseAtivo, NaturezaProcedimento, RegimeTransmissao
from hasta.core.money import Money
from hasta.score.explicacao import Regra, StatusRegra


@unique
class Severidade(IntEnum):
    BAIXA = 1
    MODERADA = 2
    RELEVANTE = 3
    GRAVE = 4
    FATAL = 5


#: Probabilidade de desfazimento atribuída a cada severidade quando o vício é
#: constatado. Valores declarados por julgamento, a serem substituídos por medição.
PRIOR_NULIDADE_POR_SEVERIDADE: dict[Severidade, Decimal] = {
    Severidade.BAIXA: Decimal("0.02"),
    Severidade.MODERADA: Decimal("0.05"),
    Severidade.RELEVANTE: Decimal("0.12"),
    Severidade.GRAVE: Decimal("0.25"),
    Severidade.FATAL: Decimal("0.50"),
}

#: Peso de um item apenas suspeito (não verificado) em relação ao constatado.
PESO_INDETERMINADO = Decimal("0.4")


@unique
class Situacao(StrEnum):
    CONSTATADO = "CONSTATADO"
    AFASTADO = "AFASTADO"
    INDETERMINADO = "INDETERMINADO"
    NAO_APLICAVEL = "NAO_APLICAVEL"


@unique
class Escopo(StrEnum):
    """Onde o item se aplica — o regime muda o que é vício."""

    QUALQUER = "QUALQUER"
    CONCURSAL = "CONCURSAL"
    EXECUCAO_CPC = "EXECUCAO_CPC"
    IMOVEL = "IMOVEL"


@dataclass(frozen=True, slots=True)
class ItemVicio:
    id: str
    titulo: str
    base_legal: str
    severidade: Severidade
    #: Como o defeito se chama quando constatado. O ``titulo`` descreve o estado
    #: desejado (é um checklist); o dossiê precisa nomear a falha, não a checagem.
    falha: str = ""
    escopo: Escopo = Escopo.QUALQUER
    status: StatusRegra = StatusRegra.VIGENTE
    observacao: str | None = None
    diligencia: str = "Conferir nos autos."
    por_que_importa: str = "Pode levar à invalidação ou ineficácia da arrematação."

    def rotulo(self, constatado: bool) -> str:
        return self.falha if constatado and self.falha else self.titulo


_CPC = "CPC"
_LFR = "Lei 11.101/2005"

CHECKLIST_VICIOS: dict[str, ItemVicio] = {
    i.id: i
    for i in (
        ItemVicio(
            "V01",
            "Intimação de todos os legitimados antes do leilão",
            f"art. 889 do {_CPC}",
            Severidade.GRAVE,
            falha="Legitimados do art. 889 sem comprovação de intimação",
            status=StatusRegra.A_VALIDAR,
            observacao="Conferir a lista de incisos vigente antes de tratar como regra fechada.",
            diligencia="Verificar comprovação de intimação de cada legitimado do art. 889.",
            por_que_importa="Falta de intimação é a causa mais comum de invalidação.",
        ),
        ItemVicio(
            "V02",
            "Prazo mínimo de publicidade entre publicação do edital e a praça",
            f"art. 887 do {_CPC}",
            Severidade.GRAVE,
            falha="Publicidade do edital abaixo do prazo mínimo adotado",
            status=StatusRegra.A_VALIDAR,
            observacao="Confirmar o prazo legal vigente; o padrão do sistema é configurável.",
            diligencia="Comparar data de publicação com a data designada para a praça.",
        ),
        ItemVicio(
            "V03",
            "Laudo de avaliação juntado aos autos",
            f"arts. 870 e 872 do {_CPC}",
            Severidade.RELEVANTE,
            falha="Laudo de avaliação não localizado nos autos",
            diligencia="Localizar o laudo ou o auto de avaliação.",
        ),
        ItemVicio(
            "V04",
            "Avaliação atual",
            "política interna; art. 873 do CPC (nova avaliação)",
            Severidade.MODERADA,
            falha="Laudo de avaliação defasado",
            diligencia="Verificar a data-base do laudo e pedir reavaliação se defasado.",
            por_que_importa="Laudo defasado distorce deságio e alimenta impugnação.",
        ),
        ItemVicio(
            "V05",
            "Impugnação pendente à avaliação",
            f"art. 873 do {_CPC}",
            Severidade.RELEVANTE,
            falha="Impugnação à avaliação pendente",
            diligencia="Conferir se há incidente de impugnação da avaliação em curso.",
        ),
        ItemVicio(
            "V06",
            "Penhora averbada na matrícula",
            f"art. 844 do {_CPC}",
            Severidade.MODERADA,
            falha="Penhora não averbada na matrícula",
            escopo=Escopo.IMOVEL,
            diligencia="Conferir averbação da penhora na certidão de matrícula.",
            por_que_importa="Sem averbação, terceiro adquirente de boa-fé pode ser oposto.",
        ),
        ItemVicio(
            "V07",
            "Concorrência de penhoras e ordem de preferência resolvida",
            f"arts. 797 e 908 do {_CPC}",
            Severidade.MODERADA,
            falha="Penhoras concorrentes sem ordem de preferência resolvida",
            diligencia="Mapear penhoras concorrentes e a ordem de preferência.",
        ),
        ItemVicio(
            "V08",
            "Lance mínimo acima do patamar de preço vil",
            f"art. 891 do {_CPC}",
            Severidade.GRAVE,
            falha="Lance mínimo em patamar de preço vil",
            escopo=Escopo.EXECUCAO_CPC,
            diligencia="Comparar o lance mínimo com 50% da avaliação atualizada.",
            por_que_importa="Arrematação por preço vil é anulável.",
        ),
        ItemVicio(
            "V09",
            "Ausência de alegação de impenhorabilidade ou bem de família",
            f"art. 833 do {_CPC}; Lei 8.009/1990",
            Severidade.GRAVE,
            falha="Impenhorabilidade ou bem de família alegado",
            diligencia="Verificar se há alegação pendente de impenhorabilidade.",
        ),
        ItemVicio(
            "V10",
            "Alienação concursal com previsão no plano ou autorização judicial",
            f"arts. 66, 142 e 145 da {_LFR}",
            Severidade.GRAVE,
            falha="Alienação concursal sem previsão no plano nem autorização judicial",
            escopo=Escopo.CONCURSAL,
            diligencia="Localizar a previsão no plano ou a decisão que autorizou a venda.",
        ),
        ItemVicio(
            "V11",
            "Ausência de recurso com efeito suspensivo sobre a alienação",
            f"arts. 995 e 1.019 do {_CPC}",
            Severidade.GRAVE,
            falha="Recurso com efeito suspensivo pendente sobre a alienação",
            diligencia="Consultar segunda instância por agravo com efeito suspensivo.",
            por_que_importa="Suspensão derruba a praça e consome o custo de preparação.",
        ),
        ItemVicio(
            "V12",
            "Descrição do bem coerente entre edital, laudo e matrícula",
            "política interna de conferência documental",
            Severidade.RELEVANTE,
            falha="Descrição do bem divergente entre edital, laudo e matrícula",
            diligencia="Confrontar área, confrontações e benfeitorias nos três documentos.",
            por_que_importa="Divergência descritiva gera litígio sobre o objeto arrematado.",
        ),
        ItemVicio(
            "V13",
            "Autos acessíveis para verificação",
            "política interna de diligência",
            Severidade.MODERADA,
            falha="Autos sob segredo de justiça: verificação impossível",
            diligencia="Avaliar se há acesso regular aos autos.",
        ),
        ItemVicio(
            "V14",
            "Edital estável após o início da publicidade",
            f"art. 886 do {_CPC}",
            Severidade.MODERADA,
            falha="Edital retificado após o início da publicidade",
            diligencia="Verificar retificações posteriores à primeira publicação.",
        ),
    )
}

NOTAS_DE_REGIME: dict[str, Regra] = {
    r.id: r
    for r in (
        Regra(
            "N01",
            "Na falência não incide a vedação do preço vil: aliena-se pelo maior valor ofertado",
            f"art. 142, § 2º, da {_LFR}",
            StatusRegra.A_VALIDAR,
            "Conferir a redação vigente. Se confirmada, é a assimetria central do nicho: "
            "o piso de preço do art. 891 do CPC não se aplica.",
        ),
        Regra(
            "N02",
            "Tributos do imóvel sub-rogam-se no preço da arrematação em hasta pública",
            "art. 130, parágrafo único, do CTN",
            StatusRegra.VIGENTE,
        ),
        Regra(
            "N03",
            "Aquisição em processo de falência ou de recuperação não gera sucessão tributária",
            "art. 133, § 1º, do CTN",
            StatusRegra.VIGENTE,
        ),
    )
}


class ContextoVicios(BaseModel):
    """Fatos do checklist. ``None`` é desconhecido — e desconhecido gera lacuna."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    regime: RegimeTransmissao
    natureza: NaturezaProcedimento
    classe_ativo: ClasseAtivo

    legitimados_art_889_pendentes: tuple[str, ...] | None = None
    dias_entre_publicacao_e_praca: int | None = None
    laudo_existe: bool | None = None
    laudo_idade_meses: int | None = None
    avaliacao_impugnada: bool | None = None
    penhora_averbada: bool | None = None
    penhoras_concorrentes: int | None = None
    lance_minimo: Money | None = None
    avaliacao_atualizada: Money | None = None
    impenhorabilidade_alegada: bool | None = None
    previsao_no_plano_ou_autorizacao: bool | None = None
    recurso_suspensivo_pendente: bool | None = None
    divergencia_descritiva: bool | None = None
    segredo_justica: bool = False
    edital_retificado_apos_publicidade: bool | None = None

    # Parâmetros de política, explícitos para poderem ser revisados sem mexer no motor.
    dias_minimos_publicidade: int = Field(default=5, ge=0)
    meses_maximos_laudo: int = Field(default=24, ge=1)
    fracao_preco_vil: Decimal = Field(default=Decimal("0.5"), gt=0, le=1)


@dataclass(frozen=True, slots=True)
class Constatacao:
    item: ItemVicio
    situacao: Situacao
    detalhe: str | None = None

    @property
    def peso(self) -> Decimal:
        if self.situacao is Situacao.CONSTATADO:
            return PRIOR_NULIDADE_POR_SEVERIDADE[self.item.severidade]
        if self.situacao is Situacao.INDETERMINADO:
            return PRIOR_NULIDADE_POR_SEVERIDADE[self.item.severidade] * PESO_INDETERMINADO
        return Decimal(0)

    def __str__(self) -> str:
        detalhe = f" — {self.detalhe}" if self.detalhe else ""
        rotulo = self.item.rotulo(self.situacao is Situacao.CONSTATADO)
        return f"{self.item.id} {self.situacao.value}: {rotulo}{detalhe}"


@dataclass(frozen=True, slots=True)
class ResultadoVicios:
    constatacoes: tuple[Constatacao, ...]
    notas: tuple[Regra, ...]
    lacunas: tuple[Lacuna, ...]
    #: Risco de desfazimento atribuível a vícios efetivamente constatados.
    indice_risco_nulidade: Decimal
    #: Quanto do checklist permanece não verificado — é diligência, não defeito.
    indice_incerteza: Decimal

    @property
    def constatados(self) -> tuple[Constatacao, ...]:
        return tuple(c for c in self.constatacoes if c.situacao is Situacao.CONSTATADO)

    @property
    def indeterminados(self) -> tuple[Constatacao, ...]:
        return tuple(c for c in self.constatacoes if c.situacao is Situacao.INDETERMINADO)

    @property
    def itens_a_validar(self) -> tuple[str, ...]:
        return tuple(
            c.item.id
            for c in self.constatacoes
            if c.item.status is StatusRegra.A_VALIDAR and c.situacao is not Situacao.NAO_APLICAVEL
        )

    @property
    def severidade_maxima_constatada(self) -> Severidade | None:
        constatados = self.constatados
        return max((c.item.severidade for c in constatados), default=None)

    @property
    def risco_pessimista(self) -> Decimal:
        """Vícios constatados **e** o que ainda pode aparecer — margem de segurança."""
        sobrevivencia = (Decimal(1) - self.indice_risco_nulidade) * (
            Decimal(1) - self.indice_incerteza
        )
        return (Decimal(1) - sobrevivencia).quantize(Decimal("0.0001"))

    @property
    def checklist_completo(self) -> bool:
        return not self.indeterminados


def _aplicavel(item: ItemVicio, ctx: ContextoVicios) -> bool:
    if item.escopo is Escopo.QUALQUER:
        return True
    if item.escopo is Escopo.CONCURSAL:
        return ctx.regime.concursal or ctx.natureza.concursal
    if item.escopo is Escopo.EXECUCAO_CPC:
        return not ctx.regime.concursal and not ctx.natureza.concursal
    return ctx.classe_ativo in {ClasseAtivo.IMOVEL_URBANO, ClasseAtivo.IMOVEL_RURAL}


def _de_bool(esperado_ausente: bool | None) -> Situacao:
    """Fato booleano em que ``True`` significa problema presente."""
    if esperado_ausente is None:
        return Situacao.INDETERMINADO
    return Situacao.CONSTATADO if esperado_ausente else Situacao.AFASTADO


def _avaliar(item: ItemVicio, ctx: ContextoVicios) -> Constatacao:  # noqa: C901
    if not _aplicavel(item, ctx):
        return Constatacao(item, Situacao.NAO_APLICAVEL)

    match item.id:
        case "V01":
            pendentes = ctx.legitimados_art_889_pendentes
            if pendentes is None:
                return Constatacao(item, Situacao.INDETERMINADO)
            if pendentes:
                return Constatacao(
                    item, Situacao.CONSTATADO, f"sem comprovação: {', '.join(pendentes)}"
                )
            return Constatacao(item, Situacao.AFASTADO)
        case "V02":
            dias = ctx.dias_entre_publicacao_e_praca
            if dias is None:
                return Constatacao(item, Situacao.INDETERMINADO)
            if dias < ctx.dias_minimos_publicidade:
                return Constatacao(
                    item,
                    Situacao.CONSTATADO,
                    f"{dias} dias, mínimo adotado {ctx.dias_minimos_publicidade}",
                )
            return Constatacao(item, Situacao.AFASTADO, f"{dias} dias")
        case "V03":
            if ctx.laudo_existe is None:
                return Constatacao(item, Situacao.INDETERMINADO)
            return Constatacao(item, Situacao.AFASTADO if ctx.laudo_existe else Situacao.CONSTATADO)
        case "V04":
            idade = ctx.laudo_idade_meses
            if idade is None:
                return Constatacao(item, Situacao.INDETERMINADO)
            if idade > ctx.meses_maximos_laudo:
                return Constatacao(item, Situacao.CONSTATADO, f"laudo com {idade} meses")
            return Constatacao(item, Situacao.AFASTADO, f"laudo com {idade} meses")
        case "V05":
            return Constatacao(item, _de_bool(ctx.avaliacao_impugnada))
        case "V06":
            if ctx.penhora_averbada is None:
                return Constatacao(item, Situacao.INDETERMINADO)
            return Constatacao(
                item, Situacao.AFASTADO if ctx.penhora_averbada else Situacao.CONSTATADO
            )
        case "V07":
            n = ctx.penhoras_concorrentes
            if n is None:
                return Constatacao(item, Situacao.INDETERMINADO)
            if n > 1:
                return Constatacao(item, Situacao.CONSTATADO, f"{n} penhoras")
            return Constatacao(item, Situacao.AFASTADO)
        case "V08":
            if ctx.lance_minimo is None or ctx.avaliacao_atualizada is None:
                return Constatacao(item, Situacao.INDETERMINADO)
            razao = ctx.lance_minimo.razao(ctx.avaliacao_atualizada)
            if razao < ctx.fracao_preco_vil:
                return Constatacao(
                    item, Situacao.CONSTATADO, f"lance mínimo em {razao:.0%} da avaliação"
                )
            return Constatacao(item, Situacao.AFASTADO, f"lance mínimo em {razao:.0%}")
        case "V09":
            return Constatacao(item, _de_bool(ctx.impenhorabilidade_alegada))
        case "V10":
            previsao = ctx.previsao_no_plano_ou_autorizacao
            if previsao is None:
                return Constatacao(item, Situacao.INDETERMINADO)
            return Constatacao(item, Situacao.AFASTADO if previsao else Situacao.CONSTATADO)
        case "V11":
            return Constatacao(item, _de_bool(ctx.recurso_suspensivo_pendente))
        case "V12":
            return Constatacao(item, _de_bool(ctx.divergencia_descritiva))
        case "V13":
            return Constatacao(
                item, Situacao.CONSTATADO if ctx.segredo_justica else Situacao.AFASTADO
            )
        case "V14":
            return Constatacao(item, _de_bool(ctx.edital_retificado_apos_publicidade))
        case _:  # pragma: no cover - catálogo e motor evoluem juntos
            raise NotImplementedError(f"item {item.id} sem avaliador")


def _notas(ctx: ContextoVicios) -> tuple[Regra, ...]:
    notas: list[Regra] = []
    if ctx.regime is RegimeTransmissao.LFR_141_II_FALENCIA or (
        ctx.natureza is NaturezaProcedimento.FALENCIA
    ):
        notas.append(NOTAS_DE_REGIME["N01"])
        notas.append(NOTAS_DE_REGIME["N03"])
    if ctx.classe_ativo in {ClasseAtivo.IMOVEL_URBANO, ClasseAtivo.IMOVEL_RURAL}:
        notas.append(NOTAS_DE_REGIME["N02"])
    return tuple(dict.fromkeys(notas))


def _agregar(constatacoes: tuple[Constatacao, ...], situacao: Situacao) -> Decimal:
    """Agregação por independência aproximada — prior, não medição."""
    sobrevivencia = Decimal(1)
    for c in constatacoes:
        if c.situacao is situacao:
            sobrevivencia *= Decimal(1) - c.peso
    return (Decimal(1) - sobrevivencia).quantize(Decimal("0.0001"))


def cacar_vicios(ctx: ContextoVicios) -> ResultadoVicios:
    """Roda o checklist inteiro e devolve constatações, notas, lacunas e risco."""
    constatacoes = tuple(_avaliar(item, ctx) for item in CHECKLIST_VICIOS.values())
    lacunas = tuple(
        Lacuna(
            campo=f"vicio.{c.item.id}",
            por_que_importa=c.item.por_que_importa,
            diligencia_recomendada=c.item.diligencia,
        )
        for c in constatacoes
        if c.situacao is Situacao.INDETERMINADO
    )
    return ResultadoVicios(
        constatacoes=constatacoes,
        notas=_notas(ctx),
        lacunas=lacunas,
        indice_risco_nulidade=_agregar(constatacoes, Situacao.CONSTATADO),
        indice_incerteza=_agregar(constatacoes, Situacao.INDETERMINADO),
    )
