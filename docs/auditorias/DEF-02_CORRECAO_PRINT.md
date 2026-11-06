# DEF-02 — Correção da saída concorrente de `print`

**Eixo:** A · **Branch:** `eixo-a/DEF-02-print-atomico` · **Base:** `origin/dev` em `d2ee3f1` (merge do PR #40/DEF-01; SHA remoto confirmado por `git ls-remote` em 06/11) · **Data:** 06/11/2026.

## Causa e correção

O gerador emitia uma sequência de operadores `<<` diretamente sobre `std::cout` para cada `PrintStmt`. Em `par`, outra thread podia escrever entre o rótulo, os argumentos e o `std::endl` de uma mesma instrução. A reprodução anterior à mudança deu **13/20 PASS** no oráculo T02 e apenas **7/20** saídas com as dez linhas exatamente íntegras; entre as saídas observadas houve `1200` e `Fatorial de 5:Fibonacci: `.

Cada `PrintStmt` agora constrói os mesmos argumentos, espaços e tipos em um `std::ostringstream` local, na mesma ordem. A escrita do conteúdo pronto e do `std::endl` ocorre dentro de um `std::lock_guard` sobre um mutex global do C++ gerado. O cabeçalho é comum aos caminhos legado e Fork/Join; o mutex sincroniza as threads de cada processo. A avaliação dos argumentos ocorre antes da aquisição do mutex, mantendo o tempo da seção crítica pequeno. A ordem entre prints de threads distintas continua livre. Nenhuma API, sintaxe, semântica de `par` ou de Fork/Join foi alterada.

## Arquivos desta entrega

- `src/codegen.py`: buffer por instrução e escrita protegida.
- `src/cpp_template.py`: inclusão de `<mutex>` e mutex compartilhado no C++ gerado.
- `tests/2026_2/core07/test_print_atomic.py`: duas branches `par`, 40 linhas com três argumentos por branch, 20 execuções nos caminhos legado e Fork/Join; confere a multiplicidade exata de cada linha, saída sequencial (espaços, booleanos, negativos e `\n` embutido), `stderr` e código de saída.
- Este registro de causa, testes e handoff.

## Validação executada

Ambiente: Windows 11; Python 3.12.4 da `.venv`; G++ UCRT64 16.2.0 (`C:\msys64\ucrt64\bin\g++.exe`). Os JSONs da baseline estão em `output/core01/` (ignorados pelo Git).

| Comando/checagem | Resultado real | Evidência |
|---|---|---|
| `python -B scripts/baseline_t01_t07.py --only T02 --repeat 20`, **antes** | 13/20 PASS, exit 1; auditoria independente do `stdout`: 7/20 com linhas exatas | `output/core01/run-20261106-163321/baseline.json` |
| `python -B -m unittest discover -s tests/2026_2/core07 -p test_print_atomic.py -v` | 2 testes PASS, 0 falhas; 20 execuções por caminho, 80 linhas concorrentes completas em cada execução | saída do unittest |
| `python -B scripts/baseline_t01_t07.py --only T02 --repeat 20`, **depois** | 20/20 PASS, exit 0; auditoria independente: 20/20 com exatamente `Fatorial de 5: 120` e `Fibonacci:` seguido de `0,1,1,2,3,5,8,13` em linhas próprias | `output/core01/run-20261106-163553/baseline.json` |
| `python -B scripts/baseline_t01_t07.py --only T01,T07 --repeat 5` | T01 5/5 PASS; T07 PASS, mutação TAC PASS, limites com `-D_GLIBCXX_ASSERTIONS` PASS; comparação com TAC histórico INFO | `output/core01/run-20261106-163707/baseline.json` |
| `python -B tests/2026_2/core07/verify_integration.py` | PASS com `CXX` e diretório UCRT64 no `PATH` do processo; CLI, dois handles, loopback, falha de worker e serviço CORE-08 | saída do smoke |
| `python -B tests/2026_2/core08/smoke_legacy.py` | PASS; CLI e Web antiga | saída do smoke |

Uma primeira tentativa do smoke CORE-07, com `CXX` definido mas sem o diretório das DLLs UCRT64 no `PATH` do subprocesso, falhou na carga do executável (`exit 3221225595`, stdout/stderr vazios). A repetição com o `PATH` configurado apenas nesse processo passou. Não houve alteração persistente do ambiente.

O teste focado confere todas as 80 linhas de cada execução por contagem exata. A auditoria T02 conferiu o texto bruto de cada tentativa, além do status do oráculo existente, que pode aceitar intercalações.

## Limitações e handoff

- Os resultados são observações desta máquina e dessas repetições; não medem uma taxa universal de falhas. Linux e outra toolchain não foram testados nesta rodada.
- O mutex é por processo: saídas de workers remotos em processos ou computadores diferentes não são ordenadas entre si. Escritas diretas em `std::cout` fora do `PrintStmt` gerado não participam desse mutex.
- T01 foi testado em loopback, sem prova entre computadores. T07 tem oráculo de TAC mutado e limites; o snapshot histórico continua apenas informativo.
- **Impacto de interface:** nenhum. Próximos consumidores: CORE-10/QA (Eixo C), INT-02 e relatório (Eixo B), após revisão do PR pelo dono da interface/consumidor. Não marcar `DONE` antes da integração e aprovação humana.

## Verificação documental

Verificados `AGENTS.md`, `MEMORY.md`, `README.md`, `docs/01_PLANEJAMENTO_GERAL.md`, `docs/02_CONTRATOS_TECNICOS.md`, `docs/04_BACKLOG.md`, `docs/05_VALIDACAO_E_ACEITE.md` e o registro CORE-10. Este documento é a atualização necessária para o comportamento corrigido e suas evidências. `README.md` permanece adequado para uso/instalação; o contrato técnico e os critérios de aceite não mudaram. Não foram alterados os documentos normativos ou o backlog, conforme ownership e a restrição de não atualizar `planning/cards.json`. `AGENTS.md` e `MEMORY.md` foram revisados e não precisam mudar: nenhuma instrução, convenção, arquitetura ou fluxo de desenvolvimento foi alterado.

**Declaração:** a entrega não alterou `runtime/`, `legacy/`, programas oficiais nem arquivos de outros eixos.
