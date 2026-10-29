# HANDOFF — CORE-04/05: integração final do PR #15 com dev

**Responsável:** Eixo A/coordenador, execução assistida por Codex.
**Data:** 29/10/2026. **PR:** [#15](https://github.com/VictorBrasileiroo/minipar-2026-2/pull/15).
**Branch:** `eixo-a/CORE-04-05-fork-join`. **Base do PR:** `dev`.
**Contratos consultados:** C-FJ-v1 revisão 2, C-T11-v1 revisão 2,
C-WEB-v1 (catálogo de diagnósticos) e CR-CORE05-FJ-DECISOES.

## Escopo e segurança

Autorização expressa do coordenador para integrar `origin/dev`, resolver conflitos,
validar, criar commit de merge, fazer push na branch original e comentar no PR.
Não iniciar CORE-06/07, não refatorar e não fazer merge do PR no GitHub.

- Head inicial local/remoto: `8bbe1d7840a9e95c81f7651a573a8bea315ec7fa`.
- `origin/dev` integrado: `2218c465f60fcbe6fa8322e4a04f910414acca7a`, merge do #16;
  contém o merge do #14, `ec10f78b4408e308364e72c72cabacfdcd44f977`.
- `git fetch origin`, status, branches, worktrees e `ls-remote` executados;
  árvore inicialmente limpa e branch local igual à remota, sem commits exclusivos.
- Branches locais `dev` (`408afb1`) e `main` (`77d1eb3`) preservadas; worktree
  histórica `output/core02/recovery-dev` preservada.
- Merge usado: `git merge --no-commit --no-ff origin/dev`.
  Sem rebase, force push, reset ou cherry-pick.
- Publicação autorizada exclusivamente por
  `git push origin HEAD:refs/heads/eixo-a/CORE-04-05-fork-join`.
  SHA final e confirmação remota ficam no commit desta entrega e no comentário do PR.

## Resolução e arquivos afetados

Conflito real único: `src/tac.py`, em `TACGenerator.generate_text`.
Resolução pontual: manter o import e a chamada `find_fork_join`, a exceção
`NotImplementedError` com linha/CORE-06 e o percurso de `program.statements`;
remover a constante `EXPECTED_QUICKSORT_TAC` e a condição pelo nome
`quicksort_iterativo`. Nenhum arquivo inteiro foi substituído por ours/theirs.

Os 50 arquivos recebidos/combinados do merge estão enumerados, com hashes Git e
proveniência, em [CORE-04-05_INTEGRACAO_DEV_RESULTADOS.json](CORE-04-05_INTEGRACAO_DEV_RESULTADOS.json).
`docs/04_BACKLOG.md` e `planning/cards.json` foram combinados automaticamente,
preservando a autorização de CORE-04/05 e os registros já presentes em dev.
Nenhum card foi marcado DONE ou contrato aprovado por inferência.

Conferência por conteúdo: `src/semantic.py`, `src/codegen.py`, `src/cpp_template.py`,
Lexer, Parser, AST, `main.py` e BNF continuam iguais ao head inicial do #15.
Os arquivos de runtime e Web recebidos são idênticos a `origin/dev`; não há
alteração própria desses eixos, nem diferença em `legacy/` em relação a dev.
O T07 e os validadores CORE-02 são os recebidos do #16.

Documentos próprios desta integração: este handoff, seu JSON de evidências e
referência datada no handoff CORE-04/05 anterior. Demais arquivos vêm do merge.

## Validação conjunta executada

Ambiente: Windows 11, Python **3.12.4** da `.venv`, G++ UCRT64 **16.2.0**.
`CXX`, `PATH` e `PYTHONIOENCODING` definidos somente no processo e seus filhos;
nenhuma dependência instalada. Todos os nove comandos abaixo retornaram zero.

```powershell
$env:CXX = 'C:\msys64\ucrt64\bin\g++.exe'
$env:Path = 'C:\msys64\ucrt64\bin;' + $env:Path
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_core02_tac.py -v
.\.venv\Scripts\python.exe -B tests/validate_core02_native.py
.\.venv\Scripts\python.exe -B tests/2026_2/core03/verify_core03.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/verify_core0405.py
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T07
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T06
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/test_review_regressions.py
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/test_final_review.py
.\.venv\Scripts\python.exe -B scripts/validar_planejamento.py
```

| Verificação | Resultado observado e oráculo |
|---|---|
| CORE-02 TAC | **5/5 PASS**: mutação de corpo e operador, renomeação, instruções adicionais e estrutura real do T07 |
| CORE-02 nativo | **17/17 PASS** normal e **17/17 PASS** com `_GLIBCXX_ASSERTIONS`; stdout comparado com listas ordenadas, stderr vazio e exit 0 |
| T07 | **PASS**: `[5, 12, 33, 61, 98]`, TAC mutado distinto e execução com assertions sem violação nos casos cobertos |
| Snapshot TAC antigo | **INFO**: texto diferente, esperado após remoção do hardcode; não é oráculo textual novo |
| T06 | **PASS**: `[-100, -40, -3, 10, 70, 80]` |
| CORE-03 | **78 PASS, 1 KNOWN_FAIL herdado, 0 FAIL**; oráculos de strings/substr, erros e proteção de índices verificados |
| CORE-04/05 | **126/126 PASS**, Lexer/Parser/AST, FJ-SEM-01..08, isolamento, tipos, guardas diretas/CLI e smoke nativo legado |
| Revisões específicas | **26/26 PASS** e **10/10 PASS**, também incluídos nos 126, sem somá-los novamente |
| Planejamento | **PASS**, 43 cards, IDs/datas/dependências/DAG válidos |

O KNOWN_FAIL é `HERDADO-RETORNO-NUMERICO`: dedução C++ de retorno `auto`
misturando int/double, com erro real do G++. Não é sucesso funcional.
O smoke legado compila e executa, comparando stdout exato `120 ok! b\npar\n`.
As guardas FJ recusam TAC/C++, removem executável anterior e não chamam G++.
Não há nome `quicksort_iterativo` nem constante de TAC fixo em `src/tac.py`.

Medição adicional executada:

```powershell
.\.venv\Scripts\python.exe -B tests/2026_2/core0405/measure_final_review.py --depth 10 --depth 16 --depth 24 --output output/pr15-integration-20261029/metrics.json
git diff --check origin/dev
git diff --cached --check
```

Cadeias aceitas sem diagnóstico: profundidades 10/16/24 em aproximadamente
0,011/0,028/0,081 s, com 67/154/326 contextos. Tempo mede apenas o semântico;
não é benchmark de execução paralela. `implicit_none` continua **KNOWN_LIMITATION**.

`git diff --check origin/dev`: **PASS**, sem erro novo de whitespace.
`git diff --cached --check` contra o head antigo: **FAIL** por dois espaços finais
de quebra Markdown nas linhas 3 e 5 do handoff CORE-02 recebido de dev.
Arquivo confirmado idêntico a `origin/dev`, preservado como evidência histórica;
isso não foi ocultado como PASS nem motivou edição alheia. Índice sem conflitos.

Evidências locais regeneráveis (logs ignorados em `output/`):

- `output/pr15-integration-20261029/`: logs dos nove comandos, métricas e conferência do merge.
- `output/core02/run-20261029-111426-106687/validation.json`.
- `output/core03/run-170a12im/summary.json`.
- `output/core0405/run-2mvisaq4/summary.json`.
- `output/core01/run-20261029-111451/baseline.json` (T07).
- `output/core01/run-20261029-111530/baseline.json` (T06).

## Documentação, interfaces e pendências humanas

Revisados `AGENTS.md`, `MEMORY.md`, README, docs 00/01/02/03/04/05, BNF,
CR-CORE05, CR-CORE02-TAC-STATUS, handoffs CORE-02/03/04-05 e template de handoff.
Atualizados somente os três documentos próprios identificados acima.

**AGENTS.md e MEMORY.md sem alteração necessária:** não mudaram instruções,
ownership, convenções, arquitetura ou fluxo. A autorização é desta integração.
README, gramática, diagramas e pseudocódigos não exigem nova alteração: o merge
preserva as implementações já documentadas; este handoff registra o estado conjunto.
Descrições datadas de rodadas anteriores continuam históricas.

**Impacto de interface:** nenhuma nova assinatura, campo, evento ou nó AST.
Contratos compartilhados recebidos integralmente de dev, sem alteração unilateral.
O catálogo FJ-SEM-01..06 permanece; 07/08 são extensões propostas na CR e BNF,
com os significados exclusivos cobertos pelos testes. **Ratificação A/C e consulta
a B/CORE-08 permanecem pendentes**, sem bloquear a validação técnica aqui executada.
A proposta documental sobre `TAC_HARDCODED` para CORE-08 também permanece na CR própria.

T01/T02: intermitências históricas conhecidas, não reexecutados neste recorte.
T04: PARTIAL histórico, não reexecutado. T08–T11, CPUlator e execução FJ
local/remota: **UNTESTED** nesta integração. CORE-06/07 não implementados.
Retorno none implícito, unknown, múltiplas assinaturas e vida de handles mantêm
os limites já registrados para o próximo consumidor.

**Parecer técnico: SIM**, a integração dos três PRs passa nos testes pertinentes,
sem regressão nova identificada. A decisão de merge continua humana, condicionada
à revisão independente do head atualizado e às ratificações contratuais pendentes.
A aprovação anterior não é apresentada como revisão deste novo commit.
Próximos consumidores: revisores A/C (e B para diagnósticos), depois CORE-06/07/08/10.
Nenhum merge no GitHub, aprovação própria ou DONE é autorizado por este parecer.
