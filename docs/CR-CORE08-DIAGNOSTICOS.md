# CR-CORE08-DIAGNOSTICOS — proposta mínima, 30/10/2026

**Estado atual (registro REL-PRE, 09/11/2026): RATIFICADA no PR [#34](https://github.com/VictorBrasileiroo/minipar-2026-2/pull/34), mergeado em 05/11/2026.** Proposta do consumidor José Riquelme/B; aprovações de Erasmo/C e Victor/A sobre `204fe48`. Ver quadro atualizado em [contratos §1.12](02_CONTRATOS_TECNICOS.md) e [evidência GitHub](auditorias/REL-PRE_GITHUB.json). Envelopes e APIs permanecem iguais; ressalvas de rastreabilidade FJ-SEM-06/07/08 preservadas na review. Nenhuma nova regra é ratificada por esta atualização.

**Histórico da proposta, preservado abaixo:** antes do #34, a autorização de implementação local não equivalia à aprovação contratual. As menções abaixo a ratificação pendente descrevem esse estágio, já superado pelas aprovações citadas.

## Contrato anterior e lacuna

> Integração técnica local de 05/11/2026, sem ratificação: CORE-06/07 presentes
> permitem FJ válido pela CLI/API. `CPP_UNSUPPORTED_FEATURE` agora também cobre
> `CppProofError` real (representação/retorno não comprovados), com a linha do
> prefixo explícito `CORE-07 linha N:`. Sem código novo, inferência de localização
> ou alteração do envelope. `TAC_UNSUPPORTED_FEATURE` segue cobrindo recusas
> reais do TAC. Proposta e publicação do tipo task continuam dependentes de A+B.
> Evidências e limites: [integração CORE-07](auditorias/CORE-07_INTEGRACAO_DEV.md).

C-WEB-v1 §1.5 só permite os códigos enumerados. A base `29cff941` já possui erros esperados sem código compatível: FJ-SEM-01 a 08; nome nativo reservado; herança cíclica; listas de strings e indexação de strings não suportadas. TAC recusa Fork/Join com `NotImplementedError` enquanto CORE-06 não está integrado. O backend tem recusa equivalente até CORE-07. São recusas esperadas, não `INTERNAL_ERROR`. O tipo semântico `task` também não consta da lista fechada de tipos publicada por C-WEB-v1.

## Proposta v1.1, sujeita a A+B

Manter envelopes, funções e regras de fases. Acrescentar ao catálogo: `SEM_FJ_01` a `SEM_FJ_08` para as regras homônimas, `SEM_RESERVED_NAME`, `SEM_INHERITANCE_CYCLE`, `SEM_UNSUPPORTED_FEATURE`, `TAC_UNSUPPORTED_FEATURE`, `CPP_UNSUPPORTED_FEATURE`. Os dois últimos incluem a dependência ausente na mensagem. Incluir `task` nos tipos publicados; confirmar publicação genérica dos nós `ForkExpr` e `JoinExpr` já prevista no §1.4.

SEM_TYPE_MISMATCH continua cobrindo incompatibilidade real de tipos, inclusive argumento nativo incompatível e comparação/concatenação entre string e outro tipo. SEM_ARITY cobre aridade nativa. Nenhuma recusa por recurso ausente é reclassificada como incompatibilidade de tipos.

## Comportamento local enquanto pendente — revisão 03/11/2026

**PROPOSTA; DEPENDENTE DE RATIFICAÇÃO A+B.** A revisão de Riquelme no PR #19
em 03/11 solicitou corrigir fases com error e diagnostics=[] e anunciou que revisaria
esta CR. Isso não é aprovação. Não foi encontrada decisão A+B posterior na discussão
consultada; a busca de PRs pela identificação exata da CR só retornou #19.

O comportamento inicial omitindo itens sem código está documentado no histórico do
handoff. A correção agora preparada LOCALMENTE atribui os códigos propostos nos
pontos de detecção e conserva todos os diagnósticos semânticos, mensagem e linha.
Não se usa code=null como solução: o catálogo fechado não autoriza esse valor.

Nos quatro casos da revisão: SEM_RESERVED_NAME/linha 1,
SEM_UNSUPPORTED_FEATURE/linha 2, SEM_FJ_07/linha 2 e
TAC_UNSUPPORTED_FEATURE/linha 3. A guarda TAC identifica o JoinExpr na linha 3;
não foi alterado seu percurso nem implementado CORE-06. A guarda C++ equivalente
permanece, com CPP_UNSUPPORTED_FEATURE na captura do serviço. A linha vem do
prefixo explícito da exceção existente; sem localização, line=null e column=null,
sem presumir Fork/Join para outras recusas. Mensagem separada do prefixo Linha N:
conforme §1.5. Nenhum campo novo no envelope.

Também foram codificadas as demais detecções existentes sem código:
SEM_FJ_01, 03, 04, 05, 06, 08, SEM_INHERITANCE_CYCLE e
SEM_UNSUPPORTED_FEATURE para listas de strings. SEM_FJ_02 continua apenas proposto:
a detecção de aridade FJ já usa SEM_ARITY, vigente, e foi preservada.
Nenhuma regra de linguagem ou especialização foi alterada. O símbolo task continua
real e ainda pendente de ratificação. O serviço local usa a extensão proposta, não
é compatível com o catálogo v1 estrito para esses erros e não está autorizado para publicação.

Os testes novos estão em ProposedDiagnosticsTests, identificados como pendentes de
ratificação. PASS demonstra o comportamento técnico proposto; não valida aceite
contratual. FIX-01–04 e seus oráculos permanecem intactos. O teste antigo de símbolos
especializados só teve sua expectativa obsoleta de diagnostics=[] substituída por
uma asserção explicitamente provisória; nenhuma ampliação silenciosa do catálogo.

## Migração, testes e aceite

Após aprovação A+B, conferir a implementação local contra a versão ratificada, atualizar o catálogo por revisão controlada e revalidar negativos FJ, recursos não suportados e tipos. Não atualizar fixtures apenas para acomodar divergências. Após integração de #17/#18, revalidar todo o pipeline FJ na base integrada, ajustando `generate_text` à assinatura entregue pelo CORE-07; não incorporar commits informalmente.

Consumidores: WEB-03/04, CORE-08/09, inspeção didática de TAC/FJ. Revisores necessários: coordenador A e Riquelme B, com consulta C para os significados FJ. Sem mudança de runtime ou linguagem. Testes atuais e comandos estão no handoff CORE-08; a aprovação humana continua pendente.
