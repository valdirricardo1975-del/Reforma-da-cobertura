# 00 — Pesquisa de mercado: quem já faz isso, como faz, e onde estão as lacunas

> Status: concluída em 12/09/2026. Base para as decisões de arquitetura (doc 02).
> Marcadores `⚠ verificar` indicam afirmação que precisa de confirmação em fonte
> primária antes de virar regra de código (ver doc 07, checklist de validação).

## 1. Método e limites desta pesquisa

Levantamento feito por busca web em 12/09/2026, cobrindo: (a) agregadores de leilão
brasileiros, (b) plataformas de leiloeiros, (c) provedores de dados processuais,
(d) gestoras de ativos estressados, (e) comparáveis internacionais, (f) marco
regulatório vigente.

**Limite relevante do ambiente:** o sandbox onde este repositório é desenvolvido tem
egresso de rede restrito por política — domínios `*.jus.br`, sites de leiloeiros e
portais imobiliários estão bloqueados. Consequência arquitetural (não acidental):
os coletores precisam ser desenhados para rodar no ambiente do escritório, e o
desenvolvimento aqui se dá contra *fixtures* (amostras reais salvas) com testes
determinísticos. Isso é boa prática de qualquer forma — ver ADR-0006.

## 2. Mapa do mercado

### Grupo A — Agregadores de leilão para investidor (varejo/semi-profissional)

| Player | O que faz | Inteligência declarada |
|---|---|---|
| **LeilôAI** | Agregador que declara 1.300+ fontes | `Radar Judicial` (monitoramento em tempo real), `Lance Justo` (lance recomendado), `Nota de Oportunidade` 0–100 (>70 oportunidade, 40–69 investigar, <40 risco alto), estimativa de rendimento de aluguel |
| **Radar Leilão** | Busca e "inteligência" sobre leilões de leiloeiros, bancos, tribunais e portais | Normalização e comparação de oportunidades |
| **Núcleo Leilões** | 70 mil+ imóveis: judiciais, extrajudiciais, trabalhistas, retomados, venda direta Caixa | Filtros para "investidor profissional" |
| **Zuk / Portal Zuk** | Agregador gratuito, 30 mil+ imóveis | Pesquisa/filtro/comparação |

**Padrão comum e limitação estrutural:** todos operam na **camada do edital** — o dado
entra no sistema quando o leilão *já é público*. O universo é essencialmente
**imóveis** (mais veículos). O deságio é medido contra o **valor de avaliação do laudo**,
que é justamente a variável mais frágil do processo (laudo desatualizado, feito por
oficial de justiça, ou inflado para sustentar execução). Nenhum diferencia o **regime
jurídico** do ativo: um imóvel de execução fiscal e uma UPI de falência aparecem no
mesmo balaio, apesar de terem perfis de risco incomparáveis.

### Grupo B — Plataformas de leiloeiros (origem do dado, não inteligência)

Sodré Santoro (declara-se a maior da América Latina; seção `/judiciais`),
Superbid Exchange (veículos, máquinas, equipamentos, ativos de empresas —
inclusive vendedores em recuperação judicial, com a condição sinalizada no resumo
do leilão), Zukerman, Mega Leilões, Frazão, Biasi e centenas de leiloeiros
credenciados por tribunal. São **fonte primária**, com HTML heterogêneo e sem API
padronizada. Não produzem análise de oportunidade — produzem oferta.

### Grupo C — Provedores de dados processuais (monitoramento genérico)

| Player | Proposta |
|---|---|
| **Escavador** | API de dados jurídicos; extrai de todos os diários oficiais e tribunais, todas as instâncias; varejo a partir de R$ 9,90/mês |
| **JUDIT** | API de consulta e monitoramento, 90+ tribunais, dados normalizados, webhooks por movimentação |
| **Digesto** | Pesquisa e monitoramento em todos os tribunais, dashboards |
| **Predictus** | API + jurimetria/predição |
| **Kurier** | Captura de movimentações em 1ª e 2ª instância **antes da intimação oficial** |
| **Sonar / Monitor de Falências e RJs** | Acompanha diariamente novos pedidos de falência e RJ em tribunais de todo o país; cruza dados societários, patrimoniais, financeiros |
| **Processei.ia** | Monitoramento de 57+ tribunais, prazos, petições |

