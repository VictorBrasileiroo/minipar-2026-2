# Teste 8: 160 avaliações em quatro trabalhadores (card `T08-01`, Eixo C)

**Estado: `PARTIAL`.** O teste passou (32 PASS, 0 FAIL) numa **integração local, não mergeada**, da branch RUN-03 com `dev`, o PR #17 (CORE-06, TAC) e o PR #18 (CORE-07, backend C++ que chama o runtime). O cenário remoto rodou só no **loopback** (`127.0.0.1`). A prova entre dois computadores continua pendente no RUN-03 (#10). O `PASS` final depende do merge de #17 e #18 em `dev` e de repetir este roteiro em seguida.

## 1. Objetivo

Reproduzir em MiniPar a parte de avaliação da referência Python ([`docs/fontes/Teste10_Python_referencia.py`](../../../docs/fontes/Teste10_Python_referencia.py)) e o §8.3 do documento mestre. São 40 alunos × 4 atividades = 160 avaliações, divididas entre 4 avaliadores (Professor, Monitor 1, Monitor 2, Monitor 3). O teste:

- executa os trabalhadores com `fork`/`join` reais;
- recupera os 160 resultados sem perda nem duplicata;
- compara os modos sequencial e paralelo.

| Arquivo | Papel |
|---|---|
| `teste8_avaliadores.minipar` | Programa MiniPar, compilado pela CLI oficial (`main.py`). |
| `run_t08.py` | Harness: compila, roda 3 cenários, confere com um oráculo independente e grava `output/test08/results.json`. |

## 2. Correspondência com a referência Python

| Referência Python | MiniPar (`teste8_avaliadores.minipar`) |
|---|---|
| `tarefas`: 160 strings `"Aluno a - Atividade b"` | Atividade `id` 0..159, com `aluno = id/4 + 1` e `atividade = id%4 + 1` (inteiros) |
| `AVALIADORES` (lista de strings) | `nome_avaliador(k)` com cadeia de `if`, porque o backend não aceita listas de strings |
| `meu_random_uniforme` + `simular_atraso` (carga aleatória) | Carga determinística: `nota_de(id, carga)` itera o LCG `carga + s%carga` vezes |
| `trabalhador_avaliacao(avaliador, lote, fila)` | `avaliar_lote(k, inicio, fim, carga)` devolve `[k, id, nota, id, nota, ...]` |
| `multiprocessing.Process` + `Queue` | `fork avaliar_lote(...) on destino_k`: as 4 tarefas saem antes de qualquer `join`, e os handles ficam numa lista percorrida com `join` |
| Modo sequencial com 1 núcleo | Modo `seq`: 4 chamadas diretas de `avaliar_lote`, com as mesmas fatias |
| `perf_counter` | O harness mede o tempo de parede de cada processo (o MiniPar não tem builtin de relógio) |

As fatias são `[40k, 40k+40)` para `k = 0..3`, como `tamanho_fatia = 160 // 4` na referência.

O núcleo canônico (`lcg`, `nota_de`, `avaliar_lote`) é compartilhado com T09 e T10. **Não altere** nomes nem fórmulas.

## 3. Contrato de E/S

Entrada em `stdin`, uma linha por valor, nesta ordem: `modo` (`seq` ou `par`), `carga` (inteiro decimal) e os destinos `destino_0` … `destino_3`. Cada destino é `local` ou `IP:porta`. No modo `seq`, os destinos são lidos e ignorados.

Saída. Todos os valores são calculados, nunca literais:

```text
=== TESTE 8: 160 avaliacoes, 4 avaliadores ===
MODO <seq|par>
[<nome>] Concluiu: Aluno <a> - Atividade <b> (id <id>, nota <n>)   <- 160 linhas, 40 antes de cada AVALIADOR
AVALIADOR <k> <nome> <qtd>                                         <- 4 linhas; <k> é o 1º elemento devolvido pela tarefa
TOTAL <n>
UNICOS <n>
DUPLICADOS <n>
PERDIDOS <n>
SOMA_NOTAS <n>
```

