# RUN-03 — Prova de execução em dois computadores reais

**Card:** `RUN-03` · **Eixo:** C (Erasmo) · **Contrato:** C-FJ-v1 (`docs/02_CONTRATOS_TECNICOS.md` §2) · **Data desta versão:** 04/11/2026
**Critério de aceite:** provar IPs distintos e cálculo remoto verdadeiro; `join` com erro/timeout quando o worker cai.
**Programa:** `runtime/examples/demo_distribuida.cpp`, que usa a mesma biblioteca `minipar_rt` dos cards `RUN-01`/`RUN-02`.

## 1. Estado

| Item | Status | Motivo / evidência |
|---|---|---|
| Programa da prova e roteiro | pronto | Este documento e `demo_distribuida.cpp` |
| Ensaio do roteiro no loopback (mesmo PC) | **PASS como ensaio** | Seção 5. Prova que o programa e as verificações funcionam; **não** prova duas máquinas |
| **Execução em dois computadores** | **PASS** (04/11/2026), log de A pendente | Seção 6. Log do worker (B) anexado em [`RUN-03/worker_B.log`](RUN-03/worker_B.log): conexão e tarefas vindas do IP de A, executadas pelo processo de B. As cinco verificações e o exit 0 do coordenador foram conferidos pelo operador na tela de A; a saída do coordenador (`coordenador_A.txt`) ainda não foi anexada |

`RUN-03` passa a `PASS` com a seção 6 preenchida com uma execução real entre dois computadores, as cinco verificações em `PASS` e os logs dos dois lados anexados. Localhost não substitui essa prova (ADR-017, AGENTS regra 6). Na execução de 04/11 só o log de B foi anexado; a revisão decide se pede a saída de A antes do merge.

## 2. O que a demonstração verifica

O coordenador (host A) envia tarefas ao worker (host B) e imprime um resumo com cinco verificações:

| # | Verificação | Como |
|---|---|---|
| 1 | Worker em **outro computador** | A tarefa `identidade` roda no worker e devolve o hostname e o PID dele; o hostname tem de ser diferente do de A |
| 2 | **Cálculo remoto verdadeiro** com entradas diferentes | `soma_quadrados(0, 4e7)` e `soma_quadrados(4e7, 8e7)` rodam no worker e são conferidas contra o mesmo cálculo feito em A; os resultados diferem entre si |
| 3 | As tarefas foram executadas pelo processo do worker | `executed_by` de cada resultado = `host:pid` do worker |
| 4 | Comparação com execução local (doc 05 §4, passo 8) | Mesmo trabalho com destino `local`, mesma concorrência, tempos impressos |
| 5 | **Queda do worker** não trava o `join` | Tarefa `trabalho_longo(60 s)` no worker; o operador encerra o worker; o `join` (limite de 90 s) devolve `WORKER_LOST` (ou `TIMEOUT`, se a máquina sumiu da rede sem fechar a conexão) |

O worker registra em stderr, para cada conexão e tarefa: `worker_id` (host:PID), **IP:porta do coordenador**, `task_id`, função, resultado e duração. O log do worker mostra o IP de A e a saída do coordenador mostra o destino (IP de B): juntos, os dois provam os IPs distintos.

## 3. Pré-requisitos

- Dois computadores físicos na **mesma rede local** (a rede do laboratório ou um roteador doméstico). Não usar VPN pública nem expor porta na internet.
- Nos dois, o **mesmo commit** deste repositório e um G++ com C++20:
  - Windows: MSYS2 UCRT64 (`C:\msys64\ucrt64\bin\g++.exe`), igual ao SET-02;
  - Linux: `g++` 11 ou mais novo.
- Saber o IP de B na rede local (`ipconfig` no Windows, `ip -4 addr` no Linux).

## 4. Roteiro

**4.1 Compilar nas duas máquinas** (na raiz do repositório):

```powershell
# Windows (PowerShell)
$env:PATH = "C:\msys64\ucrt64\bin;$env:PATH"      # só nesta janela
New-Item -ItemType Directory -Force output\run03 | Out-Null
g++ -std=c++20 -O2 -pthread -I runtime/include runtime/examples/demo_distribuida.cpp -o output/run03/demo_distribuida.exe -lws2_32
Get-FileHash output/run03/demo_distribuida.exe -Algorithm SHA256
```

```bash
# Linux
mkdir -p output/run03
g++ -std=c++20 -O2 -pthread -I runtime/include runtime/examples/demo_distribuida.cpp -o output/run03/demo_distribuida
sha256sum output/run03/demo_distribuida
```

**4.2 Liberar a porta só para A, só na rede privada, só durante a prova** (feito pela pessoa operadora, na máquina B):

```powershell
# Windows, PowerShell como administrador, na máquina B
New-NetFirewallRule -DisplayName "MiniPar RUN-03 (temporaria)" -Direction Inbound -Protocol TCP -LocalPort 7000 `
  -RemoteAddress <IP-de-A> -Profile Private -Action Allow
