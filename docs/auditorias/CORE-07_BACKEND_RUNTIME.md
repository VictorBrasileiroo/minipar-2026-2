# HANDOFF — CORE-07 — backend integrado ao runtime

Responsável: Eixo A/coordenador. Data: 30/10/2026. Branch local:
`eixo-a/CORE-07-backend-runtime`. **Estado: PARTIAL**, disponível para revisão
local independente. Backend completo no recorte tipado demonstrado; CLI integral
BLOCKED por CORE-06 fora de `dev`. Sem stage, commit, push, PR, merge, DONE,
FROZEN ou aprovação de terceiros. Revisão por IA não substitui aceite humano.

## Base e autorização

Árvore inicialmente limpa na branch `eixo-a/CORE-06-tac-fork-join-par`, HEAD
`33bc9d9b1b66ff678fcd0b10932f1b43235c9f63`; nenhum trabalho preexistente alterado.
`git fetch origin` executado e branch nova criada diretamente de `origin/dev`
`29cff941e4e4a2b7f37b08bf3fc0d24e98c40ce1`. A exceção `safe.directory` foi
passada por comando; nenhuma configuração global foi alterada. CORE-04/05 e
runtime estão nessa base. Consulta GitHub na preparação: PR #17 aberto,
`merged=false`, head `33bc9d9`; CORE-06 não foi incorporado informalmente.

O pedido do coordenador autoriza a implementação local CORE-07 e a ampliação
delimitada a semântico, CLI, testes próprios, expectativas de bloqueio e
documentação/metadados. `ready=false`, BACKLOG e dependências administrativas
permanecem preservados. Referências lidas: AGENTS/MEMORY, docs 01/02/04/05,
C-FJ-v1 §2 revisão 2, CR-CORE05, runtime/README, handoffs CORE-04/05 e CORE-06
(o último pela branch/PR de origem). Ratificações existentes continuam pendentes.

## Implementação e arquivos

| Arquivo | Responsabilidade |
|---|---|
| `src/codegen.py` | `generate_text`, caminho FJ, especializações com declarações adiantadas, wrappers/registro, hash, worker, ordenação e compilação real |
| `src/semantic.py` | Publica contextos especializados sem sobrescrever o chamador; `CppType`/`CppTaskContext` provam representação, armazenamento e retorno por chamada na mesma AST |
| `src/cpp_template.py` | Escopo de tarefa por thread, erros controláveis, join aninhado, indexação verificada e pop de bool por valor |
| `main.py` | Reutiliza semântico/fonte no backend; executa TAC e trata sua recusa atual, sem salto de fase |
| `tests/2026_2/core07/test_core07.py` | 13 testes agrupando provas nativas, negativos e proteção de binário antigo |
| `tests/2026_2/core07/test_index_lifetime.py` | Regressão P1: temporários, referências persistentes, matrizes numéricas/textuais, bool, efeitos e oráculo C++ de lifetime |
| `tests/2026_2/core07/compile_backend.py`, `demo.minipar` | Driver explícito de prova direta do backend e exemplo reproduzível |
| `tests/2026_2/core07/compare_base.py` | Exportação de fontes de origin/dev em output e comparação pontual T01/T02/T04 |
| `tests/2026_2/core0405/verify_core0405.py` | Substitui a expectativa de bloqueio geral pela exigência de source/hash; confirma bloqueio na fase TAC, preservando demais oráculos |
| README, BNF, docs/04, planning/cards | Disponibilidade real, limitações e autorização local, sem promoção de estado |
| Este handoff e `CORE-07_RESULTADOS.json` | Resultados selecionados, fontes, oráculos, hashes e logs de worker sanitizados |

Nenhuma alteração em runtime, legacy, Web, Teste 11, Lexer, Parser, AST ou TAC.

## Decisões técnicas e interface

`generate(program, output_name, semantic=None, source=None) -> bool` e
`generate_text(program, semantic=None, source=None) -> str` são extensões
compatíveis das chamadas sem FJ. Em FJ, source é obrigatório para
`sha256(source.encode('utf-8'))`. O semântico fornecido deve ter validado a
mesma AST; se omitido, o backend cria o analisador. Erro de prova textual lança
`CppProofError`; `generate` transforma-o em diagnóstico/False e já invalidou o
executável anterior. Nenhum envelope C-WEB nem API do runtime foi alterado.

O tipo `number` da linguagem não foi redefinido. Inteiros usam o int emitido
pelos literais legados; decimais usam double; size/len têm suas representações
C++ concretas. Literais fora do intervalo int comprovado são recusados neste
recorte. Listas numéricas preservam vector<double>; matrizes preservam o tipo
do inicializador. Divisão inteira continua inteira antes da conversão do
retorno. A escolha legada de retorno double quando há divisão/decimal nos
returns é preservada, incluindo helpers. Retornos incompatíveis sem essa prova
são recusados, em vez de corrigir globalmente o defeito numérico herdado.

