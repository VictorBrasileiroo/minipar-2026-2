# Handoff — integração CORE-07 / PR #18 — 05/11/2026

**Responsável:** Eixo A/coordenador, assistido por Codex. **Estado:** integração
local preparada para revisão; sem commit, push, atualização remota do PR ou merge
remoto. Não é DONE nem aprovação contratual/humana.

## Base, autorização e preservação

Pedido do coordenador nesta sessão autoriza integrar a branch existente
`eixo-a/CORE-07-backend-runtime`, corrigir CLI/backend/serviço, atualizar os testes
de bloqueios superados e documentar as provas. As restrições administrativas de
ready/status e as ratificações contratuais não foram promovidas.

Árvore inicialmente limpa em CORE-06, HEAD `6013116`. CORE-07 local/remota em
`d7b52d5`. Fetch confirmou `origin/dev=f432cc6`, merge do PR #17, contendo também
CORE-08, Teste 11 e os commits já integrados do runtime. Não houve incorporação
avulsa de PRs de Erasmo. A branch local `dev` não foi movida.

Integração: `git merge --no-commit --no-ff origin/dev` na branch CORE-07.
Histórico preservado; HEAD continua `d7b52d5`, MERGE_HEAD aponta a `f432cc6`.
O merge fica aberto intencionalmente, com conflitos resolvidos no índice,
aguardando revisão e eventual autorização de commit. Não usar o estado de
ancestralidade de HEAD como evidência de merge concluído.

O sandbox exigiu execução autorizada para fetch, switch, merge e escrita do
índice Git. `safe.directory` foi passado por comando; nenhuma configuração
global, PATH do sistema ou dependência foi alterada. Sem rejeição de aprovação
automática. Não havia alterações preexistentes a resguardar.

## Conflitos e correções

Cinco conflitos textuais, resolvidos por trechos, sem substituir arquivos inteiros:

| Arquivo | Resolução |
|---|---|
| `main.py` | Diagnósticos léxicos e validações de dev preservados; guarda temporária removida; TAC real antes de C++; contexto semântico e fonte original encaminhados; recusa TAC mantém mensagem de erro sem dependência obsoleta |
| `src/codegen.py` | Imports por pacote e por script combinados com tipos/nós FJ e `_FJ_HEADER`; mantido `generate_text(program, semantic=None, source=None)`; removida implementação duplicada de `generate`; adotado `compile_cpp` limitado do CORE-08 com include absoluto do runtime |
| `tests/2026_2/core0405/verify_core0405.py` | TAC aninhado real e exigência de fonte preservados; rejeição obsoleta da CLI substituída por compilação e execução com stdout conferido |
| `README.md` | Seções CORE-06 e CORE-07 preservadas; estado atual de CLI/serviço atualizado |
| `BNF-grammar.md` | Convenção TAC/par_return combinada com backend e regra de lifetime; gramática preservada e bloqueios superados corrigidos |

`src/semantic.py` foi combinado automaticamente e inspecionado: diagnósticos e
símbolos do CORE-08 coexistem com contextos especializados CORE-07 e a distinção
linha/célula de matriz. `src/cpp_template.py` preserva `_FJ_HEADER`, escopo de
tarefa, joins aninhados e erros controlados. A correção `_fj_index` que percorre
a cadeia até sua raiz foi preservada, sem copiar indiscriminadamente matrizes.

`src/service.py` encaminha semantic/source da mesma requisição e captura
`CppProofError` como recusa esperada da fase C++, com o código **proposto**
`CPP_UNSUPPORTED_FEATURE`. A localização vem exclusivamente dos prefixos reais
`Linha N:` ou `CORE-07 linha N:`. Exceções inesperadas mantêm INTERNAL_ERROR.
Envelope, seis fases, APIs, isolamento de artefatos, retenção, timeout e limites
de saída permanecem. `analyze` não compila nem registra artefatos.

Compilação comum CLI/API: C++20, `-O3`, `-pthread`, `-I <repo>/runtime/include`,
`-lws2_32` em Windows, timeout 120 s e 65536 bytes por stream. Invalidação de
binário antigo, verificação de existência/tamanho e falha do compilador mantidas.

## Testes e justificativa dos oráculos

Nenhum teste removido. CORE-06, CORE-07 e CORE-04/05 agora esperam sucesso da CLI
porque CORE-06/07 estão presentes; conferem TAC real, execução e binário atual.
A falta de `source` no backend direto continua recusada sem compilar/reutilizar
binário. CORE-08 conserva símbolos sem duplicação, passa a aceitar FJ válido e
exercita a recusa real por retorno não provado, sem pular TAC.

