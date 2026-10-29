# HANDOFF — CORE-06: TAC autêntico para Fork/Join e `par`

> **Leitura temporal:** o registro abaixo até “Revisão corretiva” descreve a
> execução inicial, anterior à publicação. O coordenador publicou posteriormente
> `2fada7c`; o estado atual e as novas evidências constam na seção datada ao final.

**Responsável:** Eixo A/coordenador, desenvolvimento assistido por Codex.  
**Data:** 29/10/2026. **Branch local:** `eixo-a/CORE-06-tac-fork-join-par`.  
**Base HEAD/origin/dev:** `29cff941e4e4a2b7f37b08bf3fc0d24e98c40ce1`.

**Parecer: SIM, implementado e pronto para revisão local no recorte descrito.**
Não é DONE, integração aprovada, execução de tarefas ou homologação do compilador.
Alterações não commitadas e não staged. Não houve `git add`, commit, push, PR,
merge, rebase, cherry-pick nem implementação de CORE-07/08.

## Autorização, base e pendências administrativas

O prompt do coordenador autoriza exclusivamente desenvolvimento local de CORE-06,
apesar de `BACKLOG`, `ready=false` e ratificações pendentes. A autorização foi
registrada em `planning/cards.json` e espelhada no trecho CORE-06 do backlog.
Estados, dependências, `allowed_paths`, aprovações e contratos foram preservados.
O escopo complementar de testes/documentação vem expressamente do prompt.

Antes das alterações: árvore limpa, branch CORE-04/05 em `4a56a4f`, worktree
histórica de recuperação preservada. `git fetch origin` confirmou que `origin/dev`
continuava no SHA informado acima. A branch CORE-06, antes inexistente, foi criada
diretamente dessa referência; `merge-base HEAD origin/dev` confirmou a base.
Branches locais `dev` (`408afb1`) e `main` (`77d1eb3`) não foram atualizadas.

O sandbox inicialmente recusou a propriedade Git e a escrita de FETCH_HEAD.
Usou-se `git -c safe.directory=<este repositório>` somente por comando, sem
configuração global, e execução autorizada de fetch/criação da branch. Não houve
rejeição de aprovação automática nem mudança de permissões permanentes.

**Contrato técnico adotado:** C-FJ-v1, proposta revisão 2 de 23/10/2026, §2 de
`docs/02_CONTRATOS_TECNICOS.md`, e `docs/CR-CORE05-FJ-DECISOES.md`.
Nenhum deles foi alterado ou declarado FROZEN. Ratificações A/C da sintaxe,
isolamento e extensões FJ-SEM-07/08 continuam pendentes; B/CORE-08 é consumidor
dos diagnósticos. Esta implementação não ratifica nenhuma decisão humana.

## Diagnóstico reproduzido antes da correção

As três fontes abaixo passaram pelo frontend real, com análise semântica `True`:

| Fonte | Resultado observado na base |
|---|---|
| `func f(x){return x;} var h=fork f(10);print(join(h));` | `NotImplementedError: Linha 1: Fork/Join requer CORE-06; TAC nao gerado.` |
| `seq{print(1);}par{print(2);print(3);}` | Apenas `print 1`, `print 2`, `print 3`: concorrência apagada |
| `for(var n in [1,2]){print(n);}` | `t0 = [1, 2]`, comentário `# for n in t0`, `print n`: sem condição, passo ou retorno |

Diagnóstico adicional na revisão: inicializadores de atributos não eram
traduzidos pelo TAC legado. Uma classe com `var h=fork f();` podia perder o
disparo ao simplesmente remover a guarda geral. Agora esse caminho falha
explicitamente, inclusive chamadas que possam esconder Fork/Join transitivo.

## Implementação e arquivos

| Arquivo | Alteração |
|---|---|
| `src/tac.py` | Lowering de ForkExpr/JoinExpr, `par` separado de `seq`, iteradores, controle de fluxo e falhas explícitas |
| `tests/2026_2/core06/test_tac_fork_join.py` | 38 testes por pipeline real e invariantes internos |
| `tests/2026_2/core06/examples/*.minipar` | Três entradas reproduzíveis; TAC observado transcrito abaixo |
| `tests/2026_2/core0405/verify_core0405.py` | Oráculo do TAC atualizado; guardas CLI/C++ e smoke preservados |
| `README.md`, `BNF-grammar.md` | Disponibilidade do TAC e fronteira com C++/CLI |
| `planning/cards.json`, `docs/04_BACKLOG.md` | Autorização/evidência local de CORE-06, sem promoção de estado |
| Este handoff e `CORE-06_RESULTADOS.json` | Notação, resultados observados, exemplos, hashes e limites |

