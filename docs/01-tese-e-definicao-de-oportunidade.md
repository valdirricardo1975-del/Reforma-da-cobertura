# 01 — Tese: o que é, operacionalmente, uma "ótima oportunidade"

> Este documento existe porque a qualidade de um agente de originação é limitada pela
> precisão da definição de alvo. "Deságio grande" é uma definição ruim e produz um
> agente que encontra muito e acerta pouco.

## 1. O erro fundador dos concorrentes

O mercado ranqueia por **deságio nominal contra o laudo de avaliação**:

```
deságio_aparente = 1 − (lance_mínimo / valor_avaliação_do_laudo)
```

Três defeitos fatais:

- **O denominador é ruidoso.** O laudo pode ter 5 anos, ter sido feito por oficial de
  justiça sem vistoria interna, ou ter sido inflado para sustentar a execução. Um
  deságio de 60% sobre laudo inflado pode ser prêmio sobre mercado.
- **O numerador é incompleto.** Lance mínimo não é preço de aquisição: falta comissão
  do leiloeiro (usualmente 5%), ITBI, registro, custas, débitos que acompanham o bem,
  custo de desocupação e regularização.
- **Ignora tempo e probabilidade.** Um bem com 55% de deságio que leva 4 anos para
  virar posse mansa, com 25% de chance de a arrematação ser desfeita, é pior que um
  com 30% de deságio, blindado e desocupado.

## 2. Nossa definição

Uma oportunidade é excelente quando o **retorno esperado ajustado a risco, líquido de
todos os custos e do custo do tempo, com procedência de dados verificável, supera o
custo de capital do escritório com margem de segurança** — e quando existe **rota de
acesso executável** por nós.

### 2.1 Equação central

```
Preço_total = Lance + Comissão + Tributos_transmissão + Registro/Custas
            + Débitos_que_seguem_o_bem + Custo_desocupação + Custo_regularização

Valor_realizável = Valor_justo × (1 − haircut_liquidez)          # preço de saída realista

VPL_bruto        = Valor_realizável / (1 + k)^T_saída − Preço_total

VPL_ajustado     = P(leilão_ocorre) × [ P(não_anulado) × VPL_bruto
                                      − P(anulado) × Custo_desfazimento ]

Ranking primário = TIR_ajustada = f(VPL_ajustado, Preço_total, T_saída)
Ranking secundário = Confiança (completude e procedência dos dados)
```

Tudo em **distribuições**, não em pontos: cada termo é estimado como
`(p10, p50, p90)` e o resultado é uma faixa. Um lote só é promovido a
"oportunidade" se o **p10 da TIR ajustada** ainda superar o piso — margem de segurança
embutida, não opinada.

### 2.2 Portões rígidos (hard gates) — reprovam antes de pontuar

| Portão | Regra |
|---|---|
| **Compliance** | Conflito de interesses, impedimento legal, informação de origem não pública → bloqueio absoluto (doc 06) |
| **Blindagem mínima** | Regime jurídico do ativo precisa ser identificado e classificado; "indeterminado" não passa da triagem |
| **Procedência** | Nenhum número entra no score sem evidência rastreável (documento + trecho) |
| **Mandato** | Classe de ativo, ticket, geografia e prazo dentro do mandato configurado |
| **Cadeia dominial** | Vícios impeditivos identificados (ex.: bem indisponível, litígio sobre a titularidade) |

### 2.3 As sete dimensões pontuadas

Score 0–100 por dimensão, com pesos configuráveis por mandato. A nota composta é
**resumo**, nunca o critério: o ranking é pela TIR ajustada; a nota serve à leitura
humana rápida.

1. **Deságio efetivo** — contra *nosso* valor justo, com sinalização explícita de
   defasagem do laudo (idade, método, existência de vistoria).
2. **Blindagem jurídica** — regime de transmissão e o quanto ele é oponível.
3. **Segurança processual** — probabilidade de o ato se consumar e sobreviver.
4. **Liquidez de saída** — profundidade do mercado comparável, tempo e haircut.
5. **Custo de posse e regularização** — ocupação, débitos, licenças, passivo ambiental.
6. **Intensidade competitiva** — quantos e quais players devem disputar.
7. **Alavancagem de relacionamento** — existe rota alternativa acessível a nós?

