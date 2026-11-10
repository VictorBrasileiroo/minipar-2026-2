# RUN-05 — Benchmarks e falhas distribuídas repetíveis

**Card:** `RUN-05` · **Eixo:** C (Erasmo) · **Data:** 05/11/2026 (rodada `par_rede`: 09/11/2026) · **Base medida:** `dev` em `59ea77d` (`par_rede`: `43a7c34`)
**Critério de aceite:** cargas sequencial e paralela equivalentes; relatório sem confundir workers com núcleos físicos.
**Harness:** [`tests/2026_2/bench/run_bench.py`](../../tests/2026_2/bench/run_bench.py) (método em [`tests/2026_2/bench/README.md`](../../tests/2026_2/bench/README.md)).

## 1. Estado

| Item | Status | Evidência |
|---|---|---|
| Carga equivalente nos modos `seq` e `par` | **PASS** | As 3 × 7 execuções de cada cenário bateram com o oráculo Python: ids 0..159 sem perda nem duplicata, cada nota certa e `SOMA_NOTAS = 7557` |
| Tempos repetidos, speedup e redução (doc 05 §5) | **PASS** nesta máquina | Três rodadas independentes, 7 medições cada, mais 1 aquecimento descartado (seção 3) |
| Registro do ambiente: CPU, núcleos físicos × threads lógicas, SO, compilador, flags, commit, binário | **PASS** | Seção 2 e o campo `ambiente` de cada JSON |
| Falhas repetíveis F1–F3 | **PASS** | 3 rodadas × 5 repetições de cada falha, sem travar (seção 4) |
| Cenário `par_rede` (workers em outro computador) | **PASS** (1 rodada) | 09/11: 7 medições + aquecimento com os 4 workers na máquina B, todas iguais ao oráculo (seção 3.1), na mesma sessão do [`RUN-06`](RUN-06_REPRODUCAO_DOIS_PCS.md) |

O critério de aceite está atendido nesta máquina e o tempo com workers em outro computador foi medido em 09/11 (uma rodada, seção 3.1).

## 2. Ambiente

| Item | Valor |
|---|---|
| CPU | Intel Core Ultra 5 135U: **12 núcleos físicos, 14 threads lógicas** (núcleos de tipos diferentes; o script não separa os tipos) |
| Energia | plano do Windows "Equilibrado" |
| SO | Windows 11 Pro 10.0.26300 |
| Compilador | G++ 16.2.0 (MSYS2 UCRT64), flags do `src/codegen.py`: `-std=c++20 -O3 -pthread -I runtime/include -lws2_32` |
| Programa | `tests/2026_2/test08/teste8_avaliadores.minipar`, compilado pela CLI oficial (`main.py`) |
| Carga | `carga = 5000000` (cada nota itera o LCG entre 5 e 10 milhões de vezes); 160 avaliações em 4 fatias de 40 |
| Trabalhadores | 4 em todos os cenários paralelos |
| Medida | Tempo de parede do processo coordenador, inclusive a partida; rodadas intercaladas entre cenários |

O SHA-256 do executável muda a cada compilação (`a4621cf1…` na rodada 1, `cb3cdad6…` na rodada 2) mesmo com o mesmo fonte, porque o linker grava data e hora no cabeçalho do `.exe`. O `build_id` do runtime não muda, porque é o SHA-256 do fonte MiniPar.

## 3. Tempos

Mediana de 7 medições por cenário em cada rodada; speedup = `Tseq/Tpar` e redução = `100·(Tseq−Tpar)/Tseq`, sobre as medianas.

| Rodada | `seq` (s) | `par_local` (s) | Speedup local | `par_loopback` (s) | Speedup loopback | Desvio do loopback (s) |
|---|---|---|---|---|---|---|
| 1 — 15:57 | 2,581 | 0,747 | **3,46** (−71,1 %) | 0,738 | **3,50** (−71,4 %) | 0,056 |
| 2 — 15:59 | 2,507 | 0,720 | **3,48** (−71,3 %) | 1,144 | **2,19** (−54,4 %) | 0,211 |
| 3 — 16:01 | 2,582 | 0,766 | **3,37** (−70,3 %) | 1,121 | **2,30** (−56,6 %) | 0,262 |

Mínimos e máximos de cada cenário estão nos resumos: [rodada 1](RUN-05/rodada1_20261105-155706.md), [rodada 2](RUN-05/rodada2_20261105-155912.md), [rodada 3](RUN-05/rodada3_20261105-160128.md). Cada execução, com tempo, exit e conferência, está no JSON da rodada.

**Leitura:**

- **`par_local` é estável** (speedup 3,37–3,48 nas três rodadas, desvio ≤ 0,04 s). Com 4 trabalhadores, o teto teórico é 4. Duas causas conhecidas explicam parte da diferença: a partida do processo entra no tempo, e as 4 fatias não têm exatamente o mesmo custo (cada nota itera `carga + s % carga` vezes). O processador também mistura núcleos de desempenho diferente; essa causa é possível, mas **não foi medida**.
- **`par_loopback` varia entre rodadas** (2,19 a 3,50; desvio de até 0,26 s). Os 4 workers são processos que dividem os mesmos núcleos da máquina e ainda pagam serialização JSON e TCP local. Na rodada 1 a máquina estava sem outra tarefa; nas rodadas 2 e 3 havia edição de arquivos em paralelo (a compilação levou 14 s, contra 8 s na rodada 1). As três rodadas ficam registradas: a rodada 1 **não** é apresentada como o resultado "verdadeiro".
- **Workers não são núcleos.** Os cenários `par_local` e `par_loopback` usam 4 trabalhadores numa máquina com 12 núcleos físicos. O speedup mede o paralelismo dentro de **um** computador, não ganho de distribuição em rede. Só o cenário `par_rede` (seção 3.1) usa a CPU de outra máquina.
- Speedup acima de 1 não era exigido (T08 README §3); o requisito é a carga ser a mesma, e isso foi conferido em todas as execuções.

