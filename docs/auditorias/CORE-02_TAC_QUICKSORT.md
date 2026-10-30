# CORE-02 — TAC autêntico e Quicksort iterativo seguro

**Responsável:** Eixo A / coordenador, execução assistida por Codex.  
**Data inicial:** 23/10/2026. **Revisão:** 26/10/2026. **Branch publicada:** `eixo-a/CORE-02-tac-quicksort-review` (PR #16).
**Base:** `origin/dev` atualizado por `git fetch origin dev`, commit `577df2091340aba1879d3dc958433a9f7b1dd460`.  
**Referências:** ADR-015/016, card CORE-02, doc 05 §2 e baseline CORE-01 (DEF-03/04).

Execução exclusivamente local autorizada pelo coordenador apesar de `ready=false` no backlog. Árvore inicialmente limpa, na branch CORE-04/05; a nova branch nasceu diretamente de `origin/dev`. Essa descrição refere-se à execução local inicial; a publicação posterior e a recuperação estão registradas abaixo. Estados dos cards preservados. **Avaliação técnica: pronto para revisão humana; não é DONE nem integração aprovada.**

## Causas e correções

**DEF-03:** `src/tac.py` retornava `EXPECTED_QUICKSORT_TAC` quando havia uma função de topo chamada `quicksort_iterativo`. O retorno antecipado ignorava o corpo e todas as demais instruções do programa, inclusive a chamada e a impressão finais. Foram removidos a constante e o desvio por nome. `generate_text` agora percorre todos os statements por `_stmt`; expressões continuam passando por `_expr`. Não foi necessário modificar o gerador genérico: ele já representa todos os nós usados pelo T07 corrigido.

O TAC gerado contém a função, a lista vazia, chamadas `len`/`stack.append`/`stack.pop`, condições, os dois laços, `continue`, partição, trocas por índice, retorno, entrada literal, chamada da função e impressão. Não há instrução especial de ordenação, placeholder `?` ou algoritmo substituído por comentário. O nome da função aparece somente como identificador normal de declaração/chamada. Renomeá-la preserva o restante do TAC; substituir seu corpo remove a partição do TAC; mudar `<=` para `>` muda a comparação correspondente.

**DEF-04:** `stack = [0, 4]` alocava dois elementos, mas as gravações `stack[sp] = ...` chegavam aos índices 2, 3 e seguintes. O T07 ativo passa a usar lista dinâmica, `append` para empilhar e `pop` para retirar. O contador manual `sp` foi eliminado. O limite inicial passa a ser `len(arr) - 1`, calculado somente dentro de `if (len(arr) > 1)`, evitando também o underflow de `size()` sem sinal em lista vazia nesta base. Nenhuma correção de `len` do CORE-03 foi incorporada.

A pilha guarda pares `(inicio, fim)`: inicia vazia ou com um par, remove sempre dois elementos e acrescenta sempre dois pares após particionar. Portanto o tamanho permanece par, e `len(stack) > 0` garante os dois `pop`. Intervalos com `inicio >= fim` são descartados antes de acessar `arr`. O particionamento e as trocas continuam sendo o Quicksort iterativo original; intervalos válidos diminuem a cada partição. Não há ordenação pronta nem resposta fixa. A lista devolvida pela função continua sendo usada pelo chamador, respeitando a passagem por valor do backend existente.

`src/codegen.py` não precisou mudar: já traduz `append` para `push_back`, `pop` para `__array_pop` e `len` para `size()`. A execução real confirmou essas operações em conjunto. O pipeline permanece **AST → TAC** e, separadamente, **AST → C++ → G++ → executável**; execução nativa não é apresentada como execução do TAC.

## Arquivos desta entrega

| Arquivo | Alteração |
|---|---|
| `src/tac.py` | Remoção de 51 linhas de hardcode/desvio, sem alteração das regras genéricas |
| `tests/teste7_quicksort_iterativo_tac.minipar` | Pilha dinâmica, limite pelo tamanho real e proteção para listas vazias/unitárias |
| `tests/test_core02_tac.py` | Cinco regressões da API real Lexer/Parser/semântico/TAC |
| `tests/validate_core02_native.py` | Validação reproduzível de 17 entradas em builds normal e com assertions; reutiliza utilitários da baseline |
| `README.md` | Comandos e link para este handoff |
| `docs/auditorias/CORE-02_TAC_QUICKSORT.md` | Este handoff, resultados, limitações e revisão documental |

Os scripts da baseline, os oráculos `.expected.*`, o relatório CORE-01 e `legacy/` permanecem intactos. Nenhum arquivo de runtime, Web didática, contrato compartilhado ou branch CORE-03/04/05 foi alterado.

## Ambiente e comandos executados

Windows 11 `10.0.26200`, Python **3.12.4** da `.venv`, G++ UCRT64 **16.2.0 (Rev6, MSYS2)** em `C:\msys64\ucrt64\bin\g++.exe`. O alias `python` de WindowsApps não iniciou no sandbox; os testes usaram o executável explícito já existente, sem instalar dependências. `CXX` e o diretório das DLLs do G++ só foram definidos no ambiente dos validadores e seus filhos.

Na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -s tests -p test_core02_tac.py -v
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T07
.\.venv\Scripts\python.exe -B scripts/baseline_t01_t07.py --only T06
.\.venv\Scripts\python.exe -B tests/validate_core02_native.py
```

| Verificação | Status observado | Oráculo/evidência |
|---|---|---|
| Regressões de TAC | **PASS**, 5/5; exit 0 | Corpo trivial com mesmo nome gera exatamente declaração `x = 1` e retorno, sem partição; renomeação; mutação do operador; estrutura/vocabulário/saltos; preservação de instruções fora da função |
| T07 MiniPar → C++ → G++ → execução | **PASS**; compilação e execução exit 0 | `Array ordenado: [5, 12, 33, 61, 98]`, stderr vazio |
| T07 mutado pelo script CORE-01 | **PASS**; compilação exit 0 | TAC diferente do fixo; complementado pelo teste direto que compara TAC original e mutado e confere o novo corpo |
| Comparação com `.expected.tac` | **INFO**, diferente | Diferença legítima: referência histórica preservada; não usada como falha nem regravada |
| T07 com `-D_GLIBCXX_ASSERTIONS` | **PASS**; exit 0 | Mesma ordenação acima, sem stderr/abort; resultado também conferido por leitura do log |
| T06 OO | **PASS**; compilação e execução exit 0 | `10 -3 -40 80 70 -100` → `[-100, -40, -3, 10, 70, 80]` |
| Entradas adicionais no build normal | **PASS**, 17/17; exit 0 | Comparação exata de cada vetor completo com `sorted(entrada)` no validador Python |
| Mesmas entradas com assertions | **PASS**, 17/17; exit 0 | Mesmo oráculo, stderr vazio, sem timeout/violação de índice |

Os 17 casos incluem o oficial, vazio, unitário, par invertido, crescente (12), decrescente (12), todos iguais (15), repetidos, negativos, fracionários e sete listas pseudoaleatórias de tamanhos 3, 4, 6, 17, 31, 64 e 127 (`seed=202602`). A ordenação de referência Python existe somente no teste e nunca é fornecida como entrada ou código do programa compilado.

As regressões de TAC incluem um smoke de expressões, funções, chamadas, listas, leitura/escrita de índices, condição com `else`, laço `for`, `break`, negação e impressão ao lado de uma função chamada `quicksort_iterativo`. Não foi preciso ampliar a regressão nativa para caminhos inalterados de T01–T05.

Flags do pipeline: `-std=c++20 -O3 -pthread -lws2_32`. Recompilação do **mesmo C++ gerado**, sem editá-lo:

```text
C:\msys64\ucrt64\bin\g++.exe -std=c++20 -O0 -g -D_GLIBCXX_ASSERTIONS <cpp-gerado> -o <exe-assert> -pthread -lws2_32
```

## Evidências locais

Os JSONs contêm comandos, entradas, stdout, stderr, exit, timeout e versões; os diretórios contêm fontes de teste e artefatos reais. São ignorados pelo Git, mas estão disponíveis neste workspace para a revisão local autorizada.

- [T07 e verificações adversariais/limites](../../output/core01/run-20261023-141107/baseline.json).
- [TAC completo do T07](../../output/core01/run-20261023-141107/t07/output/t07.tac).
- [TAC do corpo trivial mutado](../../output/core01/run-20261023-141107/t07_mutado/output/t07_mutado.tac).
- [T06 e saída ordenada](../../output/core01/run-20261023-141253/baseline.json).
- [17 entradas, resultados esperados/obtidos e dois builds](../../output/core02/run-20261023-141253-885432/validation.json).

SHA-256 dos bytes locais (incluem a convenção de fim de linha):

| Artefato | SHA-256 |
|---|---|
| Fonte T07 corrigida | `6b573f184f262951349cf556123d4e08933019d0a56c4ae970839129f77790c4` |
| TAC T07 gerado | `c6bce0b74dba2af21ffe1f65759ada558ef9865befa812669ec76b6bab66d2e9` |
| Binário T07 normal | `e86fbfda500fd60907f8ac26832e4eba72461483dbb72e3c8c4185420eec42a3` |

Trecho real do início do TAC do T07:

```text
func quicksort_iterativo:
t0 = []
stack = t0
param arr
t1 = call len, 1
t2 = t1 > 1
ifFalse t2 goto ENDIF_0
param 0
t3 = call stack.append, 1
param arr
t4 = call len, 1
t5 = t4 - 1
param t5
t6 = call stack.append, 1
```

Trecho real do corpo trivial mutado pelo script de baseline:

```text
func quicksort_iterativo:
x = 1
return arr
endfunc quicksort_iterativo
```

## Limitações e próximo consumidor

- Validação nativa realizada neste Windows/G++ apenas; Linux e outros toolchains **UNTESTED**. Assertions verificam os acessos executados nestes casos; não constituem prova formal para toda entrada.
- TAC é uma representação textual inspecionada e testada estruturalmente; não foi implementado ou executado um interpretador de TAC. Os testes não certificam todos os nós/combinações da linguagem.
- Quicksort mantém o pivô final e pode ter tempo quadrático para entradas ordenadas/repetidas; não houve refatoração de desempenho.
- DEF-01/02 (T01/T02 intermitentes), strings/coleções do CORE-03 e demais limitações herdadas permanecem fora deste recorte. Não foram corrigidos nem declarados aprovados.
- `seq`/`par` continuam com o tratamento anterior no TAC. Fork/Join e a distinção de paralelismo pertencem ao **CORE-06**. O próximo consumidor recebe o percurso genérico existente sem a interceptação por nome; APIs `generate_text(program)` e `generate(program, output_name)` e seu formato genérico permanecem iguais.
- **Impacto de interface:** o texto do T07 deixa de coincidir com o snapshot histórico e passa a incluir o programa inteiro. Consumidores CORE-06/CORE-08 devem usar o texto derivado da AST. A previsão contratual de `TAC_HARDCODED` era temporária, até CORE-02; não foi alterado o contrato compartilhado nem implementado serviço Web nesta tarefa.

## Verificação documental obrigatória

Verificados `AGENTS.md`, `MEMORY.md`, `README.md`, docs 01/02/03/04/05, doc 08, baseline CORE-01, `BNF-grammar.md` e template de handoff.

- **Atualizados:** README (uso/validação e referência ao novo comportamento) e este handoff.
- **AGENTS.md:** nenhuma atualização necessária. Não mudou ownership, instrução, convenção, arquitetura ou fluxo; a execução local excepcional foi autorizada nesta solicitação, sem criar regra permanente.
- **MEMORY.md:** nenhuma atualização necessária. A política operacional permanece válida; os resultados específicos do card estão neste handoff, sem duplicá-los como regra permanente.
- **BNF:** nenhuma atualização necessária. Apenas operações de coleção, sintaxe e regras já existentes foram utilizadas; não há produção nova.
- **Diagramas/pseudocódigos:** não há modelo ativo do T07 a corrigir nos documentos inspecionados. A descrição/invariante do algoritmo atualizado está neste handoff. Pipeline da ADR-015 e do doc 08 permanece correto.
- **CORE-01 e doc 08:** preservados como evidências históricas das respectivas bases, sem reescrever as falhas passadas.
- **Planejamento, contratos e backlog:** não alterados. A correção executa a ADR-016 e o aceite existente do CORE-02, sem mudança de assinatura/campo/evento ou aprovação automática.

**Handoff:** revisão humana do coordenador/Eixo A; após autorização de publicação, revisão de consumidor para integração. CORE-06 recebe o TAC genérico; CORE-10 pode reproduzir a regressão e CORE-08 consumir o texto real. Nenhum outro eixo nem `legacy/` foi modificado.

## Auditoria de manutenção — 26/10/2026 (PR #16)

Autorização expressa do coordenador nesta tarefa: corrigir documentação pertinente, commitar e publicar na branch original e comentar no PR. Abrange README e notas documentais compartilhadas. A exceção inicial com `ready=false` foi autorizada pelo coordenador para execução local; não transforma contratos pendentes em aprovados nem cards em DONE.

Histórico verificado por `git log origin/dev`: `a61d61e` foi publicado em dev e revertido por `dc7bf47`; `d5d0b52` foi publicado e revertido por `c67f061`. A correção foi reapresentada em `5d0429671111d550fa7e78262082c4f4b992ceb1`, na branch deste PR. Esses commits e reverts são preservados. `origin/dev` consultado nesta auditoria está em `84934b9` e inclui #7/#8/#9; nenhuma publicação desta manutenção tem dev/main como destino.

Erasmo aprovou o PR em 26/10 com ressalvas não bloqueantes. Este novo commit documental poderá exigir renovação da aprovação. Publicação é verificável pelo head remoto e pelo comentário de handoff; não se declara merge ou aprovação deste agente.

Validação novamente executada com Python 3.12.4 da `.venv` e G++ UCRT64 16.2.0 (os mesmos quatro comandos acima): 5/5 testes TAC PASS; T07 PASS, mutação PASS, limites PASS e comparação textual com snapshot INFO/diferente; T06 PASS; 17/17 casos nativos e 17/17 com assertions PASS. Evidências: `output/core01/run-20261026-175616/baseline.json`, `output/core01/run-20261026-175627/baseline.json`, `output/core02/run-20261026-175631-174923/validation.json`. `git diff --check`: PASS. T01/T02 intermitentes e T04 parcial permanecem como baseline histórica; não reexecutados neste recorte documental.

Pendências fora do CORE-02: underflow genérico de `len(x)-1` neste backend (o CORE-03 contém a correção de comprimento com sinal); TAC de for-in sem laço real; continue de do-while pulando a condição; fallback `?`; break/continue fora de laço com labels inexistentes; parâmetros formais ausentes na declaração TAC; parâmetros intercalados em chamadas aninhadas. São achados preexistentes da revisão, não corrigidos nem certificados por esta rodada. Exigem card/aceite próprios antes de ampliar o gerador (consumidores CORE-06/08/10).

O snapshot `.expected.tac` permanece byte a byte intacto, com aviso no seu diretório. Docs 00/08 preservam o diagnóstico histórico, acrescentando referência ao estado deste PR; doc 11 mantém o aceite de integração aberto. O catálogo C-WEB-v1 e PEND-WEB-05 não foram removidos: a proposta `docs/CR-CORE02-TAC-STATUS.md` registra a atualização dependente de aprovação de A/B. Nenhuma assinatura/campo/evento foi alterada.

Documentos verificados: AGENTS, MEMORY, README, docs 00/01/02/03/04/05/08/11, BNF, baseline e template de handoff. Atualizados README, este handoff, notas 00/08/11, CR e aviso dos oráculos. AGENTS e MEMORY não precisam mudar: não houve nova regra permanente, ownership ou fluxo; a autorização é específica desta tarefa. BNF e diagramas não precisam mudar, pois o código funcional e a sintaxe foram preservados. Próximos consumidores: revisores do #16 e CORE-06/08/10.
