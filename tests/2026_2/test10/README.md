# Teste 10 — 160 avaliações + Mandelbrot + Sierpinski (card `T10-01`, Eixo C)

**Estado: `PARTIAL`.** As 126 verificações do harness deram `PASS` em três execuções completas (30/10/2026), e os 4 mutantes do programa foram detectados. O card fica `PARTIAL` porque:

- o build usou uma **integração local, ainda não mergeada**: RUN-03 + `dev` + PR #17 (CORE-06, TAC) + PR #18 (CORE-07, backend C++ que chama o runtime);
- o cenário remoto rodou **só no loopback** (6 processos worker no mesmo computador). Isso prova o protocolo e a distribuição das tarefas, mas não a execução entre computadores. A prova em duas máquinas depende do RUN-03 (#10);
- o formato de saída do Sierpinski (ASCII + SVG renderizado pelo harness) é uma **proposta** para a ADR-014, que continua `EM ABERTO` até o coordenador decidir.

## 1. Objetivo

O Teste 10 amplia o Teste 9 com um **sexto trabalhador lógico**, que gera o Tapete de Sierpinski (documento mestre §8.4). O teste precisa mostrar que:

- as 160 atividades são processadas, sem perda nem duplicação;
- os dois fractais são **calculados**: mudam com os parâmetros e conferem caractere a caractere com oráculos independentes;
- o Sierpinski é um trabalho **de verdade do modelo Fork/Join**: sai num `fork` como os outros cinco, e não depois dos `join` no processo principal, como na referência Python (`docs/05_VALIDACAO_E_ACEITE.md`: "Sierpinski só depois de join sem registrar");
- `seq` e `par` executam **a mesma carga** (comparação justa, sem o "benchmark injusto" apontado em `docs/05`).

## 2. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `teste10_dois_fractais.minipar` | Programa MiniPar: núcleo canônico do T08 copiado (`lcg`, `nota_de`, `avaliar_lote`), `mandelbrot` do T09, `sierpinski` iterativo, agregação e saída |
| `run_t10.py` | Harness: compila pela CLI, executa os cenários, aplica os oráculos Python, renderiza o SVG e grava as evidências |
| `README.md` | Este documento |

As evidências vão para `output/test10/`, que não é versionado: `results.json`, `stdout_<conjunto>_<cenário>.txt`, `workers/worker<N>.stderr.log` (com o instante `time.monotonic()` de cada linha), `mandelbrot.txt` e `sierpinski.svg`.

## 3. Relação com a referência Python

A referência é `docs/fontes/Teste10_Python_referencia.py`.

| Aspecto | Referência Python | MiniPar T10 |
|---|---|---|
| Atividades | 160 strings `"Aluno a - Atividade b"` | IDs numéricos 0..159: o backend CORE-07 não aceita listas de strings |
| Carga | `random` + laço de atraso (não determinístico) | LCG determinístico `s' = (75 s + 74) mod 65537`, como no T08/T09; nota `s % 101` |
| Mandelbrot | `50, 20, 100` fixos | parâmetros lidos da entrada; `50x20x100` reproduz a referência (mesma fórmula do T09) |
| Sierpinski | `turtle`, recursivo, grau 4, desenhado **no processo principal depois dos `join`** dos outros cinco | função `sierpinski(grau)` **iterativa**, executada num `fork` próprio (6º trabalho), devolve o tapete em ASCII (`#` cheio, espaço vazio) |
| Saída gráfica | janela Turtle | ASCII na saída do programa + `output/test10/sierpinski.svg` gerado pelo harness **a partir do texto impresso** |
| Comparação seq × par | o modo sequencial e o paralelo não executam o mesmo conjunto de trabalhos | `seq` faz as mesmas 6 chamadas, diretas e na mesma ordem |
| Tempo | `perf_counter` dentro do programa | medido pelo harness, porque MiniPar não tem relógio nativo |

**Por que iterativo.** No CORE-07, funções chamadas por `fork` não podem usar globais nem recursão. O programa usa a caracterização aritmética do tapete: a célula `(i, j)` fica vazia se, em algum dígito da base 3, `i` e `j` valem 1 ao mesmo tempo. O harness confere essa regra contra uma construção **recursiva** independente (8 subquadrados) para os graus 1 a 4, antes de usá-la como oráculo.

## 4. Contrato de E/S

Entrada, uma linha por valor:

```text
modo        seq | par
carga       inteiro (passos mínimos do LCG por atividade)
largura     inteiro (Mandelbrot)
altura      inteiro (Mandelbrot)
max_iter    inteiro (Mandelbrot)
grau        inteiro (Sierpinski; lado = 3^grau)
destino0..3 avaliadores 0..3 ("local" ou "host:porta")
destino4    mandelbrot
destino5    sierpinski
```

No modo `seq`, os destinos são lidos e ignorados. No modo `par`, os **6 `fork` saem antes do primeiro `join`**. Os números são lidos por `para_inteiro` (dígitos via `substr`), pelo mesmo motivo do T08/T09: `to_number` devolve `double` e o backend exige `int` no `%`.

Saída (exata):

```text
=== TESTE 10: 160 avaliacoes + Mandelbrot + Sierpinski ===
MODO <seq|par>
AVALIADOR <k> <nome> <qtd>        (4 linhas, k = 0..3)
TOTAL <n>
UNICOS <n>
DUPLICADOS <n>
PERDIDOS <n>
SOMA_NOTAS <n>
=== MANDELBROT <largura>x<altura> max_iter=<m> ===
<altura linhas de largura caracteres de " .:-=+#%@">
=== FIM MANDELBROT ===
=== SIERPINSKI grau=<g> ===
<3^g linhas de 3^g caracteres '#' ou ' '>
=== FIM SIERPINSKI ===
```

## 5. Como executar

Da raiz do repositório (Windows, `g++` 16.2 UCRT64 no PATH):

```powershell
python tests/2026_2/test10/run_t10.py                    # carga 2000000, workers nas portas 7401..7406
python tests/2026_2/test10/run_t10.py --carga 500000     # outra carga
python tests/2026_2/test10/run_t10.py --port-base 7410   # workers em 7411..7416 (faixa permitida 7400-7419)
```

Exit `0`: todas as verificações PASS; `1`: alguma FAIL; `2`: BLOCKED (backend Fork/Join CORE-07 ausente, mensagem `BLOCKED: backend CORE-07 ausente`).

Execução manual, com o mesmo binário nos papéis de coordenador e worker:

```powershell
python main.py tests/2026_2/test10/teste10_dois_fractais.minipar teste10   # gera output/teste10.exe
output/teste10.exe --minipar-worker 7401 --bind 127.0.0.1                  # um terminal por worker (7401..7406)
# entrada do coordenador: par, 2000000, 50, 20, 100, 3, 127.0.0.1:7401 ... 127.0.0.1:7406
```

## 6. Oráculo (Python, independente do programa)

1. **Notas (SOMA_NOTAS):** forma fechada do LCG afim com `m = 65537` primo, `s_n = (a^n·s0 + c·(a^n − 1)·(a−1)^{-1}) mod m`. O harness confere a fórmula contra um laço ingênuo para as cargas 1, 2, 7, 50 e 300 e os 160 IDs.
2. **Contagem:** em cada cenário, `TOTAL 160`, `UNICOS 160`, `DUPLICADOS 0`, `PERDIDOS 0`, 4 avaliadores × 40 com nomes corretos. O agregado (contadores, SOMA_NOTAS e os dois fractais) tem de ser **idêntico em todos os cenários** do mesmo conjunto de parâmetros.
3. **Mandelbrot:** recalculado em Python com a fórmula da referência, comparado caractere a caractere. Os conjuntos A e B produzem fractais diferentes, o que exclui saída fixa.
4. **Sierpinski:** tamanho `3^g × 3^g`; exatamente `8^g` células cheias; igual, caractere a caractere, à regra da base 3, que por sua vez é conferida contra a construção recursiva (graus 1–4).
5. **Remoto (6 workers, loopback):** 6 PIDs distintos, iguais aos PIDs dos processos criados pelo harness; cada worker com exatamente 1 `TASK` e 1 `RESULT ok`, com a função esperada (4 `avaliar_lote`, 1 `mandelbrot`, 1 `sierpinski`); nenhum worker executa o fluxo principal.
6. **Concorrência:** os 6 `TASK`, incluindo `mandelbrot` e `sierpinski`, chegam aos workers **antes** do primeiro `RESULT` de `avaliar_lote`. Se o Sierpinski fosse disparado só depois de um `join`, essa verificação falharia.

O harness não guarda saída esperada fixa: tudo vem das fórmulas acima.

**Mutação.** Quatro variantes erradas do programa foram compiladas e passadas pelo mesmo harness (`--carga 200000`); todas deram exit `1`:

| Mutante | Alteração | FAILs |
|---|---|---|
| `lote_perde` | `while (i < fim - 1)` em `avaliar_lote` | 25 (39 por avaliador, `TOTAL 156`, `PERDIDOS 4`) |
| `nota_mais1` | `return s % 101 + 1` | 5 (`SOMA_NOTAS` diverge do oráculo) |
| `mandel_k` | índice da paleta com `* 7` | 5 (15 linhas do Mandelbrot diferentes) |
| `sierp_ou` | `\|\|` no lugar de `&&` na regra | 10 (64 células cheias em vez de 512) |

## 7. Resultados reais (30/10/2026, `--carga 2000000`, porta-base 7400)

Três execuções completas: `PASS: 126/126 checagens PASS`, exit `0` em todas.

| Cenário | Exit | Exec. 1 | Exec. 2 |
|---|---|---|---|
| A `seq` (50x20x100, grau 3) | 0 | 1.391 s | 1.482 s |
| A `par` local | 0 | 0.355 s | 0.340 s |
| A `par` remoto (6 workers loopback) | 0 | 0.397 s | 0.391 s |
| B `seq` (30x12x60, grau 2) | 0 | 1.698 s | 1.216 s |
| B `par` local | 0 | 0.368 s | 0.375 s |

Os tempos são **apenas informativos**: incluem o início do processo, foram medidos pelo harness e a máquina tinha outros processos ativos. O teste não exige speedup.

- Agregado, igual nos 5 cenários: `TOTAL 160`, `UNICOS 160`, `DUPLICADOS 0`, `PERDIDOS 0`, `SOMA_NOTAS 7630` (igual ao oráculo e ao T08/T09, que usam o mesmo núcleo).
- Remoto, execução 1: PIDs `12940, 23004, 13360, 12904` (avaliar_lote), `13892` (mandelbrot) e `21088` (sierpinski). Os `TASK` de `mandelbrot` e `sierpinski` chegaram em +0.0 e +0.7 ms; o primeiro `RESULT` de `avaliar_lote` veio em +281.9 ms (margem de 263.5 ms após o último `TASK`). Execução 2: margem de 271.7 ms.
- Sierpinski grau 3 (início, 27×27, 512 células cheias):

```text
###########################
# ## ## ## ## ## ## ## ## #
###########################
###   ######   ######   ###
# #   # ## #   # ## #   # #
###   ######   ######   ###
###########################
# ## ## ## ## ## ## ## ## #
###########################
#########         #########
# ## ## #         # ## ## #
```

- Sierpinski grau 2 (completo, 9×9, 64 células cheias):

```text
#########
# ## ## #
#########
###   ###
# #   # #
###   ###
#########
# ## ## #
#########
```

**Ambiente:** Windows 11 Pro 10.0.26300, 14 CPUs lógicas, Python 3.14.7, g++ 16.2.0 (MSYS2 UCRT64, Rev3), flags do backend `-std=c++20 -O3 -pthread -lws2_32` + `-I runtime/include`. HEAD da integração local: `f09bdea`.

## 8. Divergências e achados

- **Sierpinski paralelo** e no modelo Fork/Join, em vez de Turtle no processo principal após os `join`. É a correção pedida em `docs/05` e está documentada aqui.
- **Saída gráfica:** ASCII + SVG (`output/test10/sierpinski.svg`, gerado pelo harness só a partir do texto impresso pelo programa). É a proposta deste card para a **ADR-014**, que ainda depende de decisão do coordenador.
- **Grau parametrizado:** a referência usa grau 4 (81×81). O teste usa graus 3 e 2 para manter a saída legível; o programa aceita grau 4 sem alteração.
- **Carga equivalente:** `seq` e `par` executam os mesmos 6 trabalhos.
- **IDs numéricos**, **LCG determinístico** e **tempo medido fora do programa**: mesmos motivos do T08/T09.
- **Achados do CORE-07** (registrados para o Eixo A, `src/` não alterado): `to_number` devolve `double` e `%` com `double` é rejeitado, daí `para_inteiro`; `/` entre `int` trunca mesmo em função com retorno `double` (o Mandelbrot usa `* 1.0`, como no T09).
- **Não testado:** dois computadores (RUN-03 #10), worker morto durante o T10 (coberto no runtime pelo RT-09) e Linux.
