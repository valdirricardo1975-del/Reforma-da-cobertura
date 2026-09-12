# 03 — Modelo de domínio canônico

> É o ativo mais durável do sistema (ADR-0001). Fontes mudam; isto fica.

## 1. Primitiva de procedência: `Evidencia`

Nenhum campo relevante existe sem lastro. `Evidencia` é a unidade atômica do sistema.

```python
class Evidencia:
    id: UUID
    documento_id: UUID          # aponta para snapshot imutável
    localizador: str            # "p.14, §3" | "tabela 2, linha 7" | seletor CSS | offset
    trecho: str                 # texto literal que sustenta a afirmação
    campo: str                  # caminho canônico, ex.: "lote.lance_minimo_1a_praca"
    valor: JSON                 # valor extraído, já tipado
    extrator: str               # "parser:esaj_edital@2.1" | "llm:escriba@2026-09"
    confianca: float            # 0–1
    origem: Origem              # PUBLICA | CLIENTE | RELACIONAMENTO | INTERNA  (doc 06)
    coletado_em: datetime
    conflita_com: list[UUID]    # evidências divergentes, mantidas — nunca sobrescritas
```

Regras invioláveis:
1. Conflito de evidências **não** se resolve por sobrescrita: registra-se e a política de
   precedência (fonte oficial > leiloeiro > notícia) escolhe o valor *efetivo*, mantendo
   a divergência visível no dossiê.
2. `origem != PUBLICA` nunca entra em cálculo de oportunidade (portão L6).
3. Todo número do score é rastreável até um conjunto de `Evidencia`.

## 2. Entidades

### `Procedimento`
Processo judicial, em qualquer ritmo (concursal ou não).

| Campo | Notas |
|---|---|
`numero_cnj` | chave natural (20 dígitos, validação de dígito verificador)
`tribunal`, `grau`, `orgao_julgador` | vara empresarial é sinal de qualidade
`natureza` | `RJ · FALENCIA · RE_EXTRAJUDICIAL · EXEC_TITULO · EXEC_FISCAL · EXEC_TRABALHISTA · INSOLVENCIA_CIVIL`
`estado` | máquina de estados §4
`segredo_justica` | se sim, coleta e uso restritos
`datas_chave` | distribuição, deferimento, AGC, homologação, decretação, encerramento
`valor_causa`, `passivo_declarado`, `passivo_habilitado` |

### `Devedor` e `GrupoEconomico`
`cnpj/cpf`, `razao_social`, nomes anteriores, `cnae` (proxy de intensidade de ativos),
`porte`, sócios, consolidação processual/substancial, ligações societárias.
*Pseudonimização obrigatória para pessoa física (doc 06).*

### `AtorProcessual`
`tipo ∈ {ADMINISTRADOR_JUDICIAL, JUIZ, LEILOEIRO, GESTOR_JUDICIAL, ADVOGADO, CREDOR, FUNDO, PERITO}`

Métricas observadas — **o grafo de atores é diferencial (eixo 5 do doc 00)**:

| Métrica | Uso |
|---|---|
| `qualidade_documental` do AJ | previsibilidade e completude do dossiê |
| `tempo_mediano_ate_leilao` da vara | insumo de `T_posse` |
| `taxa_lote_deserto` do leiloeiro | previsão de 2ª/3ª praça e de deságio realizável |
| `taxa_anulacao` por vara/leiloeiro | insumo de `P(anulado)` |
| `frequencia_de_disputa` por fundo | insumo de intensidade competitiva |
| nota de desempenho do CNJ (Prov. 255) | quando publicada, entra como *feature* |

### `Ativo`
Bem individualizado, independente de estar ofertado.

`classe ∈ {IMOVEL_URBANO, IMOVEL_RURAL, PLANTA_INDUSTRIAL, MAQUINA_EQUIPAMENTO,
VEICULO, FROTA, ESTOQUE, MARCA_IP, PARTICIPACAO_SOCIETARIA, CARTEIRA_CREDITO,
PRECATORIO, CREDITO_FISCAL, DIREITO_LITIGIOSO, UPI, OUTRO}`

