# HANDOFF — CORE-06: TAC autêntico para Fork/Join e `par`

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
