# HANDOFF — INT-01 — Smoke de integração dos três eixos

**Responsável:** Eixo C (Erasmo) | **Branch:** `eixo-c/INT-01-smoke-integracao` (PR #24, draft, empilhado sobre o `RUN-04`); execução na base de integração local `local/wip-int01` | **Data:** 30/10/2026 | **Contratos usados:** C-FJ-v1 (§2), C-WEB-v1 (§1.2–1.7)

**Estado do card: PARTIAL / BLOCKED. Não marcar DONE.** O segmento A (Eixos A+C) passou na base de integração local; o segmento B (serviço CORE-08) passou só no recorte sem Fork/Join; o segmento C (Web didática) está BLOCKED porque o WEB-03 não começou. No `planning/cards.json` o INT-01 fica `BLOCKED`, `ready=false`, com o PR #24 em draft. As dependências `CORE-07`, `WEB-03` e `RUN-04` não estão concluídas. A execução foi antecipada pelo Eixo C (plano do M2 de 30/10) para encontrar os defeitos de integração cedo. Ela não promove o estado de nenhum outro card. A e B precisam validar os segmentos deles.

## 1. Objetivo e escopo

Ter **um script único e reproduzível** (`scripts/smoke_int01.py`) que exercite o caminho de ponta a ponta de cada eixo e dê um status real por segmento:

| Seg. | Eixos | O que exercita | Base |
|---|---|---|---|
| A | A+C | Programa MiniPar com 2 `fork` e 2 `join`, depois CLI `main.py` (Lexer, Parser, Semântico, TAC, C++, g++), depois o executável com destino `local` e com um worker no loopback | worktree `int01`: RUN-03 + `dev` + PR #17 (CORE-06) + PR #18 (CORE-07), mesclados só localmente |
| B | A+B | `src/service.py` (CORE-08, PR #19): `analyze` → `compile_program` → `execute` → `get_artifact`, com os envelopes do C-WEB-v1 conferidos campo a campo | worktree separada `int01-core08`: só o PR #19 sobre `dev`, executada em subprocesso isolado |
| C | B | Se `web_didatica/` já chama o serviço real (WEB-03) | inspeção estática; nenhum servidor iniciado, nenhuma porta aberta |

O segmento B roda em outra árvore porque o **PR #19 conflita com os PRs #17/#18 em `src/codegen.py` e `src/tac.py`**, conflito verificado pelo Eixo C ao montar a integração local. Resolver esse conflito cabe ao Eixo A. O smoke não tenta resolvê-lo e nunca importa as duas árvores `src/` no mesmo processo Python.

Fora do escopo: a prova entre dois computadores (RUN-03, PR #10), os testes 8–10 e a Web antiga.

## 2. Ambiente

| Item | Valor |
|---|---|
| SO | Windows 11 Pro 10.0.26300 |
| Python | 3.14.7 (`C:\Python314\python.exe`, o mesmo nos dois subprocessos) |
| C++ | `g++.EXE (Rev3, Built by MSYS2 project) 16.2.0` (UCRT64, no PATH do usuário) |
| `int01` HEAD | `f09bdea5396bb8fc1391aa140e6c6a53cbb6fe46` (`local: CORE-07` sobre `local: CORE-06` sobre o merge de `dev` em RUN-03) |
| `int01-core08` HEAD | `28e7329f09d217779e5f5480740f59282b40702b` (PR #19 sobre `dev` `29cff94`) |
| `src/service.py` testado | SHA-256 `42e42ee50e2f3375c0774c2ad0fa3eae49b6b5c59e79fbed17cbb065551b5059` |
| Portas | só 7500–7519 em `127.0.0.1` (worker na 7500, controle negativo na 7501) |

Nada foi instalado e nenhuma configuração global ou PATH foi alterado. Os processos foram encerrados pelo handle/PID que o próprio script criou (nunca `taskkill /IM`). Depois das execuções, `tasklist` não mostrou nenhum `int01_segA.exe` vivo.

## 3. Comandos

Na raiz do worktree `int01`:

```powershell
python scripts/smoke_int01.py                       # A, B e C; resultados em output/int01/results.json
python scripts/smoke_int01.py --only A --port-base 7500 --timeout 30
python scripts/smoke_int01.py --only B --core08-root ..\int01-core08   # ou $env:MINIPAR_CORE08_ROOT
python scripts/smoke_int01.py --only C
```

- **Raiz do CORE-08:** `--core08-root`, depois a variável `MINIPAR_CORE08_ROOT`, depois a pasta irmã `../int01-core08`. Se nenhuma tiver `src/service.py`, o segmento B fica **BLOCKED** com o motivo (testado: `--core08-root ./nao-existe` dá `B0 BLOCKED`).
- **Código de saída:** `0` quando nenhuma verificação executada falhou. Nesse caso cada segmento não BLOCKED é PASS, ou é PARTIAL formado só por PASS mais BLOCKED. `1` quando houve FAIL; `2` para argumentos inválidos (testado: `--port-base 8000`). **Exit 0 com BLOCKED/PARTIAL não conclui o card**, e o script imprime isso no resumo.
- Os oráculos são calculados em Python a partir dos mesmos parâmetros que geram os fontes MiniPar (`soma_quadrados(100)`, `fib(30)`, stdin `int01`). Nenhuma saída esperada foi escrita à mão.
- Cada subprocesso tem limite de tempo: compilação em 300 s, execução em `--timeout` (padrão 30 s), helper do serviço em 1200 s e espera do worker em 15 s.

Arquivos gerados (ignorados pelo Git): `output/int01/results.json`, `segA_fork.minipar`, `segA_compile.log`, `segA_worker.log`, `segB_sem_fork.minipar`, `segB_service_raw.json` (envelopes completos), `run1.log`, `run2.log`, `run_final.log`. O serviço grava seus artefatos em `int01-core08/output/web/<request_id>/`. O `git status` da árvore `int01-core08` continuou limpo.

## 4. Resultados reais

Foram três execuções completas seguidas (`run1`, `run2`, `run_final`), todas com o mesmo resultado: **A PASS, B PARTIAL, C BLOCKED, exit 0**. Os números abaixo são da `run_final` (início 16:21:16 −03:00).

### Segmento A — CLI Fork/Join + runtime: **PASS** (no loopback)

Programa (`output/int01/segA_fork.minipar`, gerado pelo script):

```minipar
func soma_quadrados(n) { ... while (i < n) { s = s + i * i; i = i + 1; } return s; }
func fib(n) { ... }                       // iterativo
var destino = input();
var h1 = fork soma_quadrados(100) on destino;
var h2 = fork fib(30) on destino;
print(join(h2));
print(join(h1));
```

Oráculo Python: `fib(30)=832040`, `sum(i*i for i in range(100))=328350`, então stdout esperado `832040\n328350\n`.

| Verificação | Resultado | Evidência |
|---|---|---|
| A1 CLI `python -B main.py output/int01/segA_fork.minipar int01_segA` | PASS | exit 0, `[Fase 1]`…`[Fase 4]` e `[SUCESSO]`; 13,1 s (g++ `-O3` com o runtime) |
| A2 artefatos | PASS | `output/int01_segA.tac`, `.cpp`, `.exe` existem e não estão vazios |
| A3 TAC | PASS | `t10 = fork soma_quadrados(t8) on t9`, `t13 = fork fib(t11) on t12`, `t14 = join h2`, `t15 = join h1` |
| A4 C++ usa o runtime | PASS | `#include "minipar_rt/minipar_rt.hpp"`, `register_function("soma_quadrados"/"fib")`, `worker_main_if_requested`, `minipar_rt::start(`, `set_build_id(` |
| A5 destino `local` | PASS | stdout `832040\n328350\n`, exit 0, stderr vazio, 263 ms |
| A6 destino `127.0.0.1:7500` (worker `int01_segA.exe --minipar-worker 7500 --bind 127.0.0.1`, PID 44180) | PASS | stdout `832040\n328350\n`, exit 0, stderr vazio, 35 ms |
| A7 log do worker | PASS | TASK e RESULT `ok` das duas funções, todos com o PID 44180 do worker (trecho abaixo) |
| A8 controle negativo `127.0.0.1:7501`, sem worker | PASS | exit 1, stdout vazio, stderr `[minipar_rt] join task-2 falhou: WORKER_UNAVAILABLE: worker 127.0.0.1:7501 indisponivel: ... erro de socket 10061`. Prova que o destino remoto é usado de fato, sem cair em execução local silenciosa |

```text
[minipar_worker Jarvis:44180] escutando em 127.0.0.1:7500 (host=Jarvis pid=44180 build_id=d0f3c84a…44b1)
[minipar_worker Jarvis:44180] TASK task-1 fn=soma_quadrados de 127.0.0.1:50676: inicio
[minipar_worker Jarvis:44180] TASK task-2 fn=fib de 127.0.0.1:50676: inicio
[minipar_worker Jarvis:44180] RESULT task-1 fn=soma_quadrados ok em 0 ms
[minipar_worker Jarvis:44180] RESULT task-2 fn=fib ok em 0 ms
```

O `build_id` do executável (`d0f3c84a…44b1`) é igual ao `source_hash` que o serviço do CORE-08 calculou para o mesmo fonte no segmento B. A regra "build_id = sha256 do fonte UTF-8" está coerente entre o backend do #18 e o serviço do #19.

**Limite:** o PASS vale para a base local `int01`, porque os PRs #17/#18 ainda não estão em `dev`, e para o **mesmo computador**. O loopback prova o protocolo e a integração compilador+runtime. Ele **não** prova a execução entre dois computadores (RUN-03).

### Segmento B — serviço C-WEB-v1 (PR #19): **PARTIAL**

Programa sem Fork/Join (`output/int01/segB_sem_fork.minipar`): as mesmas duas funções chamadas diretamente, mais `print("ola " + input())`, com stdin `int01\n`. Oráculo: `ola int01\n328350\n832040\n`. Chamadas feitas em subprocesso com `cwd=int01-core08` e `from src import service`.

| Verificação | Resultado | Evidência |
|---|---|---|
| B1 importar `src.service` e chamar a API | PASS | helper exit 0, sem exceção |
| B2 envelope `analyze` | PASS | `contract`, `operation`, `request_id` com 32 hex, `source_hash` igual ao sha256 calculado no script, seis fases na ordem e `ok`, `gpp` = `skipped/not_requested`, `artifacts` todos `null`, `diagnostics=[]`, `tac.lines` igual ao número de linhas do texto (3 ms) |
| B3 envelope `compile` | PASS | seis fases `ok`, `gpp.returncode=0`, `artifacts.*_id` igual ao `request_id` `7024828a45be481292ad7190856ae659`, `ok=true` (2,3 s) |
| B4 identidade | PASS | `request_id` diferente em `analyze` e `compile`, mesmo `source_hash` |
| B5 `execute` | PASS | as 11 chaves exatas do `minipar.execute.v1`, `ok=true`, `exit_code=0`, `timed_out=false`, stdout `ola int01\n328350\n832040\n`, igual ao oráculo, stderr vazio, sem truncamento, `error=null` (151 ms) |
| B6 `get_artifact` | PASS | `minipar_7024828a.cpp` / `.tac` / `.exe`, media types `text/x-c++src`, `text/plain`, `application/octet-stream`, arquivos em `output/web/<request_id>/` |
| B7 erros contratuais | PASS | `execute("../x")` dá `INVALID_ARGUMENT` com `exit_code=null`; `execute("0"*32)` dá `ARTIFACT_NOT_FOUND`; `get_artifact(id, "arm")` dá `INVALID_ARGUMENT` |
| B8 programa Fork/Join (o mesmo do segmento A) pelo serviço | **BLOCKED** | `analyze`: `lexer/parser/semantic=ok`, **`tac=error`**, `cpp=skipped/previous_phase_failed`, `diagnostics=[]`. Motivo: conflito do #19 com #17/#18 em `src/codegen.py` e `src/tac.py`. O #19 sozinho não tem o TAC/backend Fork/Join. Isso não é FAIL do Eixo C |

### Segmento C — Web didática (WEB-03): **BLOCKED**

A inspeção de `web_didatica/` encontrou: não há `server.py`; nenhum `.py` importa `service` ou chama `compile_program(`; nenhum `fetch` para `/api/v1/`. Os dados vêm das fixtures via `static/js/fonte_mock.js`, o que confirma o `web_didatica/README.md` ("modo mock (WEB-01)"). Motivo: **WEB-03 não iniciado**. Quando houver indícios de integração, o script passa a marcar `C1` como `UNTESTED` e pede validação com o Eixo B. Ele não sobe servidor sozinho.

## 5. Defeitos e bloqueios classificados

| ID | Seg. | Eixo responsável | Severidade | Descrição | Evidência | Próximo passo |
|---|---|---|---|---|---|---|
| INT01-01 | B | A | Alta (bloqueia FJ na Web e o INT-02) | PR #19 (CORE-08) conflita com #17/#18 em `src/codegen.py` e `src/tac.py`; o serviço não compila Fork/Join | B8: `tac=error` para o mesmo fonte que passa na CLI do segmento A | Victor integra #17/#18 em `dev` e rebaseia o #19; depois disso, repetir `--only B`, em que B8 tem de virar PASS com `execute` igual ao oráculo |
| INT01-02 | B | A | Alta (risco de integração; observado no código, **não executado**) | As interfaces divergem nas duas árvores: o #18 tem `CppCodeGenerator.generate_text(program, semantic=None, source=None)` e põe `-I runtime/include` no g++ dentro de `generate`. O #19 chama `generate_text(program)` sem `source` (que o #18 exige para o hash em FJ) e tem um `compile_cpp` próprio sem `-I runtime/include` | `int01/src/codegen.py:396,466`; `int01-core08/src/codegen.py:267,312`; `int01-core08/src/service.py` (fase `cpp`) | Na resolução do conflito, o serviço precisa passar `semantic` e `source` e compilar com o include do runtime; o handoff do CORE-08 já prevê "adaptar a assinatura textual aditiva" |
| INT01-03 | B | A+B | Média | Uma fase com erro e `diagnostics=[]` não dá ao usuário da Web nenhuma mensagem do motivo da recusa (FJ sem backend) | B8: `tac=error`, `diagnostics: []` | CR `docs/CR-CORE08-DIAGNOSTICOS.md` (pendente, A+B); a Web mostra uma falha genérica da fase até a aprovação |
| INT01-04 | C | B | Alta (bloqueia WEB-04 e INT-02) | WEB-03 não iniciado; a Web didática só usa fixtures mock | C1: sem `server.py`, sem import do serviço, sem `/api/v1` | Riquelme inicia o WEB-03 consumindo `src/service.py` (C-WEB-v1 §1.8); depois repetir `--only C` e acrescentar a verificação por cliente de teste Flask sem porta |
| INT01-05 | A | C | Alta para o aceite final | Prova entre dois computadores pendente: este smoke usa só loopback | A6/A7 usam `127.0.0.1`; RUN-03 `BLOCKED` no `cards.json`, PR #10 | Executar o roteiro `docs/evidencias/RUN-03_DOIS_COMPUTADORES.md` em duas máquinas; repetir o segmento A com o worker na máquina B |
| INT01-06 | A | A | Média | O PASS do segmento A vale para uma base **local** (#17/#18 fora de `dev`). O handoff CORE-07 ainda registra "CLI integral BLOCKED por CORE-06"; nesta base combinada, a CLI integral funciona | A1–A8 PASS em `f09bdea` | Depois do merge de #17/#18 em `dev`, repetir `python scripts/smoke_int01.py --only A` em `dev` e atualizar o handoff CORE-07 |
| INT01-07 | A | A | Baixa (cosmética) | `main.py` mantém a mensagem `integracao CLI CORE-06/CORE-07 pendente` no ramo `NotImplementedError` do TAC, já desatualizada com #17/#18 | `int01/main.py`, `compile_file` | Ajustar o texto na integração; o caminho não foi acionado neste smoke |

Nenhum defeito do runtime (Eixo C) apareceu: as execuções local, remota e o controle negativo se comportaram como o C-FJ-v1 especifica.

## 6. Interface exposta ao consumidor

Nenhuma interface de produto foi alterada. O script expõe só a CLI `--port-base` (7500–7518), `--only A|B|C`, `--timeout`, `--core08-root` (ou `MINIPAR_CORE08_ROOT`) e o JSON `output/int01/results.json`, com `meta`, `segments[].checks[]` (`id`, `desc`, `status`, `evidence`), `summary` e `exit_code`.

## 7. Verificação documental

- **Verificados:** `AGENTS.md`, `MEMORY.md`, `docs/04_BACKLOG.md` (ficha do INT-01), `docs/05_VALIDACAO_E_ACEITE.md`, `docs/02_CONTRATOS_TECNICOS.md` §1 (C-WEB-v1) e §2, `runtime/README.md`, `docs/auditorias/CORE-07_BACKEND_RUNTIME.md`, `docs/auditorias/CORE-08_SERVICO_FASES.md`, `web_didatica/README.md`.
- **Atualizados nesta entrega:** este documento (novo), `scripts/smoke_int01.py` (novo) e o estado do INT-01 em `docs/04_BACKLOG.md` e `planning/cards.json`.
- **Não atualizados, com justificativa:** `README.md`, `runtime/README.md` e os contratos ficam como estão, porque nenhuma API, comportamento ou regra mudou; o smoke só consome interfaces existentes. A ficha do INT-01 em `docs/04_BACKLOG.md` e o `planning/cards.json` foram atualizados para `BLOCKED` (PR #24), como nos outros cards do Eixo C; `DONE` só depois da revisão humana, do WEB-03 e da repetição em `dev`. O handoff CORE-07 (INT01-06) é do Eixo A.
- **`AGENTS.md`:** revisado, sem necessidade de mudança. Ownership, fluxo e convenções PASS/FAIL/BLOCKED/PARTIAL foram aplicados como estão, e o script não cria uma nova convenção permanente.

## 8. Pendências e próximos consumidores

- **Victor (A):** INT01-01, 02, 06 e 07 ao integrar #17/#18/#19; depois, repetir `python scripts/smoke_int01.py` em `dev`. A valida os segmentos A e B.
- **Riquelme (B):** INT01-04 (WEB-03) e, junto com A, a CR de diagnósticos (INT01-03). B valida o segmento C.
- **Eixo C:** INT01-05 (RUN-03 em duas máquinas) e a nova execução do smoke quando as dependências entrarem em `dev`.
- **INT-02:** reutiliza este script como pré-condição da regressão integral.

Sem stage, commit, push, PR ou merge. Revisão por IA não substitui a conferência humana dos logs e da demonstração.

**Declaração:** não alterei arquivos de outro eixo nem `legacy/`. Só criei `scripts/smoke_int01.py` e este documento.
