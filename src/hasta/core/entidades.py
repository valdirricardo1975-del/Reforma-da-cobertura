"""Entidades canônicas (doc 03, § 2).

O ativo durável do sistema (ADR-0001): fontes mudam — inclusive de uma vez, quando a
PNAJ entrar em operação obrigatória — e este modelo permanece.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from hasta.core.cnj import NumeroCNJ
from hasta.core.enums import (
    ClasseAtivo,
    ClasseCredito,
    MaturidadeValuation,
    Modalidade,
    NaturezaProcedimento,
    Ocupacao,
    RegimeTransmissao,
    RotaAcesso,
    StatusPraca,
    TipoAtor,
    TipoOportunidade,
    maturidade,
)
from hasta.core.estados import EstadoOportunidade, EstadoProcedimento
from hasta.core.eventos import EstagioFunil, TipoEvento
from hasta.core.intervalo import Faixa
from hasta.core.money import Money

_CFG = ConfigDict(arbitrary_types_allowed=True, extra="forbid")


class Entidade(BaseModel):
    model_config = _CFG

    id: UUID = Field(default_factory=uuid4)
    #: Evidências que sustentam os campos desta entidade (ADR-0003).
    evidencias: tuple[UUID, ...] = ()


# -- partes e atores --------------------------------------------------------


class Devedor(Entidade):
    cnpj: str | None = None
    cpf_pseudonimo: str | None = Field(
        default=None, description="PF nunca em claro no acervo analítico (doc 06, § 4)"
    )
    razao_social: str
    nomes_anteriores: tuple[str, ...] = ()
    cnae_principal: str | None = None
    uf: str | None = None
    grupo_economico_id: UUID | None = None
    consolidacao_substancial: bool = False

    @model_validator(mode="after")
    def _identificavel(self) -> Devedor:
        if not self.cnpj and not self.cpf_pseudonimo and not self.razao_social:
            raise ValueError("devedor precisa de ao menos um identificador")
        return self


class AtorProcessual(Entidade):
    tipo: TipoAtor
    nome: str
    documento: str | None = Field(default=None, description="CNPJ, OAB ou matrícula de leiloeiro")
    #: Métricas observadas — o grafo de atores é o eixo 5 de diferenciação (doc 00, § 5).
    qualidade_documental: float | None = Field(default=None, ge=0.0, le=1.0)
    tempo_mediano_ate_leilao_dias: int | None = Field(default=None, ge=0)
    taxa_lote_deserto: float | None = Field(default=None, ge=0.0, le=1.0)
    taxa_anulacao: float | None = Field(default=None, ge=0.0, le=1.0)
    frequencia_de_disputa: float | None = Field(default=None, ge=0.0)
    nota_desempenho_cnj: float | None = Field(
        default=None, description="Prov. CN-CNJ 255/2026, avaliação de leiloeiros"
    )
    casos_observados: int = Field(default=0, ge=0)


# -- procedimento -----------------------------------------------------------


class EventoProcessual(Entidade):
    tipo: TipoEvento
    ocorrido_em: date
    detectado_em: datetime
    fonte: str
    codigo_tpu: int | None = None
    resumo: str | None = None

    @property
    def estagio(self) -> EstagioFunil:
        from hasta.core.eventos import meta

        return meta(self.tipo).estagio


class Procedimento(Entidade):
    numero_cnj: str = Field(description="20 dígitos, forma canônica")
    natureza: NaturezaProcedimento
    estado: EstadoProcedimento = EstadoProcedimento.PEDIDO
    tribunal: str
    orgao_julgador: str | None = None
    vara_especializada: bool = False
    segredo_justica: bool = False
    devedor_id: UUID | None = None
    administrador_judicial_id: UUID | None = None
    juizo_id: UUID | None = None
    distribuido_em: date | None = None
    passivo_declarado: Money | None = None
    passivo_habilitado: Money | None = None
    linha_do_tempo: tuple[UUID, ...] = ()

    @model_validator(mode="after")
    def _numero_canonico(self) -> Procedimento:
        numero = NumeroCNJ.parse(self.numero_cnj)
        object.__setattr__(self, "numero_cnj", numero.canonico)
        return self

    @property
    def numero(self) -> NumeroCNJ:
        return NumeroCNJ.parse(self.numero_cnj)

    @property
    def coletavel(self) -> bool:
        """Segredo de justiça é excluído da coleta e do pipeline (doc 05, § 5.4)."""
        return not self.segredo_justica


# -- ativos e ofertas -------------------------------------------------------


class AvaliacaoOficial(Entidade):
    """Laudo dos autos: evidência com qualidade mensurável, não verdade (doc 04, § 1)."""

    valor: Money
    data_base: date
    metodo: str | None = None
    houve_vistoria: bool | None = None
    avaliador: str | None = None
    impugnada: bool = False

    def idade_em_meses(self, quando: date) -> int:
        return (quando.year - self.data_base.year) * 12 + (quando.month - self.data_base.month)


class Onus(BaseModel):
    model_config = _CFG

    tipo: str = Field(description="hipoteca, penhora, arresto, usufruto, indisponibilidade...")
    titular: str | None = None
    valor: Money | None = None
    registrado_na_matricula: bool | None = None


class Ativo(Entidade):
    classe: ClasseAtivo
    descricao: str
    procedimento_id: UUID | None = None
    devedor_id: UUID | None = None
    # identificadores por classe
    matricula: str | None = None
    cns_registro: str | None = None
    inscricao_imobiliaria: str | None = None
    placa: str | None = None
    chassi: str | None = None
    numero_serie: str | None = None
    car_sigef: str | None = None
    registro_inpi: str | None = None
    cnpj_investida: str | None = None
    # atributos
    municipio: str | None = None
    uf: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    area_m2: Decimal | None = None
    ocupacao: Ocupacao = Ocupacao.DESCONHECIDO
    onus: tuple[Onus, ...] = ()
    avaliacoes_oficiais: tuple[AvaliacaoOficial, ...] = ()

    @property
    def maturidade_valuation(self) -> MaturidadeValuation:
        """ADR-0012: a classe determina se o ativo pode receber recomendação."""
        return maturidade(self.classe)


class Praca(Entidade):
    ordem: int = Field(ge=1, le=5)
    data_inicio: datetime
    data_fim: datetime | None = None
    lance_minimo: Money
    percentual_sobre_avaliacao: Decimal | None = None
    incremento: Money | None = None
    status: StatusPraca = StatusPraca.DESIGNADA

    @model_validator(mode="after")
    def _janela_coerente(self) -> Praca:
        if self.data_fim and self.data_fim < self.data_inicio:
            raise ValueError("data_fim anterior a data_inicio")
        return self


class Edital(Entidade):
    documento_id: UUID
    publicado_em: date | None = None
    veiculos_publicacao: tuple[str, ...] = ()
    versao: int = Field(default=1, ge=1)
    retificacoes: int = Field(default=0, ge=0)
    intimacoes_comprovadas: tuple[str, ...] = Field(
        default=(), description="legitimados do art. 889 do CPC cuja intimação foi comprovada"
    )


class Lote(Entidade):
    procedimento_id: UUID
    ativos: tuple[UUID, ...] = Field(min_length=1)
    regime_transmissao: RegimeTransmissao = RegimeTransmissao.INDETERMINADO
    modalidade: Modalidade | None = None
    leiloeiro_id: UUID | None = None
    edital_id: UUID | None = None
    pracas: tuple[Praca, ...] = ()
    comissao_leiloeiro: Decimal | None = Field(default=None, ge=0, le=1)
    parcelamento_admitido: bool | None = None
    clausula_nao_sucessao: str | None = Field(
        default=None, description="texto literal do edital, quando houver"
    )
    onus_declarados_no_edital: tuple[str, ...] = ()
    impedimentos_declarados: tuple[str, ...] = ()

    @property
    def blindagem_declarada(self) -> bool:
        return bool(self.clausula_nao_sucessao) and self.regime_transmissao.concursal


class Credito(Entidade):
    """Insumo das rotas indiretas (doc 04, § 6)."""

    procedimento_id: UUID
    classe: ClasseCredito
    credor_id: UUID | None = None
    valor_habilitado: Money
    impugnado: bool = False
    desagio_observado: Decimal | None = Field(default=None, ge=0, le=1)


# -- análise ----------------------------------------------------------------


class Avaliacao(Entidade):
    """Nosso valor justo — sempre em faixa (ADR-0005)."""

    ativo_id: UUID
    metodo: str
    faixa: Faixa[Money]
    data_base: date
    versao_modelo: str
    maturidade: MaturidadeValuation
    comparaveis: tuple[str, ...] = ()


class Risco(BaseModel):
    model_config = _CFG

    titulo: str
    descricao: str
    severidade: int = Field(ge=1, le=5)
    probabilidade: float | None = Field(default=None, ge=0.0, le=1.0)
    mitigacao: str | None = None
    fonte_do_alerta: str = Field(default="advogado_do_diabo")


class Vicio(BaseModel):
    model_config = _CFG

    item: str = Field(description="item do checklist do Caçador de Vícios (doc 04, § 3)")
    constatado: bool
    fundamento: str | None = None
    evidencia_id: UUID | None = None


class Lacuna(BaseModel):
    model_config = _CFG

    campo: str
    por_que_importa: str
    diligencia_recomendada: str


class Scores(BaseModel):
    """As sete dimensões do doc 01, § 2.3 — cada uma 0–100."""

    model_config = _CFG

    desagio_efetivo: float = Field(ge=0, le=100)
    blindagem_juridica: float = Field(ge=0, le=100)
    seguranca_processual: float = Field(ge=0, le=100)
    liquidez_saida: float = Field(ge=0, le=100)
    custo_posse: float = Field(ge=0, le=100)
    intensidade_competitiva: float = Field(ge=0, le=100)
    alavancagem_relacionamento: float = Field(ge=0, le=100)


class Oportunidade(Entidade):
    lote_id: UUID
    estado: EstadoOportunidade = EstadoOportunidade.DETECTADA
    rota_acesso: RotaAcesso | None = None
    tipo: TipoOportunidade | None = None
    scores: Scores | None = None
    score_composto: float | None = Field(default=None, ge=0, le=100)
    tir_ajustada: Faixa[Decimal] | None = None
    preco_total_estimado: Money | None = None
    teto_de_lance: Money | None = None
    confianca: float | None = Field(default=None, ge=0.0, le=1.0)
    riscos: tuple[Risco, ...] = ()
    vicios: tuple[Vicio, ...] = ()
    lacunas: tuple[Lacuna, ...] = ()
    detectada_em: datetime | None = None
    edital_publicado_em: date | None = None
    motivo_descarte: str | None = None
    motivo_bloqueio: str | None = None

    @property
    def indice_antecipacao_dias(self) -> int | None:
        """KPI-assinatura (doc 02, § 3): dias entre nossa detecção e o edital."""
        if self.detectada_em is None or self.edital_publicado_em is None:
            return None
        return (self.edital_publicado_em - self.detectada_em.date()).days

    @model_validator(mode="after")
    def _terminal_exige_motivo(self) -> Oportunidade:
        if self.estado is EstadoOportunidade.DESCARTADA and not self.motivo_descarte:
            raise ValueError("descarte exige motivo: descartes são dado de treino (doc 03, § 5)")
        if self.estado is EstadoOportunidade.BLOQUEADA_COMPLIANCE and not self.motivo_bloqueio:
            raise ValueError("bloqueio exige motivo visível — filtro silencioso é risco (doc 06)")
        return self


class Resultado(Entidade):
    """Fecha o ciclo de aprendizado L9 (doc 02)."""

    lote_id: UUID
    oportunidade_id: UUID | None = None
    arrematante: str | None = None
    preco_final: Money | None = None
    ocorrido_em: date | None = None
    houve_impugnacao: bool = False
    anulada: bool = False
    nosso_valor_previsto: Money | None = None
    nosso_score_no_momento: float | None = None