Os mapas são separados por `(função, assinatura concreta)`; helpers comuns e
em tarefas reutilizam a mesma especialização quando compatíveis. Todos os
forks visitados devem concordar por função; contextos desconhecidos, funções
recursivas, assinaturas conflitantes e forks em funções sem contexto concreto
são recusados. Não há despacho amplo por Value nem escolha da última assinatura.

Valor exige return incondicional ou cobertura de ambos os ramos de if; laços
não provam totalidade. Return em par termina a lambda da branch, sem provar
retorno externo. Função sem retorno de valor produz Value none; consumo como
valor é recusado. Essa prova também percorre os helpers usados.

TaskHandle é armazenado diretamente e copiado com sua identidade. Booleanos
lidos por índice, pop ou for-in são materializados por valor, sem vazar proxies
de vector<bool>, inclusive ao indexar uma coleção temporária. Listas
homogêneas, inclusive vazia seguida de append, recebem vector<TaskHandle>.
Indexação, cópia, atribuição e coleta em for-in usam o resultado associado.
Listas sem elemento comprovado são recusadas. Listas de strings permanecem
fora do contrato C-T11 atual; classes/canais e métodos de objeto em programas
FJ não cobertos pela prova recebem recusa explícita. Programas sem FJ continuam
no caminho legado, inclusive par/canais/classes.

Pseudocódigo do backend implementado:

```text
validar a mesma AST; provar representações e retornos por chamada
agrupar forks por função; exigir uma assinatura concreta compatível
emitir protótipos e funções especializadas; emitir um wrapper por tarefa
main: definir build_id; registrar wrappers; despachar modo worker
coordenador: executar statements; em fork, avaliar/capturar cada argumento
             em Value em ordem, depois destino; chamar start
join: avaliar/copiar handle, avaliar timeout, coletar e converter o resultado
```

As lambdas imediatas de ordenação usam referências apenas para avaliar a
expressão no chamador. Os temporários e nomes de especializações recebem um
prefixo sem colisão com os identificadores da AST. O transporte para tarefas é Value por valor, materializado
antes do próximo argumento/destino. &&/|| continuam com curto-circuito nativo.

Wrapper ativa um escopo por thread; substr e índices inválidos lançam exceções.
Join no coordenador usa join_or_exit. Join dentro de tarefa usa join e lança
o erro para o runtime produzir TASK_FAILED; branches par propagam seu contexto
e exceções após a barreira. Fora de tarefa, substr mantém o exit legado.
Não se promete recuperar UB, sinais ou encerramentos externos. Não foi criado
protocolo, executor ou serializador alternativo.

Finalização normal imprime/flush e usa _Exit, como os probes do runtime: sem
cancelamento nem espera global. **Sem join não há garantia de conclusão**.

## Testes da rodada inicial (histórico preservado)

Python 3.12.4, Windows 11, G++ 16.2.0 UCRT64. Somente PATH/CXX do processo.
Os workers criados pelos testes usam --bind 127.0.0.1 e são encerrados pelo
runner. subprocessos têm limites de tempo; nada foi instalado globalmente.

```powershell
$env:CXX = 'C:\msys64\ucrt64\bin\g++.exe'
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core07 -v
.\.venv\Scripts\python.exe -B tests/2026_2/core07/compare_base.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_core02_tac.py -v
.\.venv\Scripts\python.exe -B tests/validate_core02_native.py
.\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
.\.venv\Scripts\python.exe -B runtime/tests/run_tests.py --keep-going
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T02,T03,T04,T05,T06,T07 --repeat 1
.\.venv\Scripts\python.exe -B scripts/validar_planejamento.py
git diff --check
git diff --cached --check
```

