# HANDOFF — INT-02 — Regressão integral T01–T11 e três interfaces

**Responsável:** Eixo B (Riquelme) · **Branch:** `eixo-b/INT-02-regressao-integral` (base `dev`) · **Data:** 09/11/2026
**Base medida:** `dev` em `8d07433` (merge do DEF-02, #41), com CORE-10 (#38), DEF-01 (#40) e DEF-02 (#41) integrados
**Contratos usados:** C-FJ-v1 (§2), C-WEB-v1 (§1), C-T11-v1 (§3), oráculos de `docs/05_VALIDACAO_E_ACEITE.md` §2
**Consumidores:** Eixo A (compilador) e Eixo C (runtime) validam os seus recortes; `DOC-04` (relatório); `EST-01/02` (apresentação)

> Coordenação da regressão final. Nenhum arquivo de `src/`, `runtime/`, `web_didatica/`, programa de teste ou oráculo foi alterado:
> o INT-02 só **executa** os verificadores já integrados de cada eixo e consolida o resultado.

## 1. Resultado

**Estado do card: PARTIAL.** Todos os testes e interfaces executáveis nesta máquina deram PASS, menos o T04 (PARTIAL, tolerância numérica não acordada). A exigência de **rede real** (dois computadores) não foi executada nesta rodada: está BLOCKED, com roteiro na seção 5.

| Teste | CORE-10 (05/11, `59ea77d`) | **INT-02 (09/11, `8d07433`)** | Oráculo conferido | Observação |
|---|---|---|---|---|
| T01 Calculadora cliente-servidor | FAIL intermitente (13/20) | **PASS 30/30** (10 + 20) | servidor recebe `+ 2 3` pelo canal 5101; cliente recebe `5` pelo 5102 | DEF-01 confirmado como resolvido. **Só loopback** |
| T02 Fatorial/Fibonacci `par` | FAIL intermitente (14/20) | **PASS 30/30** (10 + 20) | fatorial 5 = 120; Fibonacci `0,1,1,2,3,5,8,13`, sem saída misturada | DEF-02 confirmado como resolvido |
| T03 Neurônio | PASS | **PASS** | iterações 1, 50 e 51 do `.expected.txt` (4 casas), convergência na 51 | — |
| T04 XOR | PARTIAL | **PARTIAL** | classificação XOR certa nas 4 entradas | Valores iguais aos de 2026.1/CORE-10 (`0.0068`, `0.9865`, `0.9892`, `0.0140`); maior desvio `0.0151`; **tolerância não acordada** (INT02-01) |
| T05 Recomendação | PASS | **PASS** | os 12 produtos do `.expected.txt`, probabilidade em (0,55; 1] | — |
| T06 Quicksort OO | PASS | **PASS** | `10 -3 -40 80 70 -100` → `[-100, -40, -3, 10, 70, 80]` | — |
| T07 Quicksort iterativo/TAC | PASS | **PASS** | `[33, 12, 98, 5, 61]` → `[5, 12, 33, 61, 98]`; TAC do programa mutado muda; C++ roda com `-D_GLIBCXX_ASSERTIONS` | `.expected.tac` histórico difere (INFO, esperado desde o CORE-02) |
| T08 4 avaliadores | PASS (T08-01, loopback) | **PASS** 32 checagens + 1 INFO | `TOTAL 160`, `UNICOS 160`, `DUPLICADOS 0`, `PERDIDOS 0`, `SOMA_NOTAS 7630` = oráculo Python, cada item igual ao oráculo; 4 `TASK` antes do 1º `RESULT` | seq, par local e par remoto com 4 workers em **127.0.0.1** |
| T09 5 trabalhos | PASS (T09-01, loopback) | **PASS** 54/54 | T08 + Mandelbrot recalculado em Python (50×20×100 e 30×12×60, fractais diferentes) | idem, 5 workers no loopback |
| T10 6 trabalhos | PASS (T10-01, loopback) | **PASS** 126/126 | T09 + Sierpinski `3^g × 3^g` com `8^g` células cheias (512/729 e 64/81), gerado num `fork` próprio | Formato gráfico (ASCII + SVG) ainda depende da **ADR-014** (INT02-03) |
| T11 MiniCompilador | PASS (T11-01..03) | **PASS** 48/48 | casos 1 e 3 `22.0`, caso 2 `-84.0`, stdout igual a C-T11-v1 §3.12; entradas inválidas rejeitadas; `.arm` igual ao de referência | SHA-256 dos `.arm` atuais = dos executados no CPUlator (T11-03), seção 4 |

Frações = execuções PASS / execuções feitas, somando as duas rodadas. Um teste repetido só é PASS se **todas** as execuções passarem.

### Interfaces

| Interface | Verificação | Resultado |
|---|---|---|
| 1. Terminal (`main.py`, `menu.py`) | `tests/2026_2/core09/test_interfaces.py`: processo real `main.py` sem argumentos, menu, seleção, compilação e execução, erro sintático sem derrubar o menu, Fork/Join pela CLI (`14 42`), artefatos antigos invalidados | **PASS** 14/14 testes, nas duas rodadas |
| 2. Web original (`app.py`) | `smoke_http.py`: `main.py` opção 2 → Flask em `127.0.0.1:5000` → `/api/compile` → binário imprime `42` | **PASS** nas duas rodadas |
| 2. Web original — visual | Navegador do app em `127.0.0.1:5000`: T07 pelo explorer → Compile & Run → `Array ordenado: [5, 12, 33, 61, 98]`; abas C++ (394 linhas) e TAC (80 linhas, começa em `func quicksort_iterativo:`); fonte com string não fechada → `[ERRO LEXICO] Linha 1: String sem fechamento` e painéis C++/TAC vazios | **PASS** (fecha o BLOCKED visual do CORE-09) |
| 3. Web didática (`web_didatica/`) | `unittest discover -s web_didatica/tests`: rotas C-WEB-v1 com o serviço real e o g++, execução com stdin, timeout, downloads byte a byte, três casos do T11 | **PASS** 37/37 testes, nas duas rodadas |
| 3. Web didática — visual | Navegador do app em `127.0.0.1:5001`: exemplo T11, stdin `((2+4)*7)-(5*4)`, Compilar e executar → g++ `ok`, código de saída 0, resultado `➡️  22.0`, Assembly com `r8` e `b .`; FIX-02 → Analisar → cartão "Erro léxico · linha 1, coluna 11" | **PASS** |
| Integração dos três eixos | `scripts/smoke_int01.py`: A (CLI Fork/Join → runtime, local e worker no loopback), B (serviço CORE-08), C (Web didática pelo cliente de teste do Flask) | **PASS** A, B e C, exit 0, nas duas rodadas |

Capturas das verificações visuais: [`INT-02_capturas/`](INT-02_capturas/) (`web1_t07_compile_run.jpg`, `web1_t07_tac.jpg`, `web1_erro_lexico.jpg`, `web2_t11_compilar_executar.jpg`, `web2_fix02_erro_lexico.jpg`). Nas duas Webs a interação foi por clique; na Web original, o fonte inválido foi colocado no editor CodeMirror por `setValue` (equivale a digitar) e a compilação, pelo botão.

### Suítes de regressão do núcleo

| Suíte | Resultado (rodadas 1 e 2) |
|---|---|
| CORE-02 (TAC do T07 derivado da AST) | PASS 5/5 |
| CORE-06 (TAC de Fork/Join) | PASS 54/54 |
| CORE-07 (backend C++ + runtime, print atômico) | PASS 19/19 |
| CORE-08 (serviço de fases) | PASS 36/36 |
| DEF-01 (canal TCP herdado, inclusive stdin após 7 s) | PASS 2/2 |

**Resumo:** 10 PASS e 1 PARTIAL (T04) em T01–T11; três interfaces PASS (automático e visual); smoke dos três eixos PASS; 5 suítes PASS. **Nenhum FAIL.** Rede real BLOCKED nesta rodada.

**Sem falso PASS:** T01/T02 só são PASS porque as 30 execuções de cada passaram; T04 segue PARTIAL; "par remoto" de T08–T10 e o T01 rodam no loopback e **não** provam execução entre computadores (doc 05 §4, ADR-017); o T11 não foi reexecutado no CPUlator, e a evidência do T11-03 só vale porque os bytes dos `.arm` não mudaram.

## 2. Ambiente e reprodução

| Item | Valor |
|---|---|
| SO | Windows 11 Pro 10.0.22631, 14 CPUs lógicas |
| Python | 3.14.7 do `.venv` (Flask 3.0.0, `requeriments.txt`) |
| G++ | `C:\msys64\ucrt64\bin\g++.exe`, 16.2.0 (Rev6, MSYS2) |
| Commit | `8d0743302ffe29e012ef4a3a4cc1eeba0281637c` (`dev`), árvore sem mudanças em código de produção (só o script novo, não rastreado durante a rodada) |
| Rede | só `127.0.0.1` (portas 5000, 5001, 5101/5102, 7201–7204, 7301–7305, 7401–7406, 7500–7519) |
| Script | [`scripts/regressao_int02.py`](../../scripts/regressao_int02.py) (novo) |

```powershell
.venv\Scripts\python.exe -B scripts/regressao_int02.py --repeat 10      # rodada 1
.venv\Scripts\python.exe -B scripts/regressao_int02.py --repeat 20      # rodada 2
.venv\Scripts\python.exe -B scripts/regressao_int02.py --only T08,T11   # só algumas etapas
```

O script roda cada verificador num processo separado, grava `output/int02/run-<data>/<etapa>.log`, copia o JSON do verificador para a mesma pasta e consolida `results.json`. Exit 0 só com tudo PASS; 1 com algum FAIL; 3 sem FAIL mas com etapa PARTIAL/BLOCKED. A etapa T01–T07 recebe o **pior status por teste** (o `baseline_t01_t07.py` sai com 1 para qualquer não-PASS, inclusive PARTIAL).

| Rodada | Início | T01/T02 | Duração total | Exit |
|---|---|---|---|---|
| `run-20261109-082107` | 09/11 08:21 | ×10 | ≈ 8 min | 1 registrado (ver nota) |
| `run-20261109-083135` | 09/11 08:31 | ×20 | ≈ 9 min | 3 (T04 PARTIAL) |

Nota: a rodada 1 foi feita com a primeira versão do script, que rotulava a etapa T01–T07 como FAIL só porque o T04 é PARTIAL. Por teste não houve FAIL. O status foi recalculado no JSON anexado pela mesma regra da rodada 2, com o valor original preservado (`status_registrado_pelo_orquestrador`).

Resultado anexado: [`INT-02_RESULTADOS_2026-11-09.json`](INT-02_RESULTADOS_2026-11-09.json) (status, exit, duração, contagens, frações e SHA-256 do JSON de cada verificador; hostname e pasta do usuário removidos). Os logs completos ficam em `output/int02/` (ignorado pelo Git).

## 3. Defeitos e pendências, com severidade

| ID | Sev. | Teste | Situação em 09/11 | Responsável | Encaminhamento |
|---|---|---|---|---|---|
| DEF-01 | — | T01 | **Resolvido** (#40): 30/30, contra 13/20 no CORE-10 | A | — |
| DEF-02 | — | T02 | **Resolvido** (#41): 30/30, contra 14/20 no CORE-10 | A | — |
| INT02-01 | Baixa | T04 | Tolerância numérica não acordada; maior desvio observado `0,0151` com classificação certa | A + C (T04-TOL) | Fixar a tolerância (doc 05 §2); com `|d| ≤ 0,02` o T04 passaria. Sem ela, fica PARTIAL |
| INT02-02 | **Alta** para o aceite (G3/G5) | T08–T10, T01, runtime | Rede real com dois computadores não executada no INT-02. A prova existente é a do RUN-03 (demo, só log do worker); RUN-05 `par_rede` e RUN-06 §3 seguem pendentes | B (coordenação) + C (runtime) | Roteiro da seção 5 com a equipe, numa rede local, antes da apresentação |
| INT02-03 | Média | T10 | ADR-014 (formato do Sierpinski) `EM ABERTO` | Coordenação | Decidir a proposta do T10-01 (ASCII + SVG do harness). A execução e o oráculo do T10 estão PASS |
| INT02-04 | Baixa | — | `docs/04_BACKLOG.md` e `planning/cards.json` ainda mostram o CORE-10 `IN_REVIEW` e os DEF-01/02 "abertos", embora #38, #40 e #41 estejam no `dev` | C (DOC-03) / coordenação | Atualizar o estado do CORE-10 no próximo acerto do backlog; o INT-02 não muda card de outro eixo |

Nenhum defeito novo de compilador, runtime ou interface foi encontrado nesta rodada.

## 4. T11 e CPUlator

O `verificar_t11.py` confere, além dos oráculos de stdout, que o `.arm` extraído agora é **byte a byte** igual a `tests/2026_2/test11/arm/casoN.arm` e que o SHA-256 de cada `.arm` (inclusive `extra_ldr.arm`) está em `tests/2026_2/test11/evidencias/README.md`, onde o T11-03 registrou a execução no CPUlator (capturas `casoN_cpulator.jpg`). Como os bytes não mudaram, aquela execução vale para o código atual. O INT-02 **não** abriu o CPUlator de novo.

## 5. Rede real — roteiro pendente (BLOCKED nesta rodada)

Causa do BLOCKED: só uma máquina disponível nesta execução. Pelo doc 05 §4 e pela ADR-017, loopback não substitui a prova.

Executar com dois integrantes, na mesma rede local, seguindo **só** o `runtime/README.md` §7 (que é também a reprodução pedida pelo RUN-06):

1. Nas duas máquinas, mesmo commit (`git rev-parse HEAD`) e `python main.py tests/2026_2/test08/teste8_avaliadores.minipar teste8`; anotar o SHA-256 do `teste8.exe` (§7.2).
2. Na máquina B, liberar as portas só para A e só durante o teste (§7.3) e iniciar os 4 workers (§7.4).
3. Na máquina A, rodar o coordenador com os destinos de B (§7.5). Oráculo: `TOTAL 160`, `UNICOS 160`, `DUPLICADOS 0`, `PERDIDOS 0`, `SOMA_NOTAS` igual à do `seq` na mesma carga; log de B com `TASK`/`RESULT ok` de `avaliar_lote` e os PIDs dos workers.
4. Queda de worker (§7.6): matar um worker com tarefa pendente; o coordenador deve sair com erro `WORKER_LOST`/`TIMEOUT`, sem travar.
5. Opcional: repetir o T01 com o servidor numa máquina e o cliente na outra.
6. Mascarar os logs (§7.7, `runtime/tools/mascarar_log.py`) e anexá-los em `docs/evidencias/RUN-06/`, preenchendo a seção 3 do `RUN-06_REPRODUCAO_DOIS_PCS.md`; registrar aqui o resultado (PASS/FAIL) e o link.

Até isso ser feito, o INT-02 não pode ser `DONE`.

## 6. Limitações

- Uma máquina Windows; POSIX/Linux não testado.
- Tempos dos cenários são informativos (máquina com outros processos); o benchmark formal é o RUN-05.
- A checagem visual foi feita no navegador embutido do app (Chromium), numa janela de 800×600; outros navegadores não foram testados.
- 30 execuções sem falha de T01/T02 não garantem ausência estatística de falhas em qualquer ambiente.

## 7. Verificação documental — MANDATORY

- **Verificados:** `AGENTS.md`, `MEMORY.md`, `docs/01_PLANEJAMENTO_GERAL.md`, `docs/02_CONTRATOS_TECNICOS.md` (§1–§3), `docs/04_BACKLOG.md` (ficha do INT-02), `docs/05_VALIDACAO_E_ACEITE.md`, `docs/03_DECISOES.md` (ADR-014, ADR-017), handoffs CORE-09, CORE-10, DEF-01, DEF-02, INT-01, RUN-05/06, `tests/2026_2/test11/README.md`, `web_didatica/README.md`, `runtime/README.md` §7.
- **Atualizados nesta entrega:** este documento (novo), `INT-02_RESULTADOS_2026-11-09.json` (novo), `INT-02_capturas/` (novo), `scripts/regressao_int02.py` (novo), e o estado do INT-02 em `docs/04_BACKLOG.md` e `planning/cards.json` (`IN_REVIEW`, PARTIAL pela rede real).
- **Não atualizados, com justificativa:** `README.md`, contratos, `runtime/README.md` e `web_didatica/README.md` ficam como estão, porque nenhuma API, comportamento, rota ou procedimento mudou; o INT-02 só consome interfaces. A matriz do doc 05 §7 e o estado de CORE-10/DEF-01/DEF-02 são de outros donos (coordenação e Eixo C): ficam como proposta (INT02-04) para o DOC-04/DOC-03.
- **`AGENTS.md`:** revisado; não muda, porque nenhuma regra, convenção, propriedade de arquivo ou fluxo foi alterado. O script novo segue o padrão dos verificadores já existentes em `scripts/`.

## 8. Próximos consumidores

- **Eixo A:** conferir T01–T07 e as suítes CORE-02/06/07/08/DEF-01 (seções 1 e 3); decidir T04-TOL com o C.
- **Eixo C:** conferir T08–T10 e o smoke INT-01; conduzir a rede real (seção 5) com o B.
- **DOC-04:** usar a tabela da seção 1 e o JSON anexado no relatório; citar INT02-02 enquanto a rede real não for feita.

**Declaração:** não alterei outro eixo nem `legacy/` sem autorização de CR.