Mantidas as assinaturas `generate_text(program) -> str` e
`generate(program, output_name) -> str` (caminho em `output/`). `_stmt`, `_expr`,
`_temp`, `_label` e `_emit` permanecem o núcleo do gerador textual. Não foi criada
IR estruturada, interpretador, dependência nova nem ligação com runtime.
Parser, Lexer, AST, semântico, `main.py`, `src/codegen.py`, runtime, Web didática,
Teste 11 e `legacy/` não foram modificados.

O chamador deve validar a mesma AST semanticamente antes de pedir TAC.
O TAC não resolve novamente tipos, isolamento, nomes globais e FJ-SEM-01..08.
Os diagnósticos semânticos existentes são preservados.

## Convenção das instruções

Esta é a convenção interna textual do Eixo A para inspeção; não muda C-FJ,
AST, envelopes Web ou API C++. Não é uma afirmação de execução da IR.

| Forma | Semântica definida |
|---|---|
| `t = capture v` | Snapshot por valor da entrada da tarefa naquele ponto; listas transportáveis são copiadas recursivamente, sem referência mutável ao chamador |
| `h = fork f(tA, tB) on d` | Criar tarefa assíncrona da função global `f`, com esses valores capturados e esse destino; cada execução dinâmica da instrução produz um novo handle |
| `r = join h` | Esperar/coletar o resultado da tarefa identificada por `h`; disponibilizar o valor somente após sucesso |
| `join h` | Mesma sincronização, descartando o resultado; nenhuma constante ou retorno de none é inventado |
| `join h, timeout v` | Timeout explícito, em milissegundos; também pode ter resultado à esquerda |
| `par_begin R, N` | Iniciar ativação de região paralela com N branches, escopo externo compartilhado por referência |
| `par_spawn R, i, L` | Disparar a branch i em L e continuar o lançador sem esperar seu corpo |
| `par_branch R, i` | Entrada do contexto independente da branch i da ativação R |
| `par_end_branch R, i` | Terminar/sinalizar conclusão da branch; instrução terminal, sem fall-through |
| `par_barrier R` | Suspender o lançador até todas as branches dessa ativação R terminarem |
| `par_end R` | Fechar a região após a barreira e continuar sequencialmente |
| `it = iter_begin v` | Avaliar/bindar uma coleção uma vez e criar cursor na posição inicial, com limite final dessa iteração |
| `ok = iter_has_next it` | Testar cursor antes do fim; falso para coleção vazia |
| `v = iter_value it` | Ler/copiar o elemento atual sem avançar; copiar handle mantém a identidade da tarefa |
| `iter_next it` | Avançar uma posição do cursor |

O protocolo de iterador representa listas, listas de handles, matrizes como
coleções de linhas e coleções retornadas por `range`/helpers sem expandir o laço
durante a geração. `iter_begin` vincula a coleção existente ou mantém o valor
temporário vivo, como o range-for herdado; não aplica captura de tarefa à lista.
Não garante validade de iteradores se o programa modifica estruturalmente a
coleção durante a iteração. Tipo não iterável não ganha conversão ou coleção
inventada; o gerador textual não substitui a análise de tipos/runtime.

Operações sequenciais existentes (`param`, `call`, atribuições, labels, saltos,
índices e operações aritméticas) foram preservadas. Literais string agora usam
escapes JSON, mantendo cada instrução em uma linha e preservando UTF-8.

## Ordem, temporários, handles e controle de fluxo

**Fork:** argumentos da esquerda para a direita, cada expressão uma vez e captura
imediata antes da próxima. Depois avalia-se o destino uma vez e salva-se seu
valor. Destino ausente é `"local"`; literal ou expressão explícita não é resolvido
nem acessado por rede. O nome vem de `ForkExpr.function_name`. Argumentos são
listados na própria instrução de fork, sem disputar uma pilha `param` global.

Chamadas comuns e métodos avaliam todos os argumentos antes de emitir seus
`param` contíguos. Identificadores usados como valores de argumentos são salvos
antes de avaliar o próximo argumento; o mesmo cuidado vale para listas/matrizes.
Assim `pair(x, inc(3))` conclui `inc` antes de abrir os parâmetros de `pair`, e
`fork first(values, values.pop())` captura a lista antes do pop.

**Join:** avalia handle primeiro; se há timeout, salva esse handle antes de
avaliar o timeout. Uso como expressão cria temporário; como comando emite apenas
a sincronização. Erro/timeout significa falha explícita conforme C-FJ-v1,
sem produzir número fictício; a geração não implementa esse tratamento em runtime.
Omitir timeout preserva a política contratual (local sem limite, remoto com
padrão do runtime), sem inventar constante na IR. Não há conversão runtime de
timeout ou de resultado implementada aqui.

Cada novo temporário e label usa contador por programa, compartilhado entre
funções/branches. Identificadores, variáveis, parâmetros e iteradores da fonte
são reservados para evitar colisões com `t0`, `FOR_IN_0` etc. Regenerar a mesma
AST na mesma instância reinicia o estado e produz texto idêntico. Um temporário
de fork é um destino estático; ao executar a instrução repetidamente em um laço,
os handles dinâmicos seriam novos, não uma tarefa por localização textual.
A numeração pode aparecer fora de ordem textual quando o destino de uma coleção
é alocado antes de seus elementos; não implica reordenação da avaliação.

