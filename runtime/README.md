# Runtime de tarefas `minipar_rt` (Eixo C)

Biblioteca C++20 **header-only** que executa as tarefas de Fork/Join do MiniPar 2026.2: `start` dispara uma tarefa e `join` coleta o resultado ou um erro explícito.
Contrato: [`docs/02_CONTRATOS_TECNICOS.md` §2 (C-FJ-v1)](../docs/02_CONTRATOS_TECNICOS.md). Dono: Eixo C. O backend do compilador (`src/`, Eixo A) **consome** esta API no `CORE-07`; o runtime não altera `src/`.

| Card | Escopo | Estado |
|---|---|---|
| `RUN-01` | Runtime local: registry, `start`/`join`, isolamento, erros, `Value` | implementado e testado (seção 4) |
| `RUN-02` | Protocolo TCP, worker pré-compilado | pendente neste build: destino remoto termina com `WORKER_UNAVAILABLE` |

## 1. Arquivos

```text
runtime/
├── include/minipar_rt/
│   ├── minipar_rt.hpp   # cabeçalho único para incluir
│   ├── value.hpp        # Value, to_value, value_cast (C-FJ-v1 §2.4)
│   ├── core.hpp         # ErrorCode, TaskHandle, TaskResult, Destination, registry, Executor
│   └── api.hpp          # start, join, join_or_exit (§2.3)
└── tests/
    ├── run_tests.py         # compila e executa todos os testes
    ├── test_util.hpp        # mini framework (TEST_CASE/CHECK)
    ├── test_local.cpp       # RUN-01
    └── join_or_exit_probe.cpp
```

## 2. Uso

```cpp
#include "minipar_rt/minipar_rt.hpp"
using namespace minipar_rt;

long long soma_quadrados(long long n) { long long s = 0; for (long long i = 0; i < n; ++i) s += i * i; return s; }

int main() {
    register_function("soma_quadrados", [](const TaskArgs& a) {
        return to_value(soma_quadrados(value_cast<long long>(a.at(0))));
    });
    TaskHandle h1 = start("soma_quadrados", {1000});                    // local
    TaskHandle h2 = start("soma_quadrados", {2000}, Destination::parse("local"));
    TaskResult r = join(h1);                    // r.ok, r.value, r.error.code, r.task_id, r.executed_by
    Value v = join_or_exit(h2, 5000);           // valor, ou mensagem em stderr e exit(1)
}
```

Compilação (o mesmo comando vale para o C++ gerado pelo compilador):

```text
g++ -std=c++20 -O2 -pthread -I runtime/include programa.cpp -o programa   [+ -lws2_32 no Windows]
```

## 3. Comportamento garantido (RUN-01)

| ID | Garantia | Teste que cobre (`test_local.cpp`) |
|---|---|---|
| RT-01 | `start` não espera o cálculo; `join` espera o resultado real | `RT-01 start nao espera...`, `RT-01 join devolve calculo real` |
| RT-02 | Destino inválido não lança no `start`; `join` devolve `BAD_DESTINATION` | `RT-02 destino invalido...` |
| RT-03 | Argumentos copiados no `start` | `RT-03 argumentos copiados...` |
| RT-04 | Resultado certo independentemente da ordem de término | `RT-04 tarefas terminam fora de ordem...` |
| RT-05 | `TIMEOUT` mantém o handle válido | `RT-05 TIMEOUT mantem o handle valido` |
| RT-07 | Handle coletado ou desconhecido → `INVALID_HANDLE`; dois joins concorrentes, só um coleta | `RT-07 ...` (2 casos) |
| RT-08 | Exceção da tarefa → `TASK_FAILED` | `RT-08 excecao na tarefa...` |
| RT-10 | `start`/`join` de várias threads | `RT-10 start/join de varias threads...` |
| — | Execução concorrente real (16 × 200 ms em menos de 3,2 s, sobreposição medida) | `execucao concorrente real...` |
| — | 160 tarefas sem perda/duplicação (prévia do T08) | `160 tarefas sem perda nem duplicacao` |
| — | `join_or_exit`: valor ou `[minipar_rt] join <task> falhou: <CODIGO>: <msg>` e código 1 | `join_or_exit_probe.cpp` |

**Execução local:** cada tarefa roda em uma thread de um executor interno que cresce sob demanda. Tarefas simultâneas ganham threads distintas e rodam de fato em paralelo quando há núcleos livres. O runtime **não usa `std::thread::detach`**: com o MinGW-w64/winpthreads do G++ 16.2 UCRT64, uma thread destacada às vezes nunca executava (cerca de 1 em 2000 num teste com 4000 threads), e o `join` ficava esperando para sempre. O teste `estresse: 2000 tarefas...` protege contra essa regressão.

## 4. Testes

```powershell
python runtime/tests/run_tests.py                 # compila com -Wall -Wextra -Werror e executa
python runtime/tests/run_tests.py --cxx g++       # outro compilador
```

Binários em `output/runtime-tests/` (ignorado pelo Git). Usa `CXX` ou, no Windows, `C:\msys64\ucrt64\bin\g++.exe` quando existir.

Resultado em 22/10/2026 (Windows 11, G++ 16.2.0 UCRT64): 15/15 casos PASS e probe PASS; a suíte local repetida 30 vezes seguidas não teve falha nem travamento. Linux: `UNTESTED`.

## 5. Limitações conhecidas

- Destino remoto ainda não implementado neste card (`RUN-02`).
- Uma tarefa local que estoura o `timeout` continua executando; não existe cancelamento (o contrato não pede).
- Threads ociosas do executor ficam vivas até o fim do processo, o que é intencional.
