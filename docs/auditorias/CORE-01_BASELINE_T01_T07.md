# CORE-01 — Baseline reprodutível dos testes herdados T01–T07

**Card:** `CORE-01` · **Eixo:** C (Erasmo) · **Data:** 22/10/2026 · **Base medida:** `dev` em `56c3a1c`
**Branch:** `eixo-c/CORE-01-baseline-t01-t07` · **Consumidor:** Eixo A (`CORE-02`, `CORE-03`, `CORE-10`)

> Baseline do **código ativo do novo repositório**, sem nenhuma alteração em `src/` ou nos programas de `tests/`.
> Não substitui a regressão final (`CORE-10`). Os resultados da auditoria 2026.1 e do SET-02 não foram reaproveitados: tudo abaixo foi executado nesta rodada.

## 1. Resultado

| Teste | Status | Oráculo usado | Observação principal |
|---|---|---|---|
| T01 Calculadora cliente-servidor | **FAIL** (intermitente) | servidor recebe `+ 2 3`; cliente recebe `5` | **4/10** execuções PASS; nas outras 6 o binário trava até o timeout de 30 s (DEF-01) |
| T02 Fatorial/Fibonacci `par` | **FAIL** (intermitente) | fatorial 5 = 120; Fibonacci `0,1,1,2,3,5,8,13` | **9/10** PASS; valores calculados corretos, mas a saída é corrompida às vezes (`1200`, `2120`) porque `print` não é atômico entre threads (DEF-02) |
| T03 Neurônio | **PASS** | valores das iterações 1, 50 e 51 do `.expected.txt` (4 casas), convergência na 51, valor desejado 0 | O texto difere do `.expected.txt` (veio da referência Python); os valores batem |
| T04 XOR | **PARTIAL** | classificação XOR + valores da referência | Classificação correta nas 4 entradas; valores divergem até 0,0151 e **não há tolerância acordada** (doc 05 §2) |
| T05 Recomendação | **PASS** | os 12 produtos do `.expected.txt`, probabilidade > 0,55 | Entrada **derivada** do esperado (seção 3); comparação sem acento |
| T06 Quicksort OO | **PASS** | `10 -3 -40 80 70 -100` → `[-100, -40, -3, 10, 70, 80]` | — |
| T07 Quicksort iterativo | **PASS** (só ordenação) | `[33, 12, 98, 5, 61]` → `[5, 12, 33, 61, 98]` | Ordenação correta no build `-O3`, mas TAC fixo (DEF-03) e acesso fora dos limites (DEF-04) |

Verificações adicionais do T07 (doc 05 §2, "mutação adversarial obrigatória"):

| Verificação | Status | Evidência |
|---|---|---|
| TAC gerado = `teste7_quicksort_iterativo_tac.expected.tac` | idêntico | — |
| Mutação: mesma função `quicksort_iterativo`, corpo trivial (`var x = 1; return arr;`) | **FAIL** | O programa mutado recebe exatamente o TAC fixo: o TAC não é derivado da AST |
| C++ gerado recompilado com `-D_GLIBCXX_ASSERTIONS` | **FAIL** | `stl_vector.h:1253 ... operator[] ... Assertion '__n < this->size()' failed`, exit `0xC0000409` |

**Resumo:** 4 PASS (T03, T05, T06, T07-ordenação), 1 PARTIAL (T04), 2 FAIL intermitentes (T01, T02); TAC do T07 e limites do T07 em FAIL.
Todos os 7 programas **compilam** (`main.py` exit 0, G++ exit 0, binário novo com hash registrado).

## 2. Ambiente e reprodução

| Item | Valor |
|---|---|
| SO | Windows 11 Pro 10.0.26300 |
| Python | CPython 3.14.7 (sistema; o compilador só usa a biblioteca padrão) |
| G++ | `C:\msys64\ucrt64\bin\g++.exe` — 16.2.0 (Rev3, MSYS2), mesmo toolchain do SET-02 |
| Flags | as do `src/codegen.py` (`-std=c++20 -O3 -pthread -lws2_32`); só a verificação de limites usou `-O0 -g -D_GLIBCXX_ASSERTIONS`, compilando o mesmo `.cpp` gerado |
| PATH/CXX | `CXX` e o `bin` do G++ só no ambiente do processo do script; nada persistente alterado |
| Rede | T01 usa `127.0.0.1:5101/5102`; o script recusa rodar (BLOCKED) se as portas estiverem ocupadas e não encerra processos |

```powershell
python -B scripts/baseline_t01_t07.py --repeat 10        # rodada completa (T01/T02 x10)
python -B scripts/baseline_t01_t07.py --only T07          # um caso
```

O script grava `output/core01/run-<data>/baseline.json` (ignorado pelo Git) com, por execução: comando, stdin, stdout, stderr, exit, timeout, duração, SHA-256 da fonte e do binário. Exit: 0 tudo PASS, 1 algum FAIL/PARTIAL, 2 algum BLOCKED.

**Rodadas desta data** (todas em `56c3a1c`): `run-20261022-194437` (T01 x3), `run-20261022-194657` (T01 x10), `run-20261022-195028` (T01 x10) e `run-20261022-195555` (final, T01 e T02 x10, oráculos finais).
As rodadas intermediárias serviram para corrigir **oráculos do script** (T02 e T03 liam o formato errado), não o código testado. Somando as três rodadas com 10 repetições, o T01 passou em **13/30** execuções.