**Seq:** apenas visita os comandos em ordem, sem evento concorrente.
**Par:** um statement imediato vira uma branch; um `seq` dentro dela agrupa seus
comandos na mesma branch. O lançador emite todos os disparos e salta à barreira,
evitando cair nos corpos. Cada corpo termina com `par_end_branch`. Regiões
aninhadas têm IDs e barreiras próprios; os IDs são estáticos, e cada `par_begin`
em laços/recursão denota uma nova ativação, ligada ao contexto do chamador.
Não se criam capturas por valor para os dados compartilhados do `par`.

As pilhas de break/continue são isoladas ao entrar em branch ou função.
Laços locais restauram corretamente os destinos externos quando terminam.
Um `break`/`continue` de branch que tenta atingir laço do lançador falha
explicitamente: o semântico herdado ainda aceita esse caso, mas C++ o coloca
numa lambda onde o salto não é válido. `return` dentro de branch retorna dessa
branch (concluindo-a), conforme a lambda herdada, sem encerrar o lançador.
Nenhum salto conecta corpos de branches diferentes.

**For-in:** binding do iterável fora do laço → label de teste → teste de fim →
leitura/atribuição à variável de iteração → corpo → label do passo → avanço →
salto ao teste → label de saída. `continue` aponta ao passo; `break` à saída.
Também se corrigiu `continue` no do-while para testar a condição antes de repetir.
`&&`/`||` agora têm curto-circuito com labels, impedindo um `join`/fork no operando
direito de acontecer quando a condição o dispensaria. Um operando esquerdo
identificador é salvo se o direito puder ter efeitos.

## Exemplos efetivamente gerados

As fontes estão em `tests/2026_2/core06/examples/`, os textos gerados em
`output/core06/{capture,handles,par}.tac`. Entradas e saídas completas também
constam em [CORE-06_RESULTADOS.json](CORE-06_RESULTADOS.json).

### Captura e timeout — `capture.minipar`

```minipar
func dobro(x) { return x * 2; }
var x = 10;
var h = fork dobro(x);
x = 99;
print(join(h, 30000));
```

```text
func dobro:
t0 = x * 2
return t0
endfunc dobro
x = 10
t1 = capture x
t2 = fork dobro(t1) on "local"
h = t2
x = 99
t3 = h
t4 = join t3, timeout 30000
print t4
```

O snapshot precede a reatribuição; o resultado só alimenta print após join.
Não se afirma que 20 tenha sido executado/impresso por uma tarefa real.

### Seq e branches concorrentes — `par.minipar`

```minipar
seq { print(0); par { print(1); print(2); } print(3); }
```

```text
print 0
par_begin PAR_0, 2
par_spawn PAR_0, 0, PAR_BRANCH_2
par_spawn PAR_0, 1, PAR_BRANCH_3
goto PAR_WAIT_1
PAR_BRANCH_2:
par_branch PAR_0, 0
print 1
par_end_branch PAR_0, 0
PAR_BRANCH_3:
par_branch PAR_0, 1
print 2
par_end_branch PAR_0, 1
PAR_WAIT_1:
par_barrier PAR_0
par_end PAR_0
print 3
```

O lançador só chega ao último print após a barreira; a IR não impõe ordem entre
prints das duas branches. Cada término de branch é terminal.

### Lista de handles e coleta iterativa — `handles.minipar`

```minipar
func f() { return 7; }
var hs = [fork f(), fork f()];
for (var h in hs) { join(h); }
```

```text
func f:
return 7
endfunc f
t1 = fork f() on "local"
t2 = fork f() on "local"
t0 = [t1, t2]
hs = t0
t3 = iter_begin hs
FOR_IN_0:
t4 = iter_has_next t3
ifFalse t4 goto ENDFOR_2
t5 = iter_value t3
h = t5
join h
FOR_STEP_1:
iter_next t3
goto FOR_IN_0
ENDFOR_2:
```

Há duas criações distintas; cada iteração coleta o handle corrente. A IR
contém um corpo com back-edge, não duas execuções desenroladas pelo gerador.

## Testes executados e oráculos

Ambiente observado: Windows 11 `10.0.26200`, Python **3.12.4** da `.venv`, G++
UCRT64 **16.2.0 (Rev6, MSYS2)**. Nenhuma dependência instalada. `CXX`, DLLs no
PATH e codificação foram configurados apenas no processo dos validadores.

```powershell
$env:CXX = 'C:\msys64\ucrt64\bin\g++.exe'
$env:Path = 'C:\msys64\ucrt64\bin;' + $env:Path
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_core02_tac.py -v
.\.venv\Scripts\python.exe -B tests/validate_core02_native.py
.\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core06 -p "test_*.py" -v
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T06
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T07
.\.venv\Scripts\python.exe -B scripts/validar_planejamento.py
git -c safe.directory=C:/Users/victo/Desktop/FACULDADE/Compiladores/minipar-2026-2 diff --check
```

