# 04 — Motores de avaliação, risco e score

> Toda fórmula aqui é implementada em código determinístico, versionada
> (`versao_modelo`) e testada contra gabarito. Nenhum LLM produz estes números.

## 1. Motor 1 — Valor justo (`Avaliador`)

Saída sempre `(p10, p50, p90)` + `metodo` + `comparaveis[]` + `evidencias[]`.

### Por classe de ativo

| Classe | Método primário | Método de checagem | Sinais de ajuste |
|---|---|---|---|
| `IMOVEL_URBANO` | comparáveis de anúncio da micro-região, ajustados por área, padrão, idade e liquidez | índice de preços (FipeZAP/DataZAP) aplicado sobre laudo antigo; valor venal/ITBI | ocupação, andar, vaga, estado de conservação, condomínio |
| `IMOVEL_RURAL` | R$/ha por região + tipo de solo/uso | valor de terra nua (ITR) e pesquisas regionais | CAR/SIGEF, reserva legal, georreferenciamento, acesso, água, arrendamento vigente |
| `PLANTA_INDUSTRIAL` | custo de reposição depreciado + valor do terreno/galpão | comparável de galpão logístico (R$/m²) | licenças, subestação, passivo ambiental, especificidade (*single-purpose*) |
| `MAQUINA_EQUIPAMENTO` | comparáveis de mercado secundário (Superbid e afins) | custo de reposição depreciado | horímetro, marca, manutenção, custo de desmontagem e frete |
| `VEICULO / FROTA` | tabela FIPE ajustada por estado/quilometragem | anúncios regionais | sinistro, gravame, leilão de sucata |
| `ESTOQUE` | valor de liquidação por categoria (% do custo) | comparáveis de atacado | perecibilidade, obsolescência, sazonalidade |
| `MARCA_IP` | *royalties* evitados / múltiplo de receita | custo de reconstrução da marca | vigência INPI, oposições, uso efetivo |
| `PARTICIPACAO_SOCIETARIA` | múltiplos setoriais sobre EBITDA do RMA | valor patrimonial ajustado | acordo de sócios, dívida na investida, governança |
| `CARTEIRA_CREDITO / PRECATORIO` | fluxo descontado com curva de recuperação por safra | comparáveis de cessão | ente devedor, fase, prescrição, ordem cronológica |
| `UPI` | fluxo de caixa descontado do *going concern* | soma das partes (piso) | contratos, licenças, equipe, clientes, capital de giro necessário |

### Tratamento do laudo oficial (diferencial)

O laudo **não** é o valor justo; é uma evidência com qualidade mensurável:

```
qualidade_laudo = f(idade_em_meses, houve_vistoria, método_declarado,
                    qualificação_do_avaliador, divergência_vs_comparáveis)
```

e produz duas saídas visíveis no dossiê: `laudo_defasado_para_baixo` (tipo T3 do doc 01)
e `laudo_inflado` (deságio de vitrine, alarme falso). Nenhum concorrente faz essa
distinção — é a origem da maioria dos falsos positivos do mercado.

## 2. Motor 2 — Blindagem jurídica (`Grau de Blindagem` 0–100)

Determinado por regras, não por opinião. Entradas: `regime_transmissao`, texto do
edital, plano homologado, decisão autorizadora, natureza do procedimento, ônus.

| Faixa | Situação típica |
|---|---|
| 90–100 | Falência, art. 141, II, com não-sucessão expressa no edital, sem exceção do § 1º aplicável, cadeia dominial limpa |
| 70–89 | UPI em RJ (art. 60, § 1º) com plano homologado e cláusula expressa, risco residual de tese de grupo econômico |
| 45–69 | Alienação concursal sem cláusula expressa, ou modalidade alternativa (arts. 144/145) sem blindagem explicitada |
| 20–44 | Execução comum (CPC): sub-rogação tributária no preço (art. 130, § único, do CTN), mas condomínio e outros passivos a apurar `⚠ verificar jurisprudência sobre débitos condominiais` |
| 0–19 | Regime indeterminado, ônus não levantado, indício de fraude ou indisponibilidade |

Penalizadores automáticos: arrematante potencialmente sócio/parente/agente do devedor
(art. 141, § 1º, da LFR), ausência de publicidade regular, consolidação substancial com
passivo trabalhista relevante, existência de ação anulatória sobre o plano.

## 3. Motor 3 — Risco processual

Três estimativas, cada uma com intervalo:

```
P(leilão_ocorre_na_data) = g(agravo_pendente, histórico_da_vara, nº_de_redesignações,
                             pedido_de_suspensão, regularidade_das_intimações)

P(arrematação_anulada)   = h(vícios_detectados, completude_do_art._889_do_CPC,
                             idade/impugnação_do_laudo, taxa_histórica_da_vara,
                             hipóteses_do_art._903,_§_1º,_do_CPC)

T(posse_mansa)           = i(ocupação, necessidade_de_imissão/desocupação,
                             congestionamento_da_vara, resistência_esperada)
```

**Caçador de Vícios** — checklist executável, com evidência para cada item:

- intimação de todos os legitimados do art. 889 do CPC (executado, cônjuge, credor
  hipotecário/pignoratício, coproprietário, usufrutuário, titular de direito de
  preferência, condomínio) `⚠ verificar lista do inciso vigente`
