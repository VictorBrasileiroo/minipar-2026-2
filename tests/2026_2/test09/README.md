# Teste 9 — 160 avaliações + Mandelbrot ASCII (card `T09-01`, Eixo C)

**Estado: `PARTIAL`.** As 54 verificações do harness deram `PASS` (duas execuções completas em 30/10/2026). Mesmo assim o card fica `PARTIAL` porque:

- o build usou uma **integração local, ainda não mergeada**: RUN-03 + `dev` + PR #17 (CORE-06, TAC) + PR #18 (CORE-07, backend C++ que chama o runtime);
- o cenário remoto rodou **só no loopback** (5 processos worker no mesmo computador). Isso prova o protocolo e a distribuição das tarefas, mas não a execução entre computadores. A prova em duas máquinas depende do RUN-03 (#10).

## 1. Objetivo

O Teste 9 amplia o Teste 8 com um **quinto trabalhador lógico** que calcula o fractal de Mandelbrot em ASCII (documento mestre §8.4). O teste precisa mostrar que:

- as 160 atividades são processadas, sem perda nem duplicação;
- o fractal é **calculado**, e não um texto fixo: ele muda com os parâmetros e confere caractere a caractere com um oráculo independente;
- as 5 tarefas (4 lotes de avaliação + Mandelbrot) rodam ao mesmo tempo e são sincronizadas por `join`. O teste também precisa descartar a falha "quinta tarefa serializada" (`docs/05_VALIDACAO_E_ACEITE.md`).

## 2. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `teste9_mandelbrot.minipar` | Programa MiniPar: núcleo canônico do T08 copiado (`lcg`, `nota_de`, `avaliar_lote`), `mandelbrot`, agregação e saída |
| `run_t09.py` | Harness: compila pela CLI, executa os cenários, aplica o oráculo Python e grava as evidências |
| `README.md` | Este documento |

As evidências são gravadas em `output/test09/`, que não é versionado: `results.json`, `compile.log`, `<cenário>.stdout.txt` / `.stderr.txt` e `workers.log`, com as linhas de stderr dos 5 workers e o instante `time.monotonic()` de cada uma.

## 3. Relação com a referência Python

A referência é `docs/fontes/Teste10_Python_referencia.py`, com `trabalhador_mandelbrot` e a parte de avaliações.

| Aspecto | Referência Python | MiniPar T09 |
|---|---|---|
| Atividades | 160 strings `"Aluno a - Atividade b"` | IDs numéricos 0..159: o backend CORE-07 não aceita listas de strings |
| Divisão | 4 avaliadores, 40 cada | avaliador `k` corrige os IDs `40k..40k+39`; nomes `Professor`, `Monitor 1..3` |
| Carga | `random` + laço de atraso (não determinístico) | LCG determinístico `s' = (75 s + 74) mod 65537` com `carga + s0 % carga` passos por atividade. A nota é `s % 101` |
| Mandelbrot | `largura, altura, max_iter = 50, 20, 100` fixos | parâmetros lidos da entrada; `50x20x100` reproduz a referência |
| Índice do caractere | `int((it / max_iter) * 8)` | `(it*8 - (it*8) % max_iter) / max_iter`, só com inteiros, ou seja, `floor(it*8/max_iter)` |
| Paralelismo | `multiprocessing.Process` | `fork ... on destino` + `join` (runtime `minipar_rt`), local ou remoto |
| Tempo | `perf_counter` dentro do programa | medido pelo harness, porque MiniPar não tem relógio nativo |

**Equivalência do índice.** Para `max_iter = 100`, a forma inteira coincide com `int((it/100)*8)` da referência em todos os `it = 0..100`. O harness verifica isso a cada execução e também para `max_iter = 60`. Quando `8·it/max_iter` é inteiro (`it` = 25, 50, 75, 100), as frações `0.25`, `0.5` e `0.75` são exatas em binário. Nos outros casos, o valor fica a pelo menos `0.04` de um inteiro, e o arredondamento de `double` não muda o `int(...)`. O harness gera o fractal 50x20x100 com as duas fórmulas e confirma que são idênticos.

**Ponto flutuante.** Entre dois `int`, o `/` do MiniPar vira divisão inteira no C++ gerado (ver §8). Por isso o programa escreve `y * 1.0 / altura` e `x * 1.0 / largura`. Fora isso, as expressões seguem a mesma ordem da referência (`(y/altura)*2.4 - 1.2`, `zx*zx - zy*zy + cx`, `2.0*zx*zy + cy`), e o resultado em `double` IEEE fica igual ao do Python. Não há FMA: o g++ compila para x86-64 base, sem `-march`.

## 4. Contrato de E/S

Entrada, uma linha por valor:

```text
modo        seq | par
carga       inteiro (passos mínimos do LCG por atividade)
largura     inteiro
altura      inteiro
max_iter    inteiro
destino0..3 avaliadores 0..3 ("local" ou "host:porta")
destino4    mandelbrot
```

No modo `seq`, os destinos são lidos e ignorados, e as 5 chamadas são diretas, na mesma ordem. No modo `par`, os **5 `fork` saem antes do primeiro `join`**. Os números são convertidos por `para_inteiro`, que lê os dígitos com `substr`, porque `to_number` devolve `double` e o backend exige `int` no `%`.

Saída (exata):

```text
=== TESTE 9: 160 avaliacoes + Mandelbrot ===
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
```

A agregação é feita em MiniPar. A lista `vistos` começa com 160 zeros e recebe `+1` para cada par `(id, nota)` devolvido. Depois o programa confere se o primeiro elemento de cada lote é o `k` do avaliador. A função `mandelbrot` devolve **uma string**, com as linhas unidas por `"\n"`, e o `fork` transporta essa string.

## 5. Como executar

Da raiz do repositório (Windows, `g++` 16.2 UCRT64 no PATH):

```powershell
python tests/2026_2/test09/run_t09.py                    # carga 2000000, workers nas portas 7301..7305
python tests/2026_2/test09/run_t09.py --carga 500000     # outra carga
python tests/2026_2/test09/run_t09.py --port-base 7310   # workers em 7311..7315 (faixa permitida 7300-7319)
python tests/2026_2/test09/run_t09.py --no-remote        # só seq e par local
```

Exit `0` significa que todas as verificações deram PASS; `1`, que alguma deu FAIL; `2`, BLOCKED (backend Fork/Join CORE-07 ausente, mensagem `BLOCKED: backend CORE-07 ausente`, ou portas ocupadas).

Execução manual, com o mesmo binário fazendo os papéis de coordenador e worker:

```powershell
python main.py tests/2026_2/test09/teste9_mandelbrot.minipar teste9     # gera output/teste9.exe
output/teste9.exe --minipar-worker 7301 --bind 127.0.0.1                 # um terminal por worker
# entrada do coordenador: par, 2000000, 50, 20, 100, 127.0.0.1:7301 ... 127.0.0.1:7305
```

## 6. Oráculo (Python, independente do programa)

1. **Notas (SOMA_NOTAS):** `s0 = lcg(id+1)`, `n = carga + s0 % carga`. O estado final vem da forma fechada do LCG afim com `m = 65537` primo: `s_n = (a^n·s0 + c·(a^n − 1)·(a−1)^{-1}) mod m`, calculada com `pow` modular. Nota = `s_n % 101`. Antes de usar a fórmula, o harness confere que ela dá o mesmo resultado de um laço ingênuo para as cargas 1, 2, 3, 7, 50 e 333 e os 160 IDs.
2. **Contagem:** em cada cenário, `TOTAL 160`, `UNICOS 160`, `DUPLICADOS 0`, `PERDIDOS 0`, 4 avaliadores com 40 atividades cada e nomes corretos. O agregado (contadores + SOMA_NOTAS) tem de ser **idêntico em todos os cenários**.
3. **Fractal:** o Mandelbrot é recalculado em Python com a mesma fórmula, para cada conjunto de parâmetros, e comparado **caractere a caractere**. Se houver divergência, o harness informa a primeira posição diferente (linha, coluna). O teste usa dois conjuntos, `50x20x100` (referência) e `30x12x60`, e o harness confirma que os dois fractais esperados são diferentes, o que exclui uma saída fixa.
4. **Remoto (5 workers, loopback):** 5 PIDs distintos; cada worker com exatamente 1 `TASK` e 1 `RESULT` (`ok`); funções = 4 `avaliar_lote` + 1 `mandelbrot`.
5. **Concorrência:** os 5 `TASK` (todos, inclusive o `mandelbrot`) aparecem no stderr dos workers **antes** do primeiro `RESULT` de `avaliar_lote`. As marcas de tempo vêm de `time.monotonic()` no harness, com uma thread de leitura por worker. Se a quinta tarefa só fosse enviada depois de algum `join`, essa verificação falharia. Com `--carga 1000`, as tarefas terminam em menos de 1 ms, e a verificação **deu FAIL** (último TASK em +1.3 ms, primeiro RESULT em +0.9 ms). Isso mostra que ela discrimina de verdade.

O harness não guarda nenhuma saída esperada fixa: tudo vem das fórmulas acima.

## 7. Resultados reais (30/10/2026, `--carga 2000000`, porta-base 7300)

Duas execuções completas: `RESULTADO T09: PASS (54/54 PASS)`, exit `0` nas duas.

| Cenário | Exit | Tempo exec. 1 | Tempo exec. 2 |
|---|---|---|---|
| `seq_50x20x100` | 0 | 2.607 s | 2.620 s |
| `par_local_50x20x100` | 0 | 0.672 s | 0.678 s |
| `seq_30x12x60` | 0 | 2.211 s | 2.830 s |
| `par_local_30x12x60` | 0 | 0.739 s | 0.619 s |
| `par_remoto_50x20x100` (5 workers loopback) | 0 | 0.863 s | 0.700 s |

Os tempos são **apenas informativos**. Outros agentes e processos usavam a máquina ao mesmo tempo, então a medição é ruidosa, e o teste não exige speedup. Eles incluem o início do processo, e a medição foi feita pelo harness.

- Agregado, igual nos 5 cenários: `TOTAL 160`, `UNICOS 160`, `DUPLICADOS 0`, `PERDIDOS 0`, `SOMA_NOTAS 7630` (o oráculo pela forma fechada também dá 7630). Com `--carga 1000`, o resultado foi `SOMA_NOTAS 7760`, igual ao oráculo: o valor muda com a carga.
- Remoto, execução 1: PIDs `15996, 41300, 44400, 33736` (avaliar_lote, portas 7301–7304) e `22832` (mandelbrot, 7305). Durações informadas pelos workers: 667, 830, 830 e 787 ms nos lotes e 0 ms no Mandelbrot. Último `TASK` +0.7 ms e primeiro `RESULT` de avaliar_lote +678.2 ms, relativos ao primeiro `TASK`. Execução 2: +0.4 ms contra +598.3 ms.
- Início do fractal 50x20x100, igual ao oráculo nas 20 linhas × 50 colunas:

```text
                                .
                             ..=:.
                              @@@:
                        +@.@@@@@@@@@. :..
                       .@@@@@@@@@@@@@@:
                .     #@@@@@@@@@@@@@@@@@:
             .@:@@@- :@@@@@@@@@@@@@@@@@@:
          - .@@@@@@@@@@@@@@@@@@@@@@@@@@@
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@.
```

(As linhas reais têm 50 caracteres, com espaços à direita, e as duas primeiras são só espaços.)

- Início do fractal 30x12x60, também igual ao oráculo:

```text
                   .@
                 .@@:
              .@-@@@@@.::
             .@@@@@@@@@@.
       .:@@@:@@@@@@@@@@@=
@@@@@@@@@@@@@@@@@@@@@@@.
```

**Ambiente:** Windows 11 Pro 10.0.26300, Intel64 Family 6 Model 170 (14 CPUs lógicas), Python 3.14.7, g++ 16.2.0 (MSYS2 UCRT64, Rev3), flags do backend `-std=c++20 -O3 -pthread -lws2_32` + `-I runtime/include`.

## 8. Divergências e achados

- **IDs numéricos** em vez de strings `"Aluno a - Atividade b"`, porque o CORE-07 não aceita listas de strings.
- **Carga determinística (LCG)** em vez de `random` + atraso, para que exista um oráculo exato (SOMA_NOTAS).
- **Índice do caractere com inteiros** e sem `floor`, equivalente à referência para `max_iter = 100` (§3).
- **Tempo medido fora do programa**, porque MiniPar não tem relógio nativo.
- **Semântica de `/` (sondagem):** no C++ gerado, `/` entre dois valores `int` é divisão **inteira**. `print(7 / 2)` com variáveis `int` imprime `3`. A função `func divi(a, b) { return a / b; }` vira `double divi(auto a, auto b) { return (a / b); }`, e `divi(7, 2)` imprime `3`: o tipo de retorno é `double`, mas a divisão já foi truncada. Isso diverge do Python, onde `/` sempre dá `float`. O T09 contorna com `* 1.0`. Literais decimais como `2.4` e as somas em `double` funcionam (`print(2.4)` imprime `2.4`). O achado foi registrado para o Eixo A; `src/` não foi alterado.
- `to_number` devolve `double` (`std::stod`), e `%` com `double` é rejeitado pela análise semântica CORE-07 ("operacao inteira com decimal"). Por isso o programa usa `para_inteiro`.
- **Não testado:** dois computadores (RUN-03 #10), worker morto durante o T09 (coberto no runtime pelo RT-09, não neste teste) e Linux.
