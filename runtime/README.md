# Runtime de tarefas `minipar_rt` (Eixo C)

Biblioteca C++20 **header-only** que executa as tarefas de Fork/Join do MiniPar 2026.2, no mesmo processo ou em um worker remoto via TCP. `start` dispara uma tarefa e `join` coleta o resultado ou um erro explícito.
Contrato: [`docs/02_CONTRATOS_TECNICOS.md` §2 (C-FJ-v1)](../docs/02_CONTRATOS_TECNICOS.md). Dono: Eixo C. O backend do compilador (`src/`, Eixo A) **consome** esta API no `CORE-07`; o runtime não altera `src/`.

| Card | Escopo | Estado |
|---|---|---|
| `RUN-01` | Runtime local: registry, `start`/`join`, isolamento, erros, `Value` | implementado e testado |
| `RUN-02` | Protocolo TCP enquadrado, worker pré-compilado, falhas | implementado e testado **no loopback** (prova de protocolo) |
| `RUN-03` | Prova em dois computadores reais | programa e roteiro prontos, ensaio no loopback ok; **execução em duas máquinas BLOCKED** ([roteiro e registro](../docs/evidencias/RUN-03_DOIS_COMPUTADORES.md)) |
| `RUN-04` | Handoff da API para o backend `CORE-07` | contrato dos 13 símbolos testado; interop pela CLI PASS **na integração local com #17/#18** e no loopback (seção 5) |

## 1. Arquivos

```text
runtime/
├── include/minipar_rt/
│   ├── minipar_rt.hpp   # cabeçalho único para incluir
│   ├── value.hpp        # Value, to_value, value_cast (C-FJ-v1 §2.4)
│   ├── core.hpp         # ErrorCode, TaskHandle, TaskResult, Destination, registry, Executor
│   ├── api.hpp          # start, join, join_or_exit (§2.3)
│   ├── json.hpp         # JSON estrito das mensagens (§2.6)
│   ├── net.hpp          # sockets Winsock/POSIX, send_all/recv_exact, frames
│   ├── remote.hpp       # lado coordenador: conexão por destino, HELLO, RESULT por task_id
│   └── worker.hpp       # run_worker, worker_main_if_requested
├── examples/
│   └── demo_distribuida.cpp # RUN-03: coordenador/worker para a prova em dois computadores
└── tests/
    ├── run_tests.py         # compila e executa todos os testes
    ├── test_util.hpp        # mini framework (TEST_CASE/CHECK)
    ├── test_local.cpp       # RUN-01
    ├── join_or_exit_probe.cpp
    ├── test_protocol.cpp    # RUN-02: JSON e frames
    ├── test_worker.cpp      # RUN-02: worker usado nos testes
    ├── test_remote.cpp      # RUN-02: coordenador <-> 2 processos worker
    ├── test_interop.cpp     # RUN-04: API usada pelo C++ gerado (CORE-07), local e remoto
    ├── interop_codegen.py   # RUN-04: MiniPar -> CLI -> C++ gerado -> runtime (exige CORE-07)
    └── fixtures/run04_interop.minipar
```

## 2. Uso

```cpp
#include "minipar_rt/minipar_rt.hpp"
using namespace minipar_rt;

long long soma_quadrados(long long n) { long long s = 0; for (long long i = 0; i < n; ++i) s += i * i; return s; }

int main(int argc, char** argv) {
    set_build_id("<hash do fonte>");                       // o mesmo nas duas máquinas
    register_function("soma_quadrados", [](const TaskArgs& a) {
        return to_value(soma_quadrados(value_cast<long long>(a.at(0))));
    });
    if (int rc = worker_main_if_requested(argc, argv); rc >= 0) return rc;   // modo worker

    TaskHandle h1 = start("soma_quadrados", {1000});                          // local
    TaskHandle h2 = start("soma_quadrados", {2000}, Destination::parse("192.168.0.20:7000"));  // remoto
    TaskResult r = join(h1);                    // r.ok, r.value, r.error.code, r.task_id, r.executed_by
    Value v = join_or_exit(h2, 30000);          // valor, ou mensagem em stderr e exit(1)
}
```