A agregação é feita no MiniPar. A lista `vistos` tem 160 zeros e cada par `(id, nota)` incrementa `vistos[id]`. Um `id` fora de `[0,160)` não é contado em `vistos`, então `TOTAL` passa a diferir de `UNICOS`.

## 4. Como executar

Execute da raiz do repositório. É preciso ter `python` e `g++` com C++20 no PATH.

```text
python tests/2026_2/test08/run_t08.py                     # carga padrão 2000000, portas 7201..7204
python tests/2026_2/test08/run_t08.py --carga 200000 --port-base 7210 --timeout 120
```

Também é possível rodar manualmente:

```text
python main.py tests/2026_2/test08/teste8_avaliadores.minipar teste8      # gera output/teste8.exe
output/teste8.exe --minipar-worker 7201 --bind 127.0.0.1                  # um terminal por worker (7201..7204)
output/teste8.exe          # stdin: par / 2000000 / 127.0.0.1:7201 / ... / 127.0.0.1:7204
```

O coordenador e os workers precisam ser o **mesmo executável**, porque o runtime confere o `build_id`.

Códigos de saída do harness:

| Código | Significado |
|---|---|
| `0` | Todas as verificações deram PASS |
| `1` | Alguma verificação deu FAIL |
| `2` | BLOCKED. Por exemplo, a compilação falhou por ausência de Fork/Join no backend (`BLOCKED: backend CORE-07 ausente`) ou as portas estão ocupadas |

As portas são `port-base+1..+4`, restritas à faixa 7200–7219 e a `127.0.0.1`. O harness só encerra processos que ele mesmo iniciou, pelo handle `Popen`.

## 5. Oráculo (independente, em Python)

- **LCG.** `lcg(s) = (75·s + 74) mod 65537`. O módulo 65537 é primo e os literais cabem em `int`.
- **Nota.** `s0 = lcg(id+1)`, `passos = carga + s0 % carga` e `nota = lcg^passos(s0) % 101`. O oráculo usa a forma fechada `lcg^n(s0) = aⁿ·s0 + c·(aⁿ−1)·(a−1)⁻¹ (mod m)`, com `pow` modular. O custo é O(log n) por id, sem repetir o laço do programa.
- **Autoverificação.** A forma fechada é comparada ao laço ingênuo para as cargas 1, 2, 3, 7, 50 e 997 × 160 ids.

Verificações por cenário (`seq`, `par` local, `par` remoto):

- exit 0, cabeçalho e `MODO`;
- `AVALIADOR k nome 40` para `k = 0..3`, em ordem;
- `TOTAL 160`, `UNICOS 160`, `DUPLICADOS 0`, `PERDIDOS 0`;
- `SOMA_NOTAS` igual à soma do oráculo;
- 160 linhas de item com ids exatamente `0..159`, e em cada item aluno, atividade, nota e avaliador dono da fatia iguais ao oráculo.

Verificações entre cenários e no remoto:

- As linhas `AVALIADOR`, `TOTAL` … `SOMA_NOTAS` são idênticas nos 3 cenários.
- O C++ gerado referencia `minipar_rt` e `avaliar_lote`.
- Cada um dos 4 workers registrou exatamente 1 `TASK` e 1 `RESULT ... ok` de `fn=avaliar_lote`.
- Os 4 PIDs do log são distintos e iguais aos PIDs dos processos iniciados.
- As 4 `TASK` chegaram aos workers antes do primeiro `RESULT`. Isso prova que os forks saíram antes do primeiro join, e não em série. Essa verificação só conta com `carga >= 100000`; abaixo disso é informativa.

O tempo e o speedup são **apenas informativos**. O `docs/05` não exige speedup maior que 1.

**Prova adversarial.** Três mutantes do programa foram compilados e rodados pelo mesmo harness com `--carga 200000`. Os três geraram FAIL com exit 1:

