# DEF-01 — Correção do canal herdado no T01

**Eixo:** A · **Data:** 06/11/2026 · **Base:** `dev` em `bcb79ab` · **Branch:** `eixo-a/DEF-01-estabilizar-t01`

**Origem:** CORE-01 e CORE-10 (#38) · **Próximo consumidor:** INT-02 e revisão humana do Eixo A.

## Causa e correção

O T01 faz três envios consecutivos para a porta 5101, com um `receive` que abre e fecha um listener para cada mensagem. O emissor anterior repetia `connect()` no mesmo socket após falha; no Winsock, ele não podia ser reutilizado. Também descartava falhas de envio, ignorava o número de bytes transferidos e podia iniciar a mensagem seguinte enquanto o listener da anterior ainda fechava. O receptor podia ficar bloqueado em `accept()` sem limite.

Reprodução antes da mudança: `python -B scripts/baseline_t01_t07.py --only T01 --repeat 5` → **3/5 PASS, 2 timeouts de 30 s**. Evidência local: `output/core01/run-20261106-153926/baseline.json`. Nas falhas, a saída parou após os prompts, sem `Servidor recebeu`.

A primeira correção, só com novo socket por tentativa, envio completo e espera limitada, deu **17/20 PASS**, sem timeout; três execuções terminaram com falha explícita de envio/recebimento. Evidência local: `output/core01/run-20261106-154225/baseline.json`. Isso confirmou uma segunda janela: a conexão podia alcançar o listener anterior durante a troca entre mensagens. A correção final inclui confirmação de recebimento: o emissor encerra a escrita e aguarda um byte de confirmação; o receptor lê até EOF, fecha o listener, então confirma. O próximo `send` só começa depois desse ponto. O tipo de socket agora é `SOCKET` no Windows e `int` no POSIX; as operações verificam erros, os envios/leitura cobrem todos os bytes, a conexão tem prazo total de 5 s e as esperas do receptor e da confirmação têm limite de 5 s. A API MiniPar e as assinaturas públicas não mudaram. Falhas não são tratadas como sucesso.

## Validação executada

Ambiente: Windows 11, Python 3.12.4 da `.venv`, G++ UCRT64 16.2.0. Os comandos abaixo foram executados na raiz; para os dois smokes, `CXX=C:\msys64\ucrt64\bin\g++.exe` e o diretório do compilador foram colocados no `PATH` apenas do processo.

| Comando | Resultado |
|---|---|
| `python -B -m unittest tests/test_def01_channel.py` | **PASS**: listener iniciado após 350 ms, três mensagens consecutivas e payload de 10000 bytes recebido integralmente; envio sem listener falha explicitamente dentro do limite. |
| `python -B scripts/baseline_t01_t07.py --only T01 --repeat 20` | **PASS 20/20**, zero timeout; em todas as execuções, servidor recebeu `+ 2 3` e cliente recebeu `5`. Duração de execução do binário: 0,312–0,740 s. |
| `python -B scripts/baseline_t01_t07.py --only T07 --repeat 1` | **PASS** na ordenação, mutação adversarial do TAC e limites com `_GLIBCXX_ASSERTIONS`. |
| `python -B tests/2026_2/core07/verify_integration.py` | **PASS**: CLI, dois handles, worker loopback, falha do worker e integração CORE-08. |
| `python -B tests/2026_2/core08/smoke_legacy.py` | **PASS**: CLI e Web antiga. |

JSONs locais: `output/core01/run-20261106-155020/baseline.json` (T01), `output/core01/run-20261106-154818/baseline.json` (T07), `output/core07/integration/e2e.json` e `output/core08/legacy/smoke.json`. O diretório `output/` é ignorado pelo Git; os resultados observados estão registrados aqui. Uma rodada anterior, antes de limitar o `connect()`, também deu 20/20 (`run-20261106-154558`).

## Escopo, limites e handoff

Arquivos alterados: `src/cpp_template.py`, `tests/test_def01_channel.py`, `docs/02_CONTRATOS_TECNICOS.md` e este relatório. `src/codegen.py` foi inspecionado; a geração existente de `c_channel`, `send` e `receive` não exigiu mudança. Impacto de interface: **nenhum**. O transporte de Fork/Join não foi alterado.

**UNTESTED:** compilação e execução POSIX/Linux nesta rodada. **PARTIAL:** T01 usa loopback; não demonstra comunicação entre computadores. Vinte execuções sem falha não garantem ausência estatística de falhas em todo ambiente. As falhas distintas do T02 e a tolerância do T04 permanecem fora do DEF-01.

Documentos verificados: `README.md`, `AGENTS.md`, `MEMORY.md`, `docs/00_DOCUMENTO_MESTRE_INICIAL.md`, `docs/01_PLANEJAMENTO_GERAL.md`, `docs/02_CONTRATOS_TECNICOS.md`, `docs/04_BACKLOG.md`, `docs/05_VALIDACAO_E_ACEITE.md` e relatórios CORE-01/CORE-10. O contrato técnico recebeu a descrição atual do canal; os relatórios históricos foram preservados. `README.md`, backlog e matriz de aceite não precisaram de mudança porque o procedimento e os oráculos não mudaram e este relatório registra a nova medição. `AGENTS.md` não precisou mudar: nenhuma instrução, convenção, arquitetura ou fluxo de desenvolvimento foi alterado.

Revisão humana deve conferir o diff, os comandos e o resultado 20/20 antes do merge. Não marcar DONE antes do PR aprovado por revisor distinto do autor.
