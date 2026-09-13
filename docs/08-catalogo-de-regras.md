# 08 — Catálogo de regras para validação jurídica

> **Documento gerado automaticamente** a partir de `src/hasta/score/`.
> Não editar à mão: rode `python scripts/gerar_catalogo.py`.
> Um teste de regressão falha se o documento divergir do motor.

## Como usar este catálogo

Cada regra tem identificador, base legal, efeito numérico e status. O trabalho de
validação é percorrer as regras marcadas `⚠️ a validar`, conferir a premissa em
fonte primária e decidir entre três destinos:

1. **confirmar** — a premissa se sustenta: muda o status para `VIGENTE`;
2. **corrigir** — a premissa está imprecisa: ajusta-se o texto, a base legal ou o peso;
3. **revogar** — a premissa não se sustenta: status `REVOGADA`, e a regra deixa de
   contar no score sem desaparecer do histórico.

Enquanto houver regra `⚠️ a validar` influenciando um número, o resultado do motor
expõe quais foram, em `regras_a_validar` e `itens_a_validar` — para que ninguém
decida sem saber.

**Situação atual:** 38 regras, das quais 7 a validar.

## 1. Blindagem — base por regime de transmissão

| Regra | Regime | Base | Fundamento | Status |
|---|---|---:|---|---|
| B01 | `LFR_141_II_FALENCIA` | 80 | art. 141, II, da Lei 11.101/2005; STF, ADI 3.934 | ✅ vigente |
| B02 | `LFR_60_UPI` | 72 | art. 60 c/c art. 141, II, da Lei 11.101/2005; STF, ADI 3.934 | ✅ vigente |
| B03 | `LFR_144_145_ALTERNATIVA` | 55 | arts. 144 e 145 da Lei 11.101/2005 | ⚠️ a validar |
| B04 | `CPC_879_LEILAO` | 32 | arts. 879 e ss. do CPC | ✅ vigente |
| B05 | `CPC_880_INICIATIVA_PARTICULAR` | 30 | art. 880 do CPC | ✅ vigente |
| B06 | `LEI_9514_EXTRAJUDICIAL` | 25 | art. 27 da Lei 9.514/1997 | ✅ vigente |
| B07 | `INDETERMINADO` | 10 | — | ✅ vigente |

## 2. Blindagem — ajustes

| Regra | Condição | Efeito | Fundamento | Status |
|---|---|---:|---|---|
| B10 | clausula concursal | +12 | art. 141, II, e art. 60 da Lei 11.101/2005 | ✅ vigente |
| B11 | clausula fora do concursal | +2 | art. 141, II, da Lei 11.101/2005 (inaplicável); art. 130 do CTN | ✅ vigente |
| B12 | plano ausente | -18 | art. 60 da Lei 11.101/2005 | ✅ vigente |
| B12 | plano nao verificado | -9 | art. 60 da Lei 11.101/2005 | ✅ vigente |
| B13 | autorizacao ausente | -12 | arts. 66, 142 e 145 da Lei 11.101/2005 | ✅ vigente |
| B13 | autorizacao nao verificada | -6 | arts. 66, 142 e 145 da Lei 11.101/2005 | ✅ vigente |
| B15 | bem de terceiro | -25 | art. 49, § 3º, da Lei 11.101/2005; art. 108 da Lei 11.101/2005 | ⚠️ a validar |
| B16 | adquirente ligado ao devedor | -60 | art. 141, § 1º, da Lei 11.101/2005 | ✅ vigente |
| B17 | sucessao trabalhista | -8 | art. 69-J da Lei 11.101/2005; teses de grupo econômico e sucessão trabalhista | ⚠️ a validar |
| B18 | impugnacao pendente | -10 | art. 1.015 do CPC; art. 59, § 2º, da Lei 11.101/2005 | ✅ vigente |
| B19 | tributos sub rogados | +6 | art. 130, parágrafo único, do CTN | ✅ vigente |
| B20 | condominio edital silente | -5 | natureza propter rem; jurisprudência do STJ | ⚠️ a validar |
| B21 | edital instavel | -3 | política interna: instabilidade do instrumento | ✅ vigente |