Detalhamento matemático e calibração: doc 04.

## 3. Por que o foco em recuperação judicial e falência é a escolha certa

Não é só familiaridade do escritório — é **assimetria estrutural**:

| Fator | Execução comum (CPC) | Falência / UPI em RJ (LFR) |
|---|---|---|
| Sucessão em dívidas do devedor | Risco real, caso a caso | **Afastada por lei**: art. 141, II (falência) e art. 60, § 1º (UPI em RJ), inclusive tributárias e trabalhistas — STF, ADI 3.934 |
| Piso de preço | Preço vil: < 50% da avaliação ou do mínimo fixado (art. 891, CPC) | Aliena-se pelo maior valor ofertado, ainda que inferior à avaliação (art. 142, § 2º, LFR) `⚠ verificar redação vigente` |
| Modalidades | Leilão eletrônico (art. 879 ss.) | Leilão eletrônico/presencial/híbrido, propostas fechadas, pregão, **modalidades alternativas** (arts. 142, 144 e 145) |
| Interlocutor técnico | Oficial de justiça, cartório | **Administrador judicial** — produz laudo, arrecadação, relatórios mensais, lista de credores |
| Informação disponível | Autos e edital | Auto de arrecadação, RMAs, plano, laudos, AGC, quadro de credores |
| Rotas de acesso | Lance, adjudicação | Lance, crédito concursal, DIP, *stalking horse*, venda direta, cisão/UPI |

Traduzindo: no ambiente concursal o **risco jurídico é menor**, o **piso de preço é mais
baixo**, a **informação pública é muito mais rica** e as **rotas de entrada são múltiplas**.
É o nicho de maior retorno ajustado a risco do mercado brasileiro de ativos judiciais —
e o menos coberto por ferramenta.

Contrapartidas honestas, que o sistema precisa modelar e não esconder:
- ativo concursal costuma ser **complexo e ilíquido** (planta industrial, estoque
  específico, marca) — o haircut de liquidez é maior;
- a blindagem tem **exceções** (aquisição por sócio, parente ou agente do falido —
  art. 141, § 1º, LFR) e é **atacável** por teses de grupo econômico e sucessão
  trabalhista: é probabilidade, não certeza `⚠ verificar jurisprudência atual`;
- prazos concursais são longos e sujeitos a agravo;
- **acesso privilegiado é vedado**: nada que venha de cliente ou de posição funcional
  entra no pipeline (doc 06).

## 4. Os cinco tipos de oportunidade que o agente deve reconhecer

O agente não busca "imóvel barato". Busca padrões:

| Tipo | Assinatura detectável |
|---|---|
| **T1 — Deságio por complexidade** | Ativo que assusta o varejo (planta industrial, galpão com passivo, imóvel rural com CAR pendente) e por isso vai deserto na 1ª praça |
| **T2 — Blindagem subprecificada** | Ativo em falência/UPI, com não-sucessão expressa, precificado pelo mercado como se fosse execução comum |
| **T3 — Laudo defasado para baixo** | Avaliação antiga em micro-região que valorizou; deságio real >> deságio aparente |
| **T4 — UPI como *going concern*** | Conjunto com fluxo de caixa, licenças e contratos, cujo valor de operação excede a soma dos bens |
| **T5 — Rota indireta** | Crédito concursal com deságio que dá controle de classe, poder de voto na AGC ou moeda de pagamento no próprio leilão |

Cada tipo tem detector próprio, alvo de *recall* e alvo de precisão (doc 07).

## 5. Fronteira de autonomia (decisão explícita)

O agente é **autônomo em descobrir, extrair, avaliar, pontuar, alertar e documentar**.
O agente **não dá lance, não assina proposta, não contata contraparte e não movimenta
capital**. Toda ação externa passa por autorização humana registrada, com teto de lance
aprovado pelo comitê. Isso não é timidez: é o que torna o sistema utilizável por um
escritório de advocacia sem criar risco ético, processual e patrimonial. Ver ADR-0008.