| Teste | SHA-256 da fonte (16 primeiros) | Compilação | Execução |
|---|---|---|---|
| T01 | `1a2b11df5e3ed31b` | exit 0, 6,4 s | 30,1 s (timeout) ou < 1 s quando passa |
| T02 | `6eebdf5515c23305` | exit 0, 2,4 s | 0,09 s |
| T03 | `6a7fab171815e039` | exit 0, 2,4 s | 0,10 s |
| T04 | `fccaeba8391e2dae` | exit 0, 2,4 s | 0,13 s |
| T05 | `8d4924789ebd80da` | exit 0, 3,1 s | 0,12 s |
| T06 | `26564f422dd68c9b` | exit 0, 2,4 s | 0,08 s |
| T07 | `481fea6e0f4ab976` | exit 0, 2,2 s | 0,11 s |

## 3. Entradas (stdin) e oráculos

| Teste | stdin | Origem do oráculo |
|---|---|---|
| T01 | `+`, `2`, `3` (uma por linha) | doc 05 §2 |
| T02 | — | doc 05 §2 |
| T03 | — | `tests/expected_results/teste3_neuronio.expected.txt`, comparado por valor |
| T04 | — | `teste4_rede_neural_xor.expected.txt`; doc 05 §2 (tolerância em aberto) |
| T05 | `1 0 0 0 0 1 0 0 0 1 0 0 1 0 0 0` (uma por linha) | `teste5_recomendacao.expected.txt` |
| T06 | `10 -3 -40 80 70 -100` | `teste6_quicksort_classes.expected.txt` |
| T07 | — | `teste7_quicksort_iterativo_tac.expected.txt` (saída) e `.expected.tac` |

**T05 — entrada derivada.** A base 2026.1 não registra o histórico de compras usado para gerar o esperado. O `.expected.txt` lista 12 dos 16 produtos; os 4 ausentes (índices 0 Smartphone, 5 Jeans, 9 Micro-ondas e 12 Ficção) foram tratados como "já comprados". Com essa entrada, a saída tem exatamente os 12 produtos esperados. O PASS vale para **essa** entrada; se o trio tiver outra entrada oficial, repetir.

**T04 — tolerância.** Valores obtidos: `0.00684395`, `0.986493`, `0.98925`, `0.0140296`; referência `0.0089`, `0.9769`, `0.9758`, `0.0291`. Os mesmos números já aparecem na auditoria 2026.1 (doc 05 §2), ou seja, o comportamento é estável. Fica `PARTIAL` até A+C fixarem a tolerância.

## 4. Defeitos encaminhados ao Eixo A

C não corrige `src/` (AGENTS regra 3). Cada item abaixo é um pedido para card de A.

| ID | Sev. | Teste | Defeito | Evidência | Card sugerido |
|---|---|---|---|---|---|
| DEF-01 | P1 | T01 | Canal TCP perde mensagem e o receptor bloqueia para sempre | 6/10 travam após os prompts; o servidor nunca imprime `Servidor recebeu` | novo card de A (ou `CORE-09`); `RUN-02` oferece transporte alternativo |
| DEF-02 | P2 | T02 (todo `par`) | `print` com vários argumentos não é atômico entre threads: linhas e números se misturam (`1200`, `2120`) | 1/10 corrompida; 3/10 com linhas intercaladas | novo card de A (`src/cpp_template.py`/`codegen.py`) |
| DEF-03 | P0 | T07 | TAC do Quicksort fixo por nome de função | mutação recebe o TAC fixo; `src/tac.py:13` e `:225-226` (`EXPECTED_QUICKSORT_TAC`) | `CORE-02` (já previsto, ADR-016) |
| DEF-04 | P0 | T07 | Programa de teste escreve fora do vetor `stack` | `stack = [0, 4]` tem tamanho 2 e o laço grava `stack[2]`, `stack[3]`…; asserção da libstdc++ aborta | `CORE-02` (já previsto) |

**DEF-01: hipótese de causa** (lida do código, não instrumentada): em `src/cpp_template.py`, `MiniParChannel::sendData` tenta `connect` até 50 vezes **no mesmo socket**. No Winsock, um socket cujo `connect` falhou não pode ser reutilizado, então se a primeira tentativa acontece antes de o receptor abrir o listener, todas as outras falham. A mensagem é descartada sem erro. `receiveData` abre um listener novo **por mensagem** e faz um único `recv` sem enquadramento, então fica parado em `accept` esperando uma mensagem que já foi perdida. O listener também usa `INADDR_ANY` (todas as interfaces). O C-FJ (CON-01) e o `RUN-02` tratam esses pontos no runtime novo (conexão persistente, `send_all`/`recv_exact`, timeout), mas o `c_channel` herdado só muda por card de A (doc 02 §2.6).

## 5. Limitações

- Uma máquina, Windows e G++ UCRT64; Linux não foi testado.
- T01 roda em loopback: prova troca entre threads/sockets do mesmo processo, **não** comunicação entre computadores.
- O PASS do T07 cobre só a ordenação no build `-O3`. O acesso fora dos limites é comportamento indefinido e só "funciona" por acaso.
- As 10 repetições medem a frequência do problema nesta máquina, não uma taxa garantida.

## 6. Verificação documental

- Documentos verificados: `AGENTS.md`, `MEMORY.md`, `docs/01`, `02`, `04`, `05`, `08_ESTADO_DA_BASE_2026_1.md`, `auditorias/SET-02_AMBIENTE_E_SMOKE.md`.
- Criados: este relatório e `scripts/baseline_t01_t07.py`, com o uso descrito no docstring.
- `docs/05_VALIDACAO_E_ACEITE.md` §7 (matriz de estados): **fora do escopo de arquivos do card**. Linha sugerida para o coordenador: `22/10 · 56c3a1c | FAIL* | FAIL* | PASS | PARTIAL | PASS | PASS | PASS (TAC fixo/limites FAIL) | UNTESTED…`, em que `*` indica intermitente; detalhes neste relatório.
- `AGENTS.md`: sem mudança, porque o card não altera regras, convenções, arquitetura ou fluxo.