Identificadores por classe: `matricula`+`cns_registro`, `inscricao_imobiliaria`,
`placa`/`chassi`/`renavam`, `numero_serie`, `car`/`sigef`, `inpi`, `cnpj_investida`.
Demais: `localizacao` (geo + endereço normalizado), `area`, `descricao_original`,
`ocupacao ∈ {DESOCUPADO, OCUPADO_TERCEIRO, OCUPADO_DEVEDOR, INVADIDO, LOCADO, DESCONHECIDO}`,
`onus[]` (hipoteca, penhora, arresto, usufruto, indisponibilidade, alienação fiduciária),
`passivos_associados[]` (IPTU, condomínio, ambiental, trabalhista),
`avaliacoes_oficiais[]` (`valor`, `data`, `metodo`, `houve_vistoria`, `avaliador`).

### `Lote`
O que é ofertado — pode agrupar vários `Ativo`.

`regime_transmissao ∈ {LFR_141_II_FALENCIA, LFR_60_UPI, CPC_879_LEILAO,
CPC_880_INICIATIVA_PARTICULAR, LEI_9514_EXTRAJUDICIAL, LFR_144_145_ALTERNATIVA, OUTRO}`
→ **este campo é a chave da dimensão "blindagem"**.

`modalidade ∈ {LEILAO_ELETRONICO, PRESENCIAL, HIBRIDO, PROPOSTA_FECHADA, PREGAO, VENDA_DIRETA}`,
`comissao_leiloeiro`, `condicoes_pagamento` (parcelamento art. 895 do CPC quando cabível),
`onus_declarados_no_edital`, `clausula_nao_sucessao` (texto + presença),
`impedimentos_declarados`.

### `Praca`
`ordem` (1ª/2ª/3ª), `data_inicio`, `data_fim`, `lance_minimo`, `percentual_sobre_avaliacao`,
`incremento`, `status ∈ {DESIGNADA, SUSPENSA, REALIZADA, DESERTA, CANCELADA}`.

### `Edital`
`documento_id`, `publicacoes[]` (DJEN/DJE/jornal/PNAJ), `versoes[]` (retificações são
sinal forte de risco), `intimacoes_comprovadas[]` (checagem do art. 889 do CPC).

### `Credito`
Para as rotas indiretas: `classe ∈ {I_TRABALHISTA, II_GARANTIA_REAL, III_QUIROGRAFARIO,
IV_ME_EPP, EXTRACONCURSAL}`, `valor_habilitado`, `status`, `credor_id`,
`negociabilidade`, `desagio_observado` quando houver cessão pública.

### `Avaliacao` (nossa)
`metodo`, `valor_p10/p50/p90`, `comparaveis[]`, `data_base`, `versao_modelo`,
`evidencias[]`.

### `Oportunidade`
`lote_id`, `rota_acesso`, `scores` (7 dimensões), `tir_ajustada_p10/p50/p90`,
`teto_de_lance`, `confianca`, `riscos[]` (Advogado do Diabo), `vicios[]` (Caçador de
Vícios), `lacunas[]` (o que falta saber), `estado` §5, `indice_antecipacao_dias`.

### `Resultado`
`arrematante`, `preco_final`, `data`, `houve_impugnacao`, `desfecho`,
`nosso_valor_previsto` → alimenta L9.

## 3. Taxonomia de eventos (ponte com o DataJud)

O DataJud expõe **metadados e movimentações codificadas** (TPU/CNJ) — não o texto. O DJEN
expõe **o texto das publicações**. A combinação é o coração do funil P0–P5.

Mapeamos códigos TPU → `TipoEvento` canônico (tabela de mapeamento versionada em
`src/hasta/core/eventos.py`, a ser preenchida na Fase 1 com os códigos reais
`⚠ verificar tabela TPU vigente`):

