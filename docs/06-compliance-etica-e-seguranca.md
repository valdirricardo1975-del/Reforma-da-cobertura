# 06 — Compliance, ética profissional e segurança

> Um agente de originação de ativos judiciais **dentro de um escritório de advocacia
> especializado em insolvência** tem um risco que nenhum concorrente tem: a
> possibilidade de misturar informação obtida no exercício profissional com decisão de
> investimento próprio. Resolver isso em código, e não em política, é ao mesmo tempo
> obrigação e diferencial comercial (dossiê auditável de origem da informação).

Este documento é requisito funcional, não anexo. A camada L6 **bloqueia**.

## 1. Portão 1 — Impedimentos legais de arrematar

Verificação automática, por lote, antes de qualquer exibição:

| Verificação | Regra |
|---|---|
| **Advogado da causa** | Advogados que atuam ou atuaram no processo (e seus escritórios) não podem arrematar bens naquele processo, sob pena de nulidade e sanção ético-disciplinar. → cruzar o `numero_cnj` do lote com a base de processos do escritório (todas as OABs, todos os sócios e associados) |
| **Auxiliares da Justiça** | Art. 497, III, do Código Civil veda a aquisição, ainda que em hasta pública, por juízes, secretários de tribunal, árbitros, peritos e outros serventuários ou auxiliares da Justiça, quanto aos bens sobre que se litigar em juízo de que sirvam. → checar se qualquer pessoa vinculada ao veículo de aquisição ocupa tais funções |
| **Art. 141, § 1º, da LFR** | Na falência, a blindagem sucessória **não** se aplica a arrematante sócio, parente ou agente do falido. → é impedimento econômico e sinalizador de fraude |
| **Impedimentos do edital** | Restrições específicas declaradas no instrumento |
| **Administrador judicial e equipe** | Se o escritório atua como AJ no procedimento, aquisição está fora de questão |

Resultado possível: `BLOQUEADA_COMPLIANCE(motivo, evidência)`. Bloqueio é **definitivo
e visível** — não é filtro silencioso, porque a ausência inexplicada de um lote no feed
é, ela mesma, um risco de decisão.

## 2. Portão 2 — Muralha ética em código (ADR-0009)

Toda `Evidencia` carrega `origem`:

| `origem` | Significado | Pode alimentar o pipeline de investimento? |
|---|---|---|
| `PUBLICA` | fonte pública/oficial acessível a qualquer pessoa | **Sim** |
| `CLIENTE` | obtida em razão de relação com cliente ou de peça sob sigilo | **Nunca** |
| `RELACIONAMENTO` | comunicação privada de terceiro (AJ, credor, colega) | **Não**, sem autorização formal registrada |
| `INTERNA` | análise produzida por nós a partir de dado `PUBLICA` | Sim, herdando a origem mais restritiva das entradas |

Implementação:
- `origem` é **propagada por herança**: qualquer derivação assume a origem mais
  restritiva das suas entradas (rótulo "pegajoso");
- o cálculo de score chama `assert_origem_publica(evidencias)` — violação levanta
  exceção, não aviso;
- lote tocado por evidência não pública entra em **quarentena**, com registro de
  auditoria, e só sai por decisão humana documentada (ex.: o mesmo fato apareceu depois
  em fonte pública — e então a evidência pública substitui a restrita);
- relatório periódico de quarentenas para o comitê de ética do escritório.

Efeito colateral valioso: podemos **provar** que a decisão se sustentou apenas em
informação pública. Nenhum concorrente pode oferecer isso a um investidor.

## 3. Portão 3 — Conflito de interesses e concorrência com o cliente

- Cruzamento do devedor/grupo e dos credores do lote com a base de clientes e de
  partes adversas do escritório;
- classificação em `SEM_CONFLITO`, `CONFLITO_POTENCIAL` (vai para decisão humana) e
  `CONFLITO_DIRETO` (bloqueio);
- registro de que a oportunidade **não** estava sendo perseguida por cliente do
  escritório na mesma matéria, quando aplicável.

## 4. LGPD e postura frente à ANPD

Contexto: a ANPD colocou **raspagem de dados** no topo da sua agenda de fiscalização
para 2025–2026, e a jurisprudência reafirma que dado público não é dado livre —
finalidade, necessidade e transparência continuam exigíveis.

Nossas regras:

| Princípio | Como cumprimos |
|---|---|
| **Finalidade** | propósito declarado e restrito: análise de oportunidade de aquisição de ativos em alienação judicial |
| **Necessidade / minimização** | pessoa física entra apenas para resolução de identidade e verificação de impedimento; nada de perfilamento de indivíduos |
| **Base legal** | dados de processo público + legítimo interesse, com teste de proporcionalidade documentado; nunca dado sensível |
| **Pseudonimização** | CPF e nome de PF cifrados/segregados; tabelas analíticas usam identificador interno |
| **Retenção** | política por tipo de dado; expurgo automático de PF não necessária |
| **Transparência** | inventário de fontes e finalidades disponível; registro de operações de tratamento |
| **Segurança** | cifragem em repouso e em trânsito, acesso por papel, log de acesso |
| **Segredo de justiça** | exclusão automática e expurgo registrado |

## 5. Termos de uso e propriedade intelectual das fontes

- Preferência absoluta por fonte oficial (doc 05, § 5);
- **não raspar agregadores concorrentes** — além do risco contratual, é dependência de
  base alheia, o oposto da nossa tese;
- respeitar bloqueio técnico e `robots.txt`; nunca contornar captcha ou autenticação;
- guardar, por fonte, a avaliação de postura (semáforo) e a data da última revisão;
- conteúdo de terceiros é usado como **evidência citada**, não republicado em massa.

## 6. Segurança da informação

- Segredos em gerenciador dedicado (nunca no repositório); `.env` fora do versionamento;
- separação de ambientes (dev com *fixtures*, produção com dados reais);
- *object storage* de snapshots com versionamento e WORM, cifrado;
- log de auditoria *append-only* (quem consultou qual oportunidade, quem aprovou o quê);
- backup testado com restauração periódica — dossiê perdido é decisão perdida;
- princípio do menor privilégio para chaves de API de provedores processuais.

## 7. Limites de autonomia (repete ADR-0008 porque importa)

O sistema **não**: dá lance, assina proposta, contata AJ/leiloeiro/credor, transfere
recursos, publica nada em nome do escritório. Recomendação e teto de lance são insumos
de decisão humana, registrada em ata do comitê, com o dossiê e sua procedência anexados.

## 8. Antes da Fase 1 (pendências que exigem decisão humana)

1. **Veículo de aquisição:** quem compra? O escritório não deveria arrematar em nome
   próprio; definir estrutura (holding, fundo, clube de investidores, cliente) e a
   separação formal em relação à atividade advocatícia. → questão para os sócios.
2. **Parecer interno** sobre aquisição de ativos em procedimentos concursais por
   estrutura ligada a escritório atuante na matéria — abrangendo Estatuto da OAB,
   Código de Ética e o art. 497 do Código Civil.
3. **Política de quarentena** e composição do comitê que decide sobre casos
   `CONFLITO_POTENCIAL`.
4. **Base de processos do escritório** disponível para cruzamento automático (é o
   insumo do Portão 1; sem ela o portão não funciona).