| Verificação | Resultado real | Oráculo |
|---|---|---|
| CORE-06 | **38 PASS, 0 FAIL** | TAC-01..16, ordem/captura, chamadas aninhadas, listas/matrizes, laços, regiões, barreiras, saltos/nomes, mutações, rejeições explícitas, arquivo TAC e guardas |
| CORE-02 TAC | **5 PASS, 0 FAIL** | Corpo/operador/nome mutados, fluxo/vocabulário do T07 e instruções adicionais |
| CORE-02 nativo | **17/17 PASS normal + 17/17 PASS com assertions** | Cada vetor integral comparado com `sorted(entrada)`, stderr vazio e execução bem-sucedida |
| CORE-03 | **78 PASS, 1 KNOWN_FAIL, 0 FAIL** | Stdout exato, erros semânticos/G++, substr e índices; falha herdada explicitamente identificada |
| CORE-04/05 | **126 PASS, 0 FAIL** | Frontend/AST, FJ-SEM-01..08, tipos/isolamento, novo oráculo TAC, guardas e smoke nativo |
| Revisões CORE-04/05 | Incluídas nos **126**, sem contar novamente | `verify_core0405.py` carrega `test_review_regressions.py` (26) e `test_final_review.py` (10) |
| T06 | **PASS** | `[-100, -40, -3, 10, 70, 80]` |
| T07 | **PASS** | `[5, 12, 33, 61, 98]`; mutação TAC PASS; limites/assertions PASS |
| Snapshot histórico T07 | **INFO** | TAC diferente do `.expected.tac`, diferença legítima preservada |
| Planejamento | **PASS** | 43 cards, IDs/datas/dependências/DAG válidos |
| `git diff --check` | **PASS** | Sem erros de whitespace |

Os 38 testes são oráculos da representação e das proteções, não testes de
execução do TAC. Exemplos usam Lexer → Parser → SemanticAnalyzer → TACGenerator.
ASTs diretas são usadas apenas nas fronteiras inválidas/sem suporte.

Logs desta rodada: `output/core06/{core02,native,core03,core0405,core06,t06,t07}.log`.
Evidências nativas completas da rodada final:

- `output/core02/run-20261029-114637-022440/validation.json`;
- `output/core03/run-lnld_pil/summary.json`;
- `output/core0405/run-tu45obo4/summary.json`;
- `output/core01/run-20261029-114636/baseline.json` (T06);
- `output/core01/run-20261029-114657/baseline.json` (T07).

Na primeira rodada paralela, T06/T07 escolheram o mesmo diretório por segundo;
o relatório resumo colidiu. Ambos foram repetidos separadamente, produzindo os
dois diretórios finais acima. Não se usam resumos sobrescritos como evidência.

**KNOWN_FAIL preservado:** HERDADO-RETORNO-NUMERICO, retorno C++ `auto` misturando
int/double, com erro real do compilador. **T01/T02:** intermitências herdadas
continuam abertas; não foram reexecutados nesta tarefa. **T04:** estado parcial
histórico e divergências numéricas continuam; não foi homologado nem reexecutado.
T08–T11, rede entre computadores e CPUlator não foram executados neste card.

## Limitações e fronteira com CORE-07

- O TAC é textual e não executável neste projeto. `par_spawn`, `capture` e
  iteradores têm a semântica acima, sem implementação de VM ou runtime novo.
- `main.py` continua recusando FJ antes de TAC/C++; seu texto diagnóstico legado
  ainda menciona CORE-06/07. O acesso ao TAC FJ nesta entrega é pela API direta.
  `CppCodeGenerator.generate` continua retornando False/CORE-07, sem chamar G++.
  Testes verificam remoção do executável antigo e ausência de artefatos novos;
  arquivo antigo não é apresentado como compilação válida.
- **Sem suporte explícito:** argumentos de construtores não eram representados
  pelo TAC e agora são recusados; em programas FJ, inicializadores de atributos
  com efeitos/chamadas são recusados conservadoramente, mesmo se uma chamada
  específica não tiver FJ. Isso evita apagar disparos/sincronizações transitivos.
  Inicializadores simples e métodos preservam o tratamento legado. Não se
  implementou um modelo novo de inicialização de objetos neste card.
- AST desconhecida em comando/expressão, expressão obrigatória ausente,
  fork sem função/argumento válido, fork descartado e saltos sem laço no contexto
  atual falham explicitamente, sem `?`, `END` ou `CONTINUE` fictícios.
- Permanecem limites herdados de inferência genérica, retornos implícitos none,
  coleções mutadas e ausência de prova de consumo único de handles. Ver CR-CORE05.
  Nomes locais seguem a notação simbólica herdada: não foi introduzido SSA,
  resolvedor de bindings ou executor de memória/escopos para toda a linguagem.