**Padrão comum:** vendem *encanamento* (movimentação processual normalizada e alerta).
Nenhum avalia **ativo**, nenhum precifica **oportunidade de aquisição**, nenhum modela
**risco de desfazimento da arrematação**. O Monitor de Falências chega perto na
detecção de RJ/falência, mas para na notícia — não desce ao ativo.

### Grupo D — Especialistas em ativos estressados (tese sem máquina de originação)

Jive Investments (pioneira e maior independente; nasceu da carteira do Lehman
Brothers no Brasil em 2010), Starboard Partners (equity/híbrido, dívida nova,
compra de dívida no secundário, DIP), além de Mav, Canvas, Prisma e dezenas de
fundos — o mercado virou "indústria", com 6,3 mil+ empresas em RJ no 1º semestre
de 2026. Assessores e administradores judiciais (Alvarez & Marsal, Deloitte,
Laspro, Brasil Trustee, Nexus e outros) detêm o dado bruto. Estruturadores como
**Save Asset Intelligence** se posicionam em estruturação de ativos em RJ e falência.

**Padrão comum:** a originação é **relacional e manual** — telefone, relacionamento com
AJ, banco de investimento, sell-side process. Escala limitada pela agenda de pessoas.
É exatamente aqui que um agente de software cria vantagem desproporcional.

### Grupo E — Comparáveis internacionais (o que o Brasil ainda não tem)

| Player | Lição transferível |
|---|---|
| **Xclaim** | Marketplace/corretora de *bankruptcy claims*: 10 mil+ credores, ~US$ 1 bi liquidado, dados de mercado em tempo real e motor de *matching* |
| **Claims Market (Cherokee Acquisition)** | US$ 883,9 milhões em 740 transações de venda de créditos concursais |
| **Reorg / Debtwire** | Inteligência de reestruturação assinada por credores institucionais |
| **Ten-X / Auction.com / Xome** | Leilão de imóveis com precificação e dados padronizados |
| **PropStream / RealtyTrac** | Dados de *foreclosure* + AVM + filtros de investidor |
| **Stretto / Epiq / Kroll Restructuring** | *Claims agents*: publicam listas de credores e documentos **estruturados** por caso |

O diferencial estrutural dos EUA são duas camadas que o Brasil não tem: **(i)** dados de
caso estruturados (PACER + claims agents) e **(ii)** um mercado secundário líquido de
créditos concursais. No Brasil, essas duas camadas precisam ser *construídas*. Quem
construir primeiro a camada estruturada de casos concursais tem a originação.

## 3. As sete lacunas que ninguém cobre bem hoje

1. **Todos começam no edital.** O ciclo concursal emite sinais 3 a 18 meses antes do
   edital (deferimento do processamento, relatórios do AJ, plano com UPI, autorização
   do art. 66, auto de arrecadação, nomeação de leiloeiro, juntada de laudo). Ninguém
   monta o funil a montante.
2. **Deságio medido contra o laudo, não contra valor de mercado defensável.** O laudo é
   ruidoso; o deságio "de vitrine" pode ser ilusório ou, ao contrário, subestimado.
3. **Regime jurídico ignorado.** Ativo vendido em falência (art. 141, II, LFR) e UPI em
   RJ (art. 60, § 1º) transferem-se **sem sucessão nas obrigações do devedor, inclusive
   tributárias e trabalhistas** — constitucionalidade confirmada pelo STF na ADI 3.934.
   Isso é um perfil de risco radicalmente diferente do leilão de execução comum. Nenhum
   agregador pontua isso.
4. **Risco processual não é modelado.** Probabilidade de o leilão ocorrer na data, de
   vício de intimação (art. 889, CPC) gerar invalidação (art. 903, § 1º), de agravo
   suspender a praça, de o laudo ser impugnado — tudo fica por conta do investidor.
5. **Monoclasse.** O acervo concursal é multiativo: imóveis urbanos e rurais, plantas
   industriais, máquinas, estoques, frotas, marcas e IP, carteiras de recebíveis,
   participações, precatórios, créditos fiscais, direitos litigiosos e a própria UPI
   como *going concern*. As plataformas cobrem imóvel e veículo.
6. **Rota de acesso única.** Todos assumem "dar lance no leilão". Frequentemente a
   melhor rota é comprar o crédito concursal com deságio, financiar DIP, ser
   *stalking horse* de uma UPI, propor venda direta (arts. 144/145, LFR) ou adjudicar.
7. **Competição não é prevista.** Ninguém estima *quantos e quais* players vão disputar
   o lote — o que determina o preço de fechamento e, portanto, se vale entrar.

