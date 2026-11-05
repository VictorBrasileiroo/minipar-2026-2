# Benchmarks e falhas distribuídas (card `RUN-05`, Eixo C)

`run_bench.py` mede o tempo do Teste 8 nos modos sequencial e paralelo e repete três falhas do runtime. O resultado de cada rodada é publicado em [`docs/evidencias/RUN-05_BENCHMARKS.md`](../../../docs/evidencias/RUN-05_BENCHMARKS.md).

## 1. Carga

A carga é o programa do Teste 8 ([`../test08/teste8_avaliadores.minipar`](../test08/teste8_avaliadores.minipar)): 160 avaliações divididas em 4 fatias de 40. Os modos `seq` e `par` fazem **as mesmas 160 avaliações, com as mesmas fatias e a mesma `carga`**. Muda só quem executa:

| Cenário | O que executa as 4 fatias |
|---|---|
| `seq` | 4 chamadas diretas, em sequência, num processo e numa thread |
| `par_local` | 4 `fork` com destino `local`: 4 threads do mesmo processo |
| `par_loopback` | 4 `fork` para 4 workers (processos separados) em `127.0.0.1`, na mesma máquina |
| `par_rede` | 4 `fork` para workers já iniciados em **outro computador** (`--destinos-rede`) |

Uma execução só entra na estatística se a saída bater com o oráculo Python do [`run_t08.py`](../test08/run_t08.py): exit 0, `MODO` certo, ids 0..159 sem perda nem duplicata, cada nota igual à do oráculo e `SOMA_NOTAS` correta. O script importa o oráculo, o parser, a compilação e a classe `Worker` do `run_t08.py`, sem copiar código, e compila num executável próprio (`output/bench_t08.exe`) para não sobrescrever o do T08.

## 2. Método

- Uma rodada de **aquecimento** por cenário, descartada.
- `--reps` rodadas medidas, **intercaladas** (seq, par_local, par_loopback, [par_rede], seq, ...), para que uma variação de temperatura ou de carga da máquina afete todos os cenários de forma parecida.
- Tempo = tempo de parede do processo coordenador, inclusive a partida do processo (o MiniPar não tem builtin de relógio). Com `carga` alta, a partida pesa pouco.
- Estatística por cenário: mediana, média, desvio, mínimo e máximo. Speedup = `Tseq/Tpar` e redução = `100·(Tseq−Tpar)/Tseq`, ambos sobre a **mediana** (doc 05 §5).
- Registro do ambiente: modelo da CPU, **núcleos físicos** e **threads lógicas** (separados), plano de energia (Windows), SO, G++, flags de compilação, commit e SHA-256 do binário.

**Workers não são núcleos.** No `par_local` e no `par_loopback`, os 4 trabalhadores dividem os núcleos da mesma máquina. O speedup máximo nesses cenários é limitado pelos núcleos físicos livres, e o `par_loopback` ainda paga a serialização e o TCP local. Só o `par_rede` usa a CPU de outro computador.

## 3. Falhas repetíveis

Cada falha roda `--reps-falhas` vezes com processos novos:

| ID | Montagem | Esperado |
|---|---|---|
| F1 | Os 4 destinos são portas livres de `127.0.0.1`, sem worker | `join` falha com `WORKER_UNAVAILABLE`, exit 1, em menos de 30 s |
| F2 | 4 workers reais; depois do `TASK` no log do worker 0, o script mata **só esse processo** (que ele mesmo criou) | `join` falha com `WORKER_LOST`, exit 1, sem travar. Se a tarefa terminar antes do kill, a rodada é inconclusiva e conta como falha |
| F3 | Servidor falso que responde `HELLO_OK` (C-FJ-v1 §2.6), recebe os 4 `TASK` e nunca responde; `MINIPAR_RT_REMOTE_TIMEOUT_MS=3000` só no ambiente do coordenador | `join` falha com `TIMEOUT` depois de pelo menos 3 s, exit 1 |

Um coordenador que não termina dentro do limite da falha é morto pelo script e registrado como `travou`.

## 4. Como executar

Da raiz do repositório, com `python` e `g++` (C++20) no PATH:

```text
python tests/2026_2/bench/run_bench.py --rapido                                   # smoke: carga 200000, 2 rodadas, 1x cada falha
python tests/2026_2/bench/run_bench.py --carga 5000000 --reps 7 --reps-falhas 5   # rodada publicada
python tests/2026_2/bench/run_bench.py --sem-falhas --port-base 7600              # só tempos, outras portas
```

Portas: `port-base+1` a `port-base+13` em `127.0.0.1` (padrão 7501–7513). Se alguma estiver ocupada, o cenário vira `BLOCKED`; o script nunca encerra processos alheios.

### Cenário em dois computadores (`par_rede`)

1. As duas máquinas no **mesmo commit**. Compile nas duas: `python main.py tests/2026_2/test08/teste8_avaliadores.minipar bench_t08`. O `build_id` é o SHA-256 do fonte, então o mesmo fonte gera binários compatíveis.
2. Na máquina B, libere as portas 7501–7504 no firewall só durante o teste (roteiro em [`runtime/README.md`](../../../runtime/README.md)) e suba 4 workers, um por terminal:
   `output/bench_t08.exe --minipar-worker 7501 --bind <IP-de-B>` (e 7502, 7503, 7504).
3. Na máquina A:
   `python tests/2026_2/bench/run_bench.py --carga 5000000 --reps 7 --destinos-rede <IP-de-B>:7501,<IP-de-B>:7502,<IP-de-B>:7503,<IP-de-B>:7504`
4. Guarde os logs dos workers de B. No relatório, os IPs aparecem mascarados (`192.168.x.N`).

## 5. Saída

- Linhas `[PASS]`, `[FAIL]`, `[BLOCKED]` e `[INFO]` no terminal.
- `output/bench/run-<data>/bench.json`: ambiente, cada execução (rodada, ok, tempo, exit), estatística, speedup e cada repetição de falha.
- `output/bench/run-<data>/resumo.md`: as tabelas usadas na evidência.
- Exit 0 se tudo PASS, 1 se algum FAIL, 2 se algum BLOCKED.

`output/` é ignorado pelo Git. A cópia publicada fica em `docs/evidencias/RUN-05/`.