Primeira rodada CORE-08: 35 PASS e 1 FAIL, por uma terceira expectativa antiga
de C++ bloqueado em `test_specialization_not_duplicated`. Corrigida para sucesso
e igualdade dos símbolos publicados. Log/JSON anteriores preservados em
`output/core07/integration/core08-first.{log,json}`.

O runner novo `verify_integration.py` inicialmente esperava WORKER_UNAVAILABLE
na queda de uma conexão já estabelecida. A execução retornou WORKER_LOST;
o oráculo foi corrigido conforme C-FJ §2, RT-09 e catálogo de erros, sem alterar
runtime/produção. WORKER_UNAVAILABLE é falha ao conectar; WORKER_LOST é perda
com tarefa pendente. A primeira tentativa permanece em `e2e.log` e seu diretório
`official-eb21nwm9`; a rodada final fica em `e2e-final.log`/`e2e.json`.

| Verificação | Resultado atual | Evidência |
|---|---|---|
| CORE-06 | PASS, 54 testes | `output/core07/integration/core06.log` |
| CORE-07, incluindo lifetime | PASS, 17 testes | `output/core07/integration/core07.log`, `output/core07/run-rgyjaqv3/results.json` |
| CORE-08 | PASS, 36 testes, zero falhas/erros, 98,860 s | `output/core08/tests-final.{json,log}` |
| CORE-04/05 | PASS, 126 testes | `output/core0405/run-q8p9n8vx/summary.json` |
| CORE-03 | 78 PASS, 1 KNOWN_FAIL, 0 novas FAIL | `output/core03/run-3cxask3l/summary.json` |
| CORE-02 TAC | PASS, 5 testes | `output/core07/integration/core02-tac.log` |
| CORE-02 nativo/assertions | PASS, 17 + 17 casos | `output/core02/run-20261105-085353-870658/validation.json` |
| Teste 11 | PASS, 48/48 verificações locais | `output/core07/integration/test11.log` |
| Terminal e Web antiga | PASS, stdout `5\n`; negativo léxico também conferido | `output/core08/legacy/smoke.json` |
| Runtime | PASS nas cinco etapas do runner, incluindo dois workers e queda em loopback | `output/core07/integration/runtime.log` |
| Planejamento | PASS, 43 cards | `output/core07/integration/planning.log` |
| `git diff --check` | PASS, exit 0, sem diferenças não staged | Conferência final local |
| `git diff --cached --check origin/dev` | PASS, exit 0, recorte do PR | Conferência final local |
| `git diff --cached --check` contra HEAD | FAIL herdado, exit 1, oito ocorrências em artefatos Teste 11 de dev | Três `.arm` com linha final vazia, três `.stdout.txt` com espaço no prompt, e os dois equivalentes `extra_ldr` |
| Baseline adicional T02–T07 | T02 FAIL; T03/T05/T06/T07 PASS; T04 PARTIAL | `output/core01/run-20261105-085655/baseline.json` |

Falha herdada CORE-03: HERDADO-RETORNO-NUMERICO, dedução C++ inconsistente
int/double. T02 falhou nesta execução: Fibonacci `[1,1,2,3,5,8,13]`, ausente o
zero inicial; intermitência de impressão concorrente já registrada no handoff
CORE-07. Não foi alterada para obter PASS. T04 classifica XOR corretamente,
mas mantém divergências numéricas sem tolerância acordada. T01 original não
foi reexecutado; seu bind amplo e suas intermitências continuam fora deste recorte.

Whitespace herdado não foi corrigido: os oito arquivos do Teste 11 são idênticos
a origin/dev, preservados como evidência/oráculo do Eixo B. A falha do diff
integral do merge não é promovida a PASS pelo sucesso do recorte do PR.
O runner CORE-08 registra 36 sucessos/zero falhas em JSON e termina com OK; seus
probes intencionais emitem traceback de logging e erro sintático no stderr.
O redirecionamento PowerShell pode registrar NativeCommandError nesses probes;
esses logs foram preservados, e a avaliação usa também o resultado do unittest.

## Provas ponta a ponta

Runner: `tests/2026_2/core07/verify_integration.py`. Fonte e comandos integrais,
stdin/stdout/stderr, log de worker e envelopes reais em
`output/core07/integration/e2e.json`; diretório final `official-7rtv0pg9`.

