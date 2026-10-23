# HANDOFF — CORE-04 + CORE-05

**Responsável:** Eixo A/coordenador + Codex. **Data:** 23/10/2026.
**Branch local:** `eixo-a/CORE-04-05-fork-join`.
**Base:** `a21f172412073d5dc351644b72764e520aafdd4c`, igual ao head do
[PR #14](https://github.com/VictorBrasileiroo/minipar-2026-2/pull/14), ainda aberto na consulta desta execução.
Workspace inicialmente limpo. A branch original CORE-03 foi preservada.

## Autorização e contrato consultado

O coordenador autorizou expressamente este recorte local, a base empilhada sobre
CORE-03, a BNF, testes próprios e uma proteção mínima contra falso sucesso do backend.
O JSON/backlog ainda registra `ready=false`; esta autorização rege a execução,
sem alterar estados históricos, aprovações, `DONE` ou `FROZEN`.
Nenhum commit, push, PR, merge, rebase ou cherry-pick foi realizado.

Contrato usado: **C-FJ-v1, proposta de congelamento, revisão 1**, §2.1/2.2 do
[PR #7](https://github.com/VictorBrasileiroo/minipar-2026-2/pull/7), head
`6856a20ef9e2e6ea9a5016d442677848a5157819`, lido com `git show` sem integração.
A sintaxe dessa proposta foi adotada pela autorização do A nesta tarefa;
o contrato compartilhado não foi editado nem aprovado pelo agente.

Compatibilidade futura conferida por leitura de `api.hpp` e `value.hpp` dos
[PR #8](https://github.com/VictorBrasileiroo/minipar-2026-2/pull/8) (`18d454a`) e
[PR #9](https://github.com/VictorBrasileiroo/minipar-2026-2/pull/9) (`7af4a41`):
`start(function_id, TaskArgs, Destination)` retorna `TaskHandle`;
`join_or_exit(handle, timeout_ms)` retorna `Value`; destino omitido é local;
`Value` admite números, bool, string, listas recursivas e `none`, sem objetos,
canais ou handles. Nenhum código de runtime foi incorporado ou executado.

## CORE-04 — Implementado

- Tokens reservados `FORK`, `JOIN`, `ON`, sem reservar nomes maiores como `forked`.
- Expressões primárias `fork f(args) [on expressão]` e `join(handle[, timeout])`;
  também aceitas como comandos com `;`.
- AST específica com linha e coluna de origem. Argumentos, destino, handle e
  timeout são subárvores, sem avaliação nem captura durante o parsing.
- Precedência, chamadas, propriedades, índices e blocos existentes preservados.
  `on` consome expressão completa, conforme a produção do contrato. Para usar um
  operador depois do destino, agrupar: `(fork f() on "local") == h`.
- Diagnósticos sintáticos seguem o mecanismo existente (`stderr`, `SystemExit(1)`),
  incluindo função ausente, parênteses incompletos, destino/argumento ausente,
  `join()` vazio e terceiro argumento de join.

## CORE-05 — Implementado

| Regra | Recorte e oráculos exercitados |
|---|---|
| FJ-SEM-01 | Função global, inclusive declarada depois; rejeitar nome inexistente, variável, classe, builtin, método isolado, função de bloco e sombreamento local |
| FJ-SEM-02 | Aridade exata; rejeitar argumentos ausentes/extras |
| FJ-SEM-03 | Reconhecer `task` em variáveis, atribuição, cópia de handle e listas homogêneas; rejeitar número, string, objeto e variável sem tipo; verificar helper genérico nas chamadas conhecidas |
| FJ-SEM-04 | Destino string e timeout numérico quando conhecidos, inclusive resultados de funções; valor `"host:abc"` fica para o runtime |
| FJ-SEM-05 | Resolução lexical para leitura/escrita de globais; percorrer funções, métodos e inicializadores de objetos usados pela tarefa, inclusive ciclos recursivos; respeitar parâmetros, locais, `for`, blocos e sombreamento; recusar captura de `this` em função global |
| FJ-SEM-06 | Rejeitar argumentos/retornos conhecidos de objeto, canal ou task, inclusive listas aninhadas, append, escrita por índice, chamadas auxiliares e ramos de retorno; recusar aritmética que esconda esses tipos |

Cada chamada examinada recebe os tipos parciais dos seus argumentos e um escopo
baseado nas declarações globais. Os locais do chamador não são usados para resolver
nomes do corpo chamado. O acompanhamento de listas respeita cópia por valor:
alterar a cópia local de uma lista não altera a informação da original.
Regras de strings e restrição temporária de listas de strings do CORE-03 preservadas.

## Arquivos alterados

- `src/lexer.py`, `src/parser.py`, `src/ast_nodes.py`: CORE-04 e percurso estrutural da AST.
- `src/semantic.py`: CORE-05 e informações parciais de tipos de tarefas.
- `main.py`, `src/tac.py`, `src/codegen.py`: somente recusa explícita de geração
  para AST contendo Fork/Join, inclusive em função não chamada.
- `BNF-grammar.md`: tokens, produções detalhadas/consolidadas, regras e limites.
- `tests/2026_2/core0405/verify_core0405.py`: suíte e executor próprios do Eixo A.
- Este handoff e `docs/auditorias/CORE-04-05_RESULTADOS.json`: evidências selecionadas.

## Interface para CORE-06 e CORE-07

Novos dataclasses em `src/ast_nodes.py`, sem modificar os campos dos nós existentes:

```python
ForkExpr(function_name: str, arguments: List[ASTNode],
         destination: Optional[ASTNode] = None, line: int = 1, column: int = 1)
JoinExpr(handle: ASTNode, timeout: Optional[ASTNode] = None,
         line: int = 1, column: int = 1)
```

`None` significa destino local ou timeout omitido, respectivamente; não é literal
string/número inserido na AST. `line` e `column` usam base 1 e apontam à palavra-chave.
`iter_child_nodes` percorre somente filhos estruturais; `find_fork_join` detecta a
construção iterativamente em qualquer posição da AST.

`SemanticAnalyzer.analyze(program)` mantém retorno `bool` e diagnóstico em stderr.
Informações adicionais **internas**, válidas para a mesma instância/AST:

- `ValueType(kind, elements=(), result=None)`: tipo parcial imutável. `elements`
  representa tipos possíveis de coleção, ou alternativas de um `unknown`;
  `result` associa o tipo parcial do retorno ao `task`.
- `Symbol.type` continua texto; `Symbol.value_type` acrescenta detalhes de
  coleções/handles. Nenhuma assinatura pública do serviço C-WEB foi modificada.
- `expression_types[id(node)]`: informações de expressões no contexto corrente.
  Os contextos de chamadas são temporários e restaurados ao retornar; este mapa
  **não é uma tabela completa de tipos por especialização de todo o programa**.
- `fork_signatures[id(fork)]`: lista de pares `(tipos_argumentos, tipo_retorno)`
  observados, com um item por assinatura distinta. Um nó em função genérica pode
  ter vários itens, inclusive desconhecidos. Não escolher simplesmente o último.
- `unresolved_fj`: observações de transporte/retorno desconhecido ou join genérico
  dependente de chamada; não representam validação concluída de tipos.

Exemplo efetivamente analisado:

```minipar
func f(x) { return x; }
var h = fork f("ok");
var r = join(h);
```

Resultado observado: análise `True`, sem stderr; `h: task` com resultado `string`,
`r: string`, assinatura do fork `(string) -> string`. Não houve execução da tarefa.

CORE-06 deve consumir os novos nós no ramo AST → TAC. CORE-07 deve consumi-los no
ramo independente AST → C++, gerar wrappers/registry reais e resolver tipos
desconhecidos com uma estratégia compatível com `Value` do contrato. O timeout
permanece expressão numérica; validação/conversão de valor para `int` ainda cabe
ao backend/runtime. Remover as proteções somente quando esses ramos tiverem
implementação e oráculos próprios; não basta deixar `generate` retornar sucesso.

## Validação e reprodução

Python 3.12.4 da venv e G++ UCRT64 16.2.0. Configuração somente no processo:

```powershell
$env:CXX = 'C:\msys64\ucrt64\bin\g++.exe'
$env:Path = 'C:\msys64\ucrt64\bin;' + $env:Path
& .\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
& .\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py --case PROVA-INT --case PROVA-08 --case PROVA-09 --case REG-LISTA --case REG-CLASSE --case REG-RECURSAO --case NEG-01 --case EXTRA-NEG-LISTA-STRING --case EXTRA-NEG-APPEND-STRING
```

| Verificação | Resultado |
|---|---|
| Suíte CORE-04/05 (AST, positivos/negativos, semântico e proteção) | PASS: 90 testes |
| Smoke nativo incluído na suíte: função recursiva, classe, string, seq/par | PASS: exit 0, stderr vazio, stdout exato `120 ok! b\npar\n` |
| CLI com Fork/Join semanticamente válido | PASS da **proteção**: exit 1, diagnóstico CORE-06/07, sem novo TAC/C++/binário e executável anterior invalidado |
| Geradores chamados diretamente com fork em função não chamada | PASS da **proteção**: TAC lança `NotImplementedError` CORE-06; C++ retorna False/CORE-07, não chama compilador e invalida binário anterior |
| Recorte CORE-03 listado acima | PASS: 9 casos, stdout/exit/stderr ou rejeição verificados |
| Inferência estática genérica/coleções mutadas por caminhos não modelados | PARTIAL, limites abaixo |
| Fork/Join MiniPar → TAC/C++ → execução local/remota | UNTESTED; geração ainda não implementada |
| Regressão integral T01–T11, rede e CPUlator | UNTESTED neste bloco |

Evidências selecionadas e hashes do código testado estão no JSON ao lado.
Cada execução usa subdiretório novo de `output/core0405/` ou `output/core03/`;
fontes, comandos, stdout, stderr e binários do smoke ficam nesses diretórios.
O JSON registra os caminhos exatos da rodada final. Casos negativos têm oráculo
por código FJ-SEM ou mensagem específica, e não apenas ausência de exceção.

## Limitações e riscos reais

- A inferência existente não preserva anotações de parâmetro no `FuncDecl` e não
  resolve todos os retornos recursivos/genéricos. Tipos desconhecidos permanecem
  explicitamente desconhecidos; transporte nesses casos é PARTIAL. Um helper com
  join de parâmetro desconhecido é adiado e reanalisado nas chamadas conhecidas;
  declaração não chamada não comprova o tipo desse join.
- A análise de coleções acompanha tipos possíveis, não índices exatos nem tempo
  de vida de cada elemento. `pop`/sobrescrita não removem tipos acumulados;
  coleções heterogêneas podem gerar diagnóstico conservador ou `unknown`.
  Mutação de atributos/objetos através de chamadas e todos os fluxos de dados não
  são modelados; não se afirma validação estática completa de FJ-SEM-06.
- A verificação de ciclos percorre cada função ativa uma vez, sem inferência por
  ponto fixo de todas as especializações recursivas. Não há prova geral de tipos
  de retorno nesses ciclos. Métodos sem tipo conhecido são recusados na tarefa
  por não permitir comprovar isolamento.
- Não há análise de consumo/uso único de handles, validade temporal, endereço,
  timeout fracionário/fora de faixa, NaN/infinito ou falhas de worker. Essas
  verificações de valor e execução dependem de CORE-07/runtime.
- Os geradores continuam sem implementar Fork/Join. O frontend aceito não prova
  execução local/remota, isolamento em runtime nem serialização real.

## Verificação documental — regra 11

Verificados: `AGENTS.md`, `MEMORY.md`, `README.md`, documentos 00/01/02/04/05,
cards CORE-04/05, template de handoff, BNF, proposta C-FJ do PR #7 e documentação
de runtime relacionada aos PRs #8/#9. BNF e este handoff/resultados foram atualizados.
`README.md`, planos e backlog não detalham a nova interface e mantêm seu contexto
operacional/histórico; não exigem alteração neste recorte. O contrato compartilhado
fica preservado conforme instrução expressa; a revisão adotada está identificada aqui.

**AGENTS.md e MEMORY.md sem alteração:** ownership, convenções, arquitetura de
ramos AST → TAC/AST → C++ e fluxo de trabalho continuam válidos. A exceção de base
e entrega exclusivamente local é autorização desta tarefa, não mudança permanente.
Nenhum arquivo de `runtime/`, `web_didatica/` ou `legacy/` foi alterado.

**Próximo consumidor:** Eixo A, CORE-06 e CORE-07; revisão humana local antes de
qualquer publicação. Cards não marcados como concluídos e PRs relacionados não integrados.