- Concorrência compartilhada de `par` não elimina data races; a representação
  não certifica programas que dependam de uma ordem entre branches.
- Nenhum wrapper, registro de funções, `value_cast`, `start/join` C++, build ID,
  transporte, worker, execução local/remota ou teste de desempenho foi iniciado.
  CORE-07 implementará isso no ramo **independente AST → C++**, preservando os
  contratos e resolvendo `fork_signatures`/`unresolved_fj` e none implícito.

## Verificação documental — regra 11

Consultados/revisados: AGENTS, MEMORY, README, BNF, documentos 00/01/02/04/05,
`planning/cards.json`, CR-CORE05, handoffs CORE-02, CORE-04/05 e integração dev,
template `docs/templates/TEMPLATE_HANDOFF.md`, testes e módulos do compilador
listados no prompt. O presente documento segue os campos do template.

**Atualizados:** README, BNF (somente estado/documentação, sem mudar gramática),
backlog/card (somente autorização/evidência), este handoff e seu JSON.
Nenhum contrato compartilhado, diagrama ou pseudocódigo de outro card foi editado.
A descrição do fluxo e a tabela de instruções acima documentam o código real.
Documentos históricos de auditoria foram preservados como evidências das bases
anteriores, não reescritos para afirmar que já tinham TAC Fork/Join.

**AGENTS.md inalterado:** ownership, ramos AST → TAC/AST → C++, regras, convenções
operacionais e fluxo continuam válidos. A notação interna do novo TAC é específica
do card e está neste handoff; a exceção de entrega local não é política permanente.
**MEMORY.md inalterado:** sua política de manutenção documental permanece íntegra;
resultados e instruções particulares desta tarefa não precisam ser duplicados ali.
Docs 00/01/05 mantêm requisitos, gates e oráculos válidos; doc 02 e CR preservam
as pendências humanas, sem alteração contratual unilateral.

## Revisão local e próximo consumidor

Revisados diff, escopo, guardas, avaliação única, labels/temporários, branches
terminais, barreiras correspondentes, for-in, break/continue, curto-circuito,
ausência de saída fixa, documentação e resultados reais. Não foi encontrada
regressão nova nos testes executados. Nenhum resultado nativo foi atribuído à
execução do TAC. O card não foi promovido a DONE e não houve publicação.

**Próximo consumidor:** coordenador/revisor independente do Eixo A; A/C para
ratificações; CORE-07 para backend, B/CORE-08 para inspeção do texto TAC e futuro
serviço. Recomenda-se revisar primeiro a convenção, os limites de atributos e
controle entre branches, depois autorizar a etapa de publicação em outra instrução.
Nenhuma segunda tarefa foi iniciada.

**Declaração:** não alterei outro eixo nem `legacy/`; o trabalho permanece local,
sem commit/stage/push/PR, na branch CORE-06, para revisão posterior do coordenador.

## Revisão corretiva — 29/10/2026: investigação anterior às correções

Autorização específica: revisar A–D, reproduzir antes de corrigir, permanecer na
mesma branch, sem add/commit/push/PR/merge/rebase. Árvore inicialmente limpa,
HEAD `2fada7ce1fbc70249c42d501566a3aa07188bf90`; base `origin/dev`
`29cff941e4e4a2b7f37b08bf3fc0d24e98c40ce1`. Um commit próprio sobre dev.
Não houve integração de dev nem mudança de branch nesta revisão.

### Publicação posterior à execução inicial — achado C: DOCUMENTAL

`git ls-remote origin refs/heads/dev refs/heads/eixo-a/CORE-06-tac-fork-join-par`
confirmou os SHAs acima nas duas branches remotas. `git log -3`, `show --stat`
e `rev-list --count origin/dev..HEAD` confirmaram o commit CORE-06 com 12 arquivos
e nenhum commit posterior na branch consultada. A consulta GitHub por repositório,
head e estado `all` retornou zero PRs. Nenhum PR foi aberto nesta revisão.

O push posterior foi realizado pelo coordenador, conforme informado no pedido;
a presença do commit remoto foi comprovada independentemente por Git. Refs Git
não identificam sozinhas quem fez o push. O relato inicial “sem commit/push” era
verdadeiro para aquela execução e permanece como histórico. Esta revisão ainda
é local, não publicada. Contratos e card não foram promovidos a FROZEN/DONE.

### Achado A: AMBIGUIDADE DOCUMENTAL; hipótese de bug refutada

Evidência anterior à correção: sete programas reais em
`output/core06_review/investigation-x0ztzjnv/investigation.json`, com fonte,
TAC publicado e anterior, compilação direta pelo backend vigente e execução
com timeout de 10 s, stdout exato, stderr vazio e exit 0:

| Sonda | Saída esperada e observada |
|---|---|
| Return direto de branch, atribuição posterior não executada | `1` |
| Returns condicionais verdadeiro/falso em branches distintas | `1 3` |
| Return em par aninhado e continuação da branch externa | `1 2` |
| Par sem return, controle | `1 2` |
| Return em seq dentro de função | `7` |
| Return de branch dentro de função e retorno posterior da função | `7` |
| Return com valor dentro de branch; valor não retorna ao lançador | `1` |

`codegen.py` emite uma lambda `[&]` por statement imediato, inicia threads e faz
join em todas. Retornar da lambda termina normalmente a thread; join espera essa
conclusão, sem depender de instrução MiniPar adicional. O contrato distingue
par compartilhado de fork isolado, sem exigir sinalização explícita após return.

**Esclarecimento da notação:** `par_end_branch R,i` é terminal no caminho normal
que o alcança. `return [valor]` é um terminal alternativo do contexto invocado:
no corpo da branch, conclui aquela branch, avalia eventual valor e o descarta no
lançador; numa função chamada, retorna dessa função. A conclusão da branch é
inerente à saída de seu contexto, seja por return ou par_end_branch. O lançador
aguarda conclusões, não a passagem obrigatória pela linha par_end_branch.
Uma linha par_end_branch após return incondicional é inalcançável naquele caminho;
não deve ser descrita como executada. O mesmo vale para statements da fonte após
return. Não se removem nem se disfarçam esses caminhos. Um seq não cria outro
destino de return; uma branch de par aninhado cria. A implementação foi preservada.

### Achado B: CONFIRMADO — regressão de aceitação, correção pontual proposta

Parser e AST preservam a lista de argumentos; o semântico visita cada expressão,
mas não valida aridade de construtor. O backend emite `std::make_shared<C>(args)`.
Classes geradas com campos públicos admitem inicialização agregada com parênteses
no C++20 empregado. Não se trata de implementar métodos construtores novos.

| Fonte resumida | Frontend | Backend direto e execução | TAC publicado |
|---|---|---|---|
| `class C{var a=0;var b=0;} new C()` | Aceito | PASS, campos `0 0` | Aceito |
| `class C{var a=0;} new C(1)` | Aceito | PASS, campo `1` | NotImplementedError |
| Campos a/b, `new C(x,y)`, x=2/y=3 | Aceito | PASS, `2 3` | NotImplementedError |
| Campos a/b, `new C(inc(2),inc(4))` | Aceito | PASS, `3 5` | NotImplementedError |
| Campos a/b, `new C(xs.pop(),9)`, xs=[1,2] | Aceito | PASS, `2 9 1` (inclui tamanho restante) | NotImplementedError |
| Classe vazia, `new C(1)` | Aceito | Rejeitado pelo G++, esperado | NotImplementedError |

A versão de TAC em dev emitia somente `new C`, descartando argumentos, chamadas
e efeitos. Portanto havia incompletude histórica **e** uma regressão nova de
aceitação na CLI após a rejeição de CORE-06. A busca nos `.minipar` ativos de tests
não encontrou argumentos de new; a BNF, porém, já contém `new RedeNeural(0.5)`.
Todas as sondas, diagnósticos G++ e TACs estão no JSON da investigação acima.

**Mudança mínima proposta, após concluir A–D:** reutilizar `_arguments` para
avaliar/salvar valores uma vez, na ordem textual adotada pelo TAC, e emitir
`t = new C(v0, v1)`. Preservar exatamente `t = new C` sem argumentos. Não misturar
parâmetros de chamadas aninhadas; não implementar aridade, construtores, herança
ou inicializadores. O backend continuará validando formas que não compila hoje.
Arquivo de produção impactado: somente `src/tac.py`. Risco: alteração legítima da
notação antes inexistente para argumentos; mitigação: oráculos de ordem/efeitos,
mutação de argumentos e comparação nativa. Testes devem falhar antes da mudança.

### Achado D: CONFIRMADO — cobertura ampliada, falhas herdadas preservadas

Script de baseline consultado antes de executar: compilação 240 s, execução 30 s,
repetições configuráveis, stdout/valores conferidos por oráculos, sem necessidade
de interação humana. T02–T07 foram executados sequencialmente em uma única rodada
com `--only T02,T03,T04,T05,T06,T07 --repeat 10`. Evidência:
`output/core01/run-20261029-122423/baseline.json`, exit 1 legítimo.

| Teste | Estado desta investigação | Observação |
|---|---|---|
| T01 original | BLOCKED | `receiveData` faz bind INADDR_ANY; não executar listener amplo nesta revisão |
| T01 restrito, sonda parcial | 2 PASS / 1 FAIL (timeout 30 s) | Só cópia C++ gerada com bind `htonl(INADDR_LOOPBACK)`, sem editar backend/runtime; não homologa original ou rede entre máquinas |
| T02 | FAIL intermitente: 5 PASS / 5 FAIL | `120` concatenado à série (`1200`); mesma falha DEF-02 histórica de print não atômico |
| T03 | PASS | Iterações 1/50/51, pesos e convergência conferidos |
| T04 | PARTIAL | Classificação correta; números divergem da referência, sem tolerância acordada |
| T05 | PASS | 12 produtos e probabilidades, para stdin derivado documentado pelo baseline |
| T06 | PASS | Vetor completo ordenado conforme oráculo |
| T07 | PASS | Ordenação, mutação TAC e build com assertions; snapshot histórico INFO |

