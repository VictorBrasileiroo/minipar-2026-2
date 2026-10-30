# CR-CORE05-FJ-DECISOES — 26/10/2026

Estado: decisões de implementação do Eixo A autorizadas nesta manutenção do PR #15;
ratificação por A/C na revisão de integração pendente. Não modifica nem congela
`docs/02_CONTRATOS_TECNICOS.md`, assinaturas de runtime, AST ou envelopes C-WEB.
Referência vigente consultada: C-FJ-v1 proposta revisão 2 de `origin/dev` em
`84934b96299337ed140a29678cec083a566a780a`, PR #7 já integrado, com #8/#9.

| Item | Antes | Decisão aplicada/proposta e consumidor |
|---|---|---|
| PEND-FJ-06 | IO dentro de tarefa permitido sem decisão | Aplicado: input/c_channel/send/receive rejeitados por FJ-SEM-05, também transitivamente. A escolha conservadora é delegada a A pela §2.2.5; print continua permitido no stdout do worker |
| PEND-FJ-07 | none ora usado em aritmética, ora rejeitado | Aplicado: join de resultado void/none conhecido só como comando; uso como valor recebe FJ-SEM-08 (extensão proposta em 27/10). O runtime continua transportando none; não há backend novo |
| join genérico | var desconhecido rejeitado como se fosse tipo inválido | Aplicado: var/unknown sem prova entra em unresolved_fj; tipo conhecido não-task ou alternativa conhecida não-task é rejeitado. Ausência de erro não é prova de segurança |
| Handle descartado | fork como comando aceito sem decisão | Aplicado em A: rejeitar fork usado como comando (FJ-SEM-07, extensão proposta em 27/10), exigindo guardar o handle para join. O parser continua aceitando a produção; o erro é semântico. Ratificar a restrição e o código novo com A/C antes de integrar |
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

## Revisão de 27/10/2026 — extensão proposta dos diagnósticos

Contrato anterior: C-FJ-v1 §2.2.2 reserva FJ-SEM-03 para join de tipo conhecido
diferente de task; FJ-SEM-06 identifica tipos que não cruzam tarefas (e §2.2.4
também o usa para aritmética de handles). A implementação de 26/10 reutilizava
03 para descarte de handle e 06 para consumo de none. Essa reutilização foi
apontada por Erasmo; a decisão de rejeitar permanece, o identificador muda.

Proposta aplicada somente nesta branch de manutenção, aguardando ratificação A/C:

| Código proposto | Significado exclusivo novo | Identificador anterior na implementação |
|---|---|---|
| FJ-SEM-07 | fork como comando descarta seu handle | FJ-SEM-03 |
| FJ-SEM-08 | join com resultado conhecido none consumido como valor | FJ-SEM-06 |

Não houve colisão de 07/08 na busca do código, testes e documentação do projeto
anterior à extensão. Preservados os significados originais de 03/06, catálogo em
docs/02, estruturas da AST, APIs runtime e envelope Web. A mudança proposta é
aditiva ao catálogo e requer revisão humana explícita de A/C; B/CORE-08 deve ser
consultado sobre a exibição dos novos códigos antes da integração. Não é FROZEN.

Migração: ratificar os identificadores e restrições nesta CR; em atualização
contratual própria acrescentar 07/08 ao catálogo vigente e alinhar fixtures da Web,
sem renomear 03/06. Os testes de descarte/none passam a esperar 07/08; testes de
join numérico/objeto e de transporte continuam esperando 03/06. Sem alteração do
texto contratual compartilhado nesta rodada.

## PEND-FJ-07 / CORE-07 — caminho de retorno implícito

Reprodução mínima preservada:

```minipar
func f(x) { if (x > 0) { return 1; } }
print(join(fork f(0)) + 1);
```

O semântico agrega os returns explícitos, sem grafo de controle ou prova de
retorno em todos os caminhos; atualmente aceita o programa com resultado
inferido number. Não acrescentamos inferência parcial que trate laços/recursão
como prova ou rejeite programas válidos indiscriminadamente nesta manutenção.
Caso conhecido continua pendente de CORE-07/PEND-FJ-07. `measure_final_review.py`
registra aceitação, diagnósticos e tempo; aceitações são KNOWN_LIMITATION, não
PASS funcional. O pipeline atual recusa qualquer FJ antes de TAC/C++, portanto
este caso não produz um binário funcional nesta branch.

Risco futuro: consumir none como número e permitir caminho sem retorno em C++
tipado. Antes de remover a guarda do backend, CORE-07 deve representar todos os
caminhos, recusar consumo potencialmente none ou validar Value em execução com
erro explícito. Critérios: f(0) nunca retorna número inventado nem invoca UB;
f(1) retorna 1; aritmética após f(0) é rejeitada/diagnosticada; join como comando
permanece válido; funções com ambos os ramos retornando número e retorno final
incondicional continuam aceitas. Cobrir laços, recursão e caminhos mistos com
testes nativos reais antes de considerar a pendência resolvida.