### 3.1 Rodada em dois computadores (`par_rede`, 09/11)

Coordenador na máquina A (a mesma das seções 2 e 3: Core Ultra 5 135U, Windows 11, G++ 16.2.0, commit `43a7c34`) e 4 workers na máquina B (`192.168.x.22:7201`–`7204`), na rede local. Os workers são o `teste8.exe` do `RUN-06`; o `bench_t08.exe` de A vem do mesmo fonte, então o `build_id` é igual e o handshake passou. Comando: `run_bench.py --carga 5000000 --reps 7 --reps-falhas 5 --destinos-rede <4 destinos de B>`.

| Cenário | Mediana (s) | Mín | Máx | Desvio | Speedup | Redução |
|---|---|---|---|---|---|---|
| `seq` (A) | 2,493 | 2,480 | 2,506 | 0,010 | — | — |
| `par_local` (A) | 0,738 | 0,726 | 0,785 | 0,020 | 3,38 | 70,4 % |
| `par_loopback` (A) | 0,747 | 0,742 | 0,759 | 0,006 | 3,34 | 70,0 % |
| `par_rede` (A → B) | 1,068 | 0,978 | 1,380 | 0,135 | **2,33** | 57,2 % |

Todas as execuções bateram com o oráculo (`SOMA_NOTAS 7557`, 160 ids sem perda nem duplicata), e F1–F3 deram PASS de novo (5× cada). Nos logs de B, cada worker registrou 8 conexões vindas de A (aquecimento + 7), todas com `RESULT ok` ([`RUN-06/worker_720N_B.log`](RUN-06/)).

**Leitura:** o `par_rede` foi mais lento que o `par_loopback` (1,068 s contra 0,747 s) e variou mais (desvio 0,135 s). A diferença inclui a conexão e o handshake pela rede local e a CPU de B, que **não foi registrada**; por isso este número não compara as duas CPUs. É uma rodada só, com 7 medições.

Arquivos: [`RUN-05/rede_20261109-142925.json`](RUN-05/rede_20261109-142925.json) e [`.md`](RUN-05/rede_20261109-142925.md).

## 4. Falhas repetíveis

Cinco repetições por rodada, com processos novos a cada vez, nas três rodadas (15 por falha). O coordenador usa o `join(h)` do programa gerado; F3 usa `MINIPAR_RT_REMOTE_TIMEOUT_MS=3000` só no ambiente do coordenador.

| ID | Montagem | Resultado | Tempo observado (15 execuções) | Linha de erro do coordenador |
|---|---|---|---|---|
| F1 | 4 destinos em portas sem worker | **PASS** 15/15: exit 1, sem travar | 2,07–2,10 s até sair | `join task-1 falhou: WORKER_UNAVAILABLE: worker 127.0.0.1:7505 indisponivel: conexao recusada ou inalcancavel: erro de socket 10061` |
| F2 | 4 workers reais; o worker 0 é morto depois do `TASK` no log dele | **PASS** 15/15: exit 1, sem travar | 7–15 ms entre o kill e a saída | `join task-1 falhou: WORKER_LOST: conexao com o worker <host>:<pid> (127.0.0.1:7509) perdida: conexao encerrada` |
| F3 | Servidor falso que responde `HELLO_OK`, recebe os 4 `TASK` e nunca responde | **PASS** 15/15: exit 1, os 4 `TASK` chegaram | 3,05–3,08 s (limite de 3 s) | `join task-1 falhou: TIMEOUT: tarefa nao concluiu em 3000 ms` |

Em F2 nenhuma repetição foi inconclusiva (a tarefa nunca terminou antes do kill). Os cerca de 2 s de F1 são o tempo que o `connect` do Windows leva para desistir de uma porta recusada no loopback: o runtime faz uma única tentativa, com limite de 3 s (`net::connect_tcp`, chamado em `remote.hpp`).

## 5. Como reproduzir

```powershell
python tests/2026_2/bench/run_bench.py --carga 5000000 --reps 7 --reps-falhas 5    # cada rodada desta evidência
python tests/2026_2/bench/run_bench.py --rapido                                    # smoke (~30 s)
```

Cada rodada grava `output/bench/run-<data>/bench.json` e `resumo.md` já anonimizados: IPs que não são loopback viram `a.b.x.d`, os hostnames viram `<host>`/`<host-remoto>` e a pasta do usuário vira `<repo>` (bench README §5). Para publicar, copie os dois para `docs/evidencias/RUN-05/`. A rodada 1 foi gerada antes de o script ganhar a função `sanitizar()`; a cópia publicada passou pela mesma função. As três rodadas publicadas só têm `127.0.0.1`, conferido de novo em 06/11 após a revisão do #36.

A anonimização do cenário remoto foi conferida em 06/11 com `--destinos-rede` apontando para `192.0.2.1` (endereço de documentação, inalcançável): as execuções falham com `WORKER_UNAVAILABLE`, como esperado, e o `bench.json`/`resumo.md` gerados não têm nenhum `192.0.2.1`, só `192.0.x.1`, inclusive no `stderr`.

Arquivos: [`RUN-05/`](RUN-05/) (3 JSON e 3 resumos).

## 6. Limitações

- Uma máquina, Windows. Linux não foi medido.
- Tempo de parede do processo inteiro: inclui a partida do executável e, no `par_loopback`, a conexão e o handshake com os 4 workers.
- 7 medições por rodada mostram a variação, mas não dão intervalo de confiança.
- O `par_rede` tem uma rodada só, e a CPU, o SO e o G++ da máquina B não foram registrados.
