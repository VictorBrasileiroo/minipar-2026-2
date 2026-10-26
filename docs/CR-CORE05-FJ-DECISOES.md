# CR-CORE05-FJ-DECISOES — 26/10/2026

Estado: decisões de implementação do Eixo A autorizadas nesta manutenção do PR #15;
ratificação por A/C na revisão de integração pendente. Não modifica nem congela
`docs/02_CONTRATOS_TECNICOS.md`, assinaturas de runtime, AST ou envelopes C-WEB.
Referência vigente consultada: C-FJ-v1 proposta revisão 2 de `origin/dev` em
`84934b96299337ed140a29678cec083a566a780a`, PR #7 já integrado, com #8/#9.

| Item | Antes | Decisão aplicada/proposta e consumidor |
|---|---|---|
| PEND-FJ-06 | IO dentro de tarefa permitido sem decisão | Aplicado: input/c_channel/send/receive rejeitados por FJ-SEM-05, também transitivamente. A escolha conservadora é delegada a A pela §2.2.5; print continua permitido no stdout do worker |
| PEND-FJ-07 | none ora usado em aritmética, ora rejeitado | Aplicado: join de resultado void/none conhecido só como comando; qualquer uso como valor recebe FJ-SEM-06. O runtime continua transportando none; não há backend novo |
| join genérico | var desconhecido rejeitado como se fosse tipo inválido | Aplicado: var/unknown sem prova entra em unresolved_fj; tipo conhecido não-task ou alternativa conhecida não-task é rejeitado. Ausência de erro não é prova de segurança |
| Handle descartado | fork como comando aceito sem decisão | Aplicado em A: rejeitar fork usado como comando (FJ-SEM-03), exigindo guardar o handle para join. O parser continua aceitando a produção; o erro é semântico. Ratificar a restrição no contrato antes de integrar; não foi acrescentado código diagnóstico público novo |
| Handles sem join em todos os fluxos | Sem análise de consumo | Continua parcial: não há prova de uso único, todos os caminhos ou vida do handle. CORE-07/runtime deve tratar a vida das tarefas reais; não presumir que armazenar garante coleta |
| Assinaturas desconhecidas/múltiplas | Assinaturas genéricas da declaração misturadas às chamadas | Aplicado: assinaturas provisórias ficam separadas; só entram no mapa final quando não há chamada especializada do mesmo fork. Chamadas realmente genéricas continuam unknown. Todas as assinaturas reais distintas são preservadas |
| PEND-FJ-02 / CORE-07 | Despacho Value ou rejeição à escolha de A | Proposta conservadora para CORE-07: agrupar todos os pontos por função global e rejeitar assinatura não comprovada ou várias assinaturas incompatíveis até implementar despacho tipado com testes. Não escolher o último item. Este PR não implementa wrappers, conversões number→int/float, TAC ou C++ FJ |

Motivo: corrigir os achados independentes de Erasmo e Riquelme, evitar stdin/canais
sem par no worker e impedir que inferência parcial seja apresentada como execução
segura. Fornecedor A, consumidores C/runtime, CORE-06/07 e testes 8–10; B/C-WEB
consome diagnósticos reais, sem mudança de envelope nesta manutenção.

Migração: revisar estas escolhas com A/C, registrar aprovação contratual explícita
e manter programas que dependam de IO em tarefa ou descarte de handles bloqueados.
Os casos de declaração genérica sem chamada não são prova para gerar wrappers.
Se a ratificação exigir mudança no contrato congelado, aplicar versão/CR antes de
integrar, preservando esta decisão e os testes como histórico. Não há aprovação
de PR nem merge automatizado nesta execução.

Testes: `verify_core0405.py` incorpora `test_review_regressions.py`: iteradores,
atribuições/concatenações/helpers, herança/ciclos/sombreamento, recursão/métodos,
cache por tipo/isolamento, diagnósticos, IO, none, descarte e assinaturas. Comandos,
resultados e limites completos no handoff CORE-04-05. Revisar antes de CORE-06/07.
