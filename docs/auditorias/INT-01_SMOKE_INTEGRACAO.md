# HANDOFF — INT-01 — Smoke de integração dos três eixos

**Responsável:** Eixo C (Erasmo) | **Branch:** `eixo-c/INT-01-smoke-integracao` (PR #24, base `dev`) | **Datas:** 30/10/2026 (primeira execução, na base de integração local `local/wip-int01`) e 05/11/2026 (execução vigente, em `dev`) | **Contratos usados:** C-FJ-v1 (§2), C-WEB-v1 (§1.2–1.7)

**Estado do card (05/11/2026): IN_REVIEW. Não marcar DONE antes da revisão humana.** O RUN-04 (#20) já está em `dev`. Os três segmentos estão PASS em `dev` (§4.0). Os parágrafos seguintes registram o histórico.

**Estado em 30/10/2026: PARTIAL / BLOCKED.** O segmento A (Eixos A+C) passou na base de integração local; o segmento B (serviço CORE-08) passou só no recorte sem Fork/Join; o segmento C (Web didática) está BLOCKED porque o WEB-03 não começou. No `planning/cards.json` o INT-01 fica `BLOCKED`, `ready=false`, com o PR #24 em draft. As dependências `CORE-07`, `WEB-03` e `RUN-04` não estão concluídas. A execução foi antecipada pelo Eixo C (plano do M2 de 30/10) para encontrar os defeitos de integração cedo. Ela não promove o estado de nenhum outro card. A e B precisam validar os segmentos deles.

> **Atualização de 05/11/2026, após o merge do WEB-03 (#30) e do WEB-04 (#31).** Branch sincronizada com `dev` (`800ace1`; execução vigente em `debc3d9`, §4.0). O segmento C deixou de ser inspeção estática: `scripts/smoke_int01.py` importa `web_didatica/server.py` num subprocesso isolado e chama as rotas com o cliente de teste do Flask, sem abrir porta (C1–C8: `server.py` importa o serviço; `POST /api/v1/analyze` e `/compile` com envelopes conferidos campo a campo; `POST /api/v1/execute` do programa Fork/Join, destino `local`, com `stdout` igual ao oráculo; `GET /api/v1/artifacts/<id>/binary` com o nome do §1.7 e SHA-256 igual ao do binário registrado; 400 `BAD_REQUEST`, 404 `ARTIFACT_NOT_FOUND` no download e `ARTIFACT_NOT_FOUND` no envelope do `execute`). Resultado com Python 3.12.10 + Flask 3.0.0 e g++ 16.2.0 (MSYS2 UCRT64): **A PASS (A1–A8), B PASS (B1–B8), C PASS (C1–C8), exit 0**. Sem Flask no Python usado, o C fica **PARTIAL** (C1 PASS, C2 BLOCKED com o motivo; testado com o Python 3.14 do sistema). INT01-04 resolvido. Continuam abertos INT01-03 (CR de diagnósticos) e INT01-05 (segmento A só no loopback).
>
> **Atualização de 05/11/2026, após o merge do #18.** O CORE-07 (#18) entrou em `dev` (`b6e2705`). Smoke repetido na própria branch sincronizada (`5596867`), sem integração local e sem `--core08-root`: segmento A **PASS** (A1–A8), segmento B **PASS** (B1–B8), segmento C **BLOCKED** (WEB-03 não iniciado). Exit 0 (na época, BLOCKED também saía com 0; desde 05/11 sai com 3). Os achados INT01-01 e INT01-02 estão resolvidos em `dev`. O card segue `BLOCKED` só pelo segmento C.

> **Atualização de 05/11/2026 (antes do merge do #18).** O CORE-06 (#17) entrou em `dev` e o PR #18 (CORE-07) foi sincronizado com `dev` pelo Eixo A, então a sua árvore já contém o CORE-08 (#19). A branch foi sincronizada de novo com `dev` (via `RUN-04`), e o script passou a usar por padrão o `src/service.py` da própria árvore (a pasta irmã `int01-core08` deixou de ser procurada). Resultados, sem `--core08-root`:
> - **Nesta base** (HEAD `2762d88`, sem o #18): segmento A **BLOCKED** (`[ERRO BACKEND] ... compilacao C++ depende de CORE-07`); segmento B **PARTIAL**: B1–B7 PASS (`src/service.py` SHA-256 `9e7c55c2…5d4e`) e B8 **BLOCKED** com `tac=ok` e `cpp=error` (`CPP_UNSUPPORTED_FEATURE`); segmento C **BLOCKED** (WEB-03). Exit 0.
> - **Integração local** (`0be890c` = esta branch + T08–T10 + PR #18 `257613f`, sem push): segmento A **PASS** (A1–A8); segmento B **PASS** (B1–B8, `src/service.py` SHA-256 `d6029024…c5dd`), ou seja, o programa Fork/Join compila e executa pelo serviço com `stdout` igual ao oráculo; segmento C **BLOCKED** (WEB-03). Exit 0.
> - Com isso, os achados INT01-01 e INT01-02 (seção 5) estão resolvidos **no PR #18**; só ficam resolvidos em `dev` depois do merge dele. O card segue PARTIAL/BLOCKED por causa do #18 e do WEB-03.

> **Atualização de 04/11/2026.** A branch foi sincronizada com `dev` (via `RUN-04`), que agora inclui o RUN-03 (#10, prova em dois computadores, mergeado em 04/11) e o CORE-08 (#19). O smoke foi repetido no HEAD `f1188dd`: segmento A **BLOCKED** (#17/#18 ainda fora de `dev`, então a CLI desta base não compila Fork/Join); segmento B com `--core08-root .`, ou seja, o `src/service.py` que está em `dev` (SHA-256 `9e7c55c2…5d4e`), B1–B7 **PASS** e B8 **BLOCKED** (TAC/backend Fork/Join ausentes); segmento C **BLOCKED** (WEB-03). Naquela data, sem `--core08-root`, o script ainda procurava a pasta irmã `int01-core08` por padrão. As seções 2 a 4 abaixo registram a execução de 30/10.

## 1. Objetivo e escopo

Ter **um script único e reproduzível** (`scripts/smoke_int01.py`) que exercite o caminho de ponta a ponta de cada eixo e dê um status real por segmento:

| Seg. | Eixos | O que exercita | Base |
|---|---|---|---|
| A | A+C | Programa MiniPar com 2 `fork` e 2 `join`, depois CLI `main.py` (Lexer, Parser, Semântico, TAC, C++, g++), depois o executável com destino `local` e com um worker no loopback | desde 05/11: `dev`. Em 30/10: worktree `int01` (RUN-03 + `dev` + #17 + #18, mesclados só localmente) |
| B | A+B | `src/service.py` (CORE-08, PR #19): `analyze` → `compile_program` → `execute` → `get_artifact`, com os envelopes do C-WEB-v1 conferidos campo a campo | desde 05/11: `src/service.py` da própria árvore (`dev`), em subprocesso isolado; `--core08-root`/`MINIPAR_CORE08_ROOT` apontam outra. Em 30/10: worktree separada `int01-core08` (só o #19) |
| C | A+B | Se `web_didatica/` chama o serviço real (WEB-03/WEB-04) | desde 05/11: `dev`, cliente de teste do Flask em subprocesso, sem servidor nem porta. Em 30/10: inspeção estática |

**Histórico (30/10):** o segmento B rodava em outra árvore porque o **PR #19 conflitava com os PRs #17/#18 em `src/codegen.py` e `src/tac.py`**, conflito verificado pelo Eixo C ao montar a integração local e resolvido pelo Eixo A antes do merge do #18. O smoke nunca importa duas árvores `src/` no mesmo processo Python.

Fora do escopo: a prova entre dois computadores (RUN-03, PR #10), os testes 8–10 e a Web antiga.

## 2. Ambiente

Tabela da execução de 30/10. A de 05/11 está em §4.0 (Python 3.12.10 + Flask 3.0.0, mesmo g++, base `dev`).

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

Na raiz do repositório (Python com Flask para o segmento C, ver `requeriments.txt`):

```powershell
python scripts/smoke_int01.py                       # A, B e C; resultados em output/int01/results.json
python scripts/smoke_int01.py --only A --port-base 7500 --timeout 30
python scripts/smoke_int01.py --only B --core08-root ..\outra-arvore    # ou $env:MINIPAR_CORE08_ROOT; padrão: esta árvore
python scripts/smoke_int01.py --only C                # grava output/int01/results_C.json
```

- **Raiz do CORE-08:** `--core08-root`, depois a variável `MINIPAR_CORE08_ROOT`, depois a própria árvore (desde 05/11; antes era a pasta irmã `../int01-core08`). Se nenhuma tiver `src/service.py`, o segmento B fica **BLOCKED** com o motivo (testado: `--core08-root ./nao-existe` dá `B0 BLOCKED`).
- **Código de saída (desde 05/11):** `0` só quando todos os segmentos executados estão PASS; `1` quando houve FAIL; `2` para argumentos inválidos (testado: `--port-base 8000` e `7519`); `3` quando não houve FAIL mas algum segmento ficou BLOCKED, PARTIAL ou UNTESTED. Assim o INT-02 pode usar o código de saída como pré-condição. Até 05/11, BLOCKED/PARTIAL saíam com `0`.
- **Falha do Fork/Join é FAIL (desde 05/11).** Com CORE-06/CORE-07 em `dev`, o A1 e o B8 não classificam mais erro do backend como BLOCKED pela mensagem.
- Os oráculos são calculados em Python a partir dos mesmos parâmetros que geram os fontes MiniPar (`soma_quadrados(100)`, `fib(30)`, stdin `int01`). Nenhuma saída esperada foi escrita à mão.
- Cada subprocesso tem limite de tempo: compilação em 300 s, execução em `--timeout` (padrão 30 s), helper do serviço em 1200 s e espera do worker em 15 s.

Arquivos gerados (ignorados pelo Git): `output/int01/results.json` (ou `results_<seg>.json` com `--only`), `segC_web_raw.json`, `segA_fork.minipar`, `segA_compile.log`, `segA_worker.log`, `segB_sem_fork.minipar`, `segB_service_raw.json` (envelopes completos), `run1.log`, `run2.log`, `run_final.log`. O serviço grava seus artefatos em `output/web/<request_id>/` da árvore usada (em 30/10, `int01-core08`).

## 4. Resultados reais

### 4.0 Execução de 05/11/2026 em `dev` (vigente)

Branch `eixo-c/INT-01-smoke-integracao` sincronizada com `dev` depois do merge do RUN-04 (#20), WEB-03 (#30) e WEB-04 (#31). HEAD `debc3d9` (`debc3d9efffff08a0ad2538b0d178c9e46bdd43e`), Python 3.12.10 com Flask 3.0.0 (`requeriments.txt`), `g++.EXE (Rev3, Built by MSYS2 project) 16.2.0`. Três execuções completas seguidas (`run1`, `run2`, `run3`), todas **A PASS, B PASS, C PASS, exit 0**. Início da última: 2026-11-05T15:16:18-03:00. O `results.json` dela está anexado em [`INT-01_RESULTADOS_2026-11-05.json`](INT-01_RESULTADOS_2026-11-05.json), com as evidências de cada check (envelopes resumidos, stdout, oráculos, SHA-256 do download).

| Check | Descrição | Status |
|---|---|---|
| A1 | CLI exit 0 e percorre Fases 1-4 (léxico/sintático, semântico, TAC, C++/g++) | PASS |
| A2 | Artefatos TAC, C++ e .exe existem e não estão vazios | PASS |
| A3 | TAC contém fork soma_quadrados/fib ... on <destino> e 2 joins | PASS |
| A4 | C++ gerado usa a API do runtime (include, register_function, worker, start, build_id) | PASS |
| A5 | Destino local: stdout == oráculo, exit 0, stderr vazio | PASS |
| A6 | Destino 127.0.0.1:7500: stdout == oráculo, exit 0, stderr vazio | PASS |
| A7 | Log do worker: TASK e RESULT ok de soma_quadrados e fib, emitidos pelo PID do worker | PASS |
| A8 | Controle negativo 127.0.0.1:7501 (sem worker): exit != 0, erro em stderr e sem o resultado do oráculo | PASS |
| B1 | Subprocesso isolado importa src.service do CORE-08 e chama a API sem exceção | PASS |
| B2 | Envelope minipar.compile.v1 de analyze conforme C-WEB-v1 §1.3/1.4 | PASS |
| B3 | Envelope minipar.compile.v1 de compile conforme C-WEB-v1 §1.3/1.4 | PASS |
| B4 | request_id distintos e source_hash igual entre analyze e compile | PASS |
| B5 | execute: envelope minipar.execute.v1 completo e stdout == oráculo | PASS |
| B6 | get_artifact cpp/tac/binary: nome, media_type e arquivo no diretório do request_id (§1.7) | PASS |
| B7 | Erros contratuais: id inválido -> INVALID_ARGUMENT; id desconhecido -> ARTIFACT_NOT_FOUND; kind 'arm' -> INVALID_ARGUMENT | PASS |
| B8 | Programa Fork/Join pelo serviço: compile + execute(local) == oráculo | PASS |
| C1 | server.py presente e importa src.service; fonte_real.js presente | PASS |
| C2 | POST /api/v1/analyze: HTTP 200 | PASS |
| C3 | Envelope minipar.compile.v1 de analyze conforme C-WEB-v1 §1.3/1.4 | PASS |
| C4 | POST /api/v1/compile do programa Fork/Join: HTTP 200 | PASS |
| C5 | Envelope minipar.compile.v1 de compile conforme C-WEB-v1 §1.3/1.4 | PASS |
| C6 | POST /api/v1/execute (destino local): HTTP 200, minipar.execute.v1 completo e stdout == oráculo | PASS |
| C7 | GET /api/v1/artifacts/<id>/binary: anexo com o nome do §1.7 e bytes iguais ao binário registrado | PASS |
| C8 | Erros do contrato pelo HTTP (§1.6/§1.8): 400 BAD_REQUEST, 404 ARTIFACT_NOT_FOUND no download, ARTIFACT_NOT_FOUND no envelope do execute | PASS |
| C9 | kind 'arm' no download -> 400 BAD_REQUEST (§1.7 + web_didatica/README.md, fora do §1.8) | PASS |

Casos negativos conferidos na mesma base: sem Flask no Python usado (Python 3.14 do sistema), `--only C` dá C1 PASS, C2 BLOCKED, segmento **PARTIAL** e exit 3; `--port-base 7519` dá exit 2; `--only B --core08-root ./nao-existe` dá B0 BLOCKED e exit 3; uma exceção injetada no meio do segmento mantém os checks anteriores e registra `C!` FAIL, com exit 1.

O segmento C cobre `web_didatica/server.py` e as rotas `/api/v1`. Ele **não** executa o front-end (`static/js/fonte_real.js`, `app.js`): só confere que `fonte_real.js` existe (C1). O fluxo no navegador foi demonstrado pelo Eixo B nos handoffs do WEB-03/WEB-04.

### 4.1 Execução de 30/10/2026 (histórico)

Em 30/10 foram três execuções completas seguidas (`run1`, `run2`, `run_final`), todas com o mesmo resultado: **A PASS, B PARTIAL, C BLOCKED, exit 0**. Os números abaixo são da `run_final` (início 16:21:16 −03:00).

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

Em 30/10 o `build_id` do log do worker (`d0f3c84a…44b1`) foi comparado **manualmente** com o `source_hash` do serviço para o mesmo fonte e coincidiu. O script **não** verifica essa igualdade: o A4 só confere que o C++ chama `set_build_id(`.

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

### Segmento C — Web didática (WEB-03): **BLOCKED** em 30/10 (PASS desde 05/11, ver atualização no topo)

Em 30/10, a inspeção de `web_didatica/` encontrou: não havia `server.py`; nenhum `.py` importa `service` ou chama `compile_program(`; nenhum `fetch` para `/api/v1/`. Os dados vêm das fixtures via `static/js/fonte_mock.js`, o que confirma o `web_didatica/README.md` ("modo mock (WEB-01)"). Motivo: **WEB-03 não iniciado**. Desde 05/11 o segmento executa C1–C9 pelo cliente de teste do Flask (§4.0); não sobe servidor nem abre porta.

## 5. Defeitos e bloqueios classificados

| ID | Seg. | Eixo responsável | Severidade | Descrição | Evidência | Próximo passo |
|---|---|---|---|---|---|---|
| INT01-01 | B | A | Alta (bloqueia FJ na Web e o INT-02) | PR #19 (CORE-08) conflita com #17/#18 em `src/codegen.py` e `src/tac.py`; o serviço não compila Fork/Join | B8: `tac=error` para o mesmo fonte que passa na CLI do segmento A | **Resolvido em 05/11/2026:** #17/#18/#19 em `dev`; B8 PASS em `dev` (§4.0) |
| INT01-02 | B | A | Alta (risco de integração; observado no código, **não executado**) | As interfaces divergem nas duas árvores: o #18 tem `CppCodeGenerator.generate_text(program, semantic=None, source=None)` e põe `-I runtime/include` no g++ dentro de `generate`. O #19 chama `generate_text(program)` sem `source` (que o #18 exige para o hash em FJ) e tem um `compile_cpp` próprio sem `-I runtime/include` | `int01/src/codegen.py:396,466`; `int01-core08/src/codegen.py:267,312`; `int01-core08/src/service.py` (fase `cpp`) | **Resolvido em 05/11/2026:** em `dev`, `src/service.py` chama `generate_text(program, semantic=semantic, source=source)` e o Fork/Join compila e executa pelo serviço (B8 e C6 PASS) |
| INT01-03 | B | A+B | Média | Uma fase com erro e `diagnostics=[]` não dá ao usuário da Web nenhuma mensagem do motivo da recusa (FJ sem backend) | B8: `tac=error`, `diagnostics: []` | Aberto: CR `docs/CR-CORE08-DIAGNOSTICOS.md` (catálogo v1.1 no PR #34, pendente de aprovação A+B); a Web mostra uma falha genérica da fase até a aprovação |
| INT01-04 | C | B | Alta (bloqueia WEB-04 e INT-02) | WEB-03 não iniciado; a Web didática só usa fixtures mock | C1: sem `server.py`, sem import do serviço, sem `/api/v1` | **Resolvido em 05/11/2026:** WEB-03 (#30) e WEB-04 (#31) em `dev`; o segmento C agora usa o cliente de teste do Flask sem porta, C1–C8 PASS |
| INT01-05 | A | C | Média (o runtime já foi provado em duas máquinas) | Este smoke usa só loopback no segmento A | A6/A7 usam `127.0.0.1`. O RUN-03 foi concluído em 04/11/2026 (PR #10 mergeado, `docs/evidencias/RUN-03_DOIS_COMPUTADORES.md`) com o programa de demonstração | Aberto (limitação declarada): opcional para o aceite do INT-01; repetir o segmento A com o worker na máquina B |
| INT01-06 | A | A | Média | O PASS do segmento A vale para uma base **local** (#17/#18 fora de `dev`). O handoff CORE-07 ainda registra "CLI integral BLOCKED por CORE-06"; nesta base combinada, a CLI integral funciona | A1–A8 PASS em `f09bdea` | **Parcial em 05/11/2026:** A1–A8 PASS em `dev` (§4.0). Resta ao Eixo A atualizar `docs/auditorias/CORE-07_BACKEND_RUNTIME.md`, que ainda diz "CLI integral BLOCKED por CORE-06" |
| INT01-07 | A | A | Baixa (cosmética) | `main.py` mantém a mensagem `integracao CLI CORE-06/CORE-07 pendente` no ramo `NotImplementedError` do TAC, já desatualizada com #17/#18 | `int01/main.py`, `compile_file` | **Resolvido em 05/11/2026:** a mensagem não existe mais no `main.py` de `dev` |

Nenhum defeito do runtime (Eixo C) apareceu: as execuções local, remota e o controle negativo se comportaram como o C-FJ-v1 especifica.

## 6. Interface exposta ao consumidor

Nenhuma interface de produto foi alterada. O script expõe só a CLI `--port-base` (7500–7518), `--only A|B|C`, `--timeout`, `--core08-root` (ou `MINIPAR_CORE08_ROOT`), os códigos de saída 0/1/2/3 (§3) e o JSON `output/int01/results.json` (`results_<seg>.json` com `--only`), com `meta`, `segments[].checks[]` (`id`, `desc`, `status`, `evidence`), `summary` e `exit_code`.

## 7. Verificação documental

- **Verificados:** `AGENTS.md`, `MEMORY.md`, `docs/04_BACKLOG.md` (ficha do INT-01), `docs/05_VALIDACAO_E_ACEITE.md`, `docs/02_CONTRATOS_TECNICOS.md` §1 (C-WEB-v1) e §2, `runtime/README.md`, `docs/auditorias/CORE-07_BACKEND_RUNTIME.md`, `docs/auditorias/CORE-08_SERVICO_FASES.md`, `web_didatica/README.md`.
- **Atualizados nesta entrega:** este documento (novo), `INT-01_RESULTADOS_2026-11-05.json` (novo, resultado anexado), `scripts/smoke_int01.py` (novo) e o estado do INT-01 em `docs/04_BACKLOG.md` e `planning/cards.json`.
- **Não atualizados, com justificativa:** `README.md`, `runtime/README.md` e os contratos ficam como estão, porque nenhuma API, comportamento ou regra mudou; o smoke só consome interfaces existentes. A ficha do INT-01 em `docs/04_BACKLOG.md` e o `planning/cards.json` estão em `IN_REVIEW` (PR #24) desde 05/11 (antes, `BLOCKED`); `DONE` só depois da revisão humana. O handoff CORE-07 (INT01-06) é do Eixo A.
- **`AGENTS.md`:** revisado, sem necessidade de mudança. Ownership, fluxo e convenções PASS/FAIL/BLOCKED/PARTIAL foram aplicados como estão, e o script não cria uma nova convenção permanente.

## 8. Pendências e próximos consumidores

- **Victor (A):** atualizar o handoff do CORE-07 (INT01-06, parte documental). A valida os segmentos A e B.
- **Riquelme (B):** junto com A, a CR de diagnósticos (INT01-03, PR #34). B valida o segmento C.
- **Eixo C:** opcionalmente, o segmento A em duas máquinas (INT01-05). O RUN-03 já está concluído (#10).
- **INT-02:** reutiliza este script como pré-condição da regressão integral; exige exit 0 (exit 3 indica segmento não PASS).

Entrega pelo PR #24 (base `dev`), sem merge pelo autor. Revisão por IA não substitui a conferência humana dos logs e da demonstração.

**Declaração:** não alterei arquivos de outro eixo nem `legacy/`. Criei `scripts/smoke_int01.py`, este documento e `INT-01_RESULTADOS_2026-11-05.json`, e atualizei só a ficha e o estado do INT-01 em `docs/04_BACKLOG.md` e `planning/cards.json`.
