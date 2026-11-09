# DOC-02 — revisão C das seções de runtime e runners da UML

**Data:** 09/11/2026 · **Revisor:** Eixo C (Erasmo), dono de `runtime/` e dos runners T08–T10 · **Documento revisado:** [UML](../15_UML_MINIPAR_2026_2.md), integrado no #42 (`a7454bc`).
**Base de código conferida:** `8d07433` (a mesma que a UML modela). `git diff 8d07433 0d9d5af -- runtime src tests scripts` está vazio: nenhuma mudança de código depois dessa base.
**Escopo:** o que pertence ao Eixo C ou depende do runtime: casos de uso UC12–UC16 (§2.1/§2.2), componente `minipar_rt` (§3.1/§3.2), classes do runtime (§4.9a/§4.9b), sequência Fork/Join (§5.2), linhas de execução e comunicação em §6 e observação 6 de §7. As demais seções foram aprovadas por A no #42 e não foram revistas aqui.

**Veredito:** **APROVADO COM RESSALVAS.** A estrutura do runtime está modelada corretamente: classes, membros, enumerações, composição `ConnectionPool`/`RemoteConnection`/`TaskState`, protocolo `HELLO`/`HELLO_OK`/`TASK`/`RESULT`, frames e semântica de `join`. Há **2 imprecisões** que contrariam o código gerado e precisam ser corrigidas pela regra 11 do AGENTS, e **4 omissões menores** recomendadas. Nenhuma exige mudança de código, contrato ou protocolo.

**Atualização (09/11):** as seis foram corrigidas na UML pelo PR #43; ver §5.

## 1. Imprecisões (corrigir antes do DOC-04)

| ID | Local | O diagrama diz | O código faz | Correção sugerida |
|---|---|---|---|---|
| RC-01 | §5.2, bloco "join h" (linhas 1473–1478) | `main` chama `join_or_exit(handle, timeout)` e recebe `Value` ou `exit 1` | O C++ gerado chama `__fj_join` ([cpp_template.py:351](../../src/cpp_template.py)) e converte com `value_cast<T>` ([codegen.py:73–75](../../src/codegen.py)). `__fj_join` só usa `join_or_exit` fora de tarefa; **dentro de tarefa** usa `join` e lança `runtime_error("<CODIGO>: <msg>")`, que vira `TASK_FAILED` da tarefa mãe (não encerra o processo, em especial o worker) | Trocar a mensagem por `__fj_join(h, timeout)` e acrescentar `alt` "fora de tarefa → join_or_exit / dentro de tarefa → join + exceção → TASK_FAILED"; mencionar `value_cast<T>` |
| RC-02 | §5.2, bloco "fork f(x) — sem destino" (linha 1451); §2.2 UC12 (linha 149) | `start("f", args)`, usando o destino padrão | O gerado sempre passa destino: `start("f", {...}, Destination::parse(std::string("local")))` ([codegen.py:66–69](../../src/codegen.py)). O destino padrão de `start` nunca é usado pelo código gerado | Escrever `start("f", args, Destination::parse("local"))` nos dois lugares |

**Evidência executada (09/11, Windows 11, G++ 16.2.0 UCRT64, Python 3.14.7):** `python -B runtime/tests/run_tests.py` → 6/6 etapas PASS e 17/17 casos de `test_interop.cpp`, incluindo `join aninhado em tarefa: falha da filha vira TASK_FAILED da mae` e `join_or_exit encerra com codigo 1` (RC-01). `python -B runtime/tests/interop_codegen.py` → (a) local, (b) worker no loopback e (c) queda do worker → `WORKER_LOST` PASS; o (a) compila um programa pelo gerador real (RC-02). Tudo no loopback: **não prova dois computadores**.

## 2. Omissões menores (recomendadas, não bloqueiam)

