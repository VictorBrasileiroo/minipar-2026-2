# CORE-10 — Regressão final T01–T07 com oráculos reais

**Card:** `CORE-10` · **Eixo:** C (Erasmo) · **Data:** 05/11/2026 · **Base medida:** `dev` em `59ea77d`
**Branch:** `eixo-c/CORE-10-regressao-final` · **Consumidores:** Eixo A (defeitos remanescentes), `INT-02` (Eixo B), relatório (`DOC-04`)

> Regressão do código de A **depois** do CORE-02 (#16), do CORE-03 (#14), do CORE-04/05 (#15), do CORE-06 (#17) e do CORE-07 (#18/#29), todos em `dev`.
> Mesmos programas, entradas e oráculos da baseline do [`CORE-01`](CORE-01_BASELINE_T01_T07.md) (`56c3a1c`, 22/10), para comparar sem trocar a régua. Nada em `src/` nem nos programas de `tests/` foi alterado.

## 1. Resultado

| Teste | CORE-01 (22/10, `56c3a1c`) | **CORE-10 (05/11, `59ea77d`)** | Oráculo | Observação |
|---|---|---|---|---|
| T01 Calculadora cliente-servidor | FAIL intermitente (13/30) | **FAIL** intermitente (**13/20**) | servidor recebe `+ 2 3`; cliente recebe `5` | As falhas são timeout de 30 s: DEF-01 continua aberto |
| T02 Fatorial/Fibonacci `par` | FAIL intermitente (9/10) | **FAIL** intermitente (**14/20**) | fatorial 5 = 120; Fibonacci `0,1,1,2,3,5,8,13` | Valores calculados certos; a saída sai corrompida (`0120`): DEF-02 continua aberto |
| T03 Neurônio | PASS | **PASS** | iterações 1, 50 e 51 do `.expected.txt` (4 casas), convergência na 51 | Formato textual difere da referência Python; os valores batem |
| T04 XOR | PARTIAL | **PARTIAL** | classificação XOR + valores da referência | Classificação certa nas 4 entradas; valores iguais aos de 22/10 (`0.0068`, `0.9865`, `0.9892`, `0.0140`); **tolerância ainda não acordada** |
| T05 Recomendação | PASS | **PASS** | os 12 produtos do `.expected.txt`, probabilidade > 0,55 | Entrada derivada (CORE-01 §3) |
| T06 Quicksort OO | PASS | **PASS** | `10 -3 -40 80 70 -100` → `[-100, -40, -3, 10, 70, 80]` | — |
| T07 Quicksort iterativo | PASS só na ordenação; TAC fixo e limites FAIL | **PASS** | `[33, 12, 98, 5, 61]` → `[5, 12, 33, 61, 98]` | Ordenação, TAC e limites agora passam (tabela abaixo) |

Frações = execuções PASS / execuções feitas (CORE-01: 3 rodadas de 10 no T01; CORE-10: 2 rodadas de 10, seção 2).

Verificações adicionais do T07 (doc 05 §2, "mutação adversarial obrigatória"):

| Verificação | CORE-01 | **CORE-10** | Evidência |
|---|---|---|---|
| Mutação: mesma função `quicksort_iterativo`, corpo trivial | FAIL (recebia o TAC fixo) | **PASS** | O TAC do programa mutado difere do TAC antigo: o TAC agora vem da AST (DEF-03 resolvido pelo CORE-02) |
| C++ gerado recompilado com `-D_GLIBCXX_ASSERTIONS` | FAIL (`__n < this->size()`) | **PASS** | Roda sem violação e imprime `Array ordenado: [5, 12, 33, 61, 98]` (DEF-04 resolvido pelo CORE-02) |
| TAC gerado = `teste7_quicksort_iterativo_tac.expected.tac` | idêntico | **INFO**, diferente | Esperado: o `.expected.tac` é o snapshot histórico do TAC fixo e foi preservado de propósito (CORE-02 §"Comparação com `.expected.tac`"). Não é usado como oráculo |

**Resumo:** 4 PASS (T03, T05, T06, T07 completo), 1 PARTIAL (T04), 2 FAIL intermitentes (T01, T02). Em relação ao CORE-01, o T07 deixou de ter TAC fixo e escrita fora do vetor; T01, T02 e T04 não mudaram.
Os 7 programas **compilam** pela CLI oficial (`main.py` exit 0, G++ exit 0, binário novo por execução).

**Não há falso PASS:** o T07 só é PASS porque as três verificações passaram de fato; T01 e T02 continuam FAIL mesmo passando na maioria das execuções, porque um teste que trava ou corrompe a saída em parte das execuções não está correto; T04 continua PARTIAL porque não existe tolerância combinada.

## 2. Ambiente e reprodução

| Item | Valor |
|---|---|
| SO | Windows 11 Pro 10.0.26300 |
| Python | CPython 3.14.7 |
| G++ | `C:\msys64\ucrt64\bin\g++.exe`, 16.2.0 (Rev3, MSYS2) |
| Flags | as do `src/codegen.py`: `-std=c++20 -O3 -pthread -I runtime/include -lws2_32`; a verificação de limites usa `-O0 -g -D_GLIBCXX_ASSERTIONS` sobre o mesmo `.cpp` gerado |
| Rede | T01 usa `127.0.0.1:5101/5102` (loopback) |
| Script | [`scripts/baseline_t01_t07.py`](../../scripts/baseline_t01_t07.py), o mesmo do CORE-01, sem alteração |

```powershell
python -B scripts/baseline_t01_t07.py --repeat 10                  # rodada completa (T01/T02 x10)
python -B scripts/baseline_t01_t07.py --only T01,T02 --repeat 10   # só a repetição dos intermitentes
```

Rodadas desta data, todas em `59ea77d`. O JSON de cada uma fica em `output/core01/run-<data>/baseline.json` (ignorado pelo Git):

| Rodada | Escopo | T01 | T02 | Exit |
|---|---|---|---|---|
| `run-20261105-155226` | T01–T07, T01/T02 x10 | 7/10 | 7/10 | 1 |
| `run-20261105-160348` | T01/T02 x10 | 6/10 | 7/10 | 1 |
| **Total** | | **13/20** | **14/20** | |

| Teste | SHA-256 da fonte (16 primeiros) | Compilação | Execução |
|---|---|---|---|
| T01 | `1a2b11df5e3ed31b` | exit 0, 3,6 s | 30,1 s quando trava (timeout); 0,6–1,7 s quando passa |
| T02 | `6eebdf5515c23305` | exit 0, 1,8 s | 0,08 s |

Os hashes das fontes são os mesmos do CORE-01: os programas de teste não mudaram.

## 3. Defeitos remanescentes e risco

| ID | Sev. | Teste | Estado em 05/11 | Risco para a entrega | Encaminhamento |
|---|---|---|---|---|---|
| DEF-01 | P1 | T01 | **aberto**. Mesmo sintoma: o receptor fica parado esperando uma mensagem que se perdeu. A hipótese de causa do CORE-01 §4 (reuso do socket depois de `connect` falho no `c_channel` herdado) não foi contestada nem corrigida | Alto na demonstração do T01: cerca de 1 em 3 execuções trava. Não afeta Fork/Join (T08–T10 usam o runtime novo, sem `c_channel`) | Eixo A: card novo ou `CORE-09`. Na demonstração, rodar de novo se travar e dizer que é um defeito conhecido |
| DEF-02 | P2 | T02 e todo `par` com `print` | **aberto**. `print` com vários argumentos não é atômico entre threads; a saída se mistura (`Fatorial de 5: 0120`) | Médio: os valores estão certos, mas a saída fica ilegível em parte das execuções | Eixo A: `src/cpp_template.py`/`codegen.py` (trava por `print`). Sem card até esta data |
| DEF-03 | P0 | T07 | **resolvido** (#16) | — | — |
| DEF-04 | P0 | T07 | **resolvido** (#16) | — | — |
| T04-TOL | — | T04 | **em aberto**: falta a tolerância numérica | Baixo: a classificação está certa e os valores são estáveis desde 2026.1 | A+C fixam a tolerância (doc 05 §2); com `|d| ≤ 0,02`, o T04 passaria |

## 4. Limitações

- Uma máquina (Windows, G++ UCRT64); Linux não foi testado nesta rodada.
- T01 roda em loopback: não prova comunicação entre computadores.
- As repetições medem a frequência da falha nesta máquina, não uma taxa garantida.
- T05 vale para a entrada derivada do CORE-01 §3.

## 5. Verificação documental

- Documentos verificados: `AGENTS.md`, `MEMORY.md`, `docs/01`, `02`, `04`, `05`, `auditorias/CORE-01_BASELINE_T01_T07.md`, `auditorias/CORE-02_TAC_QUICKSORT.md`.
- Criado: este relatório. O `scripts/baseline_t01_t07.py` não mudou, porque os oráculos do CORE-01 continuam válidos e o TAC do T07 já era tratado como verificação à parte.
- `docs/05_VALIDACAO_E_ACEITE.md` §7 (matriz de estados) está fora do escopo de arquivos do card. Linha sugerida para o coordenador: `05/11 · 59ea77d | FAIL* | FAIL* | PASS | PARTIAL | PASS | PASS | PASS | PASS | PASS (loopback) | PASS (loopback) | PASS | * intermitente; CORE-10, T08–T10, T11-03`.
- `AGENTS.md`: sem mudança, porque o card não altera regras, convenções, arquitetura nem fluxo.