T01 restrito foi compilado e executado três vezes, sequencialmente, conferindo
portas 5101/5102 antes de cada tentativa e usando somente 127.0.0.1. O executável
original foi compilado mas **nunca executado**. A instrumentação altera só uma
linha na cópia em output, com assert de substituição única; o código de mensagem
permanece igual. Evidência no JSON de investigação; não é correção do runtime.

`git diff --exit-code origin/dev HEAD` para codegen, cpp_template, parser,
semantic e fontes T01/T02 confirmou ausência de mudanças nesses caminhos.
T01 reproduz o timeout já descrito em DEF-01, e T02 reproduz DEF-02. O C++ é
gerado diretamente da AST, não do TAC. Não há evidência de regressão CORE-06
nessas falhas; nenhuma correção de canal ou impressão será feita neste card.

**Gate de investigação cumprido:** conclusões A–D registradas antes de alterar
qualquer código de produção. Próxima etapa autorizada: testes vermelhos de B,
correção mínima, novas suítes e fechamento documental, sem publicação.

### Correção aplicada após a investigação

Antes de modificar produção, `test_review_core06.py` executou 10 testes:
**3 PASS, 7 ERROR**, exit 1, em `output/core06_review/before_fix.log`.
Os sete erros foram a exceção do TAC publicado para argumentos de new, inclusive
na prova nativa agregada, que exige passar pelo TAC antes de chamar o backend.
Os controles de par/return e de new vazio passaram. Não se usaram resultados
históricos como substituto dessa reprodução.

Correção de produção limitada ao ramo `NewExpr` em `src/tac.py`: avaliar os
argumentos com `_arguments`, salvar identificadores e emitir a lista de valores
na própria instrução de alocação. Sem argumentos, manter o texto anterior.
Não se abriu uma sequência de param para a alocação; chamadas internas concluem
suas próprias sequências antes de emitir new. Exemplo real do teste:

```minipar
class Pair{var a=0;var b=0;}
var x=2;var y=3;var p=new Pair(x,y);
```

```text
# class Pair
x = 2
y = 3
t0 = x
t1 = y
t2 = new Pair(t0, t1)
p = t2
```

**Extensão da notação vigente:** `t = new C(v0, v1)` aloca C com os valores
avaliados, na ordem textual usada pelo TAC para argumentos; `t = new C` continua
sendo a forma sem argumentos. Esses valores não são capturas isoladas de fork.
A instrução não inventa método construtor nem valida aridade ou tipos de campos.
Não certifica ordem relativa de efeitos entre argumentos no C++: esse backend
continua emitindo make_shared e segue suas regras C++ herdadas, sem alteração.

A antiga rejeição `test_unrepresented_constructor_arguments_fail_explicitly`
foi atualizada legitimamente, mantendo a mesma fonte de classe vazia: agora
verifica que o TAC conserva `1` e o backend ainda recebe `make_shared<C>(1)`.
O erro real de G++ para a classe vazia foi reproduzido na investigação. Não se
converteu um programa nativo inválido em sucesso. Os outros 37 testes originais
permanecem; a suíte ganhou 10 testes, totalizando **48**.

`test_review_core06.py` cobre new vazio, literal, variáveis, chamadas aninhadas,
efeito pop único, alocação dentro de chamada externa, mutações de classe/valor,
campos agregados reais e os sete contextos de return. As execuções nativas
conferem stdout integral, stderr e exit, com timeout e artefatos próprios em
`output/core06_review/native-*/result.json`. Não interpretam TAC.

A rejeição conservadora de inicializadores de atributos com efeitos em programas
FJ permanece. A limitação histórica sobre **argumentos de new** na primeira parte
deste documento foi superada por esta correção; os demais limites continuam.
Nenhuma alteração em par/return, assinatura pública, contrato, backend ou runtime.

### Validação final da revisão

Comandos executados com CXX/UCRT64 e PATH somente do processo, Python 3.12.4 da
venv e G++ 16.2.0; sem instalação de dependências:

```powershell
$env:CXX = 'C:\msys64\ucrt64\bin\g++.exe'
$env:Path = 'C:\msys64\ucrt64\bin;' + $env:Path
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe -B output/core06_review/investigate.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core06 -p test_review_core06.py -v
# O comando anterior é a reprodução vermelha, antes da correção.
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core06 -p "test_*.py" -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_core02_tac.py -v
.\.venv\Scripts\python.exe -B tests/validate_core02_native.py
.\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T02,T03,T04,T05,T06,T07 --repeat 10
.\.venv\Scripts\python.exe -B scripts/validar_planejamento.py
git -c safe.directory=C:/Users/victo/Desktop/FACULDADE/Compiladores/minipar-2026-2 diff --check
```

