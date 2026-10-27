# HANDOFF — CORE-04 + CORE-05

**Responsável:** Eixo A/coordenador + Codex. **Data inicial:** 23/10/2026; revisão corretiva: 26/10/2026 (PR #15).
**Branch publicada:** `eixo-a/CORE-04-05-fork-join`.
**Base original empilhada:** `a21f172412073d5dc351644b72764e520aafdd4c`.
**CORE-03 corrigido integrado:** `eabe1f4138c22d074da22abc00b739bbe9b70271`
([PR #14](https://github.com/VictorBrasileiroo/minipar-2026-2/pull/14)).
**Base configurada do PR #15:** `dev`; o histórico permanece empilhado sobre #14.
Workspace inicialmente limpo. A branch original CORE-03 foi preservada.

## Autorização e contrato consultado

O coordenador autorizou expressamente este recorte local, a base empilhada sobre
CORE-03, a BNF, testes próprios e uma proteção mínima contra falso sucesso do backend.
O JSON/backlog ainda registra `ready=false`; esta autorização rege a execução,
sem alterar estados históricos, aprovações, `DONE` ou `FROZEN`.
A afirmação de execução exclusivamente local era da rodada inicial; publicação
e integração não destrutiva desta manutenção estão registradas abaixo.

Contrato da rodada inicial: **C-FJ-v1, proposta de congelamento, revisão 1**, §2.1/2.2 do
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
| FJ-SEM-03 | Reconhecer `task` em variáveis, atribuição, cópia de handle e listas homogêneas; rejeitar número, string e objeto; registrar variável sem tipo como unresolved; verificar helper genérico nas chamadas conhecidas |
| FJ-SEM-04 | Destino string e timeout numérico quando conhecidos, inclusive resultados de funções; valor `"host:abc"` fica para o runtime |
| FJ-SEM-05 | Resolução lexical para leitura/escrita de globais; percorrer funções, métodos e inicializadores de objetos usados pela tarefa, inclusive ciclos recursivos; respeitar parâmetros, locais, `for`, blocos e sombreamento; recusar captura de `this` em função global |
| FJ-SEM-06 | Rejeitar argumentos/retornos conhecidos de objeto, canal ou task, inclusive listas aninhadas, append, escrita por índice, chamadas auxiliares e ramos de retorno; recusar aritmética que esconda esses tipos |

Cada chamada relevante examinada recebe os tipos parciais dos seus argumentos e um escopo
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

## Validação inicial (23/10) e reprodução

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

**Próximo consumidor:** revisores do PR #15, Eixo A, CORE-06 e CORE-07;
publicação desta manutenção autorizada expressamente pelo coordenador. Cards não marcados como concluídos e PRs relacionados não integrados.

## Auditoria corretiva de Erasmo e Riquelme — 26/10/2026

SHA anterior: `e973ebd7df26239a5e721d9157dd147d584e5cbf`. Antes de qualquer troca,
a árvore estava limpa. CORE-03 corrigido (`df36500`) foi integrado com
`git merge --no-ff --no-commit eixo-a/CORE-03-strings-t11`, sem conflito;
a correção própria compõe o mesmo commit de merge. Preservam-se os pais e todos
os commits publicados. Não há rebase, force push, push em dev/main ou merge de PR.

A autorização expressa de 26/10 abrange src de A, testes próprios, documentação e
publicação nas branches originais. A extensão de escopo CORE-04/05 (BNF, guardas
em main/TAC/C++, testes e evidências) está nos cards e doc 04. ready/status não foram
transformados em aprovação. Nenhum arquivo de C ou B foi alterado pela correção.

Referência atual consultada via git show: **C-FJ-v1 proposta revisão 2**, §2.2.1–2.2.5,
§2.9/2.10 de `origin/dev` em `84934b96299337ed140a29678cec083a566a780a`;
essa dev inclui #7/#8/#9. A assinatura de A ainda consta pendente. O documento de
contrato desta branch é anterior e foi preservado: este handoff distingue essa
versão histórica da revisão consultada; nenhuma aprovação foi inventada.

### Reprodução antes da correção

`python -B tests/2026_2/core0405/test_review_regressions.py` antes de modificar o
semântico: 20 métodos de teste, 22 falhas de assertions/subtests e um erro de timeout,
6,649 s; log local `output/core0405-review-before.log`. F1 rejeitava o iterador de
handles e perdia concatenações; F2 aceitava globais nos ancestrais; F3 repetia
diagnósticos e alterava código independente. A cadeia de profundidade 10 com três
chamadas por nível produziu **1.180.931 visitas** (limite do teste: 1.500); a cadeia
independente de profundidade 16 excedeu 3 s. F4 aceitou IO/descarte e usos de none.
Os testes foram ampliados durante a correção; um helper comum que recebia handle
e devolvia lista ainda perdia os metadados, foi reproduzido e corrigido antes do aceite.

### Correções e limites

- **F1:** for-in deriva `value_type` dos elementos, sem fixar `Symbol.type` de
  iteradores genéricos do código independente. Listas por atribuição, concatenação,
  append, índice e helpers relevantes mantêm alternativas conhecidas; cópias são
  independentes. Join conhecido não-task é erro; alternativas conhecidas inválidas
  também são recusadas. Unknown/var real vira `unresolved_fj`, sem erro nem prova
  de segurança. O antigo teste que exigia rejeitar `var h; join(h);` foi substituído
  pelo oráculo exigido no contrato; não se relaxaram os negativos conhecidos.
- **F2:** percorre a cadeia de inicializadores na ordem ancestral → descendente,
  com a classe dona de cada inicializador; atributos da subclasse não escondem
  acessos do ancestral. Resolve membros herdados e recusa herança cíclica. Chamadas
  transitivas, recursão de funções/métodos e sombreamento continuam exercitados.
- **F3:** a passada normal continua produzindo os diagnósticos ordinários. A
  especialização emite FJ e é dirigida por funções contendo FJ, seus chamadores,
  dados contendo handles e expressões de fronteira; o fecho de funções/métodos/
  inicializadores de tarefa é analisado isolado. Cache imutável de tipo por
  `(função, argumentos ValueType, isolated, classe dona, tipos globais, fase provisória)`; escopos e
  mapas de expressão são salvos/restaurados e símbolos globais copiados. Contextos
  ativos encerram a recursão com unknown explícito; nenhum cache não isolado prova
  isolamento. Diagnósticos FJ repetidos são deduplicados por origem/contexto.
  Não se desativaram as verificações de isolamento.
- **F4:** decisões explicitadas em `docs/CR-CORE05-FJ-DECISOES.md`: IO de tarefa
  rejeitado (FJ-SEM-05); join com none conhecido só como comando, uso como valor
  rejeitado (FJ-SEM-06); fork como comando descartando handle rejeitado (FJ-SEM-03).
  Não há análise completa de consumo de handles armazenados. Assinaturas provisórias
  da declaração ficam separadas das chamadas reais; múltiplas assinaturas reais e
  unknown não são apagados. CORE-07 deve agregar por função e rejeitar casos sem
  prova até implementar despacho seguro; number/int/float ainda depende desse card.
- **Menores:** imports de AST consolidados; hashes do executor normalizam LF;
  JSONs atuais usam caminhos relativos à raiz. O backend continua recusando FJ
  explicitamente; não se implementou CORE-06/07 nem se alterou runtime.

### Validação desta manutenção

```powershell
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
.\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py
.\.venv\Scripts\python.exe -B output/audit-baseline-t01-t07.py --repeat 3
.\.venv\Scripts\python.exe -B scripts/validar_planejamento.py
git diff --check
```

G++ UCRT64 16.2.0, Python da venv 3.12.4; CXX/PATH só no processo. O script baseline
foi extraído de `84934b9:scripts/baseline_t01_t07.py` para output, ajustando somente
REPO à raiz (a branch não contém o script); oráculos preservados.

**116/116 PASS** no executor CORE-04/05, incluindo 26 métodos adversariais,
smoke nativo, AST, negativos e guardas diretas/CLI contra TAC/C++ prematuro.
Rodada final: `output/core0405/run-oanl55sv/summary.json` (2,742 s).
CORE-03 integral: **58 PASS, 1 KNOWN_FAIL, 0 FAIL**, saída 0,
`output/core03/run-frvtxb35/summary.json`. Essa rodada precede só os ajustes finais de
propagação de argumento contendo handle e fase de assinaturas provisórias; os caminhos sem FJ do CORE-03 não mudam.
O smoke nativo e a suíte FJ completa foram repetidos depois desses ajustes.
A fase provisória é herdada transitivamente, impedindo que chamadas na declaração
poluam as assinaturas reais de um fork em helper; o teste adicional falhou antes
de acrescentar a fase à chave do cache e passou após a correção.

Medição adicional (`output/core0405/review-metrics.json`): profundidades 4/8/10/16,
três chamadas por nível, 95/179/221/347 visitas e 5/9/11/17 contextos no cache,
respectivamente; ~0,001–0,004 s nesta máquina. O teste usa limite de visitas e
subprocesso de 3 s, não exige igualdade de tempo entre máquinas.

Baseline final (`output/core01/run-20261026-181014/baseline.json`), saída 1:
T01/T02 3/3 PASS nesta rodada, sem declarar estabilidade; T03/T05/T06 e ordenação
T07 PASS; T04 PARTIAL; T07-mutação/limites FAIL herdados, corrigidos separadamente
no #16. Regressões não foram ocultadas por exit 0. Planejamento e diff --check PASS.
T08–T11, execução FJ local/remota e CPUlator continuam UNTESTED nesta manutenção.

A inferência continua parcial: não há análise de fluxo/ponto fixo geral, tempo de
vida de handles nem efeito completo de mutações em atributos através de chamadas.
Unknown exige decisão conservadora no consumidor. O aceite dos testes não certifica
serialização, rede ou funcionamento do backend FJ ainda ausente.

### Documentos e integração

Verificados AGENTS, MEMORY, README, docs 00/01/02/03/04/05, BNF, contratos de runtime,
card e template de handoff. Atualizados BNF, cards CORE-04/05 e espelho doc 04,
este handoff, JSON de evidências e registro CR das decisões. CORE-03 corrigido e
seus documentos foram recebidos pelo merge. AGENTS/MEMORY não precisam mudar:
nenhum ownership, convenção ou fluxo permanente novo; a organização interna da
análise está documentada aqui, dentro do pipeline existente. README não detalha
esse algoritmo, portanto não precisa mudar. Contrato compartilhado preservado;
escolhas que precisem ratificação estão explícitas, não tratadas como FROZEN.

O PR #15 permanece com base **dev**, histórico empilhado sobre #14. Não se alterou a
base: depois do merge humano do #14 em dev, conferir ancestralidade e diff real;
se #14 entrar preservando os commits, o diff do #15 exclui naturalmente CORE-03.
Se a integração escolher squash, a coordenação deve planejar a sincronização não
destrutiva e revisar o diff, sem rebase/force push nesta manutenção. Antes de
CORE-06/07: ratificar contrato A/C e decisões acima, integrar #14/#16/#15 com revisão
independente, conferir runtime atualizado e planejar provas TAC e nativas próprias.

## Rodada final dirigida — 27/10/2026

Autorização explícita do coordenador: corrigir/publicar/comentar #14 e #15,
preservando as branches originais, sem rebase, force push, merge de PR, aprovação
automática ou DONE. #16 somente consultado. Heads iniciais confirmados por fetch,
ls-remote e GitHub: #14 `df36500f818a892a238af526cc092f0a5d6b9fe0`,
#15 `ea77d8f980d639f96372241584cb6c7397de4dc5`,
#16 `d27762d733eab55904f48289bd44c463cf55d0d5`. Árvore inicialmente limpa,
sem commits locais à frente nas branches afetadas; worktree histórica preservada.

### Integração e correções

- CORE-03 `eabe1f4138c22d074da22abc00b739bbe9b70271` publicado e recebido por merge
  separado `445423d24e590bda519a333b36ab71b5454640d8`. Os dois conflitos em semantic
  foram resolvidos mantendo coleta de classes/inicializadores e guarda de strings,
  junto ao rastreamento dos índices FJ. Suíte existente no merge: **116/116 PASS**,
  `output/core0405/run-0dy8pyzr/summary.json`. Nenhuma correção própria foi embutida
  no commit de integração desta rodada.
- Códigos de descarte/none passam de 03/06 para **FJ-SEM-07/08**, extensão proposta
  na CR, aguardando ratificação A/C e consulta ao consumidor Web. 03 permanece
  join de tipo conhecido diferente de task; 06 permanece transporte/aritmética
  proibidos segundo o contrato. docs/02 e APIs runtime/Web preservados. A seção
  histórica de 26/10 acima registra os códigos usados naquela rodada; esta revisão
  e a CR datada de 27/10 a substituem quanto a esses identificadores.
- `ValueType.__post_init__` remove somente alternativas exatamente repetidas em
  elements, preservando primeira ordem, tipos distintos e o kind unknown. O tipo
  abstrato já não descrevia posições/cardinalidade. Literais, concatenação e união
  de retornos passam pela mesma normalização. Não se generalizaram objetos, canais,
  handles ou unknown para number; chaves de contexto continuam contendo assinatura,
  isolamento, classe dona, tipos globais e fase provisória. Não se eliminou nenhuma
  verificação de isolamento nem se compartilhou contexto isolado com não isolado.
- Retorno none por caminho implícito **permanece limitação conhecida**, reproduzida
  antes/depois, com risco e aceite futuro na CR/PEND-FJ-07 para CORE-07. O semântico
  coleta returns explícitos e não prova retorno em todos os caminhos. Não se
  introduziu um analisador parcial de fluxo para tratar laços/recursão como prova.
  O caso aceito é KNOWN_LIMITATION, não PASS funcional; a guarda do backend ainda
  impede TAC/C++ FJ e executável residual. CORE-07 deve resolver antes de removê-la.

### Medição real e testes

`measure_final_review.py` executa a cadeia de Erasmo em subprocesso limitado a 90 s;
o cronômetro mede só análise semântica, parsing fora do intervalo. Mesma fonte e
toolchain antes/depois; fontes reproduzíveis pela função chain e SHA-256 no JSON.

| Profundidade | Antes (merge de integração) | Depois | Contextos antes/depois |
|---|---:|---:|---:|
| 10 | 0,405470 s | 0,005834 s | 4084 / 67 |
| 16 | excedeu timeout de 90 s | 0,014898 s | não concluído / 154 |
| 24 | não executado antes | 0,043487 s | não medido / 326 |

Não atribuir os 43 s da revisão à nossa máquina: aqui a execução de profundidade
16 foi interrompida pelo limite. O tempo de conclusão anterior é desconhecido,
sem razão de speedup calculada a partir de timeout. Repetição final da profundidade
16: 0,015754 s. Evidências: `output/core0405/final-before.json`, `final-after.json`
e `final-measure-tool-check.json`. O script final retorna erro se uma medição não
for aceita/concluída; o caso implicit_none é relatado separadamente como limitação.

Comandos realmente executados (Python 3.12.4 / G++ UCRT64 16.2.0; CXX/PATH local):

```powershell
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/test_review_regressions.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/test_final_review.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/measure_final_review.py --depth 10 --depth 16 --depth 24 --output output/core0405/final-after.json
.\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py
.\.venv\Scripts\python.exe -B output/audit-baseline-t01-t07.py --repeat 3
.\.venv\Scripts\python.exe -B scripts/validar_planejamento.py
git diff --check
```

Resultado final: **126/126 PASS**, incluindo os 26 testes F1–F6 e 10 novos casos;
`output/core0405/run-ddp49slx/summary.json`, 3,055 s. Execuções separadas:
review 26/26 em 0,148 s e final 10/10 em 0,182 s. Novos testes cobrem separação de
códigos, normalização sem apagar alternativas proibidas, mistura task/número,
objetos/handles aninhados, assinaturas number/string, cache entre contextos normais
e isolados, globais transitivos, recursão e cadeia patológica com timeout externo.
Guardas diretas/CLI e smoke nativo não-FJ continuam PASS.

CORE-03 integral após a mudança semântica: **78 PASS, 1 KNOWN_FAIL herdado, 0 FAIL**,
`output/core03/run-n2u0afov/summary.json`. Proteção de strings, negativos sem binário,
substr e listas/matrizes válidas foram reexecutados no código final do #15.

Baseline `output/core01/run-20261027-094221/baseline.json`, saída 1:
T01 3/3 PASS; T02 **1/3 PASS, 2 FAIL**, saída concorrente corrompida (`1200`),
intermitência DEF-02 conhecida, sem mascarar como PASS; T03/T05/T06/ordenação T07
PASS; T04 PARTIAL; T07-mutação/limites FAIL herdados do CORE-01, tratados no #16.
T01 continua com DEF-01 intermitente conhecido, embora tenha passado nesta rodada.
Como scripts/baseline_t01_t07.py não existe nesta branch, usado o executor extraído
de origin/dev `84934b9` para output, alterando apenas REPO; oráculos preservados.
Planejamento e diff --check PASS. Síntese em `CORE-04-05_RODADA_FINAL_RESULTADOS.json`.

### Documentos, arquivos e integração humana

Arquivos próprios desta manutenção: `src/semantic.py`, BNF, CR-CORE05, este handoff,
JSON novo de resultados e quatro arquivos em tests/2026_2/core0405 (executor,
review atualizado e dois novos arquivos). Os arquivos CORE-03 vieram por merge;
nenhum arquivo de B/C, legacy, runtime ou oráculo foi editado. Resultados anteriores
foram preservados como evidência datada.

Revisados README, AGENTS, MEMORY, docs 00/01/02/04/05, contrato vigente no origin/dev,
BNF e handoffs. Atualizados BNF, CR e evidências/handoff deste card. README e planos
não detalham a normalização; APIs e nós AST não mudaram; diagramas/pseudocódigos não
ganham nova fase. **AGENTS/MEMORY sem mudança necessária**: ownership, convenções,
arquitetura e fluxo permanecem; a política documental continua válida. A extensão
de catálogo é proposta explícita na CR, sem editar o contrato compartilhado.

#15 permanece com base dev, contém #14 atualizado como ancestral. Após integração
humana de #14, conferir novamente o diff próprio. Simulações merge-tree contra
origin/dev são limpas para #14 e #15; isso não equivale a regressão de integração.
O #16 permanece APPROVED/MERGEABLE/CLEAN no head original, sem novos commits.

**Atenção à integração #16 + #15:** simulação entre os dois heads encontrou um
conflito textual em `src/tac.py`, dentro de generate_text. A resolução humana deve
preservar import/find_fork_join e a recusa explícita de FJ do #15, mas eliminar
EXPECTED_QUICKSORT_TAC e a condição de retorno fixo conforme #16; em seguida,
percorrer a AST normalmente. Não aceitar integralmente um dos lados, pois isso
perderia a guarda FJ ou restauraria hardcode. Nenhuma branch #16 foi modificada
ou integrada nesta rodada. Ordem sugerida: #14, #16, resolver esse conflito no
#15 e revalidar os testes TAC/nativos do #16, CORE-04/05, CORE-03 e baseline antes
do último merge. Mantidas as aprovações independentes e ratificação A/C da CR.

Pendências para consumidores: CORE-06 implementar TAC FJ real e preservar TAC
autêntico do #16; CORE-07 tratar none implícito, unknown/múltiplas assinaturas,
wrappers/registry e execução real com runtime C. CORE-08 deve mapear os diagnósticos
propostos e localização MiniParLine do G++. Nenhuma execução FJ local/remota ou
ARM/CPUlator foi homologada por esta manutenção. Não marcar cards como DONE.