## 4. O fato regulatório que muda o jogo: Provimento CN-CNJ 255/2026 e a PNAJ

Em **19/08/2026** a Corregedoria Nacional de Justiça publicou o **Provimento CN-CNJ
n. 255**, com 119 artigos, consolidando a "Execução Efetiva". O **Livro VII** trata das
alienações judiciais e cria:

- a **PNAJ — Plataforma Nacional de Alienações Judiciais**: ambiente único para
  divulgação, gestão, acompanhamento e realização das alienações judiciais eletrônicas
  do país, com geração automatizada de editais e autos;
- as **Centrais/Centros de Alienação Judicial**, com juízes designados para decidir
  incidentes em sessão;
- **checklist obrigatório de entrada de bens** (Anexo I, ⚠ verificar publicação);
- **credenciamento permanente de 36 meses** e **avaliação de desempenho de leiloeiros**.

Vigência 30 dias após a publicação; **a PNAJ torna-se obrigatória 120 dias após
homologação do CNJ em ato próprio** — homologação ainda não localizada.

**Três implicações estratégicas diretas:**

1. **A amplitude de raspagem deixa de ser fosso competitivo.** Quando a oferta se
   concentra num ambiente único, "agregar 1.300 fontes" vira commodity. O valor migra
   integralmente para (a) originação a montante e (b) análise ajustada a risco.
2. **Surge dado estruturado nacional.** Checklist de entrada de bens + editais gerados
   automaticamente = campos padronizados. Quem tiver o modelo de domínio pronto
   consome no dia 1; quem tiver só *scrapers* de HTML terá que reescrever tudo.
3. **Avaliação de desempenho de leiloeiros vira dado público de qualidade** — insumo
   direto do nosso grafo de atores processuais.

Conclusão: a janela para construir o que os outros não têm é **agora**, e o desenho da
camada de fontes precisa tratar a PNAJ como *um adaptador entre outros*, pronto para
virar o principal (ADR-0002).

## 5. Onde nosso agente será singular

Seis eixos de diferenciação, todos derivados das lacunas acima e da vantagem específica
de um escritório especializado em insolvência:

| # | Eixo | Por que só nós |
|---|---|---|
| 1 | **Originação a montante** (funil P0–P5 do ciclo concursal) | Exige entender o procedimento concursal, não só ler editais |
| 2 | **Blindagem sucessória como dimensão pontuada** | Exige leitura jurídica do plano/decisão/edital, não só do lote |
| 3 | **Motor de risco processual** (P(ocorre), P(anulação), T(posse)) | Exige histórico por vara, por leiloeiro e por tipo de vício |
| 4 | **Valuation multiclasse plugável**, incluindo UPI como *going concern* | Exige modelos por classe de ativo e leitura de demonstrativos do AJ |
| 5 | **Grafo de atores processuais** (AJ, vara, leiloeiro, fundos) | Converte conhecimento tácito do escritório em ativo de dados composto |
| 6 | **Rota de acesso ótima** (lance, crédito, DIP, *stalking horse*, venda direta) | Exige capacidade de estruturação, não de busca |

Além disso, um sétimo eixo que é condição de existência num escritório de advocacia:
**trilha auditável de origem da informação** (muralha ética em código — doc 06). Nenhum
concorrente precisa disso; para nós é obrigatório e, feito bem, vira selo de confiança.

## 6. Fontes consultadas