O script de investigação é uma sonda local preservada em output; suas fontes e
resultados selecionados estão no JSON versionado. A baseline foi rodada antes
e depois da correção, sequencialmente, sem colisão de diretórios.

| Verificação após correção | Resultado real |
|---|---|
| CORE-06 | **48 PASS, 0 FAIL**, inclui os 38 oráculos originais com a atualização justificada acima |
| CORE-02 TAC | **5 PASS, 0 FAIL** |
| CORE-02 nativo | **17/17 PASS por build**, normal e com assertions |
| CORE-03 | **78 PASS, 1 KNOWN_FAIL, 0 FAIL**; HERDADO-RETORNO-NUMERICO continua com erro G++ de auto misto |
| CORE-04/05 | **126 PASS, 0 FAIL**, inclui revisões e guardas CLI/C++ |
| Planejamento | **PASS**, 43 cards |
| `git diff --check` | **PASS**, sem erros de whitespace |

Evidências: `output/core06_review/{core06,core02,native,core03,core0405,planning}.log`,
`output/core02/run-20261029-123141-643944/validation.json`,
`output/core03/run-sanu1eyg/summary.json`,
`output/core0405/run-c5nrjgsq/summary.json` e registros discriminados no JSON.

**T01–T07 após a correção:**

| Teste | Estado | Oráculo/limite |
|---|---|---|
| T01 original | **BLOCKED** | Executável original não rodado: bind em todas as interfaces proibido nesta execução |
| T01, sonda restrita anterior | **PARTIAL**, 2 PASS / 1 FAIL | Loopback instrumentado, timeout 30 s na tentativa 2; não é aprovação do teste original |
| T02 | **FAIL**, 9 PASS / 1 FAIL | Uma saída `1200` por mistura do print; repetição confirma intermitência herdada |
| T03 | **PASS** | Iterações 1/50/51, pesos com tolerância 5e-5 e convergência na 51 |
| T04 | **PARTIAL** | `0.00684395, 0.986493, 0.98925, 0.0140296`; classificação XOR correta, valores fora da referência sem tolerância acordada |
| T05 | **PASS** | 12 produtos esperados, probabilidades >0.55; stdin derivado do esperado, sem homologar outra entrada |
| T06 | **PASS** | `[-100, -40, -3, 10, 70, 80]` |
| T07 | **PASS** | `[5, 12, 33, 61, 98]`; mutação e assertions PASS; snapshot TAC histórico INFO |

Baseline final: `output/core01/run-20261029-123255/baseline.json`, exit **1**,
devido a FAIL herdado de T02 e PARTIAL de T04. A execução inicial desta revisão
teve 5/10 PASS de T02, a final teve 9/10; nenhuma das duas homologa estabilidade.
Não se alteraram oráculos, tolerâncias, canal ou impressão para obter PASS.

### Documentos e limites revistos

Atualizados nesta revisão: este handoff; JSON com `initial_execution`,
`subsequent_publication` e `corrective_review`; README sobre publicação/estado
local; BNF sobre representação já prevista de new; backlog e metadados do card
sobre os dois momentos e a autorização corretiva. Números, hashes e exemplos
históricos da execução inicial foram preservados no bloco inicial do JSON.

AGENTS.md e MEMORY.md foram relidos e permanecem inalterados: a revisão não
modifica regras permanentes, ownership, arquitetura de ramos ou política de
documentação. Não há instrução operacional nova a incorporar neles. Contratos,
CR-CORE05 e handoffs CORE-02/04/05 foram verificados e preservados: continuam
válidos como normas/pendências ou evidências históricas das suas bases.

Pendências: ratificações C-FJ-v1 e FJ-SEM-07/08, none implícito e tipos genéricos,
vida/consumo de handles, inicializadores de atributos FJ e limitações do backend
para agregados/construtores. A notação esclarecida resolve A sem nova decisão
contratual; nenhuma aprovação humana foi inferida. CORE-07 continua responsável
por wrappers, registro, conversões e execução real, sem ter sido iniciado aqui.

**Parecer da revisão: COM RESSALVAS, estável no recorte CORE-06 e pronto para
proposta de PR pelo coordenador.** A regressão B foi corrigida e A esclarecido;
T01 está bloqueado no formato original, T02 continua intermitente e T04 parcial.
Esses estados e as ratificações pendentes devem acompanhar a revisão independente.
Nenhum PR, commit, stage ou push foi realizado nesta execução. HEAD preservado
em `2fada7c`; alterações corretivas permanecem locais na mesma branch. Não houve
alteração de dev/main, runtime, Web didática, Teste 11, legado ou contratos.