## 3. Blindagem — tetos

Teto é mais honesto que desconto: sem o fato verificado, o ativo não é *um pouco*
menos blindado — ele não pode ser classificado como blindado.

| Regra | Condição | Teto | Fundamento |
|---|---|---:|---|
| B12 | plano nao verificado | 69 | art. 60 da Lei 11.101/2005 |
| B14 | cadeia dominial nao verificada | 69 | política interna de diligência |
| B22 | segredo de justica | 40 | política interna de diligência |
| B23 | regime inferido | 69 | política interna: inferência não é evidência |

## 4. Blindagem — faixas do grau

| Faixa | Grau | Leitura |
|---|---|---|
| `BLINDADO_FORTE` | 90–100 | falência com não sucessão expressa e registro conferido |
| `BLINDADO_COM_RESIDUO` | 70–89 | UPI homologada; risco residual de tese de sucessão |
| `PARCIAL` | 45–69 | alienação concursal com lacuna de verificação |
| `FRAGIL` | 20–44 | execução comum |
| `INDETERMINADO` | 0–19 | regime não identificado — não passa da triagem |

## 5. Caçador de Vícios — checklist

| Item | Verificação | Falha correspondente | Severidade | Escopo | Fundamento | Status |
|---|---|---|---|---|---|---|
| V01 | Intimação de todos os legitimados antes do leilão | Legitimados do art. 889 sem comprovação de intimação | GRAVE | `QUALQUER` | art. 889 do CPC | ⚠️ a validar |
| V02 | Prazo mínimo de publicidade entre publicação do edital e a praça | Publicidade do edital abaixo do prazo mínimo adotado | GRAVE | `QUALQUER` | art. 887 do CPC | ⚠️ a validar |
| V03 | Laudo de avaliação juntado aos autos | Laudo de avaliação não localizado nos autos | RELEVANTE | `QUALQUER` | arts. 870 e 872 do CPC | ✅ vigente |
| V04 | Avaliação atual | Laudo de avaliação defasado | MODERADA | `QUALQUER` | política interna; art. 873 do CPC (nova avaliação) | ✅ vigente |
| V05 | Impugnação pendente à avaliação | Impugnação à avaliação pendente | RELEVANTE | `QUALQUER` | art. 873 do CPC | ✅ vigente |
| V06 | Penhora averbada na matrícula | Penhora não averbada na matrícula | MODERADA | `IMOVEL` | art. 844 do CPC | ✅ vigente |
| V07 | Concorrência de penhoras e ordem de preferência resolvida | Penhoras concorrentes sem ordem de preferência resolvida | MODERADA | `QUALQUER` | arts. 797 e 908 do CPC | ✅ vigente |
| V08 | Lance mínimo acima do patamar de preço vil | Lance mínimo em patamar de preço vil | GRAVE | `EXECUCAO_CPC` | art. 891 do CPC | ✅ vigente |
| V09 | Ausência de alegação de impenhorabilidade ou bem de família | Impenhorabilidade ou bem de família alegado | GRAVE | `QUALQUER` | art. 833 do CPC; Lei 8.009/1990 | ✅ vigente |
| V10 | Alienação concursal com previsão no plano ou autorização judicial | Alienação concursal sem previsão no plano nem autorização judicial | GRAVE | `CONCURSAL` | arts. 66, 142 e 145 da Lei 11.101/2005 | ✅ vigente |
| V11 | Ausência de recurso com efeito suspensivo sobre a alienação | Recurso com efeito suspensivo pendente sobre a alienação | GRAVE | `QUALQUER` | arts. 995 e 1.019 do CPC | ✅ vigente |
| V12 | Descrição do bem coerente entre edital, laudo e matrícula | Descrição do bem divergente entre edital, laudo e matrícula | RELEVANTE | `QUALQUER` | política interna de conferência documental | ✅ vigente |
| V13 | Autos acessíveis para verificação | Autos sob segredo de justiça: verificação impossível | MODERADA | `QUALQUER` | política interna de diligência | ✅ vigente |
| V14 | Edital estável após o início da publicidade | Edital retificado após o início da publicidade | MODERADA | `QUALQUER` | art. 886 do CPC | ✅ vigente |