- [Núcleo Leilões](https://nucleoleiloes.com.br/) · [Radar Leilão](https://radarleilao.com.br/) · [LeilôAI](https://leiloai.com/) · [Portal Zuk](https://www.portalzuk.com.br/) · [Sodré Santoro — judiciais](https://www.sodresantoro.com.br/judiciais) · [Superbid Exchange](https://exchange.superbid.net/)
- [Escavador API](https://www.escavador.com/business/api) · [JUDIT — planos de API](https://judit.io/planos-api/) · [JUDIT — comparativo de APIs de consulta processual](https://judit.io/blog/api-judit/api-consulta-processual-monitoramento-processual-fornecedores-brasil-escavador-api/) · [Predictus API](https://predictus.inf.br/predictus-api/) · [Kurier](https://www.kuriertecnologia.com.br/) · [Processei.ia](https://processei.ia.br/)
- [Xclaim](https://www.x-claim.com/) · [Xclaim — Série A US$ 7M](https://finance.yahoo.com/news/bankruptcy-trading-platform-xclaim-closes-130000228.html) · [Claims Market (Cherokee)](https://claims-market.com/) · [Claim Liquid — mercado de claims](https://claimliquid.com/bankruptcy-claims-trading-market)
- [Jive Investments (XP — Indo a Fundo no Outliers)](https://conteudos.xpi.com.br/fundos-de-investimento/relatorios/jive-fundo-credito-dificuldade/) · [Starboard Partners](https://www.starboardpartners.com.br/en) · [Exame — RJ vira "indústria" e atrai dezenas de fundos](https://exame.com/invest/mercados/recuperacao-judicial-vira-industria-e-atrai-dezenas-de-fundos-no-brasil/) · [NeoFeed — reestruturação de dívida](https://neofeed.com.br/negocios/reestruturacao-de-divida-deixa-de-ser-patinho-feio-do-mercado/)
- [TMA Brasil — venda judicial de ativos na recuperação](https://www.tmabrasil.org/blog-tma-brasil/noticias-em-geral/venda-judicial-de-ativos-na-recuperacao) · [Migalhas — a venda de ativos na falência e na RJ](https://www.migalhas.com.br/coluna/novos-horizontes-do-direito-privado/381630/a-venda-de-ativos-na-falencia-e-na-recuperacao-judicial) · [Legale — UPIs e venda de ativos blindada](https://legale.com.br/blog/recuperacao-judicial-upis-e-venda-de-ativos-blindada/)
- [Migalhas — Nova arquitetura nacional das alienações judiciais](https://www.migalhas.com.br/depeso/463202/nova-arquitetura-nacional-das-alienacoes-judiciais-avancos-e-desafios) · [Migalhas — Provimento 255/CNJ](https://www.migalhas.com.br/depeso/463465/provimento-255-cnj-a-resposta-do-poder-judiciario-a-crise) · [Colégio Registral RS — Provimento CN-CNJ 255/2026](https://colegioregistralrs.org.br/noticias/21328/provimento-cn-cnj-n-255-de-19-de-agosto-de-2026/) · [TMLAdv — PNAJ](https://tmladv.com.br/blog/plataforma-nacional-alienacoes-judiciais/) · [CNJ — alienação judicial eletrônica](https://www.cnj.jus.br/conselho-regulamenta-alienacao-judicial-eletronica-conforme-novo-cpc/) · [CNJ — política para localizar bens de devedores](https://www.migalhas.com.br/quentes/463933/cnj-cria-politica-para-acelerar-execucao-e-localizar-bens-de-devedores)
- [Datajud-Wiki — API Pública](https://datajud-wiki.cnj.jus.br/api-publica/) · [CNJ — DataJud](https://www.cnj.jus.br/sistemas/datajud/) · [API do DJEN](https://chatjuridico.com.br/api-do-djen-consulta-oficial-cnj/)
- [STJ — vedação ao preço vil na alienação por iniciativa particular](https://www.stj.jus.br/sites/portalp/Paginas/Comunicacao/Noticias/2023/26092023-Vedacao-ao-preco-vil-tambem-se-aplica-a-alienacao-do-bem-por-iniciativa-particular.aspx) · [Migalhas — preço vil e laudo defasado](https://www.migalhas.com.br/depeso/457398/preco-vil-e-laudo-defasado-o-stj-alem-dos-50) · [ConJur — preço vil em leilões extrajudiciais](https://conjur.com.br/2025-nov-11/tirania-do-preco-vil-em-leiloes-extrajudiciais-encontra-seu-fim-stj-consolida-a-protecao-do-devedor-fiduciante/)
- [Rota Jurídica — quem não pode arrematar em leilão judicial](https://www.rotajuridica.com.br/artigos/quem-nao-pode-arrematar-em-leilao-judicial/) · [Grant Thornton — raspagem de dados na agenda da ANPD](https://www.grantthornton.com.br/insights/artigos-e-publicacoes/raspagem-de-dados-entenda-a-nova-prioridade-da-anpd-e-seus-efeitos/) · [Souto Correa — raspagem sob LGPD/RGPD](https://www.soutocorrea.com.br/artigos/voce-e-um-robo-a-raspagem-de-dados-sob-a-otica-da-lgpd-e-do-rgpd/)
- [Urbit AVM](https://urbit.com.br/produtos/avm) · [DataZAP](https://www.datazap.com.br/) · [Índice FipeZAP](https://www.fipe.org.br/pt-br/indices/fipezap/)
