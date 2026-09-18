"""Motor de retorno: preço total, custo de carregamento, TIR e teto de lance.

Este é o motor que converte uma avaliação em **decisão**. Ele existe porque a
estrutura de capital aprovada em 18/09/2026 (ADR-0016) tornou o custo de capital
observável: há funding contratado a CDI, com preferência nas retiradas.

Três consequências que o cálculo leva a sério:

* **Deságio não é retorno.** Entre o lance e o recebimento da venda há comissão,
  ITBI, registro, custas, débitos que seguem o bem, desocupação, regularização,
  corretagem e tributo sobre o ganho. O que sobra é o retorno.
* **Tempo custa dinheiro.** Ativo judicial leva de 12 a 36 meses para virar caixa, e
  nesse intervalo o funding corre ao CDI enquanto o imóvel não gera nada. Um deságio de
  40% pode virar retorno nulo por decurso de prazo — é o erro mais caro que este
  sistema poderia cometer, e por isso o carrego é termo obrigatório, não opcional.
* **O equity é residual e tardio.** Com preferência nas retiradas, o caixa paga
  primeiro o financiador. A TIR que interessa aos sócios é a que sobra depois disso.

**Cenários, não aritmética de quantis.** A faixa p10/p50/p90 é construída rodando o
cálculo inteiro em três cenários internamente coerentes (valor baixo *com* prazo longo
*com* custo alto), e não somando quantis de termos isolados — quantis não somam
(ver `intervalo.py`). O ranking usa o p10, e o **teto de lance é definido pelo cenário
pessimista**: o preço máximo é o que ainda supera o custo de capital quando dá errado.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum, unique

from pydantic import BaseModel, ConfigDict, Field, model_validator

from hasta.core.intervalo import Faixa
from hasta.core.money import Money

_CFG = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

MESES_POR_ANO = Decimal(12)


def _potencia(base: Decimal, expoente: Decimal) -> Decimal:
    """``base ** expoente`` com expoente fracionário, sem passar por ``float``."""
    if base <= 0:
        raise ValueError("potência exige base positiva")
    if expoente == 0:
        return Decimal(1)
    try:
        return (base.ln() * expoente).exp()
    except (InvalidOperation, OverflowError) as erro:  # pragma: no cover - guarda
        raise ValueError(f"potência fora de faixa: {base} ** {expoente}") from erro


# ---------------------------------------------------------------------------
# Parâmetros
# ---------------------------------------------------------------------------


class Custos(BaseModel):
    """Custos de transação, como percentuais de política revisáveis em comitê.

    Os padrões são praxe de mercado e **precisam de confirmação** antes de decidir
    capital: a base do ITBI varia por município (com frequência é o maior entre o valor
    da transação e o valor venal) e a tributação do ganho depende do regime do veículo.
    """

    model_config = _CFG

    comissao_leiloeiro: Decimal = Field(default=Decimal("0.05"), ge=0, le=1)
    itbi: Decimal = Field(default=Decimal("0.03"), ge=0, le=1)
    registro_e_emolumentos: Decimal = Field(default=Decimal("0.015"), ge=0, le=1)
    custas_e_despesas: Money = Money.zero()
    corretagem_na_saida: Decimal = Field(default=Decimal("0.06"), ge=0, le=1)
    #: Alíquota efetiva sobre o ganho na saída. Zero é placeholder explícito: o regime
    #: do veículo (SPE, lucro presumido ou real) é decisão do tributarista.
    tributacao_do_ganho: Decimal = Field(default=Decimal("0"), ge=0, le=1)


class Financiamento(BaseModel):
    """Estrutura de capital da operação (ADR-0016)."""

    model_config = _CFG

    #: Fração do investimento total financiada pelo sócio financiador. O padrão é
    #: ilustrativo: alavancagem alta infla a TIR e encurta a margem até a ruína, e a
    #: escolha é do comitê, não do motor.
    participacao_divida: Decimal = Field(default=Decimal("0.80"), ge=0, le=1)
    #: Custo anual do funding — CDI mais spread, se houver. Valor a confirmar.
    taxa_divida_anual: Decimal = Field(default=Decimal("0.15"), ge=0)
    #: TIR anual mínima exigida do equity pelo comitê. Valor a confirmar.
    hurdle_equity_anual: Decimal = Field(default=Decimal("0.25"), ge=0)


class Cenario(BaseModel):
    """Um estado do mundo, internamente coerente."""

    model_config = _CFG

    nome: str
    valor_justo_saida: Money
    haircut_liquidez: Decimal = Field(default=Decimal("0.10"), ge=0, le=1)
    meses_ate_posse: int = Field(ge=0, le=240)
    meses_ate_venda: int = Field(ge=1, le=360)
    debitos_que_seguem: Money = Money.zero()
    custo_desocupacao: Money = Money.zero()
    custo_regularizacao: Money = Money.zero()

    @model_validator(mode="after")
    def _prazos_coerentes(self) -> Cenario:
        if self.meses_ate_venda < self.meses_ate_posse:
            raise ValueError("venda não pode anteceder a posse")
        return self


class RiscoExecucao(BaseModel):
    """Probabilidades vindas do motor de risco processual e do Caçador de Vícios."""

    model_config = _CFG

    p_leilao_ocorre: Decimal = Field(default=Decimal("1"), ge=0, le=1)
    p_anulacao: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    #: Perda afundada se a arrematação for desfeita (custas, carrego, diligência).
    custo_desfazimento: Money = Money.zero()


@unique
class Veredito(StrEnum):
    APROVA = "APROVA"
    LIMITROFE = "LIMITROFE"
    REPROVA = "REPROVA"
    INVIAVEL = "INVIAVEL"

    @property
    def descricao(self) -> str:
        return {
            "APROVA": "supera o custo de capital com folga",
            "LIMITROFE": "supera o custo de capital por margem estreita",
            "REPROVA": "não supera o custo de capital",
            "INVIAVEL": "não devolve o capital investido",
        }[self.value]


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResultadoRetorno:
    cenario: str
    lance: Money
    investimento_total: Money
    divida: Money
    equity: Money
    juros_acumulados: Money
    divida_na_saida: Money
    valor_realizavel: Money
    liquido_da_saida: Money
    caixa_ao_equity: Money
    lucro_do_equity: Money
    meses: int
    tir_anual: Decimal | None
    multiplo: Decimal | None
    vpl_ao_hurdle: Money
    vpl_ajustado_a_risco: Money
    hurdle: Decimal
    #: Valor realizável mínimo na saída para o equity não zerar. Em operação
    #: alavancada é a métrica mais honesta de risco: TIR alta com margem fina é
    #: aposta, não investimento.
    ponto_de_ruina: Money

    @property
    def veredito(self) -> Veredito:
        if self.tir_anual is None or self.caixa_ao_equity.centavos <= 0:
            return Veredito.INVIAVEL
        if self.tir_anual < self.hurdle:
            return Veredito.REPROVA
        if self.tir_anual < self.hurdle * Decimal("1.2"):
            return Veredito.LIMITROFE
        return Veredito.APROVA

    @property
    def margem_ate_a_ruina(self) -> Decimal | None:
        """Quanto a saída pode cair, em relação a este cenário, antes de zerar o equity."""
        if self.valor_realizavel.centavos <= 0:
            return None
        return Decimal(1) - self.ponto_de_ruina.razao(self.valor_realizavel)

    @property
    def desagio_sobre_valor_justo(self) -> Decimal | None:
        """Deságio nominal do lance — o número que o mercado exibe."""
        if self.valor_realizavel.centavos == 0:
            return None
        return Decimal(1) - self.lance.razao(self.valor_realizavel)

    def linhas(self) -> tuple[str, ...]:
        """Conta aberta, na ordem em que o dinheiro se move."""
        tir = f"{self.tir_anual:.1%} a.a." if self.tir_anual is not None else "indefinida"
        return (
            f"cenário {self.cenario} — {self.meses} meses até o recebimento",
            f"  lance                        {self.lance}",
            f"  investimento total           {self.investimento_total}",
            f"    financiado                 {self.divida}",
            f"    capital próprio            {self.equity}",
            f"  juros do funding no período  {self.juros_acumulados}",
            f"  valor realizável na saída    {self.valor_realizavel}",
            f"  líquido da venda             {self.liquido_da_saida}",
            f"  (-) quitação do financiador  {self.liquido_da_saida - self.caixa_ao_equity}",
            f"  = caixa ao equity            {self.caixa_ao_equity}",
            f"  lucro do equity              {self.lucro_do_equity}",
            f"  TIR do equity                {tir}  (hurdle {self.hurdle:.1%})",
            f"  equity zera se a saída cair a {self.ponto_de_ruina}"
            + (
                f"  ({self.margem_ate_a_ruina:.0%} de margem)"
                if self.margem_ate_a_ruina is not None
                else ""
            ),
            f"  VPL ajustado a risco         {self.vpl_ajustado_a_risco}",
            f"  → {self.veredito.value}: {self.veredito.descricao}",
        )


@dataclass(frozen=True, slots=True)
class FaixaRetorno:
    """Os três cenários juntos, com o p10 comandando a decisão."""

    pessimista: ResultadoRetorno
    central: ResultadoRetorno
    otimista: ResultadoRetorno

    @property
    def tir(self) -> Faixa[Decimal]:
        """Cenário inviável entra como −100%: perda total do capital próprio.

        É leitura fiel, não artifício — se o equity zera, a TIR *é* −100%. O veredito
        `INVIAVEL` continua reportado à parte, para não confundir "perdeu tudo" com
        "rendeu pouco".
        """
        valores = sorted(
            r.tir_anual if r.tir_anual is not None else Decimal(-1)
            for r in (self.pessimista, self.central, self.otimista)
        )
        return Faixa(valores[0], valores[1], valores[2])

    @property
    def decide_pelo_p10(self) -> ResultadoRetorno:
        """O cenário que comanda: o pior dos três."""
        return min(
            (self.pessimista, self.central, self.otimista),
            key=lambda r: r.tir_anual if r.tir_anual is not None else Decimal(-1),
        )

    @property
    def veredito(self) -> Veredito:
        return self.decide_pelo_p10.veredito

    @property
    def passa_hurdle(self) -> bool:
        return self.veredito in {Veredito.APROVA, Veredito.LIMITROFE}


# ---------------------------------------------------------------------------
# Motor
# ---------------------------------------------------------------------------


def avaliar_retorno(
    lance: Money,
    cenario: Cenario,
    custos: Custos | None = None,
    financiamento: Financiamento | None = None,
    risco: RiscoExecucao | None = None,
) -> ResultadoRetorno:
    """Calcula o retorno do equity para um lance em um cenário."""
    custos = custos or Custos()
    financiamento = financiamento or Financiamento()
    risco = risco or RiscoExecucao()

    # 1. Quanto realmente sai do bolso
    preco_aquisicao = (
        lance
        + lance * custos.comissao_leiloeiro
        + lance * custos.itbi
        + lance * custos.registro_e_emolumentos
        + custos.custas_e_despesas
    )
    investimento_total = (
        preco_aquisicao
        + cenario.debitos_que_seguem
        + cenario.custo_desocupacao
        + cenario.custo_regularizacao
    )

    divida = investimento_total * financiamento.participacao_divida
    equity = investimento_total - divida

    # 2. Quanto o tempo cobra
    anos = Decimal(cenario.meses_ate_venda) / MESES_POR_ANO
    fator_divida = _potencia(Decimal(1) + financiamento.taxa_divida_anual, anos)
    divida_na_saida = divida * fator_divida
    juros_acumulados = divida_na_saida - divida

    # 3. Quanto entra na saída
    valor_realizavel = cenario.valor_justo_saida * (Decimal(1) - cenario.haircut_liquidez)
    corretagem = valor_realizavel * custos.corretagem_na_saida
    ganho_tributavel = valor_realizavel - corretagem - investimento_total
    tributo = (
        ganho_tributavel * custos.tributacao_do_ganho
        if ganho_tributavel.centavos > 0
        else Money.zero(ganho_tributavel.moeda)
    )
    liquido_da_saida = valor_realizavel - corretagem - tributo

    # 4. Preferência do financiador, e o que sobra ao equity
    caixa_ao_equity = liquido_da_saida - divida_na_saida
    lucro_do_equity = caixa_ao_equity - equity

    tir: Decimal | None = None
    multiplo: Decimal | None = None
    if equity.centavos > 0 and caixa_ao_equity.centavos > 0:
        multiplo = caixa_ao_equity.razao(equity)
        tir = _potencia(multiplo, Decimal(1) / anos) - Decimal(1)

    # 5. A que ponto a saída pode cair antes de o equity zerar
    resto_corretagem = Decimal(1) - custos.corretagem_na_saida
    ponto_de_ruina = (
        divida_na_saida * (Decimal(1) / resto_corretagem)
        if resto_corretagem > 0
        else Money.zero(divida_na_saida.moeda)
    )

    fator_desconto = _potencia(Decimal(1) + financiamento.hurdle_equity_anual, anos)
    valor_presente = caixa_ao_equity * (Decimal(1) / fator_desconto)
    vpl = valor_presente - equity

    p_nao_anula = Decimal(1) - risco.p_anulacao
    vpl_ajustado = (vpl * p_nao_anula - risco.custo_desfazimento * risco.p_anulacao) * (
        risco.p_leilao_ocorre
    )

    return ResultadoRetorno(
        cenario=cenario.nome,
        lance=lance,
        investimento_total=investimento_total,
        divida=divida,
        equity=equity,
        juros_acumulados=juros_acumulados,
        divida_na_saida=divida_na_saida,
        valor_realizavel=valor_realizavel,
        liquido_da_saida=liquido_da_saida,
        caixa_ao_equity=caixa_ao_equity,
        lucro_do_equity=lucro_do_equity,
        meses=cenario.meses_ate_venda,
        tir_anual=tir,
        multiplo=multiplo,
        vpl_ao_hurdle=vpl,
        vpl_ajustado_a_risco=vpl_ajustado,
        hurdle=financiamento.hurdle_equity_anual,
        ponto_de_ruina=ponto_de_ruina,
    )


def avaliar_faixa(
    lance: Money,
    pessimista: Cenario,
    central: Cenario,
    otimista: Cenario,
    custos: Custos | None = None,
    financiamento: Financiamento | None = None,
    risco: RiscoExecucao | None = None,
) -> FaixaRetorno:
    """Roda o cálculo nos três cenários coerentes."""
    return FaixaRetorno(
        pessimista=avaliar_retorno(lance, pessimista, custos, financiamento, risco),
        central=avaliar_retorno(lance, central, custos, financiamento, risco),
        otimista=avaliar_retorno(lance, otimista, custos, financiamento, risco),
    )


def teto_de_lance(
    pessimista: Cenario,
    custos: Custos | None = None,
    financiamento: Financiamento | None = None,
    risco: RiscoExecucao | None = None,
    tir_minima: Decimal | None = None,
    tolerancia_centavos: int = 100,
) -> Money:
    """Maior lance que ainda supera a TIR mínima **no cenário pessimista**.

    É o número que o comitê leva para a praça: acima dele, não se dá lance. Definido
    pelo cenário ruim de propósito — teto calculado no cenário central é convite a
    pagar caro (doc 01, § 2.1).

    Devolve zero quando nem um lance simbólico supera a exigência.
    """
    financiamento = financiamento or Financiamento()
    alvo = tir_minima if tir_minima is not None else financiamento.hurdle_equity_anual

    def supera(centavos: int) -> bool:
        if centavos <= 0:
            return True
        r = avaliar_retorno(
            Money(centavos, pessimista.valor_justo_saida.moeda),
            pessimista,
            custos,
            financiamento,
            risco,
        )
        return r.tir_anual is not None and r.tir_anual >= alvo

    baixo, alto = 0, pessimista.valor_justo_saida.centavos
    if supera(alto):
        return Money(alto, pessimista.valor_justo_saida.moeda)
    if not supera(1):
        return Money.zero(pessimista.valor_justo_saida.moeda)

    while alto - baixo > tolerancia_centavos:
        meio = (baixo + alto) // 2
        if supera(meio):
            baixo = meio
        else:
            alto = meio
    return Money(baixo, pessimista.valor_justo_saida.moeda)