O **mesmo binário** é o worker: `programa --minipar-worker 7000 [--bind <ip>]`. O worker escuta em `127.0.0.1` por padrão; para aceitar conexões de outro computador, passe `--bind` com o IP da máquina na rede local.

Compilação (o mesmo comando vale para o C++ gerado pelo compilador):

```text
g++ -std=c++20 -O2 -pthread -I runtime/include programa.cpp -o programa   [+ -lws2_32 no Windows]
```

**Integração com o C++ gerado (Eixo A):** o cabeçalho inclui `<winsock2.h>`/`<ws2tcpip.h>` no Windows, igual ao prelúdio de `src/cpp_template.py`. Em 22/10/2026, um `.cpp` com o `_CPP_HEADER` atual seguido de `#include "minipar_rt/minipar_rt.hpp"` compilou com `-Wall` e rodou uma tarefa (exit 0). Nenhum arquivo de `src/` foi alterado.

## 3. Comportamento garantido

| ID | Garantia | Teste que cobre |
|---|---|---|
| RT-01 | `start` não espera o cálculo nem a rede (local e remoto): o `TASK` vai para a fila da conexão e uma thread escritora envia | `test_local`: `RT-01 ...`; `test_remote`: `RT-01 remoto ...` e `worker que para de ler ...` (4 `start` de ~7 MiB cada para um worker que não lê retornam em menos de 1 s) |
| RT-02 | Destino inválido não lança no `start`; `join` devolve `BAD_DESTINATION` | `test_local`: `RT-02 ...` |
| RT-03 | Argumentos copiados no `start` | `test_local`: `RT-03 ...` |
| RT-04 | Resultado certo qualquer que seja a ordem de término, inclusive duas tarefas na mesma conexão | `test_local`/`test_remote`: `RT-04 ...` |
| RT-05 | `TIMEOUT` mantém o handle válido | `test_local`/`test_remote`: `RT-05 ...` |
| RT-06 | `join` remoto sem limite usa 60 s (`MINIPAR_RT_REMOTE_TIMEOUT_MS`) | implementação em `core.hpp`/`api.hpp` (não há teste de 60 s) |
| RT-07 | Handle coletado/desconhecido → `INVALID_HANDLE` | `test_local`: `RT-07 ...` |
| RT-08 | Exceção da tarefa → `TASK_FAILED` (local e remoto) | `test_local`: `RT-08`; `test_remote`: `erros remotos ...` |
| RT-09 | Worker morre com tarefas pendentes, ou o envio fica parado mais que `MINIPAR_RT_SEND_TIMEOUT_MS` (padrão 10000 ms) → `WORKER_LOST` sem travar | `test_remote`: `RT-09 worker morre no meio da tarefa` (processo encerrado de fato, exit 3 conferido pelo runner) e `worker que para de ler ...` (o runner usa limite de 1500 ms) |
| RT-10 | `start`/`join` de várias threads | `test_local`: `RT-10 ...` |

Critérios do card `RUN-02` ("fragmentação, frame inválido, worker indisponível e duas tarefas fora de ordem"):

| Critério | Teste |
|---|---|
| Fragmentação | `test_protocol`: `frame: recebido byte a byte`; `test_remote`: `worker aceita HELLO e TASK fragmentados byte a byte`, `coordenador: RESULT fragmentado ...` |
| Mensagens maiores que um `recv` | `test_protocol`: `frame: ... maior que 1 MiB`; `test_remote`: `mensagens maiores que 1 MiB nos dois sentidos` |
| Frame inválido | `test_protocol`: tamanho 0, acima de 8 MiB e fim no meio; `test_remote`: `frame invalido no worker ...` (4 casos: tamanho 0, 2 GiB, JSON quebrado, TASK antes do HELLO; o worker continua atendendo) e servidor falso que manda frame inválido → `PROTOCOL_ERROR` |
| Worker indisponível | `test_remote`: `worker indisponivel ...` e `depois da queda ...` → `WORKER_UNAVAILABLE` |
| Duas tarefas fora de ordem | `test_remote`: `RT-04 remoto: duas tarefas fora de ordem na mesma conexao` |
| IDs / compatibilidade de build | `test_remote`: `160 tarefas em 2 workers ...` (80 por worker, sem perda/duplicação), `build_id diferente vira VERSION_MISMATCH` e `protocol_version` diferente em `TASK` (worker) e em `RESULT` (coordenador) → `VERSION_MISMATCH` |
| Resultado acima de 8 MiB | `test_remote`: `resultado acima de 8 MiB vira TASK_FAILED ...` (resposta imediata, sem esperar o timeout; a conexão continua boa) |