## 6. Notas de regime

Não são vícios: são consequências do regime que o dossiê precisa registrar.

| Nota | Conteúdo | Fundamento | Status |
|---|---|---|---|
| N01 | Na falência não incide a vedação do preço vil: aliena-se pelo maior valor ofertado | art. 142, § 2º, da Lei 11.101/2005 | ⚠️ a validar |
| N02 | Tributos do imóvel sub-rogam-se no preço da arrematação em hasta pública | art. 130, parágrafo único, do CTN | ✅ vigente |
| N03 | Aquisição em processo de falência ou de recuperação não gera sucessão tributária | art. 133, § 1º, do CTN | ✅ vigente |

## 7. Priors de agregação de risco

Pesos **declarados por julgamento, não medidos**. Servem para ordenar diligência,
não para decidir capital; a calibração contra casos reais de anulação é entrega da
Fase 3 (doc 04, § 9).

| Severidade | Probabilidade atribuída quando constatado |
|---|---:|
| BAIXA (1) | 0.02 |
| MODERADA (2) | 0.05 |
| RELEVANTE (3) | 0.12 |
| GRAVE (4) | 0.25 |
| FATAL (5) | 0.50 |

Item apenas suspeito (não verificado) entra com peso 0.4 do valor
acima, e compõe o **índice de incerteza**, que é reportado separadamente do risco
detectado — misturar os dois esconderia se o problema é o ativo ou a diligência.

## 8. Pendências de validação

### B03 — Modalidade alternativa de alienação em procedimento concursal

- **Fundamento invocado:** arts. 144 e 145 da Lei 11.101/2005
- **O que conferir:** Conferir se a não sucessão do art. 141 alcança as modalidades alternativas.

### B15 — Ativo gravado por propriedade de terceiro (fiduciária, arrendamento)

- **Fundamento invocado:** art. 49, § 3º, da Lei 11.101/2005; art. 108 da Lei 11.101/2005
- **O que conferir:** Bem de terceiro não integra a massa; o lote pode ser impróprio, não só arriscado.

### B17 — Consolidação substancial com passivo trabalhista relevante

- **Fundamento invocado:** art. 69-J da Lei 11.101/2005; teses de grupo econômico e sucessão trabalhista
- **O que conferir:** Medir a exposição real à tese de sucessão trabalhista na jurisprudência atual.

### B20 — Débitos condominiais anteriores com edital silente

- **Fundamento invocado:** natureza propter rem; jurisprudência do STJ
- **O que conferir:** Jurisprudência nuançada entre sub-rogação no preço e responsabilidade do arrematante.

### N01 — Na falência não incide a vedação do preço vil: aliena-se pelo maior valor ofertado

- **Fundamento invocado:** art. 142, § 2º, da Lei 11.101/2005
- **O que conferir:** Conferir a redação vigente. Se confirmada, é a assimetria central do nicho: o piso de preço do art. 891 do CPC não se aplica.

### V01 — Intimação de todos os legitimados antes do leilão

- **Fundamento invocado:** art. 889 do CPC
- **O que conferir:** Conferir a lista de incisos vigente antes de tratar como regra fechada.

### V02 — Prazo mínimo de publicidade entre publicação do edital e a praça

- **Fundamento invocado:** art. 887 do CPC
- **O que conferir:** Confirmar o prazo legal vigente; o padrão do sistema é configurável.