| Verificação atual | Resultado e evidência |
|---|---|
| CORE-07 | **13 PASS**, exit 0; `output/core07/native-suite.log`, `native-command.json`, `run-puxgqyk8/results.json` |
| Provas nativas FJ | 21 execuções com stdout/exit/erro conferidos: local/remoto, números/divisão/decimais/módulo, string/bool/listas/matriz, none, captura, mutação, handles, ordem/curto-circuito, helpers, worker e falhas |
| Ordem remota | Log confirma RESULT task-2 antes de RESULT task-1, com resultados corretos; `run-puxgqyk8/worker-ids.log` |
| Worker recuperável | substr, helper com join aninhado e par falham em TASK_FAILED; após cada erro, mesmo worker retorna 42 |
| Negativos/backend | 16 casos de fonte, contexto incompatível, retorno não provado, tipos proibidos/desconhecidos; compilador falho invalida executável antigo |
| CORE-02 | **5 PASS** TAC; **17 PASS** nativo e **17 PASS** assertions |
| CORE-03 | **78 PASS, 1 KNOWN_FAIL, 0 FAIL**; HERDADO-RETORNO-NUMERICO preservado |
| CORE-04/05 | **126 PASS**; repetido após ajuste legítimo dos dois oráculos de fronteira |
| Runtime | **15 locais + probe + 7 protocolo + 19 remotos PASS**, exit 0 |
| T03/T05/T06/T07 | **PASS**, incluindo mutação TAC e assertions de T07 |
| T02 | **FAIL intermitente**: rodada inicial FAIL; comparação base e atual: **7 PASS/3 FAIL** cada, impressão intercalada |
| T04 | **PARTIAL** nas duas bases: classificação correta, números divergentes e sem tolerância acordada |
| T01 original | **BLOCKED** para execução: bind INADDR_ANY; apenas compilado |
| T01 restrito | **PARTIAL** em cópia C++ com bind loopback: base 3 PASS; atual 2 PASS/1 timeout, sem prova física |
| CORE-06/CLI integral | **BLOCKED** por PR #17 fora de dev; teste da recusa TAC e remoção de binário antigo PASS |
| Planejamento | **PASS**, 43 cards; BACKLOG/ready preservados |

Logs dos comandos e cópias dos relatórios reutilizados estão em
`output/core07/regression/`. Esses runners também preservaram seus diretórios
padrão em output/core02, core03, core0405, core01 e runtime-tests. Comparação
integral em `output/core07/base-comparison/results.json`; T01/T02/T04 geram o
mesmo corpo C++ antes/depois, excluindo o prelúdio. Não há regressão funcional
nova observada nesse recorte. T01 segue instável, não aprovado integralmente.

O JSON selecionado versionável contém a execução atual; as tentativas iniciais
do desenvolvimento continuam nos diretórios locais e não são promovidas a PASS.
Evidências históricas dos outros handoffs foram preservadas, sem reescrita.

## Reprodução mínima observada

Fonte: `tests/2026_2/core07/demo.minipar`:

```minipar
func twice(x) { return x * 2; }
var destination = input();
var a = fork twice(21) on destination;
var b = fork twice(7) on destination;
print(twice(21), join(b), join(a));
```

```powershell
.\.venv\Scripts\python.exe -B tests/2026_2/core07/compile_backend.py tests/2026_2/core07/demo.minipar demo
'local' | .\output\core07\repro\output\demo.exe
# Em outro terminal; escolher porta livre:
.\output\core07\repro\output\demo.exe --minipar-worker 7000 --bind 127.0.0.1
'127.0.0.1:7000' | .\output\core07\repro\output\demo.exe
```

Esperado e observado nos dois modos: **`42 14 42`**, exit **0**, stderr vazio.
Na execução registrada foi usada a porta livre 64180; comandos e saídas exatos
em `output/core07/repro/results.json`, worker.log e JSON selecionado.
Compilação real: G++ `-std=c++20 -O3 -pthread -I <repo>/runtime/include`, mais
`-lws2_32` no Windows; o comando completo fica no registro de cada build.
O driver prova o ramo AST→C++; não simula nem certifica execução de TAC.

## Documentação, revisão e próximo consumidor

Verificados: README, BNF, docs 01/02/04/05, CR-CORE05, runtime/README,
handoffs CORE-04/05 e CORE-06, AGENTS e MEMORY. Atualizados: README, BNF,
ficha/metadados CORE-07, este handoff e resultados. docs 01/02/05, CR e guia do
runtime não precisam mudar: regras, gramática contratada e APIs permanecem
iguais; o estado de implementação está registrado nesta entrega.

**AGENTS.md e MEMORY.md não precisam de alteração:** ownership, arquitetura
AST→TAC/AST→C++ e política operacional permanecem válidos. A autorização
específica foi registrada no card, evitando transformá-la em permissão geral.

Próximo consumidor: revisor independente local, A/C na integração e RUN-04,
seguido dos testes 8–10; depois do merge autorizado de CORE-06, repetir a CLI
completa e suas regressões. Prova física entre computadores, ratificações
contratuais e revisão humana permanecem pendentes. Não há aprovação tácita.

Diff local: implementação concentrada nos quatro arquivos autorizados, testes
próprios e documentação. `git diff --check` e `git diff --cached --check` sem
erros; índice vazio, HEAD preservado, áreas protegidas intactas. Somente fontes
e evidências selecionadas estão fora de output; nenhum binário versionável.

## Correção P1 da revisão — indexação encadeada de temporários