**Execução local:** cada tarefa roda em uma thread de um executor interno que cresce sob demanda. Tarefas simultâneas ganham threads distintas e rodam de fato em paralelo quando há núcleos livres. O runtime **não usa `std::thread::detach`**: com o MinGW-w64/winpthreads do G++ 16.2 UCRT64, uma thread destacada às vezes nunca executava (cerca de 1 em 2000 num teste com 4000 threads), e o `join` ficava esperando para sempre. O teste `estresse: 2000 tarefas...` protege contra essa regressão.

## 4. Protocolo (resumo de C-FJ-v1 §2.6)

- **TCP com conexão persistente por destino.** Frame = 4 bytes de tamanho big-endian + JSON UTF-8, com 1 a 8 MiB.
- **Mensagens:** `HELLO` (`build_id`) → `HELLO_OK` (`worker_id = host:pid`), depois `TASK` (`task_id`, `function_id`, `args`) → `RESULT` (`status` ok/error). `ERROR` fecha a conexão. `protocol_version` é conferido em toda mensagem, nos dois lados.
- **Envio:** o coordenador nunca envia na thread do `start`; uma thread escritora por conexão envia os `TASK` na ordem. Coordenador e worker usam `SO_SNDTIMEO` = `MINIPAR_RT_SEND_TIMEOUT_MS` (padrão 10000 ms): um envio sem progresso por esse tempo fecha a conexão (pendentes → `WORKER_LOST`). O limite é por falta de progresso, não pelo tempo total, então mensagens grandes em rede lenta não são cortadas enquanto avançam.
- **Resultado grande:** `RESULT` que passaria de 8 MiB volta como `status` `error` / `TASK_FAILED`.
- **Worker:** registra em stderr `worker_id`, endereço do coordenador, `task_id`, função, resultado e duração de cada tarefa.
- **Segurança:** o worker só executa funções compiladas e registradas no binário; nenhum código chega pela rede. Ele não tem autenticação nem criptografia: é para uso em rede local de laboratório, nunca exposto à internet.

## 5. Testes

```powershell
python runtime/tests/run_tests.py                 # compila com -Wall -Wextra -Werror e executa tudo
python runtime/tests/run_tests.py --cxx g++       # outro compilador
```

O runner sobe dois processos `test_worker` em portas livres de `127.0.0.1` e encerra os dois no final. O worker B **se encerra de propósito** no teste RT-09 (exit 3, conferido pelo runner). Binários e logs (`worker_A.log`, `worker_B.log`) ficam em `output/runtime-tests/` (ignorado pelo Git).

Resultado em 22/10/2026 (Windows 11, G++ 16.2.0 UCRT64): 15 casos locais + probe, 7 de protocolo, 15 remotos e o ensaio do RUN-03, **todos PASS**. A suíte completa rodou 5 vezes seguidas sem falha; a suíte local, 30 vezes.

Resultado em 23/10/2026, depois da correção da revisão do PR #9 (envio assíncrono com limite, `RESULT` acima de 8 MiB, `protocol_version` em toda mensagem): 15 locais + probe, 7 de protocolo, **19 remotos** e o ensaio do RUN-03, todos PASS no Windows 11 (G++ 16.2.0 UCRT64) e no Linux/WSL2 Ubuntu (G++ 15.2.0). Antes da correção, os 4 casos novos falhavam: o `start` ficava preso no envio, o resultado de 9 MiB só terminava no `TIMEOUT` e as mensagens com outra versão eram aceitas.

**O que estes testes NÃO provam:** execução entre dois computadores. Os testes remotos usam processos diferentes no mesmo host (loopback), ou seja, provam o protocolo. A prova em duas máquinas é o card `RUN-03`.

### Prova em dois computadores (`RUN-03`)

`examples/demo_distribuida.cpp` faz os dois papéis com o mesmo binário:

```text
máquina B:  demo_distribuida --minipar-worker 7000 --bind <IP-de-B>
máquina A:  demo_distribuida --coordenador <IP-de-B>:7000
```