- publicidade: prazo entre publicação e 1ª praça; retificações de edital
- avaliação: existência, data, impugnação pendente, atualização
- penhora: registro na matrícula, concorrência de penhoras, ordem de preferência
- competência e regularidade da constrição; bem de família; impenhorabilidade
- em concursal: autorização judicial, oitiva do Comitê/AJ, previsão no plano
- preço vil (art. 891 do CPC) quando o regime for CPC — e sua **inaplicabilidade** na
  falência (art. 142, § 2º, da LFR) `⚠ verificar redação vigente`

Cada item ausente **não** vira nota baixa silenciosa: vira `Lacuna` explícita no dossiê
com a diligência recomendada.

## 4. Motor 4 — Liquidez de saída

```
haircut_liquidez = base_por_classe
                 + ajuste_microrregião(profundidade_do_mercado)
                 + ajuste_especificidade(single_purpose, tamanho_do_ticket)
                 + ajuste_ocupação

T_saída = tempo_de_regularização + tempo_de_comercialização (por classe/região)
```

Alvo de honestidade: para planta industrial *single-purpose* em cidade pequena, o
haircut deve ser grande e o sistema deve dizer isso em vez de exibir um deságio
sedutor.

## 5. Motor 5 — Intensidade competitiva (diferencial exclusivo)

Nenhum concorrente estima quem vai disputar. Nós podemos, porque acumulamos histórico
por leiloeiro, vara, classe e faixa de ticket:

```
n_disputantes_esperado = j(classe, ticket, região, visibilidade_do_lote,
                           presença_histórica_de_fundos_no_leiloeiro,
                           nº_de_acessos/habilitações quando observável,
                           deságio_aparente — quanto mais vitrine, mais concorrência)

preço_de_fechamento_esperado = k(n_disputantes_esperado, lance_mínimo, valor_justo)
```

Uso prático: define **teto de lance** e revela o padrão T1 (ativo que assusta o varejo →
pouca concorrência → deságio real capturável). Complemento: `Alerta de 2ª/3ª praça` —
lotes com alta probabilidade de ficarem desertos são acompanhados para reentrada com
lance mínimo reduzido.

## 6. Motor 6 — Rota de acesso (`Estrategista`)

Para cada oportunidade, o sistema compara rotas e recomenda a de melhor TIR ajustada:

| Rota | Quando domina | Requisito |
|---|---|---|
| **Lance em praça** | blindagem alta, competição baixa, liquidez razoável | habilitação, caução |
| **Compra de crédito concursal** | crédito com deságio > deságio do ativo; ou dá controle de classe/voto | cessão, análise de habilitação |
| **DIP / dinheiro novo** | empresa viável, garantia sobre o ativo-alvo, prioridade legal | capital e apetite |
| **Stalking horse de UPI** | ativo de *going concern*, plano em formação | proposta vinculante, *break-up fee* |
| **Venda direta / proposta fechada (arts. 144/145)** | lote deserto ou ativo perecível | negociação com AJ e juízo |
| **Adjudicação** | quando já somos credores | título e habilitação |

A escolha é **calculada e justificada**, com as condições que a viabilizam listadas.

## 7. Score composto (resumo de leitura, não critério)

```
score = Σ wᵢ · dimensãoᵢ          i = 1..7 do doc 01, § 2.3
```

Pesos padrão propostos (ajustáveis por mandato, versionados):

| Dimensão | Peso |
|---|---|
| Deságio efetivo | 0,25 |
| Blindagem jurídica | 0,20 |
| Segurança processual | 0,18 |
| Liquidez de saída | 0,14 |
| Custo de posse/regularização | 0,10 |
| Intensidade competitiva | 0,08 |
| Alavancagem de relacionamento | 0,05 |

**Regra de exibição:** o feed ordena por `TIR_ajustada_p10`; o score aparece como rótulo.
Nenhum item entra no feed com `Confiança < 0,6` — vai para "precisa de diligência", com
a lista exata do que falta. Melhor um feed curto e confiável que um mural de 8.000 lotes.

## 8. Confiança (completude × procedência)

```
confiança = média_ponderada( completude_dos_campos_críticos,
                             qualidade_das_fontes (oficial > leiloeiro > notícia),
                             consistência_entre_fontes,
                             atualidade )
```

Isso resolve o vício do mercado de exibir tudo com aparência de certeza. Aqui a
incerteza é *visível* e comanda a fila de diligência.

## 9. Protocolo de calibração e backtesting

Sem isto, o score é opinião com cara de número.

1. **Conjunto de ouro:** 80 a 120 lotes históricos já resolvidos (arrematados ou
   desertos), com preço final conhecido, priorizando falência/RJ nas comarcas-alvo.
2. **Validação *out-of-time*:** treina/calibra até T, avalia em T+1. Nunca amostra
   aleatória — há tendência temporal forte (juros, ciclo de RJ, regulação).
3. **Métricas por motor:**
   - Avaliador: MAPE e viés contra preço final realizado;
   - Blindagem: concordância com parecer humano (κ de Cohen ≥ 0,7);
   - Risco processual: calibração (curva de confiabilidade) de `P(anulado)` e `P(ocorre)`;
   - Competição: erro em nº de disputantes e em preço de fechamento;
   - Score global: correlação de ranking (Spearman) com retorno realizado; e
     *precision@20* — dos 20 melhores, quantos teriam dado retorno acima do piso.
4. **Testes de regressão de decisão:** um conjunto de casos com decisão conhecida
   ("deveria ter passado / deveria ter sido barrado") roda a cada mudança de modelo.
5. **Ciclo de aprendizado (L9):** todo `Resultado` real reescreve as priors —
   por vara, leiloeiro, classe e micro-região.
