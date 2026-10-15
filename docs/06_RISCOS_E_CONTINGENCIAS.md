# Registro de riscos, gatilhos e planos de contingência

**Uso:** revisar no kickoff e em todos os gates. A ação de contingência deve **preservar requisitos** ou registrar claramente limitações e necessidade de confirmação do professor; não esconder falhas.

| ID | Risco | Probabilidade inicial | Impacto | Gatilho de escalada | Dono | Ação |
|---|---|---|---|---|---|---|
| R01 | Runtime remoto não integra MiniPar | Alta | Crítico | Sem prova em dois hosts até 23/10 | A+C | Congelar novas features, priorizar função mínima exportada com ID e worker pré-compilado |
| R02 | Teste 11 só emite texto ARM inválido | Alta | Crítico | Sem primeiro ARM executado até 23/10 | B | Validar instruções/registros no CPUlator antes de expandir linguagem |
| R03 | Tipo string/coleções inviabiliza T11 | Alta | Alto | MVP não compila após 21/10 | A+B | Reduzir representação do algoritmo a vetores/índices; corrigir builtins mínimos com regressão |
| R04 | Toolchain GCC 6.3 insuficiente | Alta | Alto | Sem G++20 (ou alternativa validada) até 18/10 | A | Usar toolchain isolada compatível, sem alterar ambiente global; não aceitar C++14 hack como entrega sem documentar |
| R05 | TAC fixo do Quicksort | Confirmada | Alto | Mutação T07 ainda igual | A | Implementar gerador real e testes metamórficos |
| R06 | Bug de vetor/stack T07 | Confirmada | Alto | Execução com bounds failure | A | Corrigir lógica do teste/semântica de coleções; executar sanitizer |
| R07 | Web didática depende de API não entregue | Média | Alto | Mock diverge da API real em 24/10 | A+B | Contrato frozen; contract tests; converter Web para consumir dados reais |
| R08 | Confusão de arquivos por agentes | Média | Alto | PR toca `src/` por B/C sem CR | Coord | Bloquear merge; separar alteração; revisar AGENTS/ownership |
| R09 | Coordenador com ≤3 h/dia vira gargalo | Alta | Alto | Mais de 2 PRs integração em fila ou >24h sem review P0 | Coord | Simplificar PRs, delegar revisão de módulos próprios, priorizar contratos e gates |
| R10 | Disponibilidade B/C insuficiente | Desconhecida | Crítico | Sem compromisso de horas no G0 | Equipe | Revisar marcos e redistribuir **antes** do início |
| R11 | Teste 10 GUI/Sierpinski indefinido | Média | Alto | Sem formato acordado em 20/10 | C | Implementar saída visual mínima verificável e pedir aceitação, sem alegar cumprimento automático |
| R12 | Demonstração remota depende de rede local | Média | Alto | Sem 2 PCs no G0 ou bloqueio firewall | C | Reservar hardware/rede cedo, testar portas e comandos; gravar provas como backup |
| R13 | XOR difere numericamente | Média | Médio | Sem tolerância/oráculo acordado no G1 | A | Comparar com referência/seed/tolerância; não aprovar por apenas acertar classes |
| R14 | Regressão em terminal/Web anterior | Média | Alto | T01–T07 ou Web falham após merge | A | Smoke a cada mudança central e antes do G3 |
| R15 | Incompletude do relatório/UML | Alta se deixado para final | Alto | Pseudocódigos e diagramas ausentes em 29/10 | Cada eixo + Coord | Produzir documentos junto com componentes e consolidar em G4 |
| R16 | Redistribuição indevida do código antigo | Desconhecida | Alto | Repositório público sem permissão/licença | Coord | Manter privado, creditar e verificar condições antes de abrir |
| R17 | Acúmulo de CG + MiniPar | Média | Alto | Estudos da apresentação sacrificados | Equipe | Preservar 04–10/11 e checkpoints curtos durante desenvolvimento |
| R18 | Falhas de segurança ao executar C++ via Web | Média | Alto | Serviço aberto publicamente ou sem limites | B+A | Ambiente local controlado, timeout, diretórios separados, sem deploy público |
| R19 | T08–T10 aparentam paralelo mas serializam carga | Média | Alto | Traces sem sobreposição e tempos falsos | C | Instrumentar start/end/task id, carga idêntica e join real |
| R20 | Dados de avaliação/saídas hardcoded | Média | Crítico | Resultado igual com entrada mutada | Todos | Testes metamórficos e inspeção de código gerado |

## Gatilhos de decisão

**Até 18/10 (G0):** se falta toolchain, contrato ou host para prova remota, card correspondente fica `BLOCKED`; não criar 20 tarefas concorrentes.

**Até 23/10 (G1):** sem prova remota básica e sem ARM executável: suspender polimento visual e benchmarks avançados, abrir plano de resgate técnico com donos/datas e comunicar trio.

**Até 28/10 (G2):** se T08 ou T11 ainda não end-to-end, todos os esforços opcionais são pausados. Avaliar escopo acadêmico real e disponibilidade; não prometer 03/11 automaticamente.

**Até 31/10 (G3):** sem execução integrada, priorizar teste de integração e confiabilidade; documento registra limitações e requisitos não atendidos com transparência.

**Até 03/11 (G4):** congelar versões comprovadas; correções críticas permitidas, mas mudanças estruturais precisam de decisão explícita do trio.

## Como reagir a um bloqueio de contrato

1. Registrar card, exemplo mínimo e arquivos envolvidos.
2. Confirmar se existe fixture/mock fiel.
3. Notificar fornecedor da API.
4. Se alteração for inevitável, CR assinada por fornecedor e consumidor.
5. Ajustar data do gate e cards dependentes.
6. Atualizar docs e testes antes do merge.

## Probabilidade/impacto não são métricas quantitativas

As classificações são qualitativas e devem ser revistas conforme experimentos reais. O ponto desta planilha Markdown é antecipar gatilhos, não fingir que há probabilidades numéricas.