| Mutante | Mudança | Verificações que falharam |
|---|---|---|
| `dup_fatia` | Fatia 3 deslocada em −1 | `UNICOS 159`, `DUPLICADOS 1`, `PERDIDOS 1`, `SOMA_NOTAS` divergente, avaliador errado no id 119 |
| `nota_errada` | `(s+1) % 101` | `SOMA_NOTAS` e as notas por item |
| `troca_handles` | `join` de `hs[1]` antes de `hs[0]` | `AVALIADOR 1 Professor` e o dono da fatia |

## 6. Resultados reais (30/10/2026)

Ambiente:

- Windows 11 Pro 10.0.26300, 14 CPUs lógicas;
- Python 3.14.7;
- g++ 16.2.0 (MSYS2 UCRT64, Rev3);
- worktree `local/wip-t08`, HEAD `f09bdea` (integração local de RUN-03, `dev`, #17 e #18);
- `output/teste8.exe` com sha256 `d86484e6…6b6da7`.

Comando: `python tests/2026_2/test08/run_t08.py` (carga 2000000, portas 7201–7204).

Linhas agregadas, idênticas em `seq`, `par` local e `par` remoto nas duas execuções:

```text
AVALIADOR 0 Professor 40
AVALIADOR 1 Monitor 1 40
AVALIADOR 2 Monitor 2 40
AVALIADOR 3 Monitor 3 40
TOTAL 160
UNICOS 160
DUPLICADOS 0
PERDIDOS 0
SOMA_NOTAS 7630        (oráculo Python: 7630)
```

Os tempos são de parede, por processo, e incluem a inicialização:

| Execução | Exit do harness | Verificações | `seq` (s) | `par` local (s) | `par` remoto loopback (s) | Speedup seq/par local | Speedup seq/par remoto |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 32 PASS, 0 FAIL | 2.311 | 0.948 | 0.943 | 2.44 | 2.45 |
| 2 | 0 | 32 PASS, 0 FAIL | 2.914 | 0.804 | 0.884 | 3.62 | 3.30 |
| preliminar | 0 | 32 PASS, 0 FAIL | 2.225 | 0.525 | 0.583 | 4.24 | 3.82 |

Na execução 2, cada worker recebeu sua `TASK` entre 0.087 s e 0.146 s e enviou o `RESULT` entre 0.774 s e 0.871 s. Os workers registraram `ok em 667–724 ms`, e todas as `TASK` chegaram antes do primeiro `RESULT`. Os PIDs dos workers são 4 PIDs distintos, que conferem com os processos iniciados. Os PIDs mudam a cada execução e ficam registrados em `results.json`.

Os tempos são ruidosos: outros agentes compilavam e executavam na mesma máquina durante as medições.

Calibração: o modo `seq` levou cerca de 2.2–2.9 s, dentro da faixa de 0.5 a 15 s. Por isso a **carga padrão continua 2000000**.

## 7. Divergências em relação à referência Python

1. **IDs numéricos em vez de strings.** O C-T11-v1 §3.4 e o CORE-07 não suportam listas de strings, então as tarefas viajam como inteiros. O texto `Aluno a - Atividade b` é montado na impressão.
2. **Carga determinística.** O LCG substitui o `random` com `simular_atraso`. Assim o oráculo é exato e as cargas por avaliador são comparáveis.
3. **Tempo medido externamente.** O MiniPar não tem builtin de relógio, então o harness mede o tempo de parede por processo.
4. **Parse manual da carga.** O programa usa `para_inteiro`, porque `to_number` devolve decimal e o backend recusa `%` entre inteiro e decimal.
5. **Conversão de ids e notas para inteiro.** Listas numéricas são `vector<double>` no backend. Por isso o programa atribui `id` e `nota` a variáveis declaradas como inteiro.
6. **Sem fila de resultados.** O `join` de cada handle substitui a `Queue`. A ordem de coleta é a dos handles, e o 1º elemento de cada resultado identifica o avaliador.

## 8. Pendências

- Repetir o teste após o merge de #17 e #18 em `dev`. Só então o estado pode passar de `PARTIAL` para `PASS`.
- Executar o cenário remoto em dois computadores reais (RUN-03, #10).
- O caminho `BLOCKED` (backend sem CORE-07) é tratado no harness, mas não foi exercitado nesta integração.
