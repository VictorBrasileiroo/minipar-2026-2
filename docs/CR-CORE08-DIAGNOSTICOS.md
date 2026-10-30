# CR-CORE08-DIAGNOSTICOS — proposta mínima, 30/10/2026

**Estado: PROPOSTA, não aprovada e não aplicada ao catálogo C-WEB.** Fornecedor A; consumidor José Riquelme/B. O pedido do coordenador autoriza implementar o CORE-08 localmente, sem congelar CON-02 nem inferir aprovação desta CR.

## Contrato anterior e lacuna

C-WEB-v1 §1.5 só permite os códigos enumerados. A base `29cff941` já possui erros esperados sem código compatível: FJ-SEM-01 a 08; nome nativo reservado; herança cíclica; listas de strings e indexação de strings não suportadas. TAC recusa Fork/Join com `NotImplementedError` enquanto CORE-06 não está integrado. O backend tem recusa equivalente até CORE-07. São recusas esperadas, não `INTERNAL_ERROR`. O tipo semântico `task` também não consta da lista fechada de tipos publicada por C-WEB-v1.

## Proposta v1.1, sujeita a A+B

Manter envelopes, funções e regras de fases. Acrescentar ao catálogo: `SEM_FJ_01` a `SEM_FJ_08` para as regras homônimas, `SEM_RESERVED_NAME`, `SEM_INHERITANCE_CYCLE`, `SEM_UNSUPPORTED_FEATURE`, `TAC_UNSUPPORTED_FEATURE`, `CPP_UNSUPPORTED_FEATURE`. Os dois últimos incluem a dependência ausente na mensagem. Incluir `task` nos tipos publicados; confirmar publicação genérica dos nós `ForkExpr` e `JoinExpr` já prevista no §1.4.

SEM_TYPE_MISMATCH continua cobrindo incompatibilidade real de tipos, inclusive argumento nativo incompatível e comparação/concatenação entre string e outro tipo. SEM_ARITY cobre aridade nativa. Nenhuma recusa por recurso ausente é reclassificada como incompatibilidade de tipos.

## Comportamento local enquanto pendente

Erros cobertos publicam diagnóstico estruturado diretamente do ponto de detecção. Os demais continuam acumulados em `SemanticAnalyzer.diagnostics` com `code=None`, disponíveis à inspeção local. O serviço interrompe a fase com `status=error`, preserva escopos/símbolos e **não publica** esses itens sem código aprovado. Assim, pode haver fase com erro e `diagnostics=[]`; é uma limitação explícita da entrega PARTIAL, inadequada para considerar concluída a apresentação de todos os erros da Web. Não se acrescentou campo ao envelope nem código ao catálogo. A guarda TAC encerra antes de C++/G++, sem contornar a dependência.

O símbolo `task` observado em programas FJ permanece a informação real do semântico; sua publicação está pendente de ratificação v1.1. B deve restringir a homologação atual aos programas sem FJ suportados e exibir estado genérico de fase com erro quando não houver diagnóstico. Não interpretar ausência de diagnóstico como sucesso.

## Migração, testes e aceite

Após aprovação A+B, atribuir os novos códigos nos pontos de detecção, publicar os itens hoje omitidos, atualizar catálogo e fixtures por revisão controlada e testar negativos FJ, recursos não suportados e tipos. Após integração de #17/#18, revalidar todo o pipeline FJ na base integrada, ajustando `generate_text` à assinatura entregue pelo CORE-07; não incorporar commits informalmente.

Consumidores: WEB-03/04, CORE-08/09, inspeção didática de TAC/FJ. Revisores necessários: coordenador A e Riquelme B, com consulta C para os significados FJ. Sem mudança de runtime ou linguagem. Testes atuais e comandos estão no handoff CORE-08; a aprovação humana continua pendente.