| ID | Local | Omissão | Fonte |
|---|---|---|---|
| RC-03 | §4.9a/§4.9b | `Executor` aparece só como "tarefa local" (`api ..> Executor`). Também roda a leitura (`run`) e a escritora (`write_loop`) de cada `RemoteConnection` e, no worker, `serve_connection` e cada `run_task`. O worker ainda depende de `execute`/`Registry` (só executa funções registradas no próprio binário) | [remote.hpp:88, 247](../../runtime/include/minipar_rt/remote.hpp), [worker.hpp:63, 162, 192](../../runtime/include/minipar_rt/worker.hpp) |
| RC-04 | §4.9b `RemoteConnection` | Faltam `-state_: State {Connecting, Ready, Dead}` e `-sock_: Socket` (composição, como em `WorkerConnection`). O estado explica que `submit` numa conexão `Dead` conclui a tarefa na hora com o erro da conexão; `fail_all` também chama `ConnectionPool.remove` (dependência inversa não desenhada) | [remote.hpp:94–128, 159–181](../../runtime/include/minipar_rt/remote.hpp) |
| RC-05 | Texto após §5.2 (linhas 1481–1485) | Lista de falhas incompleta: frame/mensagem inválidos → `PROTOCOL_ERROR`; envio parado por `MINIPAR_RT_SEND_TIMEOUT_MS` (padrão 10 s) → `WORKER_LOST`; `join` remoto sem timeout usa `MINIPAR_RT_REMOTE_TIMEOUT_MS` (padrão 60 s) e `TIMEOUT` mantém o handle válido. Também: `start_local` confere `find_function` na thread do chamador antes do `submit` (função ausente → `UNKNOWN_FUNCTION` sem criar thread) | [remote.hpp:33–44, 260–298](../../runtime/include/minipar_rt/remote.hpp), [core.hpp:313–324](../../runtime/include/minipar_rt/core.hpp), [api.hpp:21–26, 80–91](../../runtime/include/minipar_rt/api.hpp) |
| RC-06 | §2.1/§2.2 UC15 | Os runners `run_t08.py`, `run_t09.py`, `run_t10.py` e `smoke_int01.py` também iniciam o worker (`--minipar-worker`, loopback). Hoje UC14 só se liga ao "Operador do worker (outro computador)" | runners em `tests/2026_2/test08–10/` e `scripts/` |

## 3. Conferido sem ressalva

- §3.1/§3.2: `minipar_rt` header-only, fornece C-FJ-v1 §2.3; binário inclui o runtime e fala C-FJ-v1 §2.6 como coordenador e como worker; dono C; depende de threads e sockets do SO.
- §4.9a: `ErrorCode` (10 valores, mesma ordem), `TaskError`, `TaskHandle` (`id`, `task_id`), `TaskResult.success/failure`, `Destination` (`local`, `remote`, `parse`; IPv6 literal recusado), `TaskState`, `Registry` (nunca destruído), `join` (TIMEOUT mantém handle; coleta invalida o handle), `join_or_exit` (stderr + `_Exit(1)`).
- §4.9b: uma `RemoteConnection` por `host:porta` no `ConnectionPool`; `pending_` por `task_id`; `WorkerConnection` com `Socket` e `write_m`; `worker_main_if_requested` devolve -1 sem a flag, bind padrão `127.0.0.1`; frame de 4 bytes big-endian, 1..8 MiB (`kMaxFrame`); `FrameStatus {Ok, Closed, Invalid}`.
- §5.2: ordem `set_build_id(sha256)` → `register_function` → `worker_main_if_requested` igual a [codegen.py:136–139](../../src/codegen.py); campos de `HELLO`, `HELLO_OK`, `TASK` e `RESULT` iguais ao código; `TASK` só sai depois do `HELLO_OK` (a escritora só começa com a conexão `Ready`); `VERSION_MISMATCH` por `build_id`/`protocol_version`, `WORKER_LOST` e `WORKER_UNAVAILABLE` corretos.
- §6/§7: `Executor` como execução; `RemoteConnection`, `ConnectionPool`, `WorkerConnection` e `net` como comunicação; runtime incluído por `-I runtime/include`.
- Sonda do autor reexecutada nesta revisão: `python -B docs/auditorias/DOC-02_sondas_uml.py` → **853/853 PASS** (Python 3.14.7; sem `.venv` nesta máquina). A sonda confere nomes e membros, não a semântica das setas; RC-01..RC-06 vêm da leitura do código e dos testes acima.