O coordenador imprime cinco verificações: outro host, cálculo remoto conferido, executor = worker, comparação local e queda do worker → erro no `join`. Termina com exit 0 só se todas passarem. O roteiro completo, com compilação, a regra de firewall temporária e o registro da evidência, está em [`docs/evidencias/RUN-03_DOIS_COMPUTADORES.md`](../docs/evidencias/RUN-03_DOIS_COMPUTADORES.md).

O `run_tests.py` ensaia esse roteiro no loopback. Lá, a verificação "outro computador" **tem de** dar `FAIL` (mesmo host) e as outras quatro, `PASS`. Esse ensaio não substitui a execução em duas máquinas.

### Handoff para o backend (`RUN-04`)

O C++ gerado pelo `CORE-07` (PR #18, `src/codegen.py` e `src/cpp_template.py`) usa **13 símbolos** do runtime: `Value`, `value_cast`, `to_value`, `TaskHandle`, `TaskArgs`, `Destination::parse`, `start`, `join`, `join_or_exit`, `to_string(ErrorCode)`, `register_function`, `set_build_id` e `worker_main_if_requested`. Esses 13 são a interface entre os eixos: mudar a assinatura ou o comportamento de qualquer um exige CR (contrato C-FJ-v1).

Build esperado do programa gerado: `-std=c++20 -I runtime/include -pthread`, mais `-lws2_32` no Windows.

Dois testes protegem esse contrato:

- **`test_interop.cpp`** (dentro do `run_tests.py`, não depende de `src/`): chama os 13 símbolos do mesmo jeito que o gerador, com uma cópia do `__fj_join` e do formato dos wrappers/`main` do PR #18. São 17 casos: conversões de `Value` (número, string, bool, listas, matrizes), `Destination::parse` com textos vindos do `input()`, `TaskHandle` copiado, `TASK_FAILED`/aridade/`UNKNOWN_FUNCTION`, `join` aninhado, `BAD_DESTINATION`, `VERSION_MISMATCH` com worker de outro `build_id` e o `join_or_exit` do coordenador (exit 1). Se o runtime mudar de um jeito que quebre o backend, este teste falha primeiro.
- **`interop_codegen.py`** (exige o `CORE-07` na árvore): compila `fixtures/run04_interop.minipar` **pela CLI oficial** (`python main.py`) e executa o binário gerado em três cenários: (a) destino `local`; (b) worker no loopback com o mesmo executável, conferindo no log do worker um `TASK`/`RESULT ok` por função e o PID do worker; (c) worker encerrado pelo PID antes do `join`, que tem de terminar com `WORKER_LOST` e exit 1, sem travar. As entradas são sorteadas (semente impressa) e o resultado esperado é calculado em Python. Sem o `CORE-07`, imprime `BLOCKED: backend CORE-07 ausente` e sai com 2.

```powershell
python runtime/tests/run_tests.py                              # inclui test_interop.cpp
python runtime/tests/interop_codegen.py [--port-base 7100]     # só com o CORE-07 na árvore
```

Resultado em 30/10/2026 (Windows 11, G++ 16.2.0 UCRT64): `run_tests.py` com as 6 etapas PASS (17/17 casos do `test_interop.cpp`); `interop_codegen.py` com (a), (b) e (c) PASS, rodado na **integração local** RUN-03 + `dev` + #17 + #18, que ainda não está em `dev`. Sem o `CORE-07` na árvore, o `interop_codegen.py` dá `BLOCKED`. Nada disso prova execução em dois computadores (RUN-03).

## 6. Limitações conhecidas

- Destino só IPv4 (`host:porta`); IPv6 literal não é aceito.
- Uma tarefa que estoura o `timeout` continua executando; não existe cancelamento (o contrato não pede).
- Worker sem autenticação/TLS (ver seção 4).
- Um worker que para de ler só é detectado depois de `MINIPAR_RT_SEND_TIMEOUT_MS` sem progresso no envio; se o worker ainda lê mas nunca responde, quem limita é o timeout do `join` (60 s remoto por padrão).
- Threads ociosas do executor e de conexões ficam vivas até o fim do processo; programas de demonstração encerram com `std::_Exit` depois de imprimir tudo.