Na mesma branch, por autorização específica do coordenador, sem stage, commit,
push, PR ou merge. Estado **PARTIAL** preservado pela dependência CLI/CORE-06.
Esta seção e `p1_index_lifetime` no JSON complementam os resultados históricos
acima; não os substituem nem representam nova auditoria geral.

**Causa:** `_fj_index` usava a classe imediata `IndexExpr` como prova de
armazenamento persistente. Em `join(fork f(matrix(2,2,7)))[0][0]`, a linha
intermediária ainda pertence a um temporário. A lambda externa devolvia uma
referência à célula e destruía sua linha proprietária antes da leitura.

**Correção:** percorrer os objetos de toda a cadeia até a raiz. `decltype(auto)`
fica restrito à raiz `IdentifierExpr`; nas demais cadeias o retorno por valor
materializa o elemento antes da destruição do proprietário. Variáveis e suas
linhas/células continuam por referência, sem cópia indiscriminada de matrizes.
Mantidos objeto antes do índice, avaliação única e materialização especial de
bool dentro da lambda, inclusive para temporários e vector<bool>.

Os casos textuais exigiram também três linhas em `SemanticAnalyzer._value_type`:
`matrix(...)[i]` é uma linha/lista, não diretamente a célula. Sem essa informação,
o semântico confundia a segunda indexação válida com indexação de string e
bloqueava os casos de join e escrita persistente pedidos na revisão. A terceira
indexação de uma célula string continua rejeitada e tem teste negativo próprio.
Nenhuma redefinição de tipos da linguagem, API, runtime ou contrato.

Comandos atuais, após configurar CXX/PATH somente no processo como acima:

```powershell
# Controle negativo: snapshot anterior já preservado em output, sem executar UB
$env:PYTHONPATH = 'tests/2026_2/core07'
$env:CORE07_INDEX_CODEGEN = (Resolve-Path output/core07/p1-index-lifetime/codegen_before.py).Path
.\.venv\Scripts\python.exe -B -m unittest test_index_lifetime.IndexLifetimeTests.test_index_reference_contract -v
Remove-Item Env:CORE07_INDEX_CODEGEN
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core07 -v
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
.\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py --case INDEX-MATRIX-STRING-READ --case INDEX-MATRIX-STRING-WRITE --case INDEX-COLLECTIONS --case INDEX-SINGLE-EVALUATION --case EXTRA-NEG-LISTA-STRING
git diff --check
git diff --cached --check
```

Resultados desta correção:

- **Controle negativo confirmado:** exit 1 esperado, diagnóstico
  `CORE07_INDEX_LIFETIME` do compilador contra o snapshot anterior de codegen
  (SHA-256 `85ee9f27cdc22336d4ca9b88402696adda02842d30c0862cfbfb5440828685b5`).
  O mesmo teste passa no backend corrigido: 34 `static_assert` verificam tipo de
  referência de linhas/células persistentes e materialização de temporários e
  booleanos. O oráculo não depende de valores ocasionais nem executa UB antigo.
- **CORE-07 completo: 17 PASS**, exit 0. Quatro testes novos; seis execuções
  nativas novas com stdout/exit/stderr conferidos, além das 21 anteriores.
- **Matrizes temporárias numéricas e textuais:** leitura encadeada após função
  e após join; controles de escrita/leitura persistente, bool, matriz direta,
  objeto e índices com efeitos observáveis executados uma vez na ordem correta.
- **Reprodução original:** três execuções, todas `7\n`, exit 0, stderr vazio.
- **Regressões pertinentes:** CORE-04/05 **126 PASS**; CORE-03 indexação/strings
  **5 PASS**, sem mudar oráculos de string ou repetir a baseline geral.
- **Diagnóstico de memória indisponível:** o probe G++ com
  `-fsanitize=address` falhou no link por ausência de `-lasan`; o probe WSL
  retornou 4294967295. Nenhuma dependência instalada. O controle negativo de
  tipos é determinístico e foi executado com o compilador nativo disponível.

Fontes, C++ gerados, comandos, diagnósticos e resultados atuais em
`output/core07/p1-index-lifetime/`; `full-suite.log`, `before-test.log`,
`sanitizer-availability.json` e `regression-commands.json` identificam cada
verificação. O JSON selecionado registra os caminhos exatos dos novos diretórios,
hashes anteriores/atuais e resultados de cada execução.

Documentos revistos nesta correção: este handoff, resultados, BNF, README,
AGENTS e MEMORY. Atualizados handoff/resultados e a regra de indexação na BNF.
README continua exato e aponta para este handoff; AGENTS/MEMORY não precisam
mudar porque ownership, arquitetura, convenções e fluxo permanecem os mesmos.
Resultados históricos e restrições contratuais preservados. Revisão independente
continua pendente; nenhuma promoção administrativa ou aprovação de terceiros.
