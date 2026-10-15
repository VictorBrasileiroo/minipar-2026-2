# Preparação do trio para apresentação — 04 a 10/11/2026

**Objetivo:** garantir que os três integrantes possam demonstrar e defender a solução completa. A semana **não** é destinada a desenvolver do zero Fork/Join ou Teste 11.

## Regras gerais

- Cada pessoa estuda 100% o eixo próprio e entende o fluxo geral dos outros.
- Cada módulo precisa de 1 página de explicação: objetivo, arquitetura, classes principais, entradas/saídas, limitações e testes.
- O coordenador precisa preservar tempo para o projeto CG, com o qual o trio também está envolvido.
- O material de apresentação deve corresponder à implementação real; não prometer speedup obrigatório nem alegar distribuição baseada em localhost.
- Preparar rota de demonstração com backup caso firewall/rede/CPUlator falhe ao vivo.

## Calendário de estudo

| Data | Foco principal | Prova de aprendizado |
|---|---|---|
| 04/11 | Introdução, objetivos, arquitetura, evolução 2026.1 → 2026.2, Lexer/Parser/AST | Todos explicam pipeline da entrada até binário |
| 05/11 | Semântico, símbolos, TAC e geração C++ | Todos identificam diferença entre AST→TAC e AST→C++ |
| 06/11 | `seq/par/fork/join`, isolamento, protocolo, workers e canais | Todos explicam start/join e uma falha de worker |
| 07/11 | T08–T10, 160 tarefas, Mandelbrot, Sierpinski, benchmark | Todos explicam cargas, oráculos e speedup |
| 08/11 | T11: minilexer, AST, TAC, símbolos, ARMv7, CPUlator | Todos explicam precedência e registrador do resultado |
| 09/11 | CLI, Web original/didática, tokens/AST visual, UML, docs | Ensaio de demonstração completa |
| 10/11 | Ensaio final e backup, verificação do GitHub/relatório | Apresentação completa sem improvisar funcionalidades |

## Roteiro mínimo de demonstração

1. Fonte MiniPar simples e saída tokens/AST/semântico/TAC/C++ na nova Web.
2. Compilar e executar; mostrar binário real, não saída fake.
3. Demonstrar classe/função/recursão herdadas.
4. `fork`/`join` local com duas tarefas identificadas.
5. `fork`/`join` distribuído com dois hosts e logs identificados.
6. T08 (160 atividades), T09/T10 (fractal e simultaneidade).
7. T11: expressão infixada, AST/TAC/ARM, abrir no CPUlator, mostrar resultado.
8. Modelagem UML e componentes; fechar com regressão/testes e principais desafios.

## Perguntas para cada integrante

**Todos:** Lexer vs Parser; por que AST; semântico vs sintático; TAC; por que backend usa AST; diferença threads/processos; importância de mensagens; falso paralelismo; critérios de PASS; limites conhecidos.

**Eixo A:** BNF Fork/Join; AST nodes; tipos/strings; por que hardcode TAC era incorreto; portabilidade C++.
**Eixo B:** UI didática real vs mock; visualização AST; minilexer/parser de expressões escrito em MiniPar; ordem ARM/CPUlator.
**Eixo C:** framing TCP, IDs, worker previamente compilado, erros/timeouts, função do Join, duas máquinas reais, benchmark justo.

## Checklist de última hora

- Código/build de demonstração previamente conferido.
- Rede/hosts e binários workers preparados; logs seguros disponíveis.
- CPUlator e arquivos `.arm` testados e salvos.
- Slides e relatório sincronizados com código.
- Repositório e links abrem em conta normal.
- Roteiro por pessoa e plano B de vídeo/evidências se demo ao vivo falhar.
