# Checklist acadêmico e técnico para 11/11/2026

> Revisão REL-PRE (09/11/2026), base de execução `8d07433`, sincronizada documentalmente com `a7454bc` (#42): [relatório consolidado](auditorias/REL-PRE_FECHAMENTO_EIXO_A.md). Itens marcados referem-se ao escopo de evidência indicado, sem declarar a entrega pronta. Rede específica T08–T10, confirmação gráfica, aprovação de B às correções da UML (#43), relatório e reprodução final continuam pendentes. DOC-02 integrado no #42 com aprovação A; revisão C registrada em 09/11 com ressalvas ([parecer](auditorias/DOC-02_REVISAO_C_RUNTIME.md)).

> Checklist não é comprovação. Só marcar `[x]` após verificar arquivo, teste e evidência. Requisitos não concluídos permanecem abertos.

## Produto e compilação

- [ ] Lexer com tokens e erro léxico.
- [ ] Parser da BNF 2026.2 e AST real.
- [ ] Análise semântica, escopos/tipos e tabela de símbolos.
- [x] TAC verdadeiro, sem `EXPECTED_QUICKSORT_TAC` artificial.
- [x] Gerador C++ equivalente, compilável com G++.
- [ ] Executáveis gerados e rodando, inclusive no ambiente de entrega.
- [x] `seq`, `par`, `fork`, `join` implementados e demonstrados.
- [ ] Comunicação por canais/sockets e mensagens reais.
- [ ] Execução local e remota em dois computadores com Join e falhas verificadas.
- [ ] Comentários `#`, funções, objetos e recursão preservados conforme BNF/testes.

## Programas de teste

- [ ] T01: calculadora cliente-servidor.
- [x] T02: fatorial e Fibonacci.
- [x] T03: neurônio.
- [ ] T04: XOR com critério numérico explícito.
- [x] T05: recomendador.
- [x] T06: quicksort OO.
- [x] T07: quicksort iterativo + TAC real + sem corrupção de memória.
- [ ] T08: 160 atividades, quatro avaliadores, resultados completos.
- [ ] T09: T08 + Mandelbrot com execução concorrente verificável.
- [ ] T10: T09 + Sierpinski visual, benchmark de cargas equivalentes.
- [ ] T11: MiniCompilador escrito em MiniPar, Lexer/AST/TAC/tabela/resultado/ARM.
- [ ] T11: três expressões e `.arm` executados no CPUlator.
- [ ] Casos positivos/negativos; logs com comandos e oráculos, status honesto.

## Interfaces

- [ ] CLI/Terminal preservado.
- [ ] Web antiga preservada.
- [ ] Nova Web didática com editor e tokens.
- [ ] Nova Web didática com AST visual muito melhor que a anterior.
- [ ] Exibição semântico/símbolos/erros.
- [ ] Exibição TAC e C++.
- [ ] Compilar realmente, executar, mostrar stdout/stderr.
- [ ] Download do binário correto da execução atual.
- [ ] Instruções para iniciar as três interfaces.
- [ ] Timeout e ambiente Web local controlado.

## Gramática/modelagem/relatório

- [x] BNF MiniPar 2026.2 atualizada e compatível com testes.
- [x] Pseudocódigo Lexer.
- [x] Pseudocódigo Parser.
- [x] Pseudocódigo semântico e tratamento de erros.
- [x] Pseudocódigo tabela de símbolos.
- [x] Product Backlog.
- [x] Sprint Backlogs.
- [x] UML casos de uso (ajustes aprovados por A no #42; integrado em 09/11).
- [x] UML componentes (A no #42; revisão C de 09/11 sem ressalva no runtime).
- [x] UML classes dos componentes (A no #42; revisão C de 09/11 com omissões menores RC-03/RC-04, não bloqueantes).
- [ ] Testes de integração documentados.
- [ ] Tecnologias e ambiente declarados.
- [ ] Prints passo a passo dos programas exigidos.
- [ ] Relatório técnico completo e revisado.
- [ ] **Link do GitHub na CAPA do relatório.**
- [ ] GitHub contém código, testes e relatório; credits do legado.
- [ ] Código com comentários explicativos relevantes.

## Apresentação

- [ ] Três integrantes conseguem explicar arquitetura e pipeline.
- [ ] Cada um conhece seu eixo e as dependências dos outros.
- [ ] Ensaio completo reproduzido de checkout limpo.
- [ ] Dois hosts e CPUlator testados antes da apresentação.
- [ ] Backups de evidências sem fingir execução ao vivo.
- [ ] Slides e falas refletem o software realmente integrado.
- [ ] Links, permissões e anexos testados no dia 10/11.

## Escopo das marcações e início de REL-01

Marcas do núcleo: PRs #14–#19/#29 e regressão REL-PRE; `par`/Fork/Join demonstrados localmente e no smoke loopback. Não atestam equivalência de todos os programas possíveis. T02/T03/T05/T06/T07: baseline de 09/11; T05 só para a entrada derivada do CORE-01. T07 inclui mutação TAC e `_GLIBCXX_ASSERTIONS`, não prova universal de ausência de erros de memória. BNF/pseudocódigos: #32 integrado e review A; backlogs: #39 integrado e atualização REL-PRE. Itens amplos de produto/interfaces seguem abertos até INT-02 e ambiente final. T01 calculado em loopback está PASS, mas a exigência mais ampla de comunicação não foi encerrada por esse recorte.

- [ ] Aprovar e integrar o PR REL-PRE por revisor distinto do autor.
- [ ] Coordenador decidir critério T04 e aceite interno ADR-014; confirmação docente separada.
- [ ] Coordenador registrar tratamento ADR-018 com evidência de direitos/acesso.
- [x] DOC-02: ajustes dos casos de uso aprovados por A e PR #42 integrado (09/11, a7454bc).
- [x] C registrar revisão das seções runtime/runners da UML: [parecer C](auditorias/DOC-02_REVISAO_C_RUNTIME.md), 09/11, APROVADO COM RESSALVAS.
- [x] Corrigir RC-01..RC-06 na UML e repetir a sonda: feito por C no #43 (sonda 862/862, Mermaid 17/17; [§5 do parecer](auditorias/DOC-02_REVISAO_C_RUNTIME.md#5-correções-aplicadas-0911-pr-43)).
- [ ] B (dono do DOC-02) aprovar as correções da UML no #43.
- [x] B apresentar INT-02 em base integrada com oráculos e três interfaces (#44, 09/11); A aprovou no #44 e C validou o runtime ([validação C](auditorias/INT-02_VALIDACAO_C.md)).
- [ ] INT-02: rede real em dois computadores (B + C, roteiro do §5 do INT-02 = `runtime/README.md` §7).
- [ ] C concluir RUN-06 por outro integrante, logs dos dois hosts; tratar RUN-05 par_rede ainda PENDING.
- [ ] B consolidar DOC-04 com capa/link, anexos e limitações; revisão conjunta e merge.
- [ ] Confirmar CPUlator humano e PEND-T11-04 (Java caso 2) ou registrar a limitação explicitamente para decisão.
- [ ] Coordenador liberar `ready` do REL-01 após dependências e aceite: build de checkout limpo, logs persistidos, roteiro e limitações conferidos.

Este checklist apenas prepara REL-01. Nenhuma tag, promoção para main ou declaração de prontidão é autorizada por ele.
