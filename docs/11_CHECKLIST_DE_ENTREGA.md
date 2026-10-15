# Checklist acadêmico e técnico para 11/11/2026

> Checklist não é comprovação. Só marcar `[x]` após verificar arquivo, teste e evidência. Requisitos não concluídos permanecem abertos.

## Produto e compilação

- [ ] Lexer com tokens e erro léxico.
- [ ] Parser da BNF 2026.2 e AST real.
- [ ] Análise semântica, escopos/tipos e tabela de símbolos.
- [ ] TAC verdadeiro, sem `EXPECTED_QUICKSORT_TAC` artificial.
- [ ] Gerador C++ equivalente, compilável com G++.
- [ ] Executáveis gerados e rodando, inclusive no ambiente de entrega.
- [ ] `seq`, `par`, `fork`, `join` implementados e demonstrados.
- [ ] Comunicação por canais/sockets e mensagens reais.
- [ ] Execução local e remota em dois computadores com Join e falhas verificadas.
- [ ] Comentários `#`, funções, objetos e recursão preservados conforme BNF/testes.

## Programas de teste

- [ ] T01: calculadora cliente-servidor.
- [ ] T02: fatorial e Fibonacci.
- [ ] T03: neurônio.
- [ ] T04: XOR com critério numérico explícito.
- [ ] T05: recomendador.
- [ ] T06: quicksort OO.
- [ ] T07: quicksort iterativo + TAC real + sem corrupção de memória.
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

- [ ] BNF MiniPar 2026.2 atualizada e compatível com testes.
- [ ] Pseudocódigo Lexer.
- [ ] Pseudocódigo Parser.
- [ ] Pseudocódigo semântico e tratamento de erros.
- [ ] Pseudocódigo tabela de símbolos.
- [ ] Product Backlog.
- [ ] Sprint Backlogs.
- [ ] UML casos de uso.
- [ ] UML componentes.
- [ ] UML classes dos componentes.
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