## 4. Encaminhamento

- **B (dono do DOC-02):** corrigir RC-01 e RC-02 em `docs/15_UML_MINIPAR_2026_2.md` e, se possível, RC-03..RC-06; repetir a sonda. C revisa a correção. *(Superado pelo §5: C aplicou as correções no #43, e B as revisa.)*
- **Estado:** revisão C registrada; aceite técnico conjunto do DOC-02 continua **PARTIAL** até a correção de RC-01/RC-02 ou até a coordenação aceitar a ressalva de forma explícita. *(Ver §5.)*
- **Fora do escopo:** renderização Mermaid (UNTESTED nesta revisão), seções sem runtime (aprovadas por A), RUN-05 `par_rede` e reprodução RUN-06 em dois computadores (continuam PENDING).
- **Impacto de interface:** nenhum. Nenhum código, contrato ou diagrama alterado por esta revisão.

## 5. Correções aplicadas (09/11, PR #43)

A pedido do responsável pelo Eixo C, as correções foram aplicadas por C no próprio #43. A UML é de B (DOC-02); por isso a mudança fica sujeita à aprovação do Riquelme, revisor do #43. Só mudou o texto e os diagramas de `docs/15_UML_MINIPAR_2026_2.md`; nenhum código.

| ID | Onde | O que mudou |
|---|---|---|
| RC-01 | §5.2 (bloco "join h"), §4.6 e texto após §5.2 | `main` chama `__fj_join`. `alt` fluxo principal → `join_or_exit` / dentro de tarefa → `join`. Depois, `value_cast` ao tipo do join; no fluxo principal o erro vai para stderr com código 1, dentro de tarefa vira exceção e `TASK_FAILED` da tarefa mãe. `TIMEOUT` mantém o handle |
| RC-02 | §5.2 (bloco "fork sem destino"), §2.2 UC12/UC13, §4.6 | `start("f", args, Destination::parse("local"))`; UC13 com `Destination::parse("host:porta")` |
| RC-03 | §4.9b | `Executor` e `api` declarados no bloco; `RemoteConnection ..> Executor` (leitura e escrita), `worker ..> Executor` (conexão e tarefa), `worker ..> api` (`execute`); legenda explica |
| RC-04 | §4.9b | `RemoteConnection` ganhou `-state_: State` e `-sock_: Socket`, `*-- Socket` e `..> ConnectionPool` (`remove` em `fail_all`); legenda explica `Connecting/Ready/Dead` |
| RC-05 | §5.2 | `find_function` antes do `submit` (`UNKNOWN_FUNCTION` sem thread); notas de thread de leitura e de escritora; lista de falhas com `PROTOCOL_ERROR`, envio parado (`MINIPAR_RT_SEND_TIMEOUT_MS`, 10 s) e timeout remoto padrão (`MINIPAR_RT_REMOTE_TIMEOUT_MS`, 60 s) |
| RC-06 | §2.1, Nota 2.1, §2.2 | `UC15 «include» UC14` (worker no loopback); UC14 "incluído por UC15"; UC15 cita os runners que sobem o worker |

**Verificação:**
- `.venv/Scripts/python.exe -B docs/auditorias/DOC-02_sondas_uml.py` → **862/862 PASS**. Eram 853; entraram 2 classes, 2 membros e 5 arestas, todos conferidos com o código.
- `mermaid.parse` do `mermaid@11.4.1` (mesma versão do autor), com jsdom e Node 24 numa pasta isolada → **17/17 blocos sem erro de sintaxe**. Controle negativo: 3 blocos quebrados de propósito → 3/3 erros detectados.
- Não houve renderização visual em navegador: o desenho final das setas não foi inspecionado nesta máquina. Fica para a revisão de B no GitHub, que renderiza Mermaid.

**Estado:** RC-01..RC-06 resolvidos no #43. O aceite técnico conjunto do DOC-02 fica completo quando B aprovar o #43.