| `TipoEvento` canônico | Estágio | Lead time esperado |
|---|---|---|
`PEDIDO_RJ_DISTRIBUIDO` | P0 | 12–24 m
`DEFERIMENTO_PROCESSAMENTO` | P1 | 6–18 m
`AJ_NOMEADO` | P1 | 6–18 m
`RELACAO_CREDORES_PUBLICADA` | P1 | 6–18 m
`RMA_JUNTADO` | P1–P2 | contínuo
`AUTO_ARRECADACAO_JUNTADO` | P2 | 3–12 m
`LAUDO_AVALIACAO_JUNTADO` | P2 | 2–9 m
`PLANO_APRESENTADO` | P3 | 2–8 m
`PLANO_COM_UPI` (derivado, por leitura) | P3 | 2–8 m
`AGC_CONVOCADA` / `AGC_REALIZADA` | P3 | 1–6 m
`PLANO_HOMOLOGADO` | P3 | 1–6 m
`AUTORIZACAO_ART_66` | P3 | 1–4 m
`FALENCIA_DECRETADA` / `CONVOLACAO` | P2–P3 | 3–12 m
`LEILOEIRO_NOMEADO` | P3 | 1–3 m
`LEILAO_DESIGNADO` | P3–P4 | 15–90 d
`EDITAL_PUBLICADO` | P4 | 15–60 d
`PRACA_REALIZADA` / `LOTE_DESERTO` | P4–P5 | —
`ARREMATACAO_HOMOLOGADA` / `ANULADA` | P5 | —

Cada evento carrega `Evidencia` e entra na linha do tempo do `Procedimento`.

## 4. Máquina de estados do procedimento concursal

```
                      ┌──────────────┐
   PEDIDO ───────────►│  PROCESSAMENTO│──► RELACAO_CREDORES ──► PLANO_APRESENTADO
      │               │   DEFERIDO   │                                │
      │ indeferido    └──────────────┘                                ▼
      ▼                                                            AGC
   ARQUIVADO                                                          │
                                        ┌────────────────────┬────────┴──────────┐
                                        ▼                    ▼                   ▼
                                  PLANO_APROVADO      PLANO_REJEITADO      CONVOLACAO
                                        │                    │              EM FALENCIA
                                        ▼                    └───────────────────┤
                                  EM_CUMPRIMENTO                                 ▼
                                        │                                   ARRECADACAO
                     ┌──────────────────┼──────────────────┐                     │
                     ▼                  ▼                  ▼                     ▼
              ALIENACAO_UPI      DESCUMPRIMENTO       ENCERRADA              ALIENACAO
              (art. 60/66)              │                                (art. 141/142/144/145)
                     │                  ▼                                        │
                     └──────────► CONVOLACAO ◄───────────────────────────────────┘
```

Transições ilegais são erro de execução (invariante testada). A máquina de estados é o
que permite ao Batedor saber **o que esperar em seguida** e priorizar a coleta.

## 5. Máquina de estados da oportunidade

```
DETECTADA → QUALIFICADA → PRECIFICADA → [portões L6] → PROMOVIDA → EM_DD
   → APROVADA_COMITE → LANCE_AUTORIZADO → {ARREMATADA | PERDIDA | DESERTA}
   → POS_ARREMATACAO → SAIDA_REALIZADA
   (qualquer estado) → DESCARTADA(motivo) | BLOQUEADA_COMPLIANCE(motivo)
```

`DESCARTADA` guarda o motivo e o score no momento do descarte: descartes são dado de
treino tão valioso quanto arremates.

## 6. Resolução de identidade

Ordem de precisão decrescente, com `blocking` para escalar:

| Entidade | Chave forte | Chave fraca (exige confirmação) |
|---|---|---|
`Procedimento` | número CNJ | partes + vara + valor |
`Devedor` PJ | CNPJ | razão social normalizada + UF |
`Imóvel` | matrícula + CNS do registro | inscrição imobiliária; endereço normalizado + área |
`Veículo` | chassi/RENAVAM | placa |
`Máquina` | nº de série + fabricante | descrição + modelo |
`Ator` | CPF/CNPJ/OAB/matrícula de leiloeiro | nome normalizado + tribunal |

Fusão com confiança `< 0,9` vai para fila de revisão humana. **Nunca** se funde
automaticamente devedor PF por homonímia.

## 7. Dicionário monetário e temporal

- Todo valor é `Money(centavos: int, moeda: str)` — nunca `float`.
- Todo valor histórico carrega `data_base` e é corrigido por índice explícito
  (`IPCA`, `INCC`, `IGP-M`, `SELIC`) declarado no cálculo — comparar R$ de 2019 com R$ de
  2026 sem correção é o erro silencioso mais comum deste domínio.
- Toda data tem fuso e distingue `data_publicacao`, `data_disponibilizacao` e
  `data_evento` (diferença que muda prazo processual).