| Prova obrigatória | Resultado e oráculo |
|---|---|
| 1. Fork/join local pela CLI oficial | PASS: MiniPar → TAC → C++ → G++ → binário, exit 0, stdout `14 42\n`, stderr vazio |
| 2. Dois handles independentes | PASS: `a=twice(21)`, `b=twice(7)`; coleta `b` antes de `a`, resultados respectivos 14 e 42; suíte CORE-07 também verifica conclusão remota fora de ordem |
| 3. Worker remoto loopback do binário gerado | PASS: mesmo `program.exe --minipar-worker PORT --bind 127.0.0.1`; log confirma duas tarefas `twice`, resultado `14 42\n` |
| 4. Queda com tarefa pendente | PASS: log comprova `fn=slow: inicio`; worker realmente encerrado; coordenador retorna exit 1/WORKER_LOST dentro do limite, sem travamento; suítes também conferem worker sobrevivendo a TASK_FAILED e atendendo nova tarefa |
| 5. Mesmo fonte pela API CORE-08 | PASS: analyze, seis fases de compile, artefatos cpp/tac/binary e execute local, stdout `14 42\n`, stderr vazio |
| 6. Sem Fork/Join nas interfaces anteriores | PASS: CLI e Flask test_client com compilação/execução real, `5\n`; controles de classes, recursão, strings, canais e par nas regressões |
| 7. Matriz temporária encadeada | PASS: quatro testes de lifetime na suíte CORE-07; static_asserts de representação e execução numérica/textual, bool, persistência e ordem de efeitos |

**PARTIAL quanto a distribuição física:** loopback prova processos, protocolo e
binário gerado; não prova dois computadores. O runner do runtime imprime FAIL
esperado para hostname diferente na demo loopback e considera correto esse
resultado negativo. Evidências físicas já presentes em dev vieram do RUN-03;
não foram refeitas nem homologadas aqui. CPUlator não foi executado nesta sessão;
48/48 é o verificador local do Teste 11, preservando as evidências históricas.

## Reprodução

Python 3.12.4, Windows 11, G++ UCRT64 16.2.0. Variáveis somente no processo:

```powershell
$env:CXX='C:\msys64\ucrt64\bin\g++.exe'
$env:PATH='C:\msys64\ucrt64\bin;'+$env:PATH
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core06 -v
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/2026_2/core07 -v
.\.venv\Scripts\python.exe -B tests/2026_2/core07/verify_integration.py
.\.venv\Scripts\python.exe -B tests/2026_2/core08/verify_core08.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
.\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_core02_tac.py -v
.\.venv\Scripts\python.exe -B tests/validate_core02_native.py
.\.venv\Scripts\python.exe -B tests/2026_2/test11/verificar_t11.py
.\.venv\Scripts\python.exe -B tests/2026_2/core08/smoke_legacy.py
.\.venv\Scripts\python.exe -B runtime/tests/run_tests.py --keep-going
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T02,T03,T04,T05,T06,T07 --repeat 1
.\.venv\Scripts\python.exe -B scripts/validar_planejamento.py
git diff --check
git diff --cached --check
git diff --cached --check origin/dev
```

Não há runner único de CI neste checkout; foram usados os validadores existentes
e o pipeline oficial `main.py`, com o runner de integração complementar.

## Documentação, pendências e consumidor

Verificados AGENTS/MEMORY, README/BNF, docs 01/02/04/05, cards, CR-CORE05/08,
handoffs CORE-06/07/08, template de handoff e runtime/README. Atualizados
README, BNF, este relatório/JSON e os adendos dos handoffs/CR. Contratos,
backlog e cards só recebem as mudanças já vindas de dev, sem promoção local.
Pseudocódigo do backend no handoff CORE-07 continua exato; o pipeline de serviço
mantém suas seis fases. Não há diagrama normativo adicional impactado.

**AGENTS.md e MEMORY.md não precisam mudar:** não se alteram ownership,
arquitetura AST→TAC/AST→C++, convenções nem fluxo de revisão. A autorização é
específica desta tarefa e fica registrada aqui.

Áreas protegidas não foram editadas: runtime, Teste 11 e Web didática apenas
recebem o conteúdo já integrado em origin/dev; legacy permanece intocado.
Nenhuma instalação, porta pública ou operação Git destrutiva. A revisão humana
do PR #18 e o aceite do dono/consumidor continuam necessários. A CR-CORE08 segue
PROPOSTA e a publicação do catálogo/tipo task depende de A+B; a integração
técnica não é aprovação tácita. Próximos consumidores: revisor do #18, A/C e
RUN-04, B/CORE-08. Revisar o índice e as evidências antes de autorizar commit/push.