# depois da prova:
Remove-NetFirewallRule -DisplayName "MiniPar RUN-03 (temporaria)"
```

```bash
# Linux com ufw, na máquina B
sudo ufw allow from <IP-de-A> to any port 7000 proto tcp
# depois da prova:
sudo ufw delete allow from <IP-de-A> to any port 7000 proto tcp
```

Se o Windows abrir o aviso do firewall ao iniciar o worker, marque **apenas "Redes privadas"**.

**4.3 Iniciar o worker na máquina B:**

```powershell
output\run03\demo_distribuida.exe --minipar-worker 7000 --bind <IP-de-B> 2> output\run03\worker_B.log
```

Esperado na primeira linha do log: `[minipar_worker <host-B>:<pid>] escutando em <IP-de-B>:7000 (... build_id=minipar-demo-run03-v1)`.

**4.4 Rodar o coordenador na máquina A:**

```powershell
output\run03\demo_distribuida.exe --coordenador <IP-de-B>:7000 | Tee-Object output\run03\coordenador_A.txt
```

**4.5 Derrubar o worker no meio da tarefa.** Quando o coordenador imprimir `AGUARDANDO_QUEDA: ...`, pressione **Ctrl+C na janela do worker (máquina B)**. O coordenador deve imprimir `join(task-N) apos a queda: WORKER_LOST ...` em poucos segundos e o resumo final.

**4.6 Oráculo:** as cinco linhas do `== Resumo RUN-03 ==` em `[PASS]` e exit code 0 no coordenador. No log de B, linhas `conexao de <IP-de-A>:<porta> aceita` e `TASK task-N fn=soma_quadrados ... inicio`/`RESULT ... ok`.

**4.7 Desfazer a regra de firewall** (4.2) e guardar `coordenador_A.txt` e `worker_B.log`.

## 5. Ensaio no loopback (22/10/2026) — não é a prova

Rodado pelo `python runtime/tests/run_tests.py` (etapa `RUN-03 roteiro da demo em loopback`): worker e coordenador no **mesmo** computador (Windows 11, G++ 16.2.0 UCRT64), worker derrubado pelo runner (`kill`) ao ver `AGUARDANDO_QUEDA`. IPs locais omitidos.

```text
[coordenador] worker respondeu: host=<host-A> pid=17336 executed_by=<host-A>:17336
[coordenador] task-2 soma_quadrados(0,40000000) = 46266682 (esperado 46266682) por <host-A>:17336
[coordenador] task-3 soma_quadrados(40000000,80000000) = 842882486 (esperado 842882486) por <host-A>:17336
[coordenador] mesmo trabalho local: 307 ms (remoto 306 ms, inclui rede)
[coordenador] join(task-6) apos a queda: WORKER_LOST: conexao com o worker <host-A>:17336 (127.0.0.1:55582) perdida: conexao encerrada (em 504 ms)

== Resumo RUN-03 ==
[FAIL] worker em outro computador (hostname diferente) — MESMO HOST <host-A>: isto NAO prova duas maquinas
[PASS] duas tarefas remotas com resultados corretos e IDs certos — remoto 306 ms
[PASS] tarefas executadas pelo processo do worker — <host-A>:17336
[PASS] execucao local equivalente confere — 307 ms
[PASS] queda do worker vira erro no join, sem bloqueio infinito — WORKER_LOST
```

O `FAIL` da verificação 1 é o resultado **correto** no loopback: o programa não aceita o mesmo host como prova de duas máquinas. As outras quatro verificações mostram que o roteiro funciona.

## 6. Registro da execução real (04/11/2026)

| Campo | Máquina A (coordenador) | Máquina B (worker) |
|---|---|---|
| Data/hora | 04/11/2026, ~13:58 | 04/11/2026, ~13:58 (log gravado às 13:58) |
| Responsável | equipe (operador de A) | Erasmo (Eixo C) |
| Hostname (pode abreviar) | `pc-A` | `pc-B` |
| IP na rede local (mascarar: `192.168.x.N`) | `192.168.x.31` | `192.168.x.131` |
| SO e versão do G++ | não registrado | Windows 11, G++ 16.2.0 (MSYS2 UCRT64) |
| Commit do repositório | não registrado (o worker aceitou o `build_id` de A: `minipar-demo-run03-v1`) | `ee8739c` |
| SHA-256 do binário | não registrado | `39b65a5a35ca1cff4f270b00de3d9556b79c63b5683a7efa002261b535b1fee3` |

| # | Verificação | Status | Evidência |
|---|---|---|---|
| 1 | Worker em outro computador | PASS | Log de B: worker `pc-B` em `192.168.x.131` aceita a conexão de `192.168.x.31` (A). Resumo do coordenador conferido em A |
| 2 | Cálculo remoto correto com duas entradas | PASS | Log de B: `task-2` e `task-3` `fn=soma_quadrados` vindas de A, `ok` em 149 ms e 150 ms. Conferência contra o cálculo local feita pelo coordenador em A |
| 3 | Executado pelo processo do worker | PASS | Log de B: as tarefas rodaram no processo `pc-B:28212` |
| 4 | Comparação com execução local | PASS | Conferido na saída do coordenador em A (só no lado de A) |
| 5 | Queda do worker → erro no `join` sem travar | PASS | Log de B termina em `TASK task-6 fn=trabalho_longo ... inicio`, sem `RESULT`: o worker foi encerrado (Ctrl+C) durante a tarefa. O erro no `join` e o exit 0 foram conferidos em A |

Anexos:
- [`RUN-03/worker_B.log`](RUN-03/worker_B.log): log completo do worker, com IPs mascarados (`192.168.x.N`) e hostname trocado por `pc-B`.
- `coordenador_A.txt`: **não anexado**. As verificações 4 e 5 e o exit 0 do coordenador ficam registrados pelo operador de A, sem o log. Se a revisão pedir, a saída de A entra neste diretório.

## 7. Limitações

- Sem autenticação/criptografia no protocolo: só em rede local de laboratório.
- A verificação 1 compara hostnames. Duas máquinas com o mesmo hostname dariam falso `FAIL`; nesse caso, registre os IPs pelos logs.
- Se a máquina B sair da rede sem fechar a conexão (cabo/wi-fi), o erro chega pelo limite do `join` (`TIMEOUT`, 90 s), não por `WORKER_LOST`. As duas formas atendem ao "join com timeout quando worker cai".
